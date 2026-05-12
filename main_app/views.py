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
)


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


class ReelListView(generics.ListAPIView):
    queryset = Post.objects.filter(is_reel=True).order_by("-created_at")
    serializer_class = PostSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class PostViewSet(viewsets.ModelViewSet):
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
            queryset = queryset.filter(caption__icontains=f"#{tag}")
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
        return Response(PostSerializer(repost_post).data, status=201)


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    @action(
        detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )
    def me(self, request):
        profile, created = Profile.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)


class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all().order_by("sent_at")
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        return Message.objects.filter(
            conversation__participants__user=self.request.user
        ).order_by("sent_at")

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)
