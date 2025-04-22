import os
import json
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from dotenv import load_dotenv
from app.utils.openai_client import OpenAIClient
from app.utils.audio_processor import AudioProcessor
from app.utils.agentforce_client import AgentForceClient

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize OpenAI client
openai_client = OpenAIClient(api_key=os.getenv('OPENAI_API_KEY'))
audio_processor = AudioProcessor()

# Initialize AgentForce client
try:
    agentforce_client = AgentForceClient()
    print("AgentForce client initialized successfully")
except Exception as e:
    print(f"Warning: Could not initialize AgentForce client: {str(e)}")
    print("Voice transcription will work, but messages won't be processed by AgentForce")
    agentforce_client = None

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print('Client disconnected')

@socketio.on('audio_data')
def handle_audio_data(data):
    """Process audio data from client"""
    try:
        # Convert base64 audio data to PCM
        audio_binary = audio_processor.decode_audio(data)
        
        # Process with OpenAI's API for transcription
        transcription_response = openai_client.process_audio(audio_binary)
        transcription_text = transcription_response.get('text', '')
        
        # Send the transcription back to the client
        socketio.emit('transcription', {'text': transcription_text})
        
        # Process the transcription with AgentForce if available
        if agentforce_client and transcription_text:
            print(f"Processing transcription with AgentForce: {transcription_text}")
            agentforce_response = agentforce_client.complete_conversation(transcription_text)
            
            if agentforce_response.get('success'):
                agent_response_text = agentforce_response.get('agent_response', '')
                print(f"AgentForce response: {agent_response_text}")
                
                # Generate audio from the response
                audio_data = openai_client.text_to_speech(agent_response_text)
                
                # Send the response back to the client
                socketio.emit('chat_response', {
                    'text': agent_response_text,
                    'audio': audio_processor.encode_audio(audio_data)
                })
            else:
                error_message = agentforce_response.get('error', 'Unknown error with AgentForce')
                print(f"AgentForce error: {error_message}")
                socketio.emit('error', {'message': f"AgentForce error: {error_message}"})
        elif transcription_text:
            # If AgentForce is not available, use OpenAI directly
            print("AgentForce not available, using OpenAI instead")
            response = openai_client.generate_response(transcription_text)
            
            # Generate audio from the response
            audio_data = openai_client.text_to_speech(response)
            
            # Send the response back to the client
            socketio.emit('chat_response', {
                'text': response,
                'audio': audio_processor.encode_audio(audio_data)
            })
        
    except Exception as e:
        print(f"Error processing audio: {str(e)}")
        socketio.emit('error', {'message': str(e)})

@socketio.on('chat_request')
def handle_chat_request(data):
    """Process chat requests without audio"""
    try:
        # Get user message from the data
        user_message = data.get('message', '')
        
        if agentforce_client and user_message:
            # Process with AgentForce
            agentforce_response = agentforce_client.complete_conversation(user_message)
            
            if agentforce_response.get('success'):
                agent_response_text = agentforce_response.get('agent_response', '')
                
                # Generate audio from the response
                audio_data = openai_client.text_to_speech(agent_response_text)
                
                # Send the response back to the client
                socketio.emit('chat_response', {
                    'text': agent_response_text,
                    'audio': audio_processor.encode_audio(audio_data)
                })
            else:
                error_message = agentforce_response.get('error', 'Unknown error with AgentForce')
                socketio.emit('error', {'message': f"AgentForce error: {error_message}"})
        elif user_message:
            # If AgentForce is not available, use OpenAI directly
            response = openai_client.generate_response(user_message)
            
            # Generate audio from the response
            audio_data = openai_client.text_to_speech(response)
            
            # Send the response back to the client
            socketio.emit('chat_response', {
                'text': response,
                'audio': audio_processor.encode_audio(audio_data)
            })
        
    except Exception as e:
        print(f"Error processing chat: {str(e)}")
        socketio.emit('error', {'message': str(e)})

@socketio.on('start_vad')
def handle_start_vad():
    """Start Voice Activity Detection session"""
    try:
        session_id = openai_client.create_vad_session()
        socketio.emit('vad_session_created', {'session_id': session_id})
    except Exception as e:
        print(f"Error starting VAD session: {str(e)}")
        socketio.emit('error', {'message': str(e)})

@socketio.on('vad_audio')
def handle_vad_audio(data):
    """Process audio with VAD"""
    try:
        session_id = data.get('session_id')
        audio_binary = audio_processor.decode_audio(data.get('audio'))
        
        vad_result = openai_client.process_vad(session_id, audio_binary)
        
        # If speech is detected, also process the transcription with AgentForce
        if vad_result.get('speech_active') and vad_result.get('text'):
            transcription_text = vad_result.get('text', '')
            
            # Send the VAD result first
            socketio.emit('vad_result', vad_result)
            
            # Process with AgentForce if available
            if agentforce_client and transcription_text:
                agentforce_response = agentforce_client.complete_conversation(transcription_text)
                
                if agentforce_response.get('success'):
                    agent_response_text = agentforce_response.get('agent_response', '')
                    
                    # Generate audio from the response
                    audio_data = openai_client.text_to_speech(agent_response_text)
                    
                    # Send the response back to the client
                    socketio.emit('chat_response', {
                        'text': agent_response_text,
                        'audio': audio_processor.encode_audio(audio_data)
                    })
                else:
                    error_message = agentforce_response.get('error', 'Unknown error with AgentForce')
                    socketio.emit('error', {'message': f"AgentForce error: {error_message}"})
            elif transcription_text:
                # If AgentForce is not available, use OpenAI directly
                response = openai_client.generate_response(transcription_text)
                
                # Generate audio from the response
                audio_data = openai_client.text_to_speech(response)
                
                # Send the response back to the client
                socketio.emit('chat_response', {
                    'text': response,
                    'audio': audio_processor.encode_audio(audio_data)
                })
        else:
            # Just send the VAD result if no speech or no text
            socketio.emit('vad_result', vad_result)
    except Exception as e:
        print(f"Error processing VAD: {str(e)}")
        socketio.emit('error', {'message': str(e)})

# Endpoint to check AgentForce status
@app.route('/api/agentforce/status', methods=['GET'])
def agentforce_status():
    """Check AgentForce connection status"""
    if agentforce_client:
        status = agentforce_client.get_session_status()
        return jsonify(status)
    else:
        return jsonify({'success': False, 'error': 'AgentForce client not initialized'})

# Endpoint to test AgentForce connection
@app.route('/api/agentforce/test', methods=['POST'])
def test_agentforce():
    """Test AgentForce connection by sending a simple message"""
    try:
        if not agentforce_client:
            return jsonify({'success': False, 'error': 'AgentForce client not initialized'})
        
        # Try to authenticate
        auth_result = agentforce_client.authenticate()
        if not auth_result.get('success'):
            return jsonify(auth_result)
        
        # Try to create a session
        session_result = agentforce_client.create_session()
        if not session_result.get('success'):
            return jsonify(session_result)
        
        # Try to send a test message
        message_result = agentforce_client.send_message("Hello, this is a test message")
        return jsonify(message_result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8742))
    socketio.run(app, debug=True, host='0.0.0.0', port=port)
