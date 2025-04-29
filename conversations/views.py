import json
import os
import tempfile
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Conversation, Message, VoiceProfile, ConversationFeedback
from .serializers import (
    ConversationSerializer, ConversationListSerializer, MessageSerializer,
    VoiceProfileSerializer, ConversationFeedbackSerializer,
    TextToSpeechRequestSerializer, SpeechToTextRequestSerializer
)
from .services.conversation_service import conversation_agent
from .services.voice_service import text_to_speech, speech_to_text

# Web views
@login_required
def conversation_list_view(request):
    """View to display user's conversations"""
    conversations = Conversation.objects.filter(user=request.user)
    return render(request, 'conversations/list.html', {'conversations': conversations})

@login_required
def conversation_detail_view(request, conversation_id):
    """View to display a specific conversation"""
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    messages = conversation.messages.all()
    voice_profiles = VoiceProfile.objects.all()
    
    return render(request, 'conversations/detail.html', {
        'conversation': conversation,
        'messages': messages,
        'voice_profiles': voice_profiles
    })

@login_required
def new_conversation_view(request):
    """View to start a new conversation"""
    # Create a new conversation
    conversation = Conversation.objects.create(user=request.user, title="New Conversation")
    
    # Add a system welcome message
    Message.objects.create(
        conversation=conversation,
        content="안녕하세요! 오늘 어떻게 지내고 계신가요? 무엇을 도와드릴까요?",
        message_type="assistant",
        voice_id="default"
    )
    
    # Redirect to the conversation detail page
    return redirect('conversation_detail', conversation_id=conversation.id)

# API ViewSets
class ConversationViewSet(viewsets.ModelViewSet):
    """API endpoint for conversations"""
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ConversationListSerializer
        return ConversationSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send a message to the conversation and get a response"""
        conversation = self.get_object()
        
        # Validate message content
        content = request.data.get('content')
        content_type = request.data.get('content_type', 'text')
        voice_id = request.data.get('voice_id', 'default')
        
        if not content:
            return Response({'error': 'Message content is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Save user message
        user_message = Message.objects.create(
            conversation=conversation,
            content=content,
            content_type=content_type,
            message_type='user'
        )
        
        # Get conversation history
        messages = conversation.messages.all().order_by('created_at')
        history = [
            {"role": msg.message_type, "content": msg.content}
            for msg in messages
        ]
        
        # Get response from the conversation agent
        try:
            # Process the message with our AI agent
            response = conversation_agent(request.user, content, history)
            
            # Save the assistant response
            assistant_message = Message.objects.create(
                conversation=conversation,
                content=response['content'],
                content_type='text',
                message_type='assistant',
                sentiment_score=response.get('sentiment_score'),
                voice_id=voice_id
            )
            
            # Update conversation metadata
            conversation.total_messages += 2  # User message + Assistant message
            conversation.overall_sentiment = response.get('overall_sentiment')
            conversation.save()
            
            # Get or generate voice response if needed
            voice_file = None
            if voice_id:
                try:
                    # Generate speech from text
                    voice_result = text_to_speech(response['content'], voice_id)
                    
                    # Save the voice file
                    assistant_message.voice_file.save(
                        f"response_{assistant_message.id}.mp3",
                        voice_result['audio_file']
                    )
                    assistant_message.voice_duration = voice_result.get('duration', 0)
                    assistant_message.save()
                    
                    voice_file = assistant_message.voice_file.url
                except Exception as e:
                    print(f"Text-to-speech error: {e}")
            
            # Return both messages
            return Response({
                'user_message': MessageSerializer(user_message).data,
                'assistant_message': MessageSerializer(assistant_message).data,
                'voice_file': voice_file
            })
            
        except Exception as e:
            # Log the error
            print(f"Error processing message: {e}")
            # Return an error message
            return Response(
                {'error': 'An error occurred while processing your message'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class MessageViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for messages (read-only)"""
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Message.objects.filter(conversation__user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def conversation_messages(self, request):
        """Get messages for a specific conversation"""
        conversation_id = request.query_params.get('conversation_id')
        if not conversation_id:
            return Response({'error': 'conversation_id parameter is required'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
            messages = conversation.messages.all()
            serializer = self.get_serializer(messages, many=True)
            return Response(serializer.data)
        except Conversation.DoesNotExist:
            return Response({'error': 'Conversation not found'}, 
                           status=status.HTTP_404_NOT_FOUND)

class VoiceProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for voice profiles (read-only)"""
    queryset = VoiceProfile.objects.all()
    serializer_class = VoiceProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def sample(self, request, pk=None):
        """Get a sample of the voice profile"""
        profile = self.get_object()
        if not profile.sample_audio:
            return Response({'error': 'No sample audio available'}, 
                           status=status.HTTP_404_NOT_FOUND)
        
        return Response({'sample_url': request.build_absolute_uri(profile.sample_audio.url)})

class TextToSpeechAPIView(APIView):
    """API endpoint for text-to-speech conversion"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = TextToSpeechRequestSerializer(data=request.data)
        if serializer.is_valid():
            try:
                result = text_to_speech(
                    serializer.validated_data['text'],
                    serializer.validated_data['voice_id'],
                    serializer.validated_data['speed']
                )
                
                # Save the temporary file to a proper location
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                    temp_file.write(result['audio_file'].read())
                    temp_path = temp_file.name
                
                # Return the file as a response
                with open(temp_path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type='audio/mpeg')
                    response['Content-Disposition'] = 'attachment; filename="speech.mp3"'
                
                # Clean up the temporary file
                os.unlink(temp_path)
                
                return response
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SpeechToTextAPIView(APIView):
    """API endpoint for speech-to-text conversion"""
    permission_classes = [permissions.IsAuthenticated]
    
    @method_decorator(csrf_exempt)
    def post(self, request):
        serializer = SpeechToTextRequestSerializer(data=request.data)
        if serializer.is_valid():
            try:
                audio_file = serializer.validated_data['audio_file']
                language = serializer.validated_data['language']
                
                # Process the audio file
                result = speech_to_text(audio_file, language)
                
                return Response({
                    'text': result['text'],
                    'confidence': result.get('confidence', 0)
                })
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ConversationFeedbackViewSet(viewsets.ModelViewSet):
    """API endpoint for conversation feedback"""
    serializer_class = ConversationFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ConversationFeedback.objects.filter(conversation__user=self.request.user)
    
    def perform_create(self, serializer):
        # Ensure the conversation belongs to the user
        conversation_id = self.request.data.get('conversation')
        conversation = get_object_or_404(Conversation, id=conversation_id, user=self.request.user)
        serializer.save(conversation=conversation)
