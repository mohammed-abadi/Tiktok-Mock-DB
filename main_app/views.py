from rest_framework import generics, viewsets
from rest_framework.pagination import PageNumberPagination
from .models import Post, Profile, Conversation, Message
from .serializers import (
    PostSerializer,
    ProfileSerializer,
    ConversationSerializer,
    MessageSerializer,
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


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer


class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
