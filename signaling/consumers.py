# import json
# import asyncio
# from channels.generic.websocket import AsyncWebsocketConsumer
# from channels.db import database_sync_to_async
# from django.core.cache import cache
# import logging

# logger = logging.getLogger(__name__)

# class CallConsumer(AsyncWebsocketConsumer):
    
#     async def connect(self):
#         self.room_id = self.scope['url_route']['kwargs']['room_id']
#         self.room_group_name = f'call_{self.room_id}'
#         self.username = None
        
#         # Join room group
#         await self.channel_layer.group_add(self.room_group_name, self.channel_name)
#         await self.accept()
#         logger.info(f"WebSocket connected: {self.channel_name} to room {self.room_id}")

#     async def disconnect(self, close_code):
#         logger.info(f"WebSocket disconnected: {self.channel_name}, code: {close_code}")
        
#         try:
#             # Remove user from room
#             if self.username:
#                 await self.remove_user_from_room()
                
#                 # Notify others about user leaving
#                 await self.channel_layer.group_send(
#                     self.room_group_name,
#                     {
#                         'type': 'user_left_notification',
#                         'username': self.username,
#                         'sender_channel': self.channel_name
#                     }
#                 )
                
#                 # Send updated participant list
#                 await self.broadcast_participants_list()
                
#         except Exception as e:
#             logger.error(f"Error during disconnect: {e}")
#         finally:
#             # Leave room group
#             await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

#     async def receive(self, text_data):
#         try:
#             data = json.loads(text_data)
#             event_type = data.get('type')
#             logger.info(f"Received message type: {event_type} from {self.channel_name}")

#             if event_type == 'join':
#                 await self.handle_join(data)
#             elif event_type == 'leave':
#                 await self.handle_leave(data)
#             elif event_type == 'status-update':
#                 await self.handle_status_update(data)
#             elif event_type in ['offer', 'answer', 'candidate']:
#                 await self.handle_webrtc_signal(data)
#             else:
#                 logger.warning(f"Unknown message type: {event_type}")

#         except json.JSONDecodeError as e:
#             logger.error(f"JSON decode error: {e}")
#             await self.send_error("Invalid JSON format")
#         except Exception as e:
#             logger.error(f"Error processing message: {e}")
#             await self.send_error("Internal server error")

#     async def handle_join(self, data):
#         try:
#             username = data.get('username')
#             audio = data.get('audio', True)
#             video = data.get('video', True)

#             if not username or not username.strip():
#                 await self.send_error("Username is required")
#                 return

#             self.username = username.strip()

#             # Add user to room
#             await self.add_user_to_room(self.username, audio, video)

#             # Get current participants and send to new user
#             participants = await self.get_room_participants()
#             await self.send(text_data=json.dumps({
#                 'type': 'participants.list',
#                 'participants': participants
#             }))

#             # Notify others about the new user
#             await self.channel_layer.group_send(
#                 self.room_group_name,
#                 {
#                     'type': 'user_joined_notification',
#                     'username': self.username,
#                     'audio': audio,
#                     'video': video,
#                     'sender_channel': self.channel_name
#                 }
#             )

#             logger.info(f"User {self.username} joined room {self.room_id}")

#         except Exception as e:
#             logger.error(f"Error in handle_join: {e}")
#             await self.send_error("Failed to join room")

#     async def handle_leave(self, data):
#         try:
#             if self.username:
#                 await self.remove_user_from_room()
                
#                 # Notify others
#                 await self.channel_layer.group_send(
#                     self.room_group_name,
#                     {
#                         'type': 'user_left_notification',
#                         'username': self.username,
#                         'sender_channel': self.channel_name
#                     }
#                 )
                
#                 await self.broadcast_participants_list()
#                 logger.info(f"User {self.username} left room {self.room_id}")
                
#             await self.close()
            
#         except Exception as e:
#             logger.error(f"Error in handle_leave: {e}")

#     async def handle_status_update(self, data):
#         try:
#             if not self.username:
#                 await self.send_error("Not joined to any room")
#                 return

#             audio = data.get('audio', True)
#             video = data.get('video', True)
            
