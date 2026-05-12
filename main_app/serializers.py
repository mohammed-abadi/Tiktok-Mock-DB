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
        extra_kwargs = {"password": {"write_only": True}}

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

        profile, created = Profile.objects.get_or_create(user=user)

        if profile_pic:
            profile.profile_picture_url = profile_pic
        else:
            profile.profile_picture_url = (
                f"https://api.dicebear.com/7.x/avataaars/svg?seed={user.username}"
            )
        profile.save()

        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "email"]
