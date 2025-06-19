# from django.test import TestCase

# # Create your tests here.
# import json
# import asyncio
# from channels.generic.websocket import AsyncWebsocketConsumer
# from channels.db import database_sync_to_async
# from django.core.cache import cache
# import logging
# from datetime import datetime, timedelta

# logger = logging.getLogger(__name__)

# class CallConsumer(AsyncWebsocketConsumer):
    
#     async def connect(self):
#         self.room_id = self.scope['url_route']['kwargs']['room_id']
#         self.room_group_name = f'call_{self.room_id}'
#         self.username = None
#         self.user_id = None
        
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
#             logger.info(f"Received message type: {event_type} from {self.username or 'unknown'}")

#             if event_type == 'join':
#                 await self.handle_join(data)
#             elif event_type == 'leave':
#                 await self.handle_leave(data)
#             elif event_type == 'status-update':
#                 await self.handle_status_update(data)
#             elif event_type == 'offer':
#                 await self.handle_webrtc_offer(data)
#             elif event_type == 'answer':
#                 await self.handle_webrtc_answer(data)
#             elif event_type == 'candidate':
#                 await self.handle_webrtc_candidate(data)
#             elif event_type == 'request-offer':
#                 await self.handle_request_offer(data)
#             elif event_type == 'screen-share-start':
#                 await self.handle_screen_share_start(data)
#             elif event_type == 'screen-share-stop':
#                 await self.handle_screen_share_stop(data)
#             elif event_type == 'ping':
#                 await self.handle_ping(data)
#             else:
#                 logger.warning(f"Unknown message type: {event_type}")
#                 await self.send_error(f"Unknown message type: {event_type}")

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
#             self.user_id = f"{self.username}_{self.channel_name}"

#             # Check if username is already taken in this room
#             participants = await self.get_room_participants()
#             existing_user = next((p for p in participants if p['username'] == self.username), None)
#             if existing_user and existing_user['channel_name'] != self.channel_name:
#                 await self.send_error("Username already taken in this room")
#                 return

#             # Add user to room
#             await self.add_user_to_room(self.username, audio, video)

#             # Get current participants and send to new user
#             participants = await self.get_room_participants()
#             await self.send(text_data=json.dumps({
#                 'type': 'participants.list',
#                 'participants': participants,
#                 'your_username': self.username
#             }))

#             # Send join confirmation
#             await self.send(text_data=json.dumps({
#                 'type': 'join.success',
#                 'username': self.username,
#                 'room_id': self.room_id
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
#             screen_share = data.get('screen_share', False)
            
#             # Update user status in room
#             await self.update_user_status(self.username, audio, video, screen_share)

#             # Broadcast status update
#             await self.channel_layer.group_send(
#                 self.room_group_name,
#                 {
#                     'type': 'status_updated_notification',
#                     'username': self.username,
#                     'audio': audio,
#                     'video': video,
#                     'screen_share': screen_share,
#                     'sender_channel': self.channel_name
#                 }
#             )

#         except Exception as e:
#             logger.error(f"Error in handle_status_update: {e}")
#             await self.send_error("Failed to update status")

#     async def handle_webrtc_offer(self, data):
#         try:
#             if not self.username:
#                 await self.send_error("Not joined to any room")
#                 return

#             target_username = data.get('target')
#             if not target_username:
#                 await self.send_error("Target username is required for offer")
#                 return

#             offer = data.get('offer')
#             if not offer:
#                 await self.send_error("Offer data is required")
#                 return

#             logger.info(f"Forwarding offer from {self.username} to {target_username}")

#             # Forward offer to specific target
#             await self.channel_layer.group_send(
#                 self.room_group_name,
#                 {
#                     'type': 'webrtc_offer_forward',
#                     'offer': offer,
#                     'sender_username': self.username,
#                     'target_username': target_username,
#                     'sender_channel': self.channel_name
#                 }
#             )

