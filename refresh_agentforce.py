#!/usr/bin/env python3
"""
Refresh AgentForce Token and Session

This script refreshes the AgentForce authentication token and creates a new session,
updating the stored values in agentforce_credentials.py.

Usage:
    python refresh_agentforce.py [options]

Options:
    --force, -f       Force token refresh even if the current token might still be valid
    --verbose, -v     Show detailed output during the process
    --test, -t        Send a test message after refreshing to verify everything works
    --help, -h        Show this help message
"""

import os
import sys
import json
import time
import argparse
import importlib.util
from pathlib import Path

# Function to import agentforce_credentials from its file path
def import_credentials_module(file_path):
    if not os.path.exists(file_path):
        print(f"Error: Credentials file not found at {file_path}")
        print("Please run setup_agentforce.sh first to set up your credentials.")
        sys.exit(1)
    
    spec = importlib.util.spec_from_file_location("agentforce_credentials", file_path)
    af_creds = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(af_creds)
    return af_creds

# Function to update values in the credentials file
def update_credentials_file(file_path, access_token, instance_url, session_id, sequence_id=1):
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Update the values using string replacement
    if 'ACCESS_TOKEN = ' in content:
        content = update_value(content, 'ACCESS_TOKEN = ', f'ACCESS_TOKEN = "{access_token}"')
    else:
        # If the value doesn't exist, add it at the end
        content += f'\nACCESS_TOKEN = "{access_token}"\n'
    
    if 'INSTANCE_URL = ' in content:
        content = update_value(content, 'INSTANCE_URL = ', f'INSTANCE_URL = "{instance_url}"')
    else:
        content += f'INSTANCE_URL = "{instance_url}"\n'
    
    if 'SESSION_ID = ' in content:
        content = update_value(content, 'SESSION_ID = ', f'SESSION_ID = "{session_id}"')
    else:
        content += f'SESSION_ID = "{session_id}"\n'
    
    if 'SEQUENCE_ID = ' in content:
        content = update_value(content, 'SEQUENCE_ID = ', f'SEQUENCE_ID = {sequence_id}')
    else:
        content += f'SEQUENCE_ID = {sequence_id}\n'
    
    with open(file_path, 'w') as file:
        file.write(content)

def update_value(content, marker, new_value):
    """Update a value in the content string"""
    start_index = content.find(marker)
    if start_index == -1:
        return content
    
    start_index += len(marker)
    line_end = content.find('\n', start_index)
    
    # If there's no newline after the marker, we're at the end of the file
    if line_end == -1:
        line_end = len(content)
    
    return content[:start_index] + new_value.split('=')[1].strip() + content[line_end:]

def refresh_token(af_creds, verbose=False):
    """Refresh the AgentForce access token"""
    import requests
    
    print("Refreshing AgentForce access token...")
    
    # Build the token URL
    token_url = f'https://{af_creds.SERVER_URL}/services/oauth2/token'
    
    # Prepare request body
    request_body = {
        'grant_type': 'client_credentials',
        'client_id': af_creds.CLIENT_ID,
        'client_secret': af_creds.CLIENT_SECRET
    }
    
    print(f"Requesting token from: {token_url}")
    print(f"Using client ID: {af_creds.CLIENT_ID[:10]}...{af_creds.CLIENT_ID[-5:]}")
    
    try:
        # Make the HTTP request
        response = requests.post(
            token_url,
            data=request_body,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=30
        )
        
        # Handle the response
        if response.status_code == 200:
            # Parse the response
            token_data = response.json()
            
            if verbose:
                print("Token response received:")
                print(json.dumps(token_data, indent=2))
            else:
                print("Token response received")
            
            # Extract the access token and instance URL
            access_token = token_data.get('access_token')
            instance_url = token_data.get('instance_url')
            
            if not access_token:
                print("Error: No access token in response")
                print(f"Response: {response.text}")
                return None, None
            
            print(f"Successfully obtained new access token: {access_token[:10]}...{access_token[-5:]}")
            print(f"Instance URL: {instance_url}")
            
            return access_token, instance_url
        else:
            # Handle error response
            print(f"Error getting access token: {response.status_code} {response.reason}")
            print(f"Response: {response.text}")
            return None, None
        
    except Exception as e:
        print(f"Exception during authentication: {str(e)}")
        return None, None

