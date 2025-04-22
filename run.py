#!/usr/bin/env python3
import os
import sys

# Add the current directory to sys.path to ensure app can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.app import app, socketio

if __name__ == '__main__':
    # Check if the OpenAI API key is set
    if not os.getenv('OPENAI_API_KEY'):
        print("Warning: OPENAI_API_KEY environment variable is not set.")
        print("Please set it in app/.env or as an environment variable.")
    
    port = int(os.getenv('PORT', 8742))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print(f"Starting Claude Flask Voice Assistant on port {port}...")
    socketio.run(app, debug=debug, host='0.0.0.0', port=port)