#         except Exception as e:
#             logger.error(f"Error in handle_webrtc_offer: {e}")
#             await self.send_error("Failed to process WebRTC offer")

#     async def handle_webrtc_answer(self, data):
#         try:
#             if not self.username:
#                 await self.send_error("Not joined to any room")
#                 return

#             target_username = data.get('target')
#             if not target_username:
#                 await self.send_error("Target username is required for answer")
#                 return

#             answer = data.get('answer')
#             if not answer:
#                 await self.send_error("Answer data is required")
#                 return

#             logger.info(f"Forwarding answer from {self.username} to {target_username}")

#             # Forward answer to specific target
#             await self.channel_layer.group_send(
#                 self.room_group_name,
#                 {
#                     'type': 'webrtc_answer_forward',
#                     'answer': answer,
#                     'sender_username': self.username,
#                     'target_username': target_username,
#                     'sender_channel': self.channel_name
#                 }
#             )

#         except Exception as e:
#             logger.error(f"Error in handle_webrtc_answer: {e}")
#             await self.send_error("Failed to process WebRTC answer")

#     async def handle_webrtc_candidate(self, data):
#         try:
#             if not self.username:
#                 await self.send_error("Not joined to any room")
#                 return

#             target_username = data.get('target')
#             if not target_username:
#                 await self.send_error("Target username is required for candidate")
#                 return

#             candidate = data.get('candidate')
#             if not candidate:
#                 await self.send_error("Candidate data is required")
#                 return

#             # Forward candidate to specific target
#             await self.channel_layer.group_send(
#                 self.room_group_name,
#                 {
#                     'type': 'webrtc_candidate_forward',
#                     'candidate': candidate,
#                     'sender_username': self.username,
#                     'target_username': target_username,
#                     'sender_channel': self.channel_name
#                 }
#             )

#         except Exception as e:
#             logger.error(f"Error in handle_webrtc_candidate: {e}")
#             await self.send_error("Failed to process WebRTC candidate")

#     async def handle_request_offer(self, data):
#         """Handle request to create offer for new participant"""
#         try:
#             if not self.username:
#                 await self.send_error("Not joined to any room")
#                 return

#             target_username = data.get('target')
#             if not target_username:
#                 await self.send_error("Target username is required")
#                 return

#             logger.info(f"Requesting offer from {target_username} for {self.username}")

#             # Send request to target user to create offer
#             await self.channel_layer.group_send(
#                 self.room_group_name,
#                 {
#                     'type': 'offer_request_forward',
#                     'requester_username': self.username,
#                     'target_username': target_username,
#                     'sender_channel': self.channel_name
#                 }
#             )

#         except Exception as e:
#             logger.error(f"Error in handle_request_offer: {e}")
#             await self.send_error("Failed to request offer")

#     async def handle_screen_share_start(self, data):
#         try:
#             if not self.username:
#                 await self.send_error("Not joined to any room")
#                 return

#             await self.update_user_status(self.username, 
#                                         data.get('audio', True), 
#                                         data.get('video', True), 
#                                         True)

#             # Notify others about screen share
#             await self.channel_layer.group_send(
#                 self.room_group_name,
#                 {
#                     'type': 'screen_share_started_notification',
#                     'username': self.username,
#                     'sender_channel': self.channel_name
#                 }
#             )

#         except Exception as e:
#             logger.error(f"Error in handle_screen_share_start: {e}")

#     async def handle_screen_share_stop(self, data):
#         try:
#             if not self.username:
#                 await self.send_error("Not joined to any room")
#                 return

#             await self.update_user_status(self.username, 
#                                         data.get('audio', True), 
#                                         data.get('video', True), 
#                                         False)

#             # Notify others about screen share stop
#             await self.channel_layer.group_send(
#                 self.room_group_name,
#                 {
#                     'type': 'screen_share_stopped_notification',
#                     'username': self.username,
#                     'sender_channel': self.channel_name
#                 }
#             )

#         except Exception as e:
#             logger.error(f"Error in handle_screen_share_stop: {e}")