#             # Update user status in room
#             await self.update_user_status(self.username, audio, video)

#             # Broadcast status update
#             await self.channel_layer.group_send(
#                 self.room_group_name,
#                 {
#                     'type': 'status_updated_notification',
#                     'username': self.username,
#                     'audio': audio,
#                     'video': video,
#                     'sender_channel': self.channel_name
#                 }
#             )

#         except Exception as e:
#             logger.error(f"Error in handle_status_update: {e}")
#             await self.send_error("Failed to update status")

#     async def handle_webrtc_signal(self, data):
#         try:
#             if not self.username:
#                 await self.send_error("Not joined to any room")
#                 return

#             # Forward WebRTC signaling to other participants
#             await self.channel_layer.group_send(
#                 self.room_group_name,
#                 {
#                     'type': 'webrtc_signal_forward',
#                     'signal_data': data,
#                     'sender_channel': self.channel_name,
#                     'sender_username': self.username,
#                     'target_username': data.get('target')  # Add target username
#                 }
#             )
#         except Exception as e:
#             logger.error(f"Error in handle_webrtc_signal: {e}")
#             await self.send_error("Failed to process WebRTC signal")

#     # Room management methods using Django cache
#     async def add_user_to_room(self, username, audio, video):
#         room_key = f"call_room_{self.room_id}"
#         room_data = cache.get(room_key, {})
        
#         room_data[self.channel_name] = {
#             'username': username,
#             'audio': audio,
#             'video': video,
#             'channel_name': self.channel_name
#         }
        
#         cache.set(room_key, room_data, timeout=3600)  # 1 hour timeout

#     async def remove_user_from_room(self):
#         room_key = f"call_room_{self.room_id}"
#         room_data = cache.get(room_key, {})
        
#         if self.channel_name in room_data:
#             del room_data[self.channel_name]
            
#             if room_data:
#                 cache.set(room_key, room_data, timeout=3600)
#             else:
#                 cache.delete(room_key)

#     async def update_user_status(self, username, audio, video):
#         room_key = f"call_room_{self.room_id}"
#         room_data = cache.get(room_key, {})
        
#         if self.channel_name in room_data:
#             room_data[self.channel_name].update({
#                 'audio': audio,
#                 'video': video
#             })
#             cache.set(room_key, room_data, timeout=3600)

#     async def get_room_participants(self):
#         room_key = f"call_room_{self.room_id}"
#         room_data = cache.get(room_key, {})
#         return list(room_data.values())

#     async def broadcast_participants_list(self):
#         participants = await self.get_room_participants()
#         await self.channel_layer.group_send(
#             self.room_group_name,
#             {
#                 'type': 'participants_list_update',
#                 'participants': participants,
#                 'sender_channel': self.channel_name
#             }
#         )

#     async def send_error(self, message):
#         await self.send(text_data=json.dumps({
#             'type': 'error',
#             'message': message
#         }))

#     # Group message handlers
#     async def user_joined_notification(self, event):
#         if event['sender_channel'] != self.channel_name:
#             await self.send(text_data=json.dumps({
#                 'type': 'user.joined',
#                 'username': event['username'],
#                 'audio': event['audio'],
#                 'video': event['video']
#             }))

#     async def user_left_notification(self, event):
#         if event['sender_channel'] != self.channel_name:
#             await self.send(text_data=json.dumps({
#                 'type': 'user.left',
#                 'username': event['username']
#             }))

#     async def participants_list_update(self, event):
#         if event['sender_channel'] != self.channel_name:
#             await self.send(text_data=json.dumps({
#                 'type': 'participants.update',
#                 'participants': event['participants']
#             }))

#     async def status_updated_notification(self, event):
#         if event['sender_channel'] != self.channel_name:
#             await self.send(text_data=json.dumps({
#                 'type': 'status.updated',
#                 'username': event['username'],
#                 'audio': event['audio'],
#                 'video': event['video']
#             }))

