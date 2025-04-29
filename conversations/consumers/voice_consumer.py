import json
import asyncio
import base64
import tempfile
import os
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.files.base import ContentFile
from django.conf import settings

from ..models import Conversation, Message
from ..services.conversation_service import conversation_agent_async
from ..services.voice_service import text_to_speech_async, speech_to_text_async

class VoiceConversationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling real-time voice conversations
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope["user"]
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.conversation_group_name = f'conversation_{self.conversation_id}'
        
        # Check if the user has access to this conversation
        if not await self.user_has_access():
            await self.close()
            return
        
        # Join the conversation group
        await self.channel_layer.group_add(
            self.conversation_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send a welcome message
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to voice conversation'
        }))

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave the conversation group
        await self.channel_layer.group_discard(
            self.conversation_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'voice_data':
            # Process voice data (streaming audio chunks)
            await self.process_voice_data(data)
        elif message_type == 'text_message':
            # Process text message
            await self.process_text_message(data)
        elif message_type == 'voice_end':
            # End of voice stream, process the complete audio
            await self.process_voice_end(data)
        elif message_type == 'ping':
            # Respond to ping with pong to keep the connection alive
            await self.send(text_data=json.dumps({
                'type': 'pong'
            }))

    async def process_voice_data(self, data):
        """Process incoming voice data chunks"""
        # This is a streaming implementation
        # In a real application, you'd buffer the audio chunks
        audio_chunk = data.get('data')
        
        # Here we're just acknowledging receipt
        await self.send(text_data=json.dumps({
            'type': 'voice_chunk_received'
        }))

    async def process_voice_end(self, data):
        """Process complete voice data and generate a response"""
        try:
            # Get complete audio data
            audio_data = data.get('audio_data')
            
            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_data.split(',')[1] if ',' in audio_data else audio_data)
            
            # Create a temporary file for the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as audio_file:
                audio_file.write(audio_bytes)
                audio_path = audio_file.name
            
            # Convert speech to text
            text_result = await speech_to_text_async(audio_path)
            
            # Save user message to database
            user_message = await self.save_user_message(text_result['text'], 'voice')
            
            # Get conversation history
            history = await self.get_conversation_history()
            
            # Process with AI agent
            response = await conversation_agent_async(self.user, text_result['text'], history)
            
            # Save assistant message
            voice_id = data.get('voice_id', 'default')
            assistant_message = await self.save_assistant_message(
                response['content'], 
                'text', 
                voice_id,
                response.get('sentiment_score')
            )
            
            # Generate speech from text
            voice_result = await text_to_speech_async(response['content'], voice_id)
            
            # Save the voice file
            voice_url = await self.save_voice_file(
                assistant_message,
                voice_result['audio_data'],
                voice_result.get('duration', 0)
            )
            
            # Send response to WebSocket
            await self.send(text_data=json.dumps({
                'type': 'assistant_response',
                'message': {
                    'id': assistant_message.id,
                    'content': response['content'],
                    'voice_url': voice_url,
                    'created_at': assistant_message.created_at.isoformat()
                }
            }))
            
            # Clean up temporary file
            os.unlink(audio_path)
            
        except Exception as e:
            # Send error to client
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    async def process_text_message(self, data):
        """Process incoming text message and generate a response"""
        try:
            message_text = data.get('message')
            
            # Save user message to database
            user_message = await self.save_user_message(message_text, 'text')
            
            # Get conversation history
            history = await self.get_conversation_history()
            
            # Process with AI agent
            response = await conversation_agent_async(self.user, message_text, history)
            
            # Save assistant message
            voice_id = data.get('voice_id', 'default')
            assistant_message = await self.save_assistant_message(
                response['content'], 
                'text', 
                voice_id,
                response.get('sentiment_score')
            )
            
            # Generate speech from text if requested
            voice_url = None
            if data.get('generate_voice', True):
                voice_result = await text_to_speech_async(response['content'], voice_id)
                
                # Save the voice file
                voice_url = await self.save_voice_file(
                    assistant_message,
                    voice_result['audio_data'],
                    voice_result.get('duration', 0)
                )
            
            # Send response to WebSocket
            await self.send(text_data=json.dumps({
                'type': 'assistant_response',
                'message': {
                    'id': assistant_message.id,
                    'content': response['content'],
                    'voice_url': voice_url,
                    'created_at': assistant_message.created_at.isoformat()
                }
            }))
            
        except Exception as e:
            # Send error to client
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    @database_sync_to_async
    def user_has_access(self):
        """Check if the user has access to this conversation"""
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            return conversation.user == self.user
        except Conversation.DoesNotExist:
            return False

    @database_sync_to_async
    def save_user_message(self, content, content_type):
        """Save a user message to the database"""
        conversation = Conversation.objects.get(id=self.conversation_id)
        message = Message.objects.create(
            conversation=conversation,
            content=content,
            content_type=content_type,
            message_type='user'
        )
        
        # Update conversation metadata
        conversation.total_messages += 1
        conversation.save()
        
        return message

    @database_sync_to_async
    def save_assistant_message(self, content, content_type, voice_id, sentiment_score=None):
        """Save an assistant message to the database"""
        conversation = Conversation.objects.get(id=self.conversation_id)
        message = Message.objects.create(
            conversation=conversation,
            content=content,
            content_type=content_type,
            message_type='assistant',
            voice_id=voice_id,
            sentiment_score=sentiment_score
        )
        
        # Update conversation metadata
        conversation.total_messages += 1
        if sentiment_score is not None:
            # Simple rolling average for overall sentiment
            if conversation.overall_sentiment is None:
                conversation.overall_sentiment = sentiment_score
            else:
                conversation.overall_sentiment = (
                    (conversation.overall_sentiment * (conversation.total_messages - 1) + sentiment_score) / 
                    conversation.total_messages
                )
        conversation.save()
        
        return message

    @database_sync_to_async
    def get_conversation_history(self):
        """Get the conversation history"""
        conversation = Conversation.objects.get(id=self.conversation_id)
        messages = conversation.messages.all().order_by('created_at')
        
        # Limit history to a reasonable size
        messages = messages[-(settings.MAX_CONVERSATION_HISTORY or 20):]
        
        history = [
            {"role": msg.message_type, "content": msg.content}
            for msg in messages
        ]
        return history

    @database_sync_to_async
    def save_voice_file(self, message, audio_data, duration=0):
        """Save voice file for a message"""
        message.voice_file.save(
            f"voice_{message.id}.mp3",
            ContentFile(audio_data)
        )
        message.voice_duration = duration
        message.save()
        
        return message.voice_file.url