#     async def handle_ping(self, data):
#         """Handle ping for connection health check"""
#         await self.send(text_data=json.dumps({
#             'type': 'pong',
#             'timestamp': data.get('timestamp')
#         }))

#     # Room management methods using Django cache
#     async def add_user_to_room(self, username, audio, video):
#         room_key = f"call_room_{self.room_id}"
#         room_data = cache.get(room_key, {})
        
#         room_data[self.channel_name] = {
#             'username': username,
#             'audio': audio,
#             'video': video,
#             'screen_share': False,
#             'channel_name': self.channel_name,
#             'joined_at': datetime.now().isoformat()
#         }
        
#         cache.set(room_key, room_data, timeout=7200)  # 2 hours timeout

#     async def remove_user_from_room(self):
#         room_key = f"call_room_{self.room_id}"
#         room_data = cache.get(room_key, {})
        
#         if self.channel_name in room_data:
#             del room_data[self.channel_name]
            
#             if room_data:
#                 cache.set(room_key, room_data, timeout=7200)
#             else:
#                 cache.delete(room_key)

#     async def update_user_status(self, username, audio, video, screen_share=False):
#         room_key = f"call_room_{self.room_id}"
#         room_data = cache.get(room_key, {})
        
#         if self.channel_name in room_data:
#             room_data[self.channel_name].update({
#                 'audio': audio,
#                 'video': video,
#                 'screen_share': screen_share,
#                 'last_updated': datetime.now().isoformat()
#             })
#             cache.set(room_key, room_data, timeout=7200)

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
#             'message': message,
#             'timestamp': datetime.now().isoformat()
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
#                 'video': event['video'],
#                 'screen_share': event.get('screen_share', False)
#             }))

#     async def webrtc_offer_forward(self, event):
#         # Only send to the target user
#         if (event['sender_channel'] != self.channel_name and 
#             event['target_username'] == self.username):
#             await self.send(text_data=json.dumps({
#                 'type': 'offer',
#                 'offer': event['offer'],
#                 'username': event['sender_username']
#             }))

#     async def webrtc_answer_forward(self, event):
#         # Only send to the target user
#         if (event['sender_channel'] != self.channel_name and 
#             event['target_username'] == self.username):
#             await self.send(text_data=json.dumps({
#                 'type': 'answer',
#                 'answer': event['answer'],
#                 'username': event['sender_username']
#             }))

#     async def webrtc_candidate_forward(self, event):
#         # Only send to the target user
#         if (event['sender_channel'] != self.channel_name and 
#             event['target_username'] == self.username):
#             await self.send(text_data=json.dumps({
#                 'type': 'candidate',
#                 'candidate': event['candidate'],
#                 'username': event['sender_username']
#             }))

#     async def offer_request_forward(self, event):
#         # Only send to the target user
#         if (event['sender_channel'] != self.channel_name and 
#             event['target_username'] == self.username):
#             await self.send(text_data=json.dumps({
#                 'type': 'request.offer',
#                 'requester': event['requester_username']
#             }))

#     async def screen_share_started_notification(self, event):
#         if event['sender_channel'] != self.channel_name:
#             await self.send(text_data=json.dumps({
#                 'type': 'screen.share.started',
#                 'username': event['username']
#             }))

#     async def screen_share_stopped_notification(self, event):
#         if event['sender_channel'] != self.channel_name:
#             await self.send(text_data=json.dumps({
#                 'type': 'screen.share.stopped',
#                 'username': event['username']
#             }))



# # CallConsumer ക്ലാസിന്റെ വിശദീകരണം (മലയാളത്തിൽ)

# ## പ്രധാന ഫംഗ്ഷനുകൾ:

# ### 1. connect()
# - WebSocket കണക്ഷൻ സ്ഥാപിക്കുമ്പോൾ വിളിക്കുന്ന ഫംഗ്ഷൻ
# - റൂം ഐഡി അടിസ്ഥാനമാക്കി ഒരു ഗ്രൂപ്പിൽ ചേരുന്നു
# - കണക്ഷൻ സ്വീകരിക്കുകയും ലോഗ് ചെയ്യുകയും ചെയ്യുന്നു

