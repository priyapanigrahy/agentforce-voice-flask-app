#!/bin/bash

# Setup script for AgentForce credentials
# This script will collect and store the necessary credentials to connect to Salesforce AgentForce

# Print colorful messages
print_message() {
    echo -e "\033[1;34m>> $1\033[0m"
}

print_success() {
    echo -e "\033[1;32m>> $1\033[0m"
}

print_error() {
    echo -e "\033[1;31m>> $1\033[0m"
}

print_warning() {
    echo -e "\033[1;33m>> $1\033[0m"
}

# Check if the credentials file exists
CREDS_FILE="app/agentforce_credentials.py"
CREDS_SAMPLE_FILE="app/agentforce_credentials.py.sample"

print_message "AgentForce Credentials Setup"
print_message "-------------------------"
print_message "This script will help you set up the credentials needed to connect to Salesforce AgentForce."
echo ""

# Function to get input with validation
get_input() {
    local prompt="$1"
    local var_name="$2"
    local is_required="${3:-true}"
    local value=""
    
    while [ -z "$value" ] && [ "$is_required" = "true" ]; do
        read -p "$prompt" value
        if [ -z "$value" ] && [ "$is_required" = "true" ]; then
            print_error "This field is required. Please try again."
        fi
    done
    
    # If not required and empty, allow it
    if [ -z "$value" ] && [ "$is_required" = "false" ]; then
        read -p "$prompt" value
    fi
    
    echo "$value"
}

# Collect credentials
print_message "Please enter your Salesforce AgentForce credentials:"
SERVER_URL=$(get_input "Server URL (e.g., login.salesforce.com): ")
CLIENT_ID=$(get_input "Client ID: ")
CLIENT_SECRET=$(get_input "Client Secret: ")
AGENT_ID=$(get_input "Agent ID: ")
ORG_ID=$(get_input "Organization ID: ")

# Create the credentials file
cat > "$CREDS_FILE" << EOL
# AgentForce Credentials
# This file contains the credentials for connecting to Salesforce AgentForce

# Salesforce connection settings
SERVER_URL = "$SERVER_URL"
CLIENT_ID = "$CLIENT_ID"
CLIENT_SECRET = "$CLIENT_SECRET"
AGENT_ID = "$AGENT_ID"
ORG_ID = "$ORG_ID"

# Session tracking (don't modify these)
ACCESS_TOKEN = None
INSTANCE_URL = None
SESSION_ID = None
SEQUENCE_ID = 1
EOL

# Create a sample file for reference
cat > "$CREDS_SAMPLE_FILE" << EOL
# AgentForce Credentials SAMPLE
# This is a sample file. Copy to agentforce_credentials.py and fill in your details.

# Salesforce connection settings
SERVER_URL = "login.salesforce.com"
CLIENT_ID = "your_client_id_here"
CLIENT_SECRET = "your_client_secret_here"
AGENT_ID = "your_agent_id_here"
ORG_ID = "your_org_id_here"

# Session tracking (don't modify these)
ACCESS_TOKEN = None
INSTANCE_URL = None
SESSION_ID = None
SEQUENCE_ID = 1
EOL

# Make the credentials file non-readable by others
chmod 600 "$CREDS_FILE"

print_success "Credentials saved to $CREDS_FILE"
print_message "You can edit this file manually if needed."
echo ""

# Add to .gitignore if not already present
if ! grep -q "agentforce_credentials.py" /Users/xlengelle/Code/Claude-Flask-Voice/.gitignore; then
    echo "# AgentForce credentials" >> /Users/xlengelle/Code/Claude-Flask-Voice/.gitignore
    echo "app/agentforce_credentials.py" >> /Users/xlengelle/Code/Claude-Flask-Voice/.gitignore
    print_success "Added credentials file to .gitignore"
fi

print_success "AgentForce setup complete!"
print_message "You can now use AgentForce in your application."
