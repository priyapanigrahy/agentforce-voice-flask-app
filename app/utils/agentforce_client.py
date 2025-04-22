import os
import json
import uuid
import requests
import sys
from pathlib import Path

# Try to import credentials from the agentforce_credentials.py file
try:
    # Add the parent directory to sys.path to find the agentforce_credentials module
    sys.path.append(str(Path(__file__).parent.parent))
    import agentforce_credentials as af_creds
except ImportError:
    print("Error: AgentForce credentials not found. Please run setup_agentforce.sh first.")
    af_creds = None

class AgentForceClient:
    """
    Client for interacting with Salesforce AgentForce API
    
    This class handles authentication, session management, and communication
    with the AgentForce API.
    """
    
    def __init__(self, client_email=None):
        """
        Initialize the AgentForce client
        
        Args:
            client_email: Email of the client to associate with the session
        """
        self.client_email = client_email
        self.access_token = getattr(af_creds, 'ACCESS_TOKEN', None)
        self.instance_url = getattr(af_creds, 'INSTANCE_URL', None)
        self.session_id = getattr(af_creds, 'SESSION_ID', None)
        self.sequence_id = getattr(af_creds, 'SEQUENCE_ID', 1)
        
        # Validate that credentials are available
        if not af_creds:
            raise ValueError("AgentForce credentials not configured. Please run setup_agentforce.sh")
            
        # Validate required credentials
        required_attrs = ['SERVER_URL', 'CLIENT_ID', 'CLIENT_SECRET', 'AGENT_ID']
        missing_attrs = [attr for attr in required_attrs if not hasattr(af_creds, attr) or not getattr(af_creds, attr)]
        
        if missing_attrs:
            raise ValueError(f"Missing required AgentForce credentials: {', '.join(missing_attrs)}")
    
    def authenticate(self):
        """
        Authenticate with the AgentForce API and obtain an access token
        
        Returns:
            dict: Authentication response with access token
        """
        try:
            # Build the token URL
            token_url = f'https://{af_creds.SERVER_URL}/services/oauth2/token'
            
            # Prepare request body
            request_body = {
                'grant_type': 'client_credentials',
                'client_id': af_creds.CLIENT_ID,
                'client_secret': af_creds.CLIENT_SECRET
            }
            
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
                
                # Extract and store the access token
                self.access_token = token_data.get('access_token')
                self.instance_url = token_data.get('instance_url')
                
                # Update the module-level access token
                af_creds.ACCESS_TOKEN = self.access_token
                af_creds.INSTANCE_URL = self.instance_url
                
                if not self.access_token:
                    raise ValueError("No access token in response")
                
                return {
                    'success': True,
                    'access_token': self.access_token,
                    'instance_url': self.instance_url
                }
            else:
                # Handle error response
                error_message = f"Authentication error: {response.status_code} {response.reason}"
                print(error_message)
                print(f"Response: {response.text}")
                return {
                    'success': False,
                    'error': error_message,
                    'details': response.text
                }
        
        except Exception as e:
            error_message = f"Exception during authentication: {str(e)}"
            print(error_message)
            return {
                'success': False,
                'error': error_message
            }
    
    def create_session(self):
        """
        Create a new session with an AgentForce agent
        
        Returns:
            dict: Session creation response with session ID
        """
        try:
            # Ensure we have a valid access token
            if not self.access_token:
                auth_result = self.authenticate()
                if not auth_result.get('success'):
                    return auth_result
            
            # Build the session creation URL
            session_url = f'https://api.salesforce.com/einstein/ai-agent/v1/agents/{af_creds.AGENT_ID}/sessions'
            
            # Generate a random UUID for external session key
            random_uuid = str(uuid.uuid4())
            
            # Prepare request body
            request_body = {
                'externalSessionKey': random_uuid,
                'instanceConfig': {
                    'endpoint': self.instance_url
                },
                'streamingCapabilities': {
                    'chunkTypes': ['Text']
                },
                'bypassUser': True
            }
            
            # Make the HTTP request
            response = requests.post(
                session_url,
                json=request_body,
                headers={
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                },
                timeout=30
            )
            
            # Handle the response
            if response.status_code in [200, 201]:
                # Parse the response
                session_data = response.json()
                
                # Extract and store the session ID
                self.session_id = session_data.get('sessionId')
                self.sequence_id = 1
                
                # Update the module-level session ID
                af_creds.SESSION_ID = self.session_id
                af_creds.SEQUENCE_ID = self.sequence_id
                
                if not self.session_id:
                    raise ValueError("No session ID in response")
                
                return {
                    'success': True,
                    'session_id': self.session_id
                }
            else:
                # Handle error response
                error_message = f"Session creation error: {response.status_code} {response.reason}"
                print(error_message)
                print(f"Response: {response.text}")
                
                # If unauthorized, try to reauthenticate and retry
                if response.status_code == 401:
                    print("Token expired, reauthenticating...")
                    auth_result = self.authenticate()
                    if auth_result.get('success'):
                        return self.create_session()
                
                return {
                    'success': False,
                    'error': error_message,
                    'details': response.text
                }
        
        except Exception as e:
            error_message = f"Exception during session creation: {str(e)}"
            print(error_message)
            return {
                'success': False,
                'error': error_message
            }
    
    def send_message(self, message):
        """
        Send a message to the AgentForce agent and get the response
        
        Args:
            message: Message to send to the agent
        
        Returns:
            dict: Agent response
        """
        try:
            # Validate inputs
            if not message:
                raise ValueError("Message is required")
            
            # Ensure we have a valid session
            if not self.session_id:
                session_result = self.create_session()
                if not session_result.get('success'):
                    return session_result
            
            # Build the message URL
            message_url = f'https://api.salesforce.com/einstein/ai-agent/v1/sessions/{self.session_id}/messages'
            
            # Prepare request body
            request_body = {
                'message': {
                    'sequenceId': self.sequence_id,
                    'type': 'Text',
                    'text': message
                }
            }
            
            # Make the HTTP request
            response = requests.post(
                message_url,
                json=request_body,
                headers={
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                },
                timeout=120
            )
            
            # Handle the response
            if response.status_code == 200:
                # Parse the response
                message_data = response.json()
                
                # Extract the agent response
                agent_response = ""
                
                if 'messages' in message_data and message_data['messages']:
                    agent_response = message_data['messages'][0].get('message', '')
                
                if not agent_response:
                    agent_response = "No response from agent"
                
                # Increment the sequence ID for the next message
                self.sequence_id += 1
                af_creds.SEQUENCE_ID = self.sequence_id
                
                return {
                    'success': True,
                    'agent_response': agent_response,
                    'next_sequence_id': self.sequence_id
                }
            else:
                # Handle error response
                error_message = f"Message sending error: {response.status_code} {response.reason}"
                print(error_message)
                print(f"Response: {response.text}")
                
                # If unauthorized, try to reauthenticate and retry
                if response.status_code == 401:
                    print("Token expired, reauthenticating...")
                    auth_result = self.authenticate()
                    if auth_result.get('success'):
                        return self.send_message(message)
                
                # If session expired or not found, create a new session and retry
                if response.status_code == 404:
                    print("Session not found, creating new session...")
                    session_result = self.create_session()
                    if session_result.get('success'):
                        return self.send_message(message)
                
                return {
                    'success': False,
                    'error': error_message,
                    'details': response.text
                }
        
        except Exception as e:
            error_message = f"Exception during message sending: {str(e)}"
            print(error_message)
            return {
                'success': False,
                'error': error_message
            }
    
    def get_session_status(self):
        """
        Get the status of the current session
        
        Returns:
            dict: Session status
        """
        try:
            if not self.session_id:
                return {
                    'success': False,
                    'error': "No active session"
                }
            
            return {
                'success': True,
                'session_id': self.session_id,
                'sequence_id': self.sequence_id,
                'active': bool(self.session_id)
            }
        
        except Exception as e:
            error_message = f"Exception getting session status: {str(e)}"
            print(error_message)
            return {
                'success': False,
                'error': error_message
            }

    def complete_conversation(self, user_query):
        """
        Complete a full conversation flow - authenticate, create session if needed, and send message
        
        Args:
            user_query: Message to send to the agent
            
        Returns:
            dict: Agent response
        """
        try:
            # Ensure we have a valid access token
            if not self.access_token:
                auth_result = self.authenticate()
                if not auth_result.get('success'):
                    return auth_result
            
            # Ensure we have a valid session
            if not self.session_id:
                session_result = self.create_session()
                if not session_result.get('success'):
                    return session_result
            
            # Send the message to the agent
            return self.send_message(user_query)
        
        except Exception as e:
            error_message = f"Exception during conversation: {str(e)}"
            print(error_message)
            return {
                'success': False,
                'error': error_message
            }