# ### 2. disconnect()
# - WebSocket കണക്ഷൻ അവസാനിക്കുമ്പോൾ വിളിക്കുന്ന ഫംഗ്ഷൻ
# - ഉപയോക്താവിനെ റൂമിൽ നിന്ന് നീക്കം ചെയ്യുന്നു
# - മറ്റുള്ളവർക്ക് ഉപയോക്താവ് പോയിരിക്കുന്നതിനെക്കുറിച്ച് അറിയിക്കുന്നു
# - പങ്കാളികളുടെ പട്ടിക അപ്ഡേറ്റ് ചെയ്യുന്നു

# ### 3. receive()
# - ക്ലയന്റിൽ നിന്ന് സന്ദേശം ലഭിക്കുമ്പോൾ വിളിക്കുന്ന ഫംഗ്ഷൻ
# - JSON ഡാറ്റ പാഴ്സ് ചെയ്യുകയും ടൈപ്പ് അനുസരിച്ച് ഉചിതമായ ഹാൻഡ്ലറിലേക്ക് നയിക്കുകയും ചെയ്യുന്നു

# ## ഹാൻഡ്ലർ ഫംഗ്ഷനുകൾ:

# ### 4. handle_join()
# - ഒരു ഉപയോക്താവ് റൂമിൽ ചേരാൻ ശ്രമിക്കുമ്പോൾ വിളിക്കുന്ന ഫംഗ്ഷൻ
# - യൂസർനെയിം ശരിയാണോ എന്ന് പരിശോധിക്കുന്നു
# - ഉപയോക്താവിനെ റൂമിൽ ചേർക്കുന്നു
# - നിലവിലുള്ള പങ്കാളികളുടെ പട്ടിക അയയ്ക്കുന്നു
# - മറ്റുള്ളവർക്ക് പുതിയ ഉപയോക്താവിനെക്കുറിച്ച് അറിയിക്കുന്നു

# ### 5. handle_leave()
# - ഒരു ഉപയോക്താവ് റൂം വിടുമ്പോൾ വിളിക്കുന്ന ഫംഗ്ഷൻ
# - ഉപയോക്താവിനെ റൂമിൽ നിന്ന് നീക്കം ചെയ്യുന്നു
# - മറ്റുള്ളവർക്ക് അറിയിക്കുന്നു
# - പങ്കാളികളുടെ പട്ടിക അപ്ഡേറ്റ് ചെയ്യുന്നു

# ### 6. handle_status_update()
# - ഉപയോക്താവിന്റെ സ്റ്റാറ്റസ് (ഓഡിയോ/വീഡിയോ/സ്ക്രീൻ ഷെയർ) അപ്ഡേറ്റ് ചെയ്യുമ്പോൾ വിളിക്കുന്ന ഫംഗ്ഷൻ
# - റൂം ഡാറ്റ അപ്ഡേറ്റ് ചെയ്യുന്നു
# - മറ്റുള്ളവർക്ക് സ്റ്റാറ്റസ് മാറ്റം അറിയിക്കുന്നു

# ### 7. handle_webrtc_offer(), handle_webrtc_answer(), handle_webrtc_candidate()
# - WebRTC കണക്ഷൻ സ്ഥാപിക്കുന്നതിനായി offer, answer, candidate ഡാറ്റ കൈമാറുമ്പോൾ വിളിക്കുന്ന ഫംഗ്ഷനുകൾ
# - ലക്ഷ്യം വിഭാഗത്തിലേക്ക് ഡാറ്റ ഫോർവേർഡ് ചെയ്യുന്നു

