// Main application script for the Claude Voice Assistant

document.addEventListener('DOMContentLoaded', () => {
    // Connect to Socket.IO server
    const socket = io();
    
    // Initialize the AudioProcessor
    const audioProcessor = new AudioProcessor();
    
    // Initialize the UI Controller
    const uiController = new UIController(socket, audioProcessor);
    
    // Setup the WebSocket connection events
    socket.on('connect', () => {
        console.log('Connected to server');
        uiController.updateStatus('Ready');
    });
    
    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        uiController.updateStatus('Disconnected');
    });
    
    socket.on('error', (data) => {
        console.error('Error from server:', data.message);
        uiController.displayError(data.message);
    });
    
    // Handle transcription events
    socket.on('transcription', (data) => {
        console.log('Transcription received:', data);
        uiController.displayTranscription(data.text);
        
        // Update debug panel
        document.getElementById('transcription-debug').textContent = JSON.stringify(data, null, 2);
    });
    
    // Handle chat response events
    socket.on('chat_response', (data) => {
        console.log('Chat response received:', data);
        
        // Display the response text
        uiController.displayAssistantMessage(data.text);
        
        // Play the audio response
        if (data.audio) {
            uiController.playAudioResponse(data.audio);
        }
        
        // Update debug panel
        document.getElementById('api-debug').textContent = JSON.stringify(data, null, 2);
    });
    
    // Handle VAD result events
    socket.on('vad_result', (data) => {
        console.log('VAD result received:', data);
        
        // Update VAD status
        if (data.speech_active) {
            uiController.updateStatus('Listening', 'listening');
            
            // If there's text in the result, display it
            if (data.text) {
                uiController.displayTranscription(data.text);
            }
        } else {
            uiController.updateStatus('Ready');
        }
        
        // Update debug panel
        document.getElementById('vad-debug').textContent = JSON.stringify(data, null, 2);
    });
    
    // Handle VAD session creation events
    socket.on('vad_session_created', (data) => {
        console.log('VAD session created:', data);
        uiController.setVadSessionId(data.session_id);
    });
    
    // Initialize event listeners
    initEventListeners(socket, audioProcessor, uiController);
    
    // Check microphone permission status
    checkMicrophonePermission();
});

// Check if microphone is accessible
async function checkMicrophonePermission() {
    console.log("Checking microphone permission status...");
    try {
        // Query device permissions
        const permissionStatus = await navigator.permissions.query({name: 'microphone'})
            .catch(error => {
                console.warn("Permission API not supported, will try direct access", error);
                return { state: 'unknown' };
            });
        
        console.log("Permission status:", permissionStatus.state);
        
        // If permission is already denied, show the permissions modal
        if (permissionStatus.state === 'denied') {
            showMicrophonePermissionsModal();
            return false;
        }
        
        // If we're unsure about permission, try to access the microphone
        if (permissionStatus.state === 'unknown' || permissionStatus.state === 'prompt') {
            // Only test microphone access if the Permission API doesn't give a clear answer
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                // If we get here, we have microphone access
                console.log("Successfully accessed microphone");
                // Close the test stream
                stream.getTracks().forEach(track => track.stop());
                return true;
            } catch (error) {
                console.error("Failed microphone access test:", error);
                showMicrophonePermissionsModal();
                return false;
            }
        }
        
        return permissionStatus.state === 'granted';
    } catch (error) {
        console.error("Error checking microphone permission:", error);
        // Fall back to showing the permissions modal
        showMicrophonePermissionsModal();
        return false;
    }
}

// Show the microphone permissions modal
function showMicrophonePermissionsModal() {
    console.log("Showing microphone permissions modal");
    const modal = document.getElementById('mic-permissions-modal');
    modal.classList.add('show');
}

