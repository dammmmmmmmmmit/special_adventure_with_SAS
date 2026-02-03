class WebSocketClient {
    constructor(url) {
        this.url = url;
        this.socket = null;
        this.messageHandlers = {};
        this.isConnected = false;
    }

    async connect(token) {
        return new Promise((resolve, reject) => {
            this.socket = new WebSocket(`${this.url}?token=${token}`);
            this.socket.binaryType = 'arraybuffer';

            this.socket.onopen = () => {
                this.isConnected = true;

                // Send authentication
                this.send({
                    type: 'auth',
                    token: token
                });

                resolve();
            };

            this.socket.onmessage = (event) => {
                const message = JSON.parse(event.data);
                const handler = this.messageHandlers[message.type];

                if (handler) {
                    handler(message);
                }
            };

            this.socket.onerror = (error) => {
                console.error('WebSocket error:', error);
                reject(error);
            };

            this.socket.onclose = () => {
                this.isConnected = false;
                this.onDisconnect();
            };
        });
    }

    send(data) {
        if (this.isConnected && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(data));
        }
    }

    sendAudio(pcmData) {
        this.send({
            type: 'audio',
            data: Array.from(pcmData)
        });
    }

    on(messageType, handler) {
        this.messageHandlers[messageType] = handler;
    }

    onDisconnect() {
        // Override in implementation
    }

    disconnect() {
        if (this.socket) {
            this.socket.close();
        }
    }
}