# ### 8. handle_request_offer()
# - ഒരു പുതിയ പങ്കാളിക്ക് offer ആവശ്യപ്പെടുമ്പോൾ വിളിക്കുന്ന ഫംഗ്ഷൻ
# - ലക്ഷ്യം വിഭാഗത്തിന് request അയയ്ക്കുന്നു

# ### 9. handle_screen_share_start(), handle_screen_share_stop()
# - സ്ക്രീൻ ഷെയർ ആരംഭിക്കുമ്പോഴും അവസാനിക്കുമ്പോഴും വിളിക്കുന്ന ഫംഗ്ഷനുകൾ
# - ഉപയോക്താവിന്റെ സ്റ്റാറ്റസ് അപ്ഡേറ്റ് ചെയ്യുന്നു
# - മറ്റുള്ളവർക്ക് അറിയിക്കുന്നു

# ### 10. handle_ping()
# - കണക്ഷൻ ആരോഗ്യം പരിശോധിക്കാൻ ping സന്ദേശം കൈകാര്യം ചെയ്യുന്ന ഫംഗ്ഷൻ
# - pong പ്രതികരണം അയയ്ക്കുന്നു

# ## റൂം മാനേജ്മെന്റ് ഫംഗ്ഷനുകൾ:

# ### 11. add_user_to_room(), remove_user_from_room(), update_user_status()
# - Django cache ഉപയോഗിച്ച് റൂം ഡാറ്റ മാനേജ് ചെയ്യുന്ന ഫംഗ്ഷനുകൾ
# - ഉപയോക്താക്കളെ ചേർക്കുക/നീക്കം ചെയ്യുക/അപ്ഡേറ്റ് ചെയ്യുക

# ### 12. get_room_participants(), broadcast_participants_list()
# - റൂമിലെ പങ്കാളികളുടെ പട്ടിക ലഭിക്കുകയും ബ്രോഡ്കാസ്റ്റ് ചെയ്യുകയും ചെയ്യുന്ന ഫംഗ്ഷനുകൾ

# ### 13. send_error()
# - ക്ലയന്റിലേക്ക് പിശക് സന്ദേശങ്ങൾ അയയ്ക്കുന്ന ഫംഗ്ഷൻ

# ## ഗ്രൂപ്പ് മെസ്സേജ് ഹാൻഡ്ലറുകൾ:

# ### 14. user_joined_notification(), user_left_notification()
# - പുതിയ ഉപയോക്താക്കളുടെ വരവും പോക്കും മറ്റുള്ളവർക്ക് അറിയിക്കുന്ന ഫംഗ്ഷനുകൾ

# ### 15. participants_list_update(), status_updated_notification()
# - പങ്കാളികളുടെ പട്ടികയും സ്റ്റാറ്റസ് മാറ്റങ്ങളും അപ്ഡേറ്റ് ചെയ്യുന്ന ഫംഗ്ഷനുകൾ

# ### 16. webrtc_offer_forward(), webrtc_answer_forward(), webrtc_candidate_forward()
# - WebRTC ഡാറ്റ ലക്ഷ്യം വിഭാഗത്തിലേക്ക് ഫോർവേർഡ് ചെയ്യുന്ന ഫംഗ്ഷനുകൾ

# ### 17. screen_share_started_notification(), screen_share_stopped_notification()
# - സ്ക്രീൻ ഷെയർ ആരംഭിക്കുകയോ നിർത്തുകയോ ചെയ്യുന്നത് മറ്റുള്ളവർക്ക് അറിയിക്കുന്ന ഫംഗ്ഷനുകൾ

# ഈ കോഡ് ഒരു WebSocket-ആധാരിതമായ വീഡിയോ കോൾ സിസ്റ്റത്തിന്റെ ബാക്കെൻഡ് ഭാഗമാണ്, ഇത് Django Channels ഉപയോഗിച്ച് നിർമ്മിച്ചിരിക്കുന്നു. ഇത് റൂം-ബേസ്ഡ് കമ്മ്യൂണിക്കേഷനും WebRTC സിഗ്നലിംഗും നിയന്ത്രിക്കുന്നു.