def create_session(af_creds, access_token, instance_url, verbose=False):
    """Create a new AgentForce session"""
    import requests
    import uuid
    
    print("Creating new AgentForce session...")
    
    # Build the session creation URL - corrected to use the Einstein API endpoint
    session_url = f'{instance_url}/services/data/v59.0/einstein/ai-agent/agents/{af_creds.AGENT_ID}/sessions'
    
    print(f"Using Agent ID: {af_creds.AGENT_ID}")
    print(f"Creating session at: {session_url}")
    
    # Generate a random UUID for external session key
    random_uuid = str(uuid.uuid4())
    
    # Prepare request body
    request_body = {
        'externalSessionKey': random_uuid,
        'instanceConfig': {
            'endpoint': instance_url
        },
        'bypassUser': True
    }
    
    print(f"Request body: {json.dumps(request_body, indent=2)}")
    
    try:
        # Make the HTTP request
        response = requests.post(
            session_url,
            json=request_body,
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            },
            timeout=30
        )
        
        # Print response details
        print(f"Response status: {response.status_code} {response.reason}")
        
        # Handle the response
        if response.status_code in [200, 201]:
            # Parse the response
            session_data = response.json()
            
            print("Session response received:")
            print(json.dumps(session_data, indent=2))
            
            # Extract the session ID
            session_id = session_data.get('sessionId')
            
            if not session_id:
                print("Error: No session ID in response")
                print(f"Response: {response.text}")
                return None
            
            print(f"Successfully created new session: {session_id}")
            
            return session_id
        else:
            # Handle error response
            print(f"Error creating session: {response.status_code} {response.reason}")
            print(f"Response: {response.text}")
            
            # Try an alternative URL
            print("Trying alternative URL format...")
            alt_session_url = f'https://api.salesforce.com/einstein/ai-agent/v1/agents/{af_creds.AGENT_ID}/sessions'
            print(f"Alternative URL: {alt_session_url}")
            
            alt_response = requests.post(
                alt_session_url,
                json=request_body,
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                },
                timeout=30
            )
            
            print(f"Alternative response status: {alt_response.status_code} {alt_response.reason}")
            
            if alt_response.status_code in [200, 201]:
                # Parse the response
                alt_session_data = alt_response.json()
                
                print("Alternative session response received:")
                print(json.dumps(alt_session_data, indent=2))
                
                # Extract the session ID
                alt_session_id = alt_session_data.get('sessionId')
                
                if not alt_session_id:
                    print("Error: No session ID in alternative response")
                    print(f"Alternative response: {alt_response.text}")
                    return None
                
                print(f"Successfully created new session using alternative URL: {alt_session_id}")
                
                return alt_session_id
            else:
                print(f"Alternative approach also failed: {alt_response.status_code} {alt_response.reason}")
                print(f"Alternative response: {alt_response.text}")
                return None
        
    except Exception as e:
        print(f"Exception during session creation: {str(e)}")
        print(f"Stack trace: {e.__traceback__}")
        return None

