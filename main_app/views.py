from rest_framework import generics, viewsets, status
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
)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


# This handles the vertical scrolling feed for React
class ReelListView(generics.ListAPIView):
    queryset = Post.objects.filter(is_reel=True).order_by("-created_at")
    serializer_class = PostSerializer
    pagination_class = StandardResultsSetPagination


# Standard ViewSets for other features
class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

    @action(detail=True, methods=["post"])
    def toggle_like(self, request, pk=None):
        post = self.get_object()
        user = request.user

        # Check if user is authenticated (important for Render production)
        if not user.is_authenticated:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if user in post.likes.all():
            post.likes.remove(user)
            return Response(
                {"status": "unliked", "likes_count": post.likes.count()},
                status=status.HTTP_200_OK,
            )
        else:
            post.likes.add(user)
            return Response(
                {"status": "liked", "likes_count": post.likes.count()},
                status=status.HTTP_200_OK,
            )


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer


class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def perform_create(self, serializer):
        # Automatically set the user to the logged-in user when posting a comment
        serializer.save(user=self.request.user)
