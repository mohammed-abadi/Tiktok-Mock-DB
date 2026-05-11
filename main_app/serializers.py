from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Post, Comment, Topic, Message, Conversation


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["profile_picture_url", "bio", "location"]


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "profile"]


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.ReadOnlyField(source="sender.username")

    class Meta:
        model = Message
        fields = ["id", "conversation", "sender", "sender_name", "content", "sent_at"]


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ["id", "is_group", "messages", "created_at"]


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
    user = UserSerializer(read_only=True)
    topics = TopicSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "user",
            "media_url",
            "caption",
            "is_reel",
            "view_count",
            "created_at",
            "topics",
            "likes_count",
            "comments_count",
            "comments",
        ]

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_comments_count(self, obj):
        return obj.comments.count()
