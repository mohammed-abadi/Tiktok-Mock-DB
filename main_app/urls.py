from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    PostViewSet,
    ProfileViewSet,
    ConversationViewSet,
    CommentViewSet,
    MessageViewSet,
    CreateUserView,
    UserViewSet,
    NotificationViewSet,
)

router = DefaultRouter()
router.register(r"posts", PostViewSet, basename="post")
router.register(r"profiles", ProfileViewSet, basename="profile")
router.register(r"conversations", ConversationViewSet, basename="conversation")
router.register(r"comments", CommentViewSet, basename="comment")
router.register(r"messages", MessageViewSet, basename="message")
router.register(r"users", UserViewSet, basename="user")
router.register(r"notifications", NotificationViewSet, basename="notification")

urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("signup/", CreateUserView.as_view(), name="signup"),
    path("", include(router.urls)),
]
