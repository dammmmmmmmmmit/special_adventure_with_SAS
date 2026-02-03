class AudioCapture {
    constructor(onAudioData) {
        this.onAudioData = onAudioData;
        this.stream = null;
        this.audioContext = null;
        this.processor = null;
        this.isRecording = false;
    }

    async start() {
        try {
            // Get microphone access first
            this.stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            // Create audio context with default sample rate (browser decides)
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();

            const source = this.audioContext.createMediaStreamSource(this.stream);

            // Create processor
            this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);

            this.processor.onaudioprocess = (e) => {
                if (this.isRecording) {
                    const inputData = e.inputBuffer.getChannelData(0);

                    // Resample to 16kHz if needed for Azure Speech
                    const targetSampleRate = 16000;
                    const resampledData = this.resample(inputData, this.audioContext.sampleRate, targetSampleRate);

                    const pcmData = this.float32ToPCM16(resampledData);
                    this.onAudioData(pcmData);
                }
            };

            source.connect(this.processor);
            this.processor.connect(this.audioContext.destination);
            this.isRecording = true;

        } catch (error) {
            console.error('Microphone access error:', error);
            throw error;
        }
    }

    stop() {
        this.isRecording = false;

        if (this.processor) {
            this.processor.disconnect();
            this.processor = null;
        }

        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }

        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
    }

    float32ToPCM16(float32Array) {
        const pcm16 = new Int16Array(float32Array.length);
        for (let i = 0; i < float32Array.length; i++) {
            const s = Math.max(-1, Math.min(1, float32Array[i]));
            pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return pcm16;
    }

    resample(audioData, fromSampleRate, toSampleRate) {
        if (fromSampleRate === toSampleRate) {
            return audioData;
        }

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
}