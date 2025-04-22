import os
import json
import base64
import uuid
import websockets
import asyncio
from openai import OpenAI

class OpenAIClient:
    def __init__(self, api_key=None):
        """Initialize the OpenAI client with the given API key"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(api_key=self.api_key)
        self.vad_sessions = {}  # Store active VAD sessions
        
    def generate_response(self, user_message):
        """Generate a response using OpenAI's chat model"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful voice assistant. Keep your responses concise and conversational, suitable for speech."},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=150
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            raise
            
    def text_to_speech(self, text):
        """Convert text to speech using OpenAI's TTS API"""
        try:
            response = self.client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text
            )
            # Get audio data as bytes
            audio_data = response.read()
            return audio_data
        except Exception as e:
            print(f"Error in text-to-speech: {str(e)}")
            raise
    
    def process_audio(self, audio_data):
        """Process audio data with OpenAI's Whisper model"""
        try:
            response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=("audio.wav", audio_data)
            )
            return {"text": response.text}
        except Exception as e:
            print(f"Error in audio processing: {str(e)}")
            raise
            
    def create_vad_session(self):
        """Create a new VAD session"""
        try:
            session_id = str(uuid.uuid4())
            # In a production app, you would create a real session
            # with OpenAI's Realtime API here
            self.vad_sessions[session_id] = {"active": True}
            return session_id
        except Exception as e:
            print(f"Error creating VAD session: {str(e)}")
            raise
            
    def process_vad(self, session_id, audio_data):
        """Process audio with VAD"""
        # This is a simplified implementation
        # In a real app, you would use OpenAI's Realtime API
        try:
            if session_id not in self.vad_sessions:
                raise ValueError("Invalid session ID")
                
            # For demo purposes, we'll just transcribe the audio
            response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=("audio.wav", audio_data)
            )
            
            # In a real implementation, you would determine if speech is active
            # based on the VAD response from the Realtime API
            speech_active = len(response.text.strip()) > 0
            
            return {
                "speech_active": speech_active,
                "text": response.text if speech_active else ""
            }
        except Exception as e:
            print(f"Error in VAD processing: {str(e)}")
            raise
            
    async def realtime_transcription(self, audio_stream):
        """
        Process audio in real-time with the Realtime API
        
        Note: This is a placeholder for the actual implementation using
        OpenAI's Realtime API WebSocket connection
        """
        # In a real implementation, this would establish a WebSocket
        # connection to OpenAI's Realtime API and stream audio data
        pass
