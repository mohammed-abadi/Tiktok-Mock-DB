import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Message, Conversation
from django.contrib.auth.models import User


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # The room name comes from the URL (routing.py)
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        # Join the room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Leave the room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receive message from WebSocket (from the React frontend)
    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data["message"]
        username = data["username"]
        room_id = data["room_id"]

        # Save to database (using sync_to_async because Django ORM is synchronous)
        await self.save_message(username, room_id, message)

        # Send message to the room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat_message", "message": message, "username": username},
        )

    # Receive message from the room group
    async def chat_message(self, event):
        message = event["message"]
        username = event["username"]

        # Send message to the actual WebSocket browser client
        await self.send(
            text_data=json.dumps({"message": message, "username": username})
        )

    @sync_to_async
    def save_message(self, username, room_id, content):
        user = User.objects.get(username=username)
        conversation = Conversation.objects.get(id=room_id)
        Message.objects.create(sender=user, conversation=conversation, content=content)
