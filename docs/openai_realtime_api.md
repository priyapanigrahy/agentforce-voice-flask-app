# OpenAI Realtime API Guide

This document provides information about OpenAI's Realtime API and how it's used in this project.

## Overview

The OpenAI Realtime API provides capabilities for real-time audio processing, including:

- **Real-time Transcription**: Convert speech to text as it's being spoken
- **Voice Activity Detection (VAD)**: Detect when someone is speaking
- **Real-time Response Generation**: Generate AI responses in real-time

## Realtime API Features

### WebSocket-based Streaming

The Realtime API uses WebSockets to enable bidirectional streaming of audio data:

1. Client establishes a WebSocket connection to OpenAI's Realtime endpoint
2. Client streams audio data to the server in PCM 16-bit format
3. Server processes the audio and streams back transcriptions and responses

### Voice Activity Detection (VAD)

OpenAI's Realtime API includes a VAD system that can detect:

- When someone starts speaking
- When someone stops speaking
- Speech versus background noise

This allows the application to automatically capture user speech without requiring manual button presses.

### Real-time Transcription

The API transcribes speech in real-time, providing:

- Incremental transcriptions as words are spoken
- Final transcriptions once a speech segment is complete
- Confidence scores for transcription accuracy

### Models

The Realtime API works with specific models optimized for real-time processing:

- `gpt-4o-realtime-preview`: The flagship model for real-time audio processing
- `gpt-4o-mini-realtime-preview`: A smaller, faster model for real-time applications

## Implementation Details

### Authentication

To establish a connection with the Realtime API:

1. Obtain an ephemeral API key using the OpenAI REST API
2. Use this key to establish the WebSocket connection
3. Set appropriate headers for authentication

### Audio Format Requirements

The Realtime API expects audio in a specific format:

- PCM 16-bit
- Mono (single channel)
- 16kHz sample rate
- Little-endian byte order

In our application, we configure the `AudioContext` and `MediaRecorder` to match these requirements.

### WebSocket Communication

The communication follows this pattern:

1. Client opens WebSocket connection
2. Client sends initialization message with model and other parameters
3. Server acknowledges connection
4. Client streams audio data as it's captured
5. Server sends events (transcriptions, VAD events, responses)
6. Either side can close the connection when done

### Handling the Audio Stream

On the client side, we:

1. Capture audio using the Web Audio API
2. Process audio to match the required format
3. Chunk the audio into manageable segments
4. Send audio chunks through the WebSocket connection

## Future Implementation Improvements

As OpenAI's Realtime API evolves, we plan to enhance this implementation with:

- Full streaming response generation
- More advanced VAD configurations
- Multi-turn conversation handling
- Advanced response controls for more natural interactions

## References

For more information, refer to OpenAI's official documentation:

- [Realtime API Overview](https://platform.openai.com/docs/guides/realtime)
- [Realtime WebSocket Integration](https://platform.openai.com/docs/guides/realtime-websocket)
- [Real-time Model Capabilities](https://platform.openai.com/docs/guides/realtime-model-capabilities)
