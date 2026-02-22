/* Mock Daemon Service for JCapy Control Plane */

export class MockDaemonBridge {
   constructor(onEvent) {
      this.onEvent = onEvent;
      this.isRunning = false;
      this.eventIndex = 0;
      this.events = [
         { id: 1, type: 'THOUGHT', message: 'Analyzing project structure for security vulnerabilities...', timestamp: '11:05:01' },
         { id: 2, type: 'ACTION', message: 'Scanning src/auth.ts and config.yaml', timestamp: '11:05:04' },
         { id: 3, type: 'INTERVENTION', message: 'Sensitive action detected: WRITE_FILE', tool: 'WRITE_FILE', path: 'src/jcapy/config.py', diff: '-    MAX_FAILURES = 5\n+    MAX_FAILURES = 3', timestamp: '11:05:10' },
         { id: 4, type: 'THOUGHT', message: 'Intervention approved. Updating circuit breaker threshold.', timestamp: '11:05:45' },
         { id: 5, type: 'SUCCESS', message: 'Security policy updated successfully.', timestamp: '11:05:48' }
      ];
   }

   start() {
      this.isRunning = true;
      this.tick();
   }

   stop() {
      this.isRunning = false;
   }

   tick() {
      if (!this.isRunning || this.eventIndex >= this.events.length) return;

      const event = this.events[this.eventIndex];

      // Simulate delay
      setTimeout(() => {
         if (this.isRunning) {
            this.onEvent(event);
            this.eventIndex++;
            if (event.type !== 'INTERVENTION') {
               this.tick();
            }
         }
      }, 3000);
   }

   respondToIntervention(id, approved) {
      // Resume stream after intervention
      this.tick();
   }
}
