import os
import django
import random

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MockApp.settings")
django.setup()

from django.contrib.auth.models import User
from main_app.models import Post, Profile, Topic, Comment, Conversation, Message


def seed_data():
    print("🧹 Clearing old database records...")
    User.objects.exclude(is_superuser=True).delete()
    Topic.objects.all().delete()
    Conversation.objects.all().delete()

    print("🏷️ Creating Topics...")
    topic_names = ["Coding", "Comedy", "Gaming", "Dance", "Tech"]
    topics = [Topic.objects.create(name=name) for name in topic_names]

    print("👤 Creating Advanced Users & Profiles...")
    users_data = [
        {
            "username": "TiktokDev",
            "name": "Sarah Developer",
            "email": "sarah@mockapp.com",
            "bio": "Building the next big thing! 🚀",
        },
        {
            "username": "TechGuru",
            "name": "Marcus Tech",
            "email": "marcus@mockapp.com",
            "bio": "All about tech & code. 💻",
        },
        {
            "username": "GamerPro",
            "name": "Alex Wins",
            "email": "alex@mockapp.com",
            "bio": "Leveling up daily. 🎮",
        },
        {
            "username": "DanceStar",
            "name": "Jessica Moves",
            "email": "jess@mockapp.com",
            "bio": "Catch the rhythm! 💃",
        },
    ]

    created_users = []
    for data in users_data:
        user = User.objects.create_user(
            username=data["username"],
            email=data["email"],
            first_name=data["name"],
            password="password123",
        )

        profile, _ = Profile.objects.get_or_create(user=user)
        profile.bio = data["bio"]
        profile.profile_picture_url = (
            f"https://api.dicebear.com/7.x/avataaars/svg?seed={data['username']}"
        )
        profile.save()
        created_users.append(user)

    print("🎬 Creating Viral Reels & Generating Engagement...")
    for i in range(1, 16):
        post_author = random.choice(created_users)
        post = Post.objects.create(
            user=post_author,
            caption=f"Check out my awesome video! Drop a like! 🔥 #{random.choice(topic_names).lower()}",
            media_url="https://www.w3schools.com/html/mov_bbb.mp4",
            is_reel=True,
            view_count=random.randint(100, 50000),
        )
        post.topics.add(*random.sample(topics, k=random.randint(1, 2)))

    print("\n✅ Advanced Database successfully seeded!")
    print(
        "➡️  You can log in with any of these usernames. The password for all of them is: password123"
    )


if __name__ == "__main__":
    seed_data()
