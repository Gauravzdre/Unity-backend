from channels.generic.websocket import AsyncWebsocketConsumer
import json
from asgiref.sync import async_to_sync, sync_to_async
from .models import Message, Guild, User
from django.core.exceptions import ObjectDoesNotExist

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_group_name = await self.get_chat_group_name() 

        await self.channel_layer.group_add(self.chat_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.chat_group_name, self.channel_name)

    async def receive(self, text_data):
        message = json.loads(text_data)
        message_obj = await self.save_message(message)

        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'chat_message',  
                'message': message, 
                'message_id': message_obj.id, # Include for acknowledgments
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event)) 

    @sync_to_async
    def save_message(self, message):
        chat_type = message['chat_type'] 
        content = message['content']

        try:
            if chat_type == 'one-on-one':
                recipient = User.objects.get(id=message['recipient_id'])  
            elif chat_type == 'guild':
                guild = Guild.objects.get(id=message['guild_id']) 
            else:  # Global chat 
                guild = None 
                recipient = None 

            message_obj = Message.objects.create(
                 sender=self.scope['user'],
                 recipient=recipient,
                 guild=guild,
                 chat_type=chat_type,
                 content=content
            )
            return message_obj

        except ObjectDoesNotExist:
            raise ValueError("Recipient or guild not found")  # Or handle appropriately


    def get_chat_group_name(self):
        chat_type = self.scope['url_route']['kwargs']['chat_type']
        if chat_type == 'one-on-one':
            user_id1 = self.scope['user'].id
            user_id2 = self.scope['url_route']['kwargs']['recipient_id'] 
            user_ids = sorted([user_id1, user_id2]) 
            return f'chat.one-on-one.{user_ids[0]}-{user_ids[1]}' 
        elif chat_type == 'guild':
            guild_id = self.scope['url_route']['kwargs']['guild_id']
            return f'chat.guild.{guild_id}' 
        else:  # Global chat
            return 'chat.global'