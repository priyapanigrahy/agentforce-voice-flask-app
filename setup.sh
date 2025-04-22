#!/bin/bash

# Setup script for Claude Flask Voice Assistant

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

# Check Python version
print_message "Checking Python version..."
python_version=$(python3 --version 2>&1)
if [[ $python_version == *"not found"* ]]; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

version_number=$(echo $python_version | cut -d ' ' -f 2)
major=$(echo $version_number | cut -d '.' -f 1)
minor=$(echo $version_number | cut -d '.' -f 2)

if [[ $major -lt 3 || ($major -eq 3 && $minor -lt 8) ]]; then
    print_warning "Python version $version_number detected. We recommend Python 3.8 or higher."
else
    print_success "Python $version_number detected. ✓"
fi

# Create virtual environment
print_message "Creating virtual environment..."
if [ -d "venv" ]; then
    print_warning "Virtual environment already exists. Skipping creation."
else
    python3 -m venv venv
    print_success "Virtual environment created. ✓"
fi

# Activate virtual environment
print_message "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
print_message "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    print_success "Dependencies installed successfully. ✓"
else
    print_error "Failed to install dependencies."
    exit 1
fi

# Check for .env file and collect OpenAI API key
print_message "Setting up environment configuration..."
if [ ! -f "app/.env" ]; then
    print_message "No .env file found. Creating new configuration."
    
    # Ask for OpenAI API key
    read -p "Enter your OpenAI API key: " openai_api_key
    
    # Create .env file with the provided API key
    cat > app/.env << EOL
# OpenAI API Settings
OPENAI_API_KEY=$openai_api_key

# Flask Settings
FLASK_APP=app.py
FLASK_ENV=development

# Server Settings
PORT=8742

# Application Settings
DEFAULT_VOICE=alloy
DEFAULT_MODEL=gpt-4o
DEFAULT_REALTIME_MODEL=gpt-4o-realtime-preview-2024-12-17
DEFAULT_REALTIME_VOICE=coral

# Logging Settings
# Set to DEBUG, INFO, WARNING, ERROR, or CRITICAL
LOG_LEVEL=INFO
EOL
    print_success "Environment configuration created with your API key. ✓"
else
    # Check if OpenAI API key is set in the existing .env file
    if grep -q "OPENAI_API_KEY=your_openai_api_key_here\|OPENAI_API_KEY=" app/.env; then
        print_warning "OpenAI API key not found or appears to be a placeholder."
        read -p "Enter your OpenAI API key: " openai_api_key
        
        # Replace API key placeholder with the provided key
        sed -i '' "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$openai_api_key/" app/.env 2>/dev/null || sed -i "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$openai_api_key/" app/.env
        print_success "API key updated. ✓"
    else
        print_success "Environment file found with API key. ✓"
    fi
    
    # Also update the port in the existing .env file to the non-standard port
    if grep -q "PORT=5000" app/.env; then
        print_message "Updating port to a less common port (8742)..."
        sed -i '' "s/PORT=5000/PORT=8742/" app/.env 2>/dev/null || sed -i "s/PORT=5000/PORT=8742/" app/.env
        print_success "Port updated. ✓"
    fi
fi

# Create __init__.py in app directory to make it a proper package
if [ ! -f "app/__init__.py" ]; then
    print_message "Creating package structure..."
    echo "# This file marks the app directory as a Python package" > app/__init__.py
    print_success "Created app/__init__.py file. ✓"
fi

# Make run.py executable
chmod +x run.py

print_success "Setup complete! 🎉"
print_message "To start the application:"
echo "1. Activate the virtual environment (if not already active):"
echo "   source venv/bin/activate"
echo "2. Run the application:"
echo "   ./run.py"
echo ""
print_message "Access the application at http://localhost:8742"
