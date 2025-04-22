# Claude Flask Voice Assistant

A sleek, modern Flask application that functions as a voice assistant using OpenAI's APIs for real-time transcription, voice activity detection (VAD), and text-to-speech capabilities, with Salesforce AgentForce integration.

## Features

- **Real-time Audio Processing**: Uses OpenAI's Whisper API for high-quality speech recognition
- **Voice Activity Detection (VAD)**: Automatically detects when a user is speaking
- **Text-to-Speech**: Converts AI responses to natural-sounding speech
- **Salesforce AgentForce Integration**: Routes transcribed user queries to a Salesforce AgentForce agent
- **WebSocket Communication**: Enables real-time bidirectional communication between client and server
- **Modern UI**: Clean, intuitive interface with dark/light mode
- **Customizable Settings**: Adjust voice, VAD sensitivity, and interface preferences

## Prerequisites

- Python 3.8 or higher
- An OpenAI API key with access to the relevant models (Whisper, GPT-4, and TTS)
- Salesforce AgentForce credentials (optional, for AgentForce integration)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/claude-flask-voice.git
   cd claude-flask-voice
   ```

2. Run the setup script which will:
   - Create a virtual environment
   - Install dependencies
   - Setup environment variables
   ```
   chmod +x setup.sh
   ./setup.sh
   ```

3. (Optional) Set up AgentForce integration:
   ```
   chmod +x setup_agentforce.sh
   ./setup_agentforce.sh
   ```
   Follow the prompts to enter your Salesforce AgentForce credentials.

## Usage

1. Start the application:
   ```
   ./run.py
   ```

2. Open your web browser and navigate to:
   ```
   http://localhost:8742
   ```

3. Interact with the voice assistant:
   - **Hold-to-Talk**: Press and hold the button while speaking, then release to send
   - **VAD Mode**: Toggle VAD mode to automatically detect speech
   - **Settings**: Customize the assistant's voice and interface

## Architecture

The application is built with a Flask backend and vanilla JavaScript frontend:

- **Backend**: 
  - Flask server with Socket.IO for real-time communication
  - OpenAI client for speech-to-text and text-to-speech
  - AgentForce client for intelligent responses from Salesforce

- **Frontend**: 
  - HTML, CSS, and JavaScript for a responsive UI
  - Web Audio API for client-side audio capture
  - WebSockets for streaming audio data

### Key Components

- `app.py`: Main Flask application
- `openai_client.py`: Handles communication with OpenAI's APIs
- `agentforce_client.py`: Manages communication with Salesforce AgentForce
- `audio_processor.py`: Processes audio data on both server and client
- `app.js`: Main JavaScript application
- `ui-controller.js`: Manages the user interface
- `audio-processor.js`: Handles client-side audio processing

## AgentForce Integration

This application can route user queries to a Salesforce AgentForce agent, which provides intelligent, contextual responses based on your Salesforce data. 

### Setting Up AgentForce

1. Run the AgentForce setup script:
   ```
   ./setup_agentforce.sh
   ```

2. Enter the following credentials when prompted:
   - **Server URL**: Your Salesforce login URL (e.g., `login.salesforce.com`)
   - **Client ID**: OAuth client ID from your connected app
   - **Client Secret**: OAuth client secret from your connected app
   - **Agent ID**: ID of your AgentForce agent
   - **Organization ID**: Your Salesforce organization ID

3. The credentials will be stored securely in `app/agentforce_credentials.py`.

### How It Works

1. User speaks into the microphone
2. Audio is transcribed using OpenAI's Whisper API
3. Transcription is sent to the AgentForce agent
4. Agent processes the query and returns a response
5. Response is converted to speech using OpenAI's TTS API
6. Audio response is played back to the user

### Fallback Mechanism

If AgentForce is not configured or if there's an error connecting to AgentForce, the application will automatically fall back to using OpenAI's models directly.

## Testing AgentForce Connection

You can test your AgentForce connection by visiting:
```
http://localhost:8742/api/agentforce/test
```

This will attempt to authenticate, create a session, and send a test message to your AgentForce agent.

## Limitations

- Current implementation uses a simplified approach to real-time transcription rather than the full Realtime API
- The VAD implementation is a basic approximation and may be improved with the official OpenAI Realtime API
- Best results are achieved in quiet environments with clear speech

## Future Improvements

- Implement full integration with OpenAI's Realtime API when available
- Add conversation history persistence
- Improve error handling and recovery
- Add support for multiple languages
- Implement speech generation control for more natural interactions

## License

This project is open source and available under the MIT License.

## Acknowledgements

- OpenAI for providing the APIs that power this application
- Salesforce for the AgentForce platform
- Flask and Socket.IO for enabling the real-time web functionality
