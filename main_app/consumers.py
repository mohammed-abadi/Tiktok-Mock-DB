import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Message, Conversation
from django.contrib.auth.models import User


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action", "send")
        if action == "send":
            message = data["message"]
            username = data["username"]
            room_id = data["room_id"]

            msg_id = await self.save_message(username, room_id, message)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_event",
                    "action": "send",
                    "message": message,
                    "username": username,
                    "msg_id": msg_id,
                },
            )

        elif action == "edit":
            msg_id = data["msg_id"]
            new_content = data["message"]
            await self.edit_message(msg_id, new_content)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_event",
                    "action": "edit",
                    "msg_id": msg_id,
                    "message": new_content,
                },
            )

        elif action == "delete":
            msg_id = data["msg_id"]
            await self.delete_message(msg_id)

            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "chat_event", "action": "delete", "msg_id": msg_id},
            )

    async def chat_event(self, event):
        await self.send(text_data=json.dumps(event))

    @sync_to_async
    def save_message(self, username, room_id, content):
        user = User.objects.get(username=username)
        conversation = Conversation.objects.get(id=room_id)
        msg = Message.objects.create(
            sender=user, conversation=conversation, content=content
        )
        return msg.id

    @sync_to_async
    def edit_message(self, msg_id, content):
        Message.objects.filter(id=msg_id).update(content=content, is_edited=True)

    @sync_to_async
    def delete_message(self, msg_id):
        Message.objects.filter(id=msg_id).delete()
