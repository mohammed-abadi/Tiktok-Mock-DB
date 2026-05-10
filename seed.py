import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MockApp.settings")
django.setup()

from django.contrib.auth.models import User
from main_app.models import Post, Profile


def seed_data():
    print("Deleting old data...")
    Post.objects.all().delete()

    print("Creating users and reels...")
    # Create a test user if it doesn't exist
    user, created = User.objects.get_or_create(username="TiktokDev")
    if created:
        user.set_password("password123")
        user.save()

    # Create 25 dummy reels
    for i in range(1, 26):
        Post.objects.create(
            user=user,
            caption=f"This is viral Reel #{i} #coding #ga",
            media_url="https://www.w3schools.com/html/mov_bbb.mp4",  # Placeholder video
            is_reel=True,
            view_count=i * 100,
        )

    print(f"Successfully seeded 25 reels for user: {user.username}")


if __name__ == "__main__":
    seed_data()
