// UI Controller for the Claude Voice Assistant

class UIController {
    constructor(socket, audioProcessor) {
        this.socket = socket;
        this.audioProcessor = audioProcessor;
        this.isRecording = false;
        this.isVadActive = false;
        this.vadSessionId = null;
        this.vadInterval = null;
        this.showTranscripts = true;
        this.voice = 'alloy';
        this.conversationElement = document.getElementById('conversation');
        this.statusText = document.getElementById('status-text');
        this.statusLight = document.getElementById('status-light');
        
        // Add initialization checks
        this.checkBrowserCompatibility();
    }
    
    // Check browser compatibility for required features
    checkBrowserCompatibility() {
        const compatibilityIssues = [];
        
        // Check for required browser APIs
        if (!window.AudioContext && !window.webkitAudioContext) {
            compatibilityIssues.push("Web Audio API is not supported in this browser");
        }
        
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            compatibilityIssues.push("MediaDevices API is not supported in this browser");
        }
        
        if (!window.MediaRecorder) {
            compatibilityIssues.push("MediaRecorder API is not supported in this browser");
        }
        
        // Display issues if found
        if (compatibilityIssues.length > 0) {
            console.error("Browser compatibility issues:", compatibilityIssues);
            this.displayError(`Your browser may not be fully compatible: ${compatibilityIssues.join(", ")}`);
        } else {
            console.log("Browser compatibility check passed");
        }
        
