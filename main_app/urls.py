from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PostViewSet,
    ProfileViewSet,
    ReelListView,
    ConversationViewSet,
    CommentViewSet,
    MessageViewSet,
)

router = DefaultRouter()
router.register(r"posts", PostViewSet)
router.register(r"profiles", ProfileViewSet)
router.register(r"conversations", ConversationViewSet)
router.register(r"comments", CommentViewSet)
router.register(r"messages", MessageViewSet)

urlpatterns = [
    path("reels/", ReelListView.as_view(), name="reel-list"),
    path("", include(router.urls)),
]