def send_test_message(af_creds, access_token, session_id, sequence_id=1, verbose=False):
    """Send a test message to verify the session works"""
    import requests
    
    print("Sending test message to verify session...")
    
    # Try both URL formats
    urls = [
        f'https://api.salesforce.com/einstein/ai-agent/v1/sessions/{session_id}/messages',
        f'{af_creds.INSTANCE_URL}/services/data/v59.0/einstein/ai-agent/sessions/{session_id}/messages'
    ]
    
    # Prepare request body
    request_body = {
        'message': {
            'sequenceId': sequence_id,
            'type': 'Text',
            'text': 'This is a test message to verify the AgentForce session is working correctly.'
        }
    }
    
    for i, message_url in enumerate(urls):
        print(f"Trying URL {i+1}: {message_url}")
        
        if verbose:
            print(f"Request body: {json.dumps(request_body, indent=2)}")
        
        try:
            # Make the HTTP request
            response = requests.post(
                message_url,
                json=request_body,
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                },
                timeout=60
            )
            
            print(f"Response status: {response.status_code} {response.reason}")
            
            # Handle the response
            if response.status_code == 200:
                # Parse the response
                message_data = response.json()
                
                if verbose:
                    print("Message response received:")
                    print(json.dumps(message_data, indent=2))
                
                # Extract the agent response
                agent_response = ""
                
                if 'messages' in message_data and message_data['messages']:
                    agent_response = message_data['messages'][0].get('message', '')
                
                if not agent_response:
                    agent_response = "No response from agent"
                
                print(f"Test message successful. Agent response: {agent_response}")
                
                return True
            else:
                # Handle error response
                print(f"Error sending test message with URL {i+1}: {response.status_code} {response.reason}")
                print(f"Response: {response.text}")
                
                if i < len(urls) - 1:
                    print(f"Trying next URL format...")
                    continue
                else:
                    return False
            
        except Exception as e:
            print(f"Exception during message sending with URL {i+1}: {str(e)}")
            
            if i < len(urls) - 1:
                print("Trying next URL format...")
                continue
            else:
                return False
    
    return False

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Refresh AgentForce token and session')
    parser.add_argument('--force', '-f', action='store_true', help='Force token refresh')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed output')
    parser.add_argument('--test', '-t', action='store_true', help='Send test message after refresh')
    args = parser.parse_args()
    
    # Always be verbose if we're debugging
    verbose = args.verbose
    
    # Determine the path to the credentials file
    script_dir = Path(__file__).parent
    credentials_path = script_dir / 'app' / 'agentforce_credentials.py'
    
    print(f"Using credentials file: {credentials_path}")
    
    # Import the credentials module
    af_creds = import_credentials_module(credentials_path)
    
    # Print current credential values
    print(f"Current values:")
    print(f"- SERVER_URL: {af_creds.SERVER_URL}")
    print(f"- AGENT_ID: {af_creds.AGENT_ID}")
    print(f"- ACCESS_TOKEN: {'None' if not hasattr(af_creds, 'ACCESS_TOKEN') or not af_creds.ACCESS_TOKEN else af_creds.ACCESS_TOKEN[:10] + '...' + (af_creds.ACCESS_TOKEN[-5:] if len(af_creds.ACCESS_TOKEN) > 15 else '')}")
    print(f"- SESSION_ID: {'None' if not hasattr(af_creds, 'SESSION_ID') or not af_creds.SESSION_ID else af_creds.SESSION_ID}")
    print(f"- SEQUENCE_ID: {'None' if not hasattr(af_creds, 'SEQUENCE_ID') else af_creds.SEQUENCE_ID}")
    
    # Check if we need to refresh the token
    if args.force or not hasattr(af_creds, 'ACCESS_TOKEN') or not af_creds.ACCESS_TOKEN:
        # Refresh the token
        access_token, instance_url = refresh_token(af_creds, verbose)
        
        if not access_token or not instance_url:
            print("Failed to refresh token. Exiting.")
            sys.exit(1)
        
        # Create a new session
        session_id = create_session(af_creds, access_token, instance_url, verbose=True)
        
        if not session_id:
            print("Failed to create session. Exiting.")
            sys.exit(1)
        
        # Reset sequence ID
        sequence_id = 1
        
        # Send a test message if requested
        if args.test:
            success = send_test_message(af_creds, access_token, session_id, sequence_id, verbose=True)
            if success:
                # Increment sequence ID after successful test
                sequence_id += 1
            else:
                print("Test message failed.")
        
        # Update the credentials file
        update_credentials_file(credentials_path, access_token, instance_url, session_id, sequence_id)
        print(f"Updated credentials file: {credentials_path}")
    else:
        print(f"Token already exists: {af_creds.ACCESS_TOKEN[:10]}...{af_creds.ACCESS_TOKEN[-5:]}")
        print("Use --force to refresh anyway.")
        print(f"Current session ID: {af_creds.SESSION_ID}" if hasattr(af_creds, 'SESSION_ID') and af_creds.SESSION_ID else "No session ID found")
        print(f"Current sequence ID: {af_creds.SEQUENCE_ID}" if hasattr(af_creds, 'SEQUENCE_ID') else "No sequence ID found")
    
    print("Done.")

if __name__ == "__main__":
    main()
