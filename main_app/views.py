from django.db.models import Q
from django.contrib.auth.models import User
from rest_framework import generics, viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from .models import Post, Profile, Conversation, Message, Comment, Notification
from .serializers import (
    PostSerializer,
    ProfileSerializer,
    ConversationSerializer,
    MessageSerializer,
    CommentSerializer,
    UserSerializer,
    RegisterSerializer,
    NotificationSerializer,
)


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if hasattr(obj, "sender"):
            return obj.sender == request.user
        return getattr(obj, "user", None) == request.user


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class ProfileViewSet(viewsets.ModelViewSet):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        queryset = Profile.objects.all()
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search)
                | Q(user__first_name__icontains=search)
            )

        user_id = self.request.query_params.get("user")
        if user_id:
            queryset = queryset.filter(user__id=user_id)

        followed_by_me = self.request.query_params.get("followed_by_me")
        if followed_by_me == "true" and self.request.user.is_authenticated:
            queryset = queryset.filter(followers=self.request.user.profile)

        return queryset

    @action(
        detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )
    def me(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        return Response(self.get_serializer(profile).data)

    @action(
        detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def update_username(self, request):
        new_username = request.data.get("new_username")
        if User.objects.filter(username=new_username).exists():
            return Response({"error": "Username taken"}, status=400)
        request.user.username = new_username
        request.user.save()
        return Response({"message": "Updated"})

    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def follow(self, request, pk=None):
        profile_to_follow = self.get_object()
        user_profile = request.user.profile
        if user_profile == profile_to_follow:
            return Response({"error": "Cannot follow self"}, status=400)

        if user_profile.following.filter(id=profile_to_follow.id).exists():
            user_profile.following.remove(profile_to_follow)
            Notification.objects.filter(
                recipient=profile_to_follow.user,
                sender=request.user,
                notification_type="follow",
            ).delete()
            return Response({"status": "unfollowed"})

        user_profile.following.add(profile_to_follow)
        Notification.objects.get_or_create(
            recipient=profile_to_follow.user,
            sender=request.user,
            notification_type="follow",
        )
        return Response({"status": "followed"})

    @action(
        detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def change_password(self, request):
        user = request.user
        new_password = request.data.get("new_password")
        password_confirm = request.data.get("password_confirm")

        if not new_password or new_password != password_confirm:
            return Response(
                {"error": "Passwords do not match or are empty"}, status=400
            )

        user.set_password(new_password)
        user.save()
        return Response({"message": "Password updated successfully"})


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        queryset = Post.objects.all().order_by("-created_at")
        author = self.request.query_params.get("author")
        is_repost = self.request.query_params.get("is_repost")
        favorited_by_me = self.request.query_params.get("favorited_by_me")

        if author:
            queryset = queryset.filter(user__username=author)
        if is_repost == "true":
            queryset = queryset.filter(is_repost=True)
        elif is_repost == "false":
            queryset = queryset.filter(is_repost=False)
        if favorited_by_me == "true" and self.request.user.is_authenticated:
            queryset = queryset.filter(favorites=self.request.user)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def record_view(self, request, pk=None):
        post = self.get_object()
        if request.user not in post.viewers.all():
            post.viewers.add(request.user)
            post.view_count += 1
            post.save()
        return Response({"view_count": post.view_count})

    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def toggle_like(self, request, pk=None):
        post = self.get_object()
        if request.user in post.likes.all():
            post.likes.remove(request.user)
            Notification.objects.filter(
                recipient=post.user,
                sender=request.user,
                notification_type="like",
                post=post,
            ).delete()
            return Response({"status": "unliked", "likes_count": post.likes.count()})
        post.likes.add(request.user)
        if post.user != request.user:
            Notification.objects.get_or_create(
                recipient=post.user,
                sender=request.user,
                notification_type="like",
                post=post,
            )
        return Response({"status": "liked", "likes_count": post.likes.count()})

    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def toggle_favorite(self, request, pk=None):
        post = self.get_object()
        if request.user in post.favorites.all():
            post.favorites.remove(request.user)
            return Response({"status": "unfavorited"})
        post.favorites.add(request.user)
        return Response({"status": "favorited"})

    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def repost(self, request, pk=None):
        original = self.get_object()
        if original.is_repost and original.original_post:
            original = original.original_post

        existing = Post.objects.filter(
            user=request.user, is_repost=True, original_post=original
        ).first()
        if existing:
            existing.delete()
            Notification.objects.filter(
                recipient=original.user,
                sender=request.user,
                notification_type="repost",
                post=original,
            ).delete()
            return Response({"status": "unreposted"})

        Post.objects.create(
            user=request.user,
            media_url=original.media_url,
            caption=f"Reposted from @{original.user.username}: {original.caption}",
            is_repost=True,
            original_post=original,
        )
        if original.user != request.user:
            Notification.objects.get_or_create(
                recipient=original.user,
                sender=request.user,
                notification_type="repost",
                post=original,
            )
        return Response({"status": "reposted"})


class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user)

    @action(detail=False, methods=["post"])
    def get_or_create_direct(self, request):
        target_user_id = request.data.get("user_id")
        target_user = User.objects.get(id=target_user_id)

        convs = Conversation.objects.filter(participants=request.user).filter(
            participants=target_user
        )
        for conv in convs:
            if conv.participants.count() == 2:
                return Response(
                    ConversationSerializer(conv, context={"request": request}).data
                )

        conv = Conversation.objects.create()
        conv.participants.add(request.user, target_user)
        return Response(ConversationSerializer(conv, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def add_participant(self, request, pk=None):
        conv = self.get_object()
        user_id = request.data.get("user_id")
        user_to_add = User.objects.get(id=user_id)
        conv.participants.add(user_to_add)
        return Response(ConversationSerializer(conv, context={"request": request}).data)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        queryset = Comment.objects.all().order_by("-created_at")
        post_id = self.request.query_params.get("post")
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        return queryset

    def perform_create(self, serializer):
        comment = serializer.save(user=self.request.user)
        try:
            if comment.post.user != self.request.user:
                Notification.objects.create(
                    recipient=comment.post.user,
                    sender=self.request.user,
                    notification_type="comment",
                    post=comment.post,
                )
        except Exception as e:
            print(e)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by(
            "-created_at"
        )

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
        return Response({"unread_count": count})

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(
            is_read=True
        )
        return Response({"status": "success"})


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        qs = Message.objects.filter(
            conversation__participants=self.request.user
        ).order_by("sent_at")
        room_id = self.request.query_params.get("conversation")
        if room_id:
            qs = qs.filter(conversation_id=room_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
