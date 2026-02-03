// Initialize WebSocket client
console.log('[APP] Initializing WebSocket client...');
const wsClient = new WebSocketClient('ws://localhost:8765');

// DOM Elements
const connectBtn = document.getElementById('connect-btn');
const micBtn = document.getElementById('mic-btn');
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');
const userTranscript = document.getElementById('user-transcript');
const aiTranscript = document.getElementById('ai-transcript');

// Audio handler
let audioHandler = null;
let audioPlayer = null;
let audioChunksSent = 0;

// Update UI status
function setStatus(status, isConnected) {
    console.log(`[STATUS] ${status} (connected: ${isConnected})`);
    statusText.textContent = status;
    statusDot.className = 'dot ' + (isConnected ? 'connected' : 'disconnected');
}

// Connect button handler
connectBtn.addEventListener('click', async () => {
    if (wsClient.isConnected) {
        console.log('[APP] Disconnecting...');
        wsClient.disconnect();
        connectBtn.textContent = 'Connect';
        micBtn.disabled = true;
        setStatus('Disconnected', false);
    } else {
        try {
            console.log('[APP] Connecting to server...');
            connectBtn.textContent = 'Connecting...';
            connectBtn.disabled = true;

            // Use a demo token for now
            await wsClient.connect('demo-token');

            console.log('[APP] Connected successfully!');
            connectBtn.textContent = 'Disconnect';
            connectBtn.disabled = false;
            micBtn.disabled = false;
            setStatus('Connected', true);

        } catch (error) {
            console.error('[APP] Connection failed:', error);
            connectBtn.textContent = 'Connect';
            connectBtn.disabled = false;
            setStatus('Connection failed', false);
        }
    }
});

// Microphone button handler
micBtn.addEventListener('click', async () => {
    if (!audioHandler) {
        try {
            console.log('[MIC] Starting microphone capture...');
            audioChunksSent = 0;

            audioHandler = new AudioCapture((pcmData) => {
                audioChunksSent++;
                if (audioChunksSent % 10 === 0) {
                    console.log(`[MIC] Sent ${audioChunksSent} audio chunks`);
                }
                wsClient.sendAudio(pcmData);
            });
            await audioHandler.start();

            console.log('[MIC] Microphone started!');
            micBtn.innerHTML = '<span class="mic-icon">🔴</span> Stop Speaking';
            setStatus('Listening...', true);

        } catch (error) {
            console.error('[MIC] Microphone access failed:', error);
            alert('Could not access microphone. Please allow microphone access.');
        }
    } else {
        console.log('[MIC] Stopping microphone...');
        audioHandler.stop();
        audioHandler = null;
        micBtn.innerHTML = '<span class="mic-icon">🎤</span> Start Speaking';
        setStatus('Connected', true);
    }
});

// WebSocket message handlers
wsClient.on('ready', () => {
    console.log('[WS] Server ready signal received!');
    setStatus('Ready', true);
});

wsClient.on('partial_transcript', (message) => {
    console.log('[STT PARTIAL]', message.text);
    userTranscript.textContent = message.text;
    userTranscript.className = 'transcript user partial';
});

wsClient.on('final_transcript', (message) => {
    console.log('[STT FINAL]', message.text);
    userTranscript.textContent = message.text;
    userTranscript.className = 'transcript user final';
});

wsClient.on('audio', (message) => {
    console.log(`[TTS] Received audio chunk (${message.data.length} samples)`);
    // Play received audio
    if (!audioPlayer) {
        audioPlayer = new AudioPlayer();
    }
    const audioData = new Uint8Array(message.data);
    audioPlayer.playPCM(audioData);
});

wsClient.on('error', (message) => {
    console.error('[ERROR] Server error:', message.message);
    setStatus('Error: ' + message.message, false);
});

wsClient.on('warning', (message) => {
    console.warn('[WARNING]', message.message);
});

// Handle disconnect
wsClient.onDisconnect = () => {
    console.log('[WS] Disconnected from server');
    connectBtn.textContent = 'Connect';
    micBtn.disabled = true;
    setStatus('Disconnected', false);

    if (audioHandler) {
        audioHandler.stop();
        audioHandler = null;
        micBtn.innerHTML = '<span class="mic-icon">🎤</span> Start Speaking';
    }
};

console.log('[APP] App initialized. Click Connect to start.');
