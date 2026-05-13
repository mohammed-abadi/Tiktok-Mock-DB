from django.db.models import Q
from django.contrib.auth.models import User
from rest_framework import generics, viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from .models import Post, Profile, Conversation, Message, Comment
from .serializers import (
    PostSerializer,
    ProfileSerializer,
    ConversationSerializer,
    MessageSerializer,
    CommentSerializer,
    UserSerializer,
    RegisterSerializer,
)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination for consistent feed loading.
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class CreateUserView(generics.CreateAPIView):
    """
    Handles revamped registration: Username, Email, Name, and Passwords.
    """

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class ProfileViewSet(viewsets.ModelViewSet):
    """
    Handles profile customization, viewing, and user search.
    """

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
        return queryset

    @action(
        detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )
    def me(self, request):
        """
        Custom endpoint to fetch the logged-in user's profile info.
        """
        profile, created = Profile.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    @action(
        detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def update_username(self, request):
        """
        Endpoint to change username with an availability check.
        """
        new_username = request.data.get("new_username")
        if not new_username:
            return Response(
                {"error": "New username required"}, status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(username=new_username).exists():
            return Response(
                {"error": "Username already taken"}, status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        user.username = new_username
        user.save()
        return Response(
            {"message": "Username updated successfully", "new_username": new_username}
        )


class ReelListView(generics.ListAPIView):
    """
    Specifically fetches videos marked as reels for the main feed.
    """

    queryset = Post.objects.filter(is_reel=True).order_by("-created_at")
    serializer_class = PostSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class PostViewSet(viewsets.ModelViewSet):
    """
    Handles video uploads, feed filtering, likes, favorites, and reposts.
    """

    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        queryset = Post.objects.all().order_by("-created_at")
        search = self.request.query_params.get("search")
        tag = self.request.query_params.get("tag")

        if search:
            queryset = queryset.filter(
                Q(caption__icontains=search) | Q(user__username__icontains=search)
            )
        if tag:
            queryset = queryset.filter(topics__name__icontains=tag)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def toggle_like(self, request, pk=None):
        post = self.get_object()
        if request.user in post.likes.all():
            post.likes.remove(request.user)
            return Response({"status": "unliked", "likes_count": post.likes.count()})
        post.likes.add(request.user)
        return Response({"status": "liked", "likes_count": post.likes.count()})

    @action(detail=True, methods=["post"])
    def toggle_favorite(self, request, pk=None):
        post = self.get_object()
        if request.user in post.favorites.all():
            post.favorites.remove(request.user)
            return Response({"status": "unfavorited"})
        post.favorites.add(request.user)
        return Response({"status": "favorited"})

    @action(detail=True, methods=["post"])
    def repost(self, request, pk=None):
        original = self.get_object()
        repost_post = Post.objects.create(
            user=request.user,
            media_url=original.media_url,
            caption=f"Reposted from @{original.user.username}: {original.caption}",
            is_repost=True,
            original_post=original,
        )
        return Response(
            PostSerializer(repost_post).data, status=status.HTTP_201_CREATED
        )

    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def follow(self, request, pk=None):
        """
        Custom endpoint to follow/unfollow a profile.
        """
        profile_to_follow = self.get_object()
        user_profile = request.user.profile

        if user_profile == profile_to_follow:
            return Response(
                {"error": "You cannot follow yourself"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user_profile.following.filter(id=profile_to_follow.id).exists():
            user_profile.following.remove(profile_to_follow)
            return Response({"status": "unfollowed"})

        user_profile.following.add(profile_to_follow)
        return Response({"status": "followed"})


class ConversationViewSet(viewsets.ModelViewSet):
    """
    Manages user conversations.
    """

    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user)


class CommentViewSet(viewsets.ModelViewSet):
    """
    Manages post comments.
    """

    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MessageViewSet(viewsets.ModelViewSet):
    """
    Manages individual messages within conversations.
    """

    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        return Message.objects.filter(
            conversation__participants=self.request.user
        ).order_by("sent_at")

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Optional: Allows the frontend to fetch basic details of any user.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