        return compatibilityIssues.length === 0;
    }
    
    // Status management
    updateStatus(text, lightClass = '') {
        this.statusText.textContent = text;
        
        // Reset classes
        this.statusLight.classList.remove('listening', 'processing', 'speaking');
        
        // Add the specified class
        if (lightClass) {
            this.statusLight.classList.add(lightClass);
        }
    }
    
    // Recording management
    async startRecording() {
        if (this.isRecording) {
            console.log("Already recording, ignoring startRecording request");
            return;
        }
        
        try {
            this.isRecording = true;
            this.updateStatus('Initializing microphone...', 'processing');
            
            console.log("Attempting to start recording");
            await this.audioProcessor.startRecording();
            
            console.log("Recording started successfully");
            this.updateStatus('Listening', 'listening');
        } catch (error) {
            console.error('Error starting recording:', error);
            this.isRecording = false;
            this.updateStatus('Error', 'error');
            
            // Display error with more helpful message
            let errorMessage = 'Failed to start recording.';
            
            if (error.name === 'NotAllowedError' || error.message.includes('denied') || error.message.includes('permission')) {
                errorMessage = 'Microphone access denied. Please check your browser permissions and make sure microphone access is allowed for this site.';
            } else if (error.name === 'NotFoundError' || error.message.includes('not found')) {
                errorMessage = 'No microphone found. Please connect a microphone and try again.';
            }
            
            this.displayError(errorMessage);
        }
    }
    
    async stopRecording() {
        if (!this.isRecording) {
            console.log("Not recording, ignoring stopRecording request");
            return;
        }
        
        try {
            this.isRecording = false;
            this.updateStatus('Processing', 'processing');
            
            console.log("Attempting to stop recording");
            const audioData = await this.audioProcessor.stopRecording();
            
            console.log("Recording stopped successfully, audio data length:", audioData.length);
            
            // Send the audio data to the server
            this.socket.emit('audio_data', audioData);
            
            // Display user message with transcription placeholder
            this.displayUserMessage('...');
        } catch (error) {
            console.error('Error stopping recording:', error);
            this.updateStatus('Error', 'error');
            this.displayError(`Failed to process recording: ${error.message}`);
        }
    }
    
    // VAD management
    toggleVAD() {
        if (this.isVadActive) {
            this.stopVAD();
        } else {
            this.startVAD();
        }
    }
    
    startVAD() {
        if (this.isVadActive) {
            console.log("VAD already active, ignoring startVAD request");
            return;
        }
        
        this.isVadActive = true;
        this.updateStatus('Starting VAD', 'processing');
        
        // Request a new VAD session from the server
        this.socket.emit('start_vad');
        
        // Update the toggle button
        const toggleVadButton = document.getElementById('toggle-vad');
        toggleVadButton.innerHTML = '<i class="fas fa-volume-mute"></i> Stop VAD';
        toggleVadButton.classList.add('active');
    }
    
    stopVAD() {
        if (!this.isVadActive) {
            console.log("VAD not active, ignoring stopVAD request");
            return;
        }
        
        this.isVadActive = false;
        this.vadSessionId = null;
        
        if (this.vadInterval) {
            clearInterval(this.vadInterval);
            this.vadInterval = null;
        }
        
        this.updateStatus('Ready');
        
        // Update the toggle button
        const toggleVadButton = document.getElementById('toggle-vad');
        toggleVadButton.innerHTML = '<i class="fas fa-volume-up"></i> Start VAD';
        toggleVadButton.classList.remove('active');
        
        // Stop the audio processor if it's running
        this.audioProcessor.stopVADProcessing();
    }
    
    setVadSessionId(sessionId) {
        this.vadSessionId = sessionId;
        console.log('VAD session ID set:', sessionId);
        
        // Start sending audio chunks for VAD processing
        this.startVADProcessing();
    }
    
    startVADProcessing() {
        if (!this.vadSessionId) {
            console.log("No VAD session ID, can't start VAD processing");
            return;
        }
        
        this.updateStatus('VAD Active', 'listening');
        
        // Start sending audio chunks to the server
        this.audioProcessor.startVADProcessing(audioChunk => {
            this.socket.emit('vad_audio', {
                session_id: this.vadSessionId,
                audio: audioChunk
            });
        });
    }
    
    // Message display
    displayUserMessage(text) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message user';
        messageElement.innerHTML = `
            <div class="avatar">
                <i class="fas fa-user"></i>
            </div>
            <div class="message-content">
                <p>${text}</p>
            </div>
        `;
        
        this.conversationElement.appendChild(messageElement);
        this.scrollToBottom();
        
        return messageElement;
    }
    
    displayAssistantMessage(text) {
        this.updateStatus('Speaking', 'speaking');
        
        const messageElement = document.createElement('div');
        messageElement.className = 'message assistant';
        messageElement.innerHTML = `
            <div class="avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <p>${text}</p>
            </div>
        `;
        
        this.conversationElement.appendChild(messageElement);
        this.scrollToBottom();
        
        return messageElement;
    }
    
    displayTranscription(text) {
        // If we don't want to show transcripts, return
        if (!this.showTranscripts) return;
        
        // Find the last user message (if it exists)
        const userMessages = this.conversationElement.querySelectorAll('.message.user');
        
        if (userMessages.length > 0) {
            // Update the last user message with the transcription
            const lastUserMessage = userMessages[userMessages.length - 1];
            const messageContent = lastUserMessage.querySelector('.message-content p');
            
            if (messageContent) {
                messageContent.textContent = text;
            }
        } else {
            // If there's no existing user message, create one
            this.displayUserMessage(text);
        }
        
        this.scrollToBottom();
    }
    
    displayError(message) {
        const errorElement = document.createElement('div');
        errorElement.className = 'message error';
        errorElement.innerHTML = `
            <div class="avatar">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <div class="message-content">
                <p>Error: ${message}</p>
            </div>
        `;
        
        this.conversationElement.appendChild(errorElement);
        this.scrollToBottom();
        
        // Also log to debug panel
        const apiDebug = document.getElementById('api-debug');
        if (apiDebug) {
            apiDebug.textContent = JSON.stringify({ error: message }, null, 2);
        }
        
        return errorElement;
    }
    
    // Audio playback
    playAudioResponse(audioData) {
        const audio = new Audio(audioData);
        audio.addEventListener('ended', () => {
            this.updateStatus('Ready');
        });
        audio.play().catch(error => {
            console.error('Error playing audio:', error);
            this.updateStatus('Ready');
        });
    }
    
    // Helper methods
    scrollToBottom() {
        this.conversationElement.scrollTop = this.conversationElement.scrollHeight;
    }
    
    // Settings management
    saveSettings() {
        // Save voice preference
        const voiceSelect = document.getElementById('voice-select');
        this.voice = voiceSelect.value;
        
        // Save show transcripts preference
        const showTranscriptsToggle = document.getElementById('show-transcripts');
        this.showTranscripts = showTranscriptsToggle.checked;
        
        // Save dark mode preference
        const darkModeToggle = document.getElementById('dark-mode');
        document.body.classList.toggle('light-mode', !darkModeToggle.checked);
        
        console.log('Settings saved:', {
            voice: this.voice,
            showTranscripts: this.showTranscripts,
            darkMode: darkModeToggle.checked
        });
    }
    
    setShowTranscripts(value) {
        this.showTranscripts = value;
    }
    
    setVoice(value) {
        this.voice = value;
    }
}
