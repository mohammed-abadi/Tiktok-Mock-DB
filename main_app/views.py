from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from .models import Post
from .serializers import PostSerializer


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class ReelListView(generics.ListAPIView):
    queryset = Post.objects.filter(is_reel=True).order_by("-created_at")
    serializer_class = PostSerializer
    pagination_class = StandardResultsSetPagination
