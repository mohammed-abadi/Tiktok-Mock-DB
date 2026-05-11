from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PostViewSet, ProfileViewSet, ReelListView, ConversationViewSet

router = DefaultRouter()
router.register(r"posts", PostViewSet)
router.register(r"profiles", ProfileViewSet)
router.register(r"conversations", ConversationViewSet)

urlpatterns = [
    # The dedicated Reels feed for your TikTok scroll
    path("reels/", ReelListView.as_view(), name="reel-list"),
    # Everything else (posts, profiles, etc.)
    path("", include(router.urls)),
]
