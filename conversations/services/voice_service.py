import os
import asyncio
import requests
import base64
import json
import tempfile
import time
from typing import Dict, Any, BinaryIO, Optional
from django.conf import settings

# For Naver Clova API
from urllib.parse import urlencode
import hmac
import hashlib

def text_to_speech(text: str, voice_id: str = "default", speed: float = 1.0) -> Dict[str, Any]:
    """
    Convert text to speech using Naver Clova TTS API
    
    Args:
        text: Text to convert to speech
        voice_id: Voice profile ID to use
        speed: Speech speed (0.5 to 2.0)
        
    Returns:
        Dict containing audio file and metadata
    """
    try:
        # Prepare request to Naver Clova TTS API
        url = "https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts"
        
        # Map our voice_id to Naver's speaker IDs
        # Default voice mapping
        speaker_mapping = {
            "default": "nara",           # 한국어 여성 화자
            "calm_female": "nara",       # 차분한 여성
            "calm_male": "jinho",        # 차분한 남성
            "cheerful_female": "mijin",  # 명랑한 여성
            "cheerful_male": "chunghyun",# 명랑한 남성
            "empathetic_female": "dara", # 공감적인 여성
            "empathetic_male": "shinji", # 공감적인 남성
            "soothing_female": "yuna",   # 부드러운 여성
            "soothing_male": "matt"      # 부드러운 남성
        }
        
        # Use mapping or fallback to default
        speaker = speaker_mapping.get(voice_id, "nara")
        
        # Prepare request headers
        headers = {
            "X-NCP-APIGW-API-KEY-ID": settings.NAVER_CLIENT_ID,
            "X-NCP-APIGW-API-KEY": settings.NAVER_CLIENT_SECRET,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # Prepare request data
        data = {
            "speaker": speaker,
            "text": text,
            "speed": str(speed),
            "format": "mp3"
        }
        
        # Make the request
        response = requests.post(url, headers=headers, data=urlencode(data))
        
        if response.status_code == 200:
            # Create a response object
            result = {
                "audio_file": response.content,
                "content_type": "audio/mpeg",
                "duration": estimate_audio_duration(len(response.content), "mp3")
            }
            return result
        else:
            # Fallback to OpenAI TTS if Naver fails
            return text_to_speech_openai(text, voice_id, speed)
            
    except Exception as e:
        print(f"Error in text_to_speech: {e}")
        # Fallback to OpenAI TTS
        return text_to_speech_openai(text, voice_id, speed)

def text_to_speech_openai(text: str, voice_id: str = "alloy", speed: float = 1.0) -> Dict[str, Any]:
    """
    Fallback TTS using OpenAI's API
    """
    try:
        import openai
        
        # Set up OpenAI client
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Map our voice IDs to OpenAI's voice options
        voice_mapping = {
            "default": "alloy",           # 중립적
            "calm_female": "nova",        # 차분한 여성
            "calm_male": "onyx",          # 차분한 남성
            "cheerful_female": "shimmer", # 밝은 여성
            "cheerful_male": "fable",     # 밝은 중성
            "empathetic_female": "nova",  # 공감적인 여성
            "empathetic_male": "echo",    # 공감적인 중성
            "soothing_female": "shimmer", # 부드러운 여성
            "soothing_male": "onyx"       # 부드러운 남성
        }
        
        # Use mapping or fallback to default
        voice = voice_mapping.get(voice_id, "alloy")
        
        # Create speech
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
            speed=speed
        )
        
        # Get audio data
        audio_data = response.content
        
        # Create a response object
        result = {
            "audio_file": audio_data,
            "content_type": "audio/mpeg",
            "duration": estimate_audio_duration(len(audio_data), "mp3")
        }
        
        return result
        
    except Exception as e:
        print(f"Error in text_to_speech_openai: {e}")
        # Return empty audio as last resort
        return {
            "audio_file": b"",
            "content_type": "audio/mpeg",
            "duration": 0
        }

def speech_to_text(audio_file: BinaryIO, language: str = "ko-KR") -> Dict[str, Any]:
    """
    Convert speech to text using Naver Clova STT API
    
    Args:
        audio_file: Audio file to convert
        language: Language code
        
    Returns:
        Dict containing transcribed text and metadata
    """
    try:
        # Prepare request to Naver Clova STT API
        url = "https://naveropenapi.apigw.ntruss.com/recog/v1/stt"
        
        # Prepare request headers
        headers = {
            "X-NCP-APIGW-API-KEY-ID": settings.NAVER_CLIENT_ID,
            "X-NCP-APIGW-API-KEY": settings.NAVER_CLIENT_SECRET,
            "Content-Type": "application/octet-stream"
        }
        
        # Parameters
        params = {
            "lang": language
        }
        
        # Make the request
        response = requests.post(
            url, 
            headers=headers, 
            params=params,
            data=audio_file.read() if hasattr(audio_file, 'read') else audio_file
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "text": result.get("text", ""),
                "confidence": result.get("confidence", 0)
            }
        else:
            # Fallback to OpenAI Whisper if Naver fails
            return speech_to_text_openai(audio_file, language)
            
    except Exception as e:
        print(f"Error in speech_to_text: {e}")
        # Fallback to OpenAI Whisper
        return speech_to_text_openai(audio_file, language)

def speech_to_text_openai(audio_file: BinaryIO, language: str = "ko-KR") -> Dict[str, Any]:
    """
    Fallback STT using OpenAI's Whisper API
    """
    try:
        import openai
        
        # Set up OpenAI client
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Create a temporary file to save the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            # Write audio content
            if hasattr(audio_file, 'read'):
                temp_file.write(audio_file.read())
            else:
                temp_file.write(audio_file)
            
            temp_path = temp_file.name
        
        # Open the temporary file
        with open(temp_path, 'rb') as audio:
            # Transcribe using Whisper
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio,
                language=language.split('-')[0]  # OpenAI expects just 'ko' not 'ko-KR'
            )
        
        # Clean up temporary file
        os.unlink(temp_path)
        
        # Return the transcription
        return {
            "text": response.text,
            "confidence": 0.9  # OpenAI doesn't provide confidence scores
        }
        
    except Exception as e:
        print(f"Error in speech_to_text_openai: {e}")
        return {
            "text": "음성을 인식할 수 없었습니다. 다시 시도해주세요.",
            "confidence": 0
        }

def estimate_audio_duration(audio_size_bytes: int, format: str = "mp3") -> float:
    """
    Estimate audio duration based on file size
    
    Args:
        audio_size_bytes: Size of audio file in bytes
        format: Audio format (mp3, etc.)
    
    Returns:
        Estimated duration in seconds
    """
    # Very rough estimation for MP3:
    # Assuming 128 kbps bitrate, which is ~16 KB per second
    if format.lower() == "mp3":
        return audio_size_bytes / (16 * 1024)
    
    # Default fallback
    return audio_size_bytes / (16 * 1024)

async def text_to_speech_async(text: str, voice_id: str = "default", speed: float = 1.0) -> Dict[str, Any]:
    """Async wrapper for text_to_speech"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, text_to_speech, text, voice_id, speed)

async def speech_to_text_async(audio_file: BinaryIO, language: str = "ko-KR") -> Dict[str, Any]:
    """Async wrapper for speech_to_text"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, speech_to_text, audio_file, language)
