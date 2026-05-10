from rest_framework import viewsets, permissions
from .models import Post, Profile, Topic, Comment
from .serializers import PostSerializer, ProfileSerializer


class PostViewSet(viewsets.ModelViewSet):

    queryset = Post.objects.all().order_by("-created_at")
    serializer_class = PostSerializer

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):

        serializer.save(user=self.request.user)


class ProfileViewSet(viewsets.ModelViewSet):

    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
