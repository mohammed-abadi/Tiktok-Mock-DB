from django.contrib import admin

from django.contrib import admin
from .models import Profile, Post, Topic, Comment, Conversation, Message, Participant

admin.site.register(Profile)
admin.site.register(Post)
admin.site.register(Topic)
admin.site.register(Comment)
admin.site.register(Conversation)
admin.site.register(Message)
