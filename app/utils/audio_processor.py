import base64
import io
import numpy as np
import soundfile as sf
import tempfile
import wave
import os

class AudioProcessor:
    def __init__(self):
        """Initialize the AudioProcessor"""
        self.sample_rate = 16000  # Default sample rate for OpenAI's API
    
    def decode_audio(self, base64_audio):
        """Decode base64 audio data to PCM format"""
        try:
            # Decode base64 to binary
            base64_data = base64_audio.split(',')[1] if ',' in base64_audio else base64_audio
            audio_binary = base64.b64decode(base64_data)
            
            # Return the binary data directly - it's already in WAV format from the browser
            return audio_binary
        except Exception as e:
            print(f"Error decoding audio: {str(e)}")
            raise
    
    def encode_audio(self, audio_data):
        """Encode audio data to base64 for sending to the client"""
        try:
            # Encode to base64
            base64_audio = base64.b64encode(audio_data).decode('utf-8')
            return f"data:audio/mp3;base64,{base64_audio}"
        except Exception as e:
            print(f"Error encoding audio: {str(e)}")
            raise

    def convert_to_pcm16(self, audio_data, sample_rate=16000):
        """Convert audio data to PCM 16-bit format at the specified sample rate"""
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_filename = temp_file.name
                temp_file.write(audio_data)
            
            # Read with soundfile
            data, orig_sample_rate = sf.read(temp_filename)
            
            # Delete the temporary file
            os.unlink(temp_filename)
            
            # Convert to mono if stereo
            if len(data.shape) > 1:
                data = np.mean(data, axis=1)
            
            # Resample if necessary
            if orig_sample_rate != sample_rate:
                # Simple resampling
                duration = len(data) / orig_sample_rate
                target_length = int(duration * sample_rate)
                data = np.interp(
                    np.linspace(0, 1, target_length),
                    np.linspace(0, 1, len(data)),
                    data
                )
            
            # Normalize to 16-bit range
            data = np.clip(data * 32767, -32768, 32767).astype(np.int16)
            
            # Convert to bytes using wave
            buffer = io.BytesIO()
            with wave.open(buffer, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 2 bytes for 16-bit
                wf.setframerate(sample_rate)
                wf.writeframes(data.tobytes())
            
            buffer.seek(0)
            return buffer.read()
            
        except Exception as e:
            print(f"Error converting audio to PCM16: {str(e)}")
            raise
    
    # Helper method to convert base64 to audio
    def base64_to_audio(self, base64_data):
        # Remove the data URL prefix if present
        base64_string = base64_data.split(',')[1] if ',' in base64_data else base64_data
        
        # Convert base64 to binary
        binary_data = base64.b64decode(base64_string)
        
        return binary_data
    
    # Helper methods for better API compatibility with previous version
    def encode(self, blob):
        if isinstance(blob, bytes):
            base64_data = base64.b64encode(blob).decode('utf-8')
            return f"data:audio/wav;base64,{base64_data}"
        return self.encode_audio(blob)
    
    def decode(self, base64_data):
        return self.base64_to_audio(base64_data)
