from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Post, Comment, Topic, Message, Conversation


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source="user.username")
    name = serializers.ReadOnlyField(source="user.first_name")

    class Meta:
        model = Profile
        fields = [
            "id",
            "username",
            "name",
            "profile_picture_url",
            "bio",
            "location",
            "created_at",
        ]


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
        fields = ["id", "user", "body", "parent_comment", "has_replies", "created_at"]

    def get_has_replies(self, obj):
        return obj.replies.exists()


class PostSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    topics = TopicSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    likes_count = serializers.IntegerField(source="likes.count", read_only=True)

    class Meta:
        model = Post
        fields = "__all__"

    def get_user(self, obj):
        return {
            "username": obj.user.username,
            "profile_pic": obj.user.profile.profile_picture_url,
        }


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.ReadOnlyField(source="sender.username")

    class Meta:
        model = Message
        fields = ["id", "conversation", "sender", "sender_name", "content", "sent_at"]


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    participants = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ["id", "participants", "messages", "created_at"]

    def get_participants(self, obj):
        profiles = Profile.objects.filter(user__in=obj.participants.all())
        return ProfileSerializer(profiles, many=True).data
