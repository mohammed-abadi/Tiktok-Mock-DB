from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (
    PostViewSet,
    ProfileViewSet,
    ReelListView,
    ConversationViewSet,
    CommentViewSet,
    MessageViewSet,
    CreateUserView,
)

router = DefaultRouter()
router.register(r"posts", PostViewSet, basename="post")
router.register(r"profiles", ProfileViewSet)
router.register(r"conversations", ConversationViewSet, basename="conversation")
router.register(r"comments", CommentViewSet)
router.register(r"messages", MessageViewSet, basename="message")

# auth routes
urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("signup/", CreateUserView.as_view(), name="signup"),
    path("reels/", ReelListView.as_view(), name="reel-list"),
    path("", include(router.urls)),
]
