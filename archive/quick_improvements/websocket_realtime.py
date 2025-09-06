"""
Real-time WebSocket Implementation
Add to your project for live meter data updates
"""

# websocket_consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.serializers import serialize

class MeterDataConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'meter_data_live'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def meter_data_update(self, event):
        """Send meter data to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'meter_update',
            'data': event['data']
        }))

# routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/meter-data/$', consumers.MeterDataConsumer.as_asgi()),
]

# Add to settings.py
INSTALLED_APPS = [
    # ... existing apps
    'channels',
]

ASGI_APPLICATION = 'meter_dashboard.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}