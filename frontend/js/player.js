class AudioPlayer {
    constructor() {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        this.queuedAudio = [];
        this.isPlaying = false;
    }

    async playPCM(pcmArray) {
        // Convert PCM bytes to audio buffer
        const audioBuffer = this.audioContext.createBuffer(
            1, // mono
            pcmArray.length / 2, // 16-bit samples
            16000 // sample rate
        );

        const channelData = audioBuffer.getChannelData(0);

        // Convert Int16 PCM to Float32
        for (let i = 0; i < pcmArray.length / 2; i++) {
            const int16 = (pcmArray[i * 2 + 1] << 8) | pcmArray[i * 2];
            channelData[i] = int16 / 32768.0;
        }

        // Queue or play immediately
        if (this.isPlaying) {
            this.queuedAudio.push(audioBuffer);
        } else {
            this.playBuffer(audioBuffer);
        }
    }

    playBuffer(buffer) {
        const source = this.audioContext.createBufferSource();
        source.buffer = buffer;
        source.connect(this.audioContext.destination);

        source.onended = () => {
            this.isPlaying = false;

            // Play next in queue
            if (this.queuedAudio.length > 0) {
                const nextBuffer = this.queuedAudio.shift();
                this.playBuffer(nextBuffer);
            }
        };

        this.isPlaying = true;
        source.start();
    }
}