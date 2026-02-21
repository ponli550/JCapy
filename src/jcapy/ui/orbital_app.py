# SPDX-License-Identifier: Apache-2.0
import logging
from typing import Optional
from jcapy.ui.app import JCapyApp
from jcapy.core.client import JCapyClient

logger = logging.getLogger('jcapy.ui.orbital')

class JCapyOrbitalApp(JCapyApp):
    """
    Orbital TUI: A stateless thin-client version of JCapy.
    Connects to a background daemon via gRPC and mTLS.
    """
    def __init__(self, host: str = 'localhost', port: int = 50051, **kwargs):
        super().__init__(**kwargs)
        self.orbital_host = host
        self.orbital_port = port
        self.client: Optional[JCapyClient] = None
        self.is_orbital = True

    def on_mount(self) -> None:
        """Initialize connection to the daemon."""
        logger.info(f"Connecting to JCapy Daemon at {self.orbital_host}:{self.orbital_port}...")
        self.client = JCapyClient(host=self.orbital_host, port=self.orbital_port)

        if self.client.connect():
            self.notify(f"Connected to Orbital Brain: {self.orbital_host}:{self.orbital_port}")
            # Start background log streaming
            self.run_worker(self._stream_remote_logs(), thread=True, name="remote_logs")
        else:
            self.notify("⚠️ Could not connect to Orbital Brain. Falling back to Local Mode.", severity="error")
            self.is_orbital = False

        super().on_mount()

    async def _stream_remote_logs(self):
        """Worker to stream logs from the remote daemon into the TUI."""
        if not self.client: return

        from textual.widgets import RichLog

        def log_callback(log_entry):
            try:
                log = self.query_one("#terminal-log", RichLog)
                self.call_from_thread(log.write, self._ansi_to_text(log_entry.content))
            except:
                pass

        self.client.stream_logs(log_callback)

if __name__ == "__main__":
    app = JCapyOrbitalApp()
    app.run()
