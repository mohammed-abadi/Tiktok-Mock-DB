from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Post, Comment, Topic, Message, Conversation, Notification


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source="user.username")
    name = serializers.ReadOnlyField(source="user.first_name")
    user_id = serializers.ReadOnlyField(source="user.id")
    followers_count = serializers.IntegerField(source="followers.count", read_only=True)
    following_count = serializers.IntegerField(source="following.count", read_only=True)
    is_followed_by_me = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            "id",
            "user_id",
            "username",
            "name",
            "profile_picture_url",
            "bio",
            "location",
            "followers_count",
            "following_count",
            "is_followed_by_me",
            "created_at",
        ]

    def get_is_followed_by_me(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.followers.filter(id=request.user.profile.id).exists()
        return False


class RegisterSerializer(serializers.ModelSerializer):
    password_confirm = serializers.CharField(write_only=True)
    name = serializers.CharField(source="first_name", required=True)
    email = serializers.EmailField(required=True)
    profile_picture_url = serializers.URLField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "name",
            "password",
            "password_confirm",
            "profile_picture_url",
        ]

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        if User.objects.filter(email=data["email"]).exists():
            raise serializers.ValidationError(
                {"email": "This email is already in use."}
            )
        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        profile_pic = validated_data.pop("profile_picture_url", "")
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            first_name=validated_data.get("first_name", ""),
            password=validated_data["password"],
        )
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.profile_picture_url = (
            profile_pic
            or f"https://api.dicebear.com/7.x/avataaars/svg?seed={user.username}"
        )
        profile.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "email"]


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ["id", "name"]


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    has_replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "user",
            "post",
            "body",
            "parent_comment",
            "has_replies",
            "created_at",
        ]

    def get_has_replies(self, obj):
        return obj.replies.exists()


class PostSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    topics = TopicSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    likes_count = serializers.IntegerField(source="likes.count", read_only=True)
    favorites_count = serializers.IntegerField(source="favorites.count", read_only=True)
    comments_count = serializers.IntegerField(source="comments.count", read_only=True)

    class Meta:
        model = Post
        fields = "__all__"

    def get_user(self, obj):
        try:
            profile_url = obj.user.profile.profile_picture_url
            profile_id = obj.user.profile.id
        except Exception:
            profile_url = ""
            profile_id = None
        return {
            "id": obj.user.id,
            "profile_id": profile_id,
            "username": obj.user.username,
            "profile_picture_url": profile_url,
        }


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.ReadOnlyField(source="sender.username")

    class Meta:
        model = Message
        fields = [
            "id",
            "conversation",
            "sender",
            "sender_name",
            "content",
            "sent_at",
            "is_edited",
        ]


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    participants = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ["id", "participants", "messages", "created_at"]

    def get_participants(self, obj):
        profiles = Profile.objects.filter(user__in=obj.participants.all())
        return ProfileSerializer(profiles, many=True, context=self.context).data


class NotificationSerializer(serializers.ModelSerializer):
    sender_name = serializers.ReadOnlyField(source="sender.username")
    sender_avatar = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "recipient",
            "sender",
            "sender_name",
            "sender_avatar",
            "notification_type",
            "post",
            "created_at",
            "is_read",
        ]

    def get_sender_avatar(self, obj):
        try:
            return obj.sender.profile.profile_picture_url
        except Exception:
            return f"https://ui-avatars.com/api/?name={obj.sender.username}"