#     async def webrtc_signal_forward(self, event):
#         if (event['sender_channel'] != self.channel_name and 
#             (not event.get('target_username') or 
#             event['target_username'] == self.username)):
#             signal_data = event['signal_data']
#             signal_data['username'] = event['sender_username']
#             await self.send(text_data=json.dumps(signal_data))







import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache
import logging
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import base64

logger = logging.getLogger(__name__)

class CallConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling video calls with end-to-end encryption.
    Manages room participants, WebRTC signaling, and encryption key exchange.
    """
    
    async def connect(self):
        """Handle new WebSocket connection with encryption setup"""
        try:
            self.room_id = self.scope['url_route']['kwargs']['room_id']
            self.room_group_name = f'call_{self.room_id}'
            self.username = None
            
            # Generate RSA key pair for this connection
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            self.public_key = self.private_key.public_key()
            
            # Join room group
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
            logger.info(f"WebSocket connected: {self.channel_name} to room {self.room_id}")
            
        except Exception as e:
            logger.error(f"Connection error: {e}")
            await self.close(code=4001)

    async def disconnect(self, close_code):
        """Clean up on WebSocket disconnect"""
        logger.info(f"WebSocket disconnected: {self.channel_name}, code: {close_code}")
        
        try:
            if self.username:
                await self.remove_user_from_room()
                await self.notify_user_left()
                await self.broadcast_participants_list()
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
        finally:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            event_type = data.get('type')
            logger.debug(f"Received {event_type} from {self.channel_name}")

            handler = {
                'join': self.handle_join,
                'leave': self.handle_leave,
                'status-update': self.handle_status_update,
                'offer': self.handle_webrtc_signal,
                'answer': self.handle_webrtc_signal,
                'candidate': self.handle_webrtc_signal,
                'public_key': self.handle_public_key,
            }.get(event_type)

            if handler:
                await handler(data)
            else:
                logger.warning(f"Unknown message type: {event_type}")
                await self.send_error("Unknown message type")

        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
            await self.send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"Message handling error: {e}")
            await self.send_error("Internal server error")

    async def handle_join(self, data):
        """Process join request from client"""
        try:
            username = data.get('username', '').strip()
            if not username:
                await self.send_error("Username is required")
                return

            self.username = username
            public_key_jwk = data.get('public_key')

            # Add user to room with media status
            await self.add_user_to_room(
                username,
                data.get('audio', True),
                data.get('video', True),
                public_key_jwk
            )

            # Send current participants to new user
            participants = await self.get_room_participants()
            await self.send_participants_list(participants)

            # Notify others about new user
            await self.notify_user_joined()
            logger.info(f"User {username} joined room {self.room_id}")

        except Exception as e:
            logger.error(f"Join error: {e}")
            await self.send_error("Failed to join room")

    async def handle_leave(self, data):
        """Process leave request from client"""
        try:
            if self.username:
                await self.remove_user_from_room()
                await self.notify_user_left()
                await self.broadcast_participants_list()
                logger.info(f"User {self.username} left room {self.room_id}")
            
            await self.close()
        except Exception as e:
            logger.error(f"Leave error: {e}")

    async def handle_status_update(self, data):
        """Update user's audio/video status"""
        try:
            if not self.username:
                await self.send_error("Not joined to any room")
                return

            await self.update_user_status(
                self.username,
                data.get('audio', True),
                data.get('video', True)
            )
            await self.notify_status_update()
            
        except Exception as e:
            logger.error(f"Status update error: {e}")
            await self.send_error("Failed to update status")

    async def handle_webrtc_signal(self, data):
        """Forward WebRTC signaling messages to target user"""
        try:
            if not self.username:
                await self.send_error("Not joined to any room")
                return

            target = data.get('target')
            if not target:
                logger.warning("No target specified for WebRTC signal")
                return

            # Forward the signal to the target user
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'forward_signal',
                    'signal_data': data,
                    'sender_channel': self.channel_name,
                    'sender_username': self.username,
                    'target_username': target
                }
            )
        except Exception as e:
            logger.error(f"WebRTC signal error: {e}")
            await self.send_error("Failed to process WebRTC signal")

    async def handle_public_key(self, data):
        """Handle public key exchange between peers"""
        try:
            sender = data.get('from')
            target = data.get('target')
            key_jwk = data.get('key')

            if not all([sender, target, key_jwk]):
                logger.warning("Invalid public key message")
                return

            # Forward the public key to the target user
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'forward_signal',
                    'signal_data': {
                        'type': 'public_key',
                        'from': sender,
                        'key': key_jwk
                    },
                    'sender_channel': self.channel_name,
                    'sender_username': sender,
                    'target_username': target
                }
            )
        except Exception as e:
            logger.error(f"Public key exchange error: {e}")

    # Room management methods
    async def add_user_to_room(self, username, audio, video, public_key=None):
        """Add user to room cache with their status"""
        room_key = f"call_room_{self.room_id}"
        room_data = cache.get(room_key, {})
        
        room_data[self.channel_name] = {
            'username': username,
            'audio': audio,
            'video': video,
            'channel_name': self.channel_name,
            'public_key': public_key
        }
        
        cache.set(room_key, room_data, timeout=3600)

    async def remove_user_from_room(self):
        """Remove user from room cache"""
        room_key = f"call_room_{self.room_id}"
        room_data = cache.get(room_key, {})
        
        if self.channel_name in room_data:
            del room_data[self.channel_name]
            cache.set(room_key, room_data, timeout=3600) if room_data else cache.delete(room_key)

    async def update_user_status(self, username, audio, video):
        """Update user's media status in room cache"""
        room_key = f"call_room_{self.room_id}"
        room_data = cache.get(room_key, {})
        
        if self.channel_name in room_data:
            room_data[self.channel_name].update({
                'audio': audio,
                'video': video
            })
            cache.set(room_key, room_data, timeout=3600)

    async def get_room_participants(self):
        """Get current list of room participants"""
        room_key = f"call_room_{self.room_id}"
        return list(cache.get(room_key, {}).values())

    # Notification methods
    async def notify_user_joined(self):
        """Notify room about new user"""
        user_data = cache.get(f"call_room_{self.room_id}", {}).get(self.channel_name, {})
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'username': self.username,
                'audio': user_data.get('audio', True),
                'video': user_data.get('video', True),
                'sender_channel': self.channel_name
            }
        )

    async def notify_user_left(self):
        """Notify room about user leaving"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'username': self.username,
                'sender_channel': self.channel_name
            }
        )

    async def notify_status_update(self):
        """Notify room about status change"""
        user_data = cache.get(f"call_room_{self.room_id}", {}).get(self.channel_name, {})
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'status_updated',
                'username': self.username,
                'audio': user_data.get('audio', True),
                'video': user_data.get('video', True),
                'sender_channel': self.channel_name
            }
        )

    async def broadcast_participants_list(self):
        """Send updated participants list to all users"""
        participants = await self.get_room_participants()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'participants_list',
                'participants': participants,
                'sender_channel': self.channel_name
            }
        )

    async def send_participants_list(self, participants):
        """Send participants list to single user"""
        await self.send(text_data=json.dumps({
            'type': 'participants',
            'participants': participants
        }))

    async def send_error(self, message):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))

    # Message handlers
    async def user_joined(self, event):
        """Handle user joined notification"""
        if event['sender_channel'] != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'user_joined',
                'username': event['username'],
                'audio': event['audio'],
                'video': event['video']
            }))

    async def user_left(self, event):
        """Handle user left notification"""
        if event['sender_channel'] != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'user_left',
                'username': event['username']
            }))

    async def status_updated(self, event):
        """Handle status update notification"""
        if event['sender_channel'] != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'status_updated',
                'username': event['username'],
                'audio': event['audio'],
                'video': event['video']
            }))

    async def participants_list(self, event):
        """Handle participants list update"""
        if event['sender_channel'] != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'participants',
                'participants': event['participants']
            }))

    async def forward_signal(self, event):
        """Forward signaling message to target user"""
        if (event['sender_channel'] != self.channel_name and 
            event.get('target_username') == self.username):
            signal_data = event['signal_data']
            signal_data['from'] = event['sender_username']
            await self.send(text_data=json.dumps(signal_data))