class AudioPlayer {
    constructor() {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        this.queuedAudio = [];
        this.isPlaying = false;
        this.sourceSampleRate = 16000; // Azure TTS output rate

        console.log(`[PLAYER] Initialized. Browser sample rate: ${this.audioContext.sampleRate}Hz, Source: ${this.sourceSampleRate}Hz`);
    }

    async playPCM(pcmArray) {
        // pcmArray is a Uint8Array containing 16-bit PCM samples (little-endian)
        const numSamples = pcmArray.length / 2;

        // Create a DataView for proper byte reading
        const dataView = new DataView(pcmArray.buffer, pcmArray.byteOffset, pcmArray.byteLength);

        // Convert Int16 PCM (little-endian) to Float32
        const floatData = new Float32Array(numSamples);
        for (let i = 0; i < numSamples; i++) {
            const int16 = dataView.getInt16(i * 2, true); // true = little-endian
            floatData[i] = int16 / 32768.0;
        }

        // Resample if browser sample rate is different from source
        let finalData = floatData;
        let finalSampleRate = this.sourceSampleRate;

        if (this.audioContext.sampleRate !== this.sourceSampleRate) {
            // Resample to browser's sample rate
            finalData = this.resample(floatData, this.sourceSampleRate, this.audioContext.sampleRate);
            finalSampleRate = this.audioContext.sampleRate;
            console.log(`[PLAYER] Resampled from ${this.sourceSampleRate}Hz to ${this.audioContext.sampleRate}Hz`);
        }

        // Create audio buffer at browser's sample rate
        const audioBuffer = this.audioContext.createBuffer(
            1, // mono
            finalData.length,
            finalSampleRate
        );

        audioBuffer.getChannelData(0).set(finalData);

        console.log(`[PLAYER] Playing ${finalData.length} samples at ${finalSampleRate}Hz`);

        // Queue or play immediately
        if (this.isPlaying) {
            this.queuedAudio.push(audioBuffer);
        } else {
            this.playBuffer(audioBuffer);
        }
    }

    resample(audioData, fromSampleRate, toSampleRate) {
        const ratio = fromSampleRate / toSampleRate;
        const newLength = Math.round(audioData.length / ratio);
        const result = new Float32Array(newLength);

        for (let i = 0; i < newLength; i++) {
            const srcIndex = i * ratio;
            const srcIndexFloor = Math.floor(srcIndex);
            const srcIndexCeil = Math.min(srcIndexFloor + 1, audioData.length - 1);
            const t = srcIndex - srcIndexFloor;

            // Linear interpolation
            result[i] = audioData[srcIndexFloor] * (1 - t) + audioData[srcIndexCeil] * t;
        }

        return result;
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