// Initialize all event listeners
function initEventListeners(socket, audioProcessor, uiController) {
    const holdToTalkButton = document.getElementById('hold-to-talk');
    const toggleVadButton = document.getElementById('toggle-vad');
    const settingsButton = document.getElementById('settings-button');
    const closeSettingsButton = document.getElementById('close-settings');
    const saveSettingsButton = document.getElementById('save-settings');
    const toggleDebugButton = document.getElementById('toggle-debug');
    const debugPanel = document.getElementById('debug-panel');
    const settingsModal = document.getElementById('settings-modal');
    const retryMicAccessButton = document.getElementById('retry-mic-access');
    const closePermissionsModalButton = document.getElementById('close-permissions-modal');
    
    // Hold-to-talk button events
    holdToTalkButton.addEventListener('mousedown', async () => {
        const hasPermission = await checkMicrophonePermission();
        if (hasPermission) {
            uiController.startRecording();
        }
    });
    
    holdToTalkButton.addEventListener('mouseup', () => {
        if (uiController.isRecording) {
            uiController.stopRecording();
        }
    });
    
    holdToTalkButton.addEventListener('mouseleave', () => {
        if (uiController.isRecording) {
            uiController.stopRecording();
        }
    });
    
    // Touch events for mobile
    holdToTalkButton.addEventListener('touchstart', async (e) => {
        e.preventDefault();
        const hasPermission = await checkMicrophonePermission();
        if (hasPermission) {
            uiController.startRecording();
        }
    });
    
    holdToTalkButton.addEventListener('touchend', (e) => {
        e.preventDefault();
        if (uiController.isRecording) {
            uiController.stopRecording();
        }
    });
    
    // Toggle VAD button
    toggleVadButton.addEventListener('click', async () => {
        const hasPermission = await checkMicrophonePermission();
        if (hasPermission) {
            uiController.toggleVAD();
        }
    });
    
    // Settings modal events
    settingsButton.addEventListener('click', () => {
        settingsModal.classList.add('show');
    });
    
    closeSettingsButton.addEventListener('click', () => {
        settingsModal.classList.remove('show');
    });
    
    saveSettingsButton.addEventListener('click', () => {
        uiController.saveSettings();
        settingsModal.classList.remove('show');
    });
    
    // Debug panel events
    toggleDebugButton.addEventListener('click', () => {
        debugPanel.classList.toggle('expanded');
    });
    
    // Microphone permissions modal events
    retryMicAccessButton.addEventListener('click', async () => {
        try {
            // Try to get microphone access
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            // If successful, close the modal
            document.getElementById('mic-permissions-modal').classList.remove('show');
            // Close the test stream
            stream.getTracks().forEach(track => track.stop());
            // Update UI
            uiController.updateStatus('Ready');
        } catch (error) {
            console.error("Failed to get microphone access:", error);
            // Show more detailed error in UI
            const errorDetail = document.createElement('p');
            errorDetail.className = 'error-detail';
            errorDetail.textContent = `Error: ${error.name} - ${error.message}`;
            errorDetail.style.color = 'var(--error)';
            errorDetail.style.marginTop = '10px';
            
            // Remove any existing error detail
            const oldError = document.querySelector('.error-detail');
            if (oldError) {
                oldError.remove();
            }
            
            // Add the new error detail
            document.querySelector('.permissions-content').appendChild(errorDetail);
        }
    });
    
    closePermissionsModalButton.addEventListener('click', () => {
        document.getElementById('mic-permissions-modal').classList.remove('show');
    });
    
    // Settings sliders and inputs
    const vadSensitivity = document.getElementById('vad-sensitivity');
    const vadSensitivityValue = document.getElementById('vad-sensitivity-value');
    
    vadSensitivity.addEventListener('input', () => {
        vadSensitivityValue.textContent = `${vadSensitivity.value}%`;
    });
    
    // Dark mode toggle
    const darkModeToggle = document.getElementById('dark-mode');
    
    darkModeToggle.addEventListener('change', () => {
        document.body.classList.toggle('light-mode', !darkModeToggle.checked);
    });
    
    // Show transcripts toggle
    const showTranscriptsToggle = document.getElementById('show-transcripts');
    
    showTranscriptsToggle.addEventListener('change', () => {
        uiController.setShowTranscripts(showTranscriptsToggle.checked);
    });
    
    // Voice select
    const voiceSelect = document.getElementById('voice-select');
    
    voiceSelect.addEventListener('change', () => {
        uiController.setVoice(voiceSelect.value);
    });
    
    // Handle clicks outside the modals to close them
    window.addEventListener('click', (e) => {
        if (e.target === settingsModal) {
            settingsModal.classList.remove('show');
        }
    });
    
    // Add keyboard shortcut for hold-to-talk (spacebar)
    document.addEventListener('keydown', async (e) => {
        // If spacebar is pressed and no modal is open
        if (e.code === 'Space' && 
            !settingsModal.classList.contains('show') && 
            !document.getElementById('mic-permissions-modal').classList.contains('show') &&
            !e.target.tagName.match(/INPUT|TEXTAREA|SELECT|BUTTON/i)) {
            
            e.preventDefault(); // Prevent scrolling
            if (!uiController.isRecording) {
                const hasPermission = await checkMicrophonePermission();
                if (hasPermission) {
                    uiController.startRecording();
                }
            }
        }
    });
    
    document.addEventListener('keyup', (e) => {
        // If spacebar is released
        if (e.code === 'Space' && 
            !e.target.tagName.match(/INPUT|TEXTAREA|SELECT|BUTTON/i)) {
            
            if (uiController.isRecording) {
                uiController.stopRecording();
            }
        }
    });
    
    // Expand debug panel by default in development
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        debugPanel.classList.add('expanded');
    }
}
