# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.group_name = f'user_{self.user_id}'
        
        print(f"WebSocket connected for user {self.user_id}")  # Debug
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        print(f"WebSocket disconnected for user {self.user_id}")  # Debug

    async def send_notification(self, event):
        # Remove the 'notification' key from event
        try:
            print(f"Sending notification: {event}")  # Debug
            await self.send(text_data=json.dumps({
                "id": event["id"],
                "title": event["title"],
                "message": event["message"],
                "timetable_id": event["timetable_id"],
                "created_at": event["created_at"],
                "is_read": event.get("is_read", False)
            }))
        except Exception as e:
            print(f"Error sending notification: {e}")  # Debug