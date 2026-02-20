/* Live Orbital Bridge Service for JCapy Control Plane */

export class WebSocketBridge {
   constructor(onEvent) {
      this.onEvent = onEvent;
      this.socket = null;
      this.reconnectAttempts = 0;
      this.maxReconnectAttempts = 5;
      this.url = "ws://localhost:8000/ws";
   }

   start() {
      console.log(`[Orbital] Connecting to Bridge at ${this.url}...`);
      this.socket = new WebSocket(this.url);

      this.socket.onopen = () => {
         console.log("[Orbital] Link Established.");
         this.reconnectAttempts = 0;
         this.onEvent({ type: 'STATUS', message: 'CONNECTION_ACTIVE' });
      };

      this.socket.onmessage = (event) => {
         try {
            const payload = JSON.parse(event.data);
            // Payload structure: { topic: string, data: any }
            this.onEvent(payload.data);
         } catch (e) {
            console.error("[Orbital] Message Decode Error:", e);
         }
      };

      this.socket.onclose = () => {
         console.warn("[Orbital] Link Severed.");
         this.attemptReconnect();
      };

      this.socket.onerror = (err) => {
         console.error("[Orbital] Socket Error:", err);
      };
   }

   send(message) {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
         this.socket.send(JSON.stringify(message));
      } else {
         console.error("[Orbital] Cannot send message: Connection not open.");
      }
   }

   attemptReconnect() {
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
         this.reconnectAttempts++;
         const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);
         console.log(`[Orbital] Attempting reconnect ${this.reconnectAttempts} in ${delay}ms...`);
         setTimeout(() => this.start(), delay);
      } else {
         this.onEvent({ type: 'ERROR', message: 'TERMINAL_LINK_FAILURE' });
      }
   }

   stop() {
      if (this.socket) {
         this.socket.close();
      }
   }
}
