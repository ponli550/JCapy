# SPDX-License-Identifier: Apache-2.0
import logging
import json
import threading
from typing import Optional, Dict, Any, Callable
from datetime import datetime

import grpc
from jcapy.core.proto import jcapy_pb2, jcapy_pb2_grpc
from jcapy.core.ssl_utils import get_grpc_credentials
from jcapy.utils.updates import VERSION

logger = logging.getLogger('jcapy.client')

class JCapyClient:
    """
    Unified client for JCapy 2.0 Orbital Architecture.
    Handles communication with the background daemon (jcapyd) via gRPC.
    """

    def __init__(self, host: str = 'localhost', port: int = 50051):
        self.host = host
        self.port = port
        self.channel = None
        self.stub = None
        self._connected = False

    def connect(self, timeout: int = 2) -> bool:
        """Connect to the JCapy Daemon."""
        try:
            target = f"{self.host}:{self.port}"
            # Secure gRPC with mTLS
            try:
                credentials = get_grpc_credentials(is_server=False)
                self.channel = grpc.secure_channel(target, credentials)
                logger.info("Using SECURE mTLS channel")
            except Exception as e:
                logger.warning(f"Failed to initialize secure channel: {e}. Falling back to INSECURE.")
                self.channel = grpc.insecure_channel(target)

            self.stub = jcapy_pb2_grpc.JCapyOrchestratorStub(self.channel)

            # Simple health check/ping using GetStatus
            # Increase timeout if needed
            grpc.channel_ready_future(self.channel).result(timeout=timeout)
            self._connected = True
            logger.info(f"Connected to JCapy Daemon at {target}")
            return True
        except Exception as e:
            self._connected = False
            logger.warning(f"Could not connect to JCapy Daemon: {e}")
            return False

    def execute(self, command_str: str, context: Optional[Dict[str, str]] = None) -> jcapy_pb2.CommandResponse:
        """Execute a command on the daemon."""
        if not self._connected and not self.connect():
            return jcapy_pb2.CommandResponse(
                status="failure",
                message="Daemon not reachable"
            )

        try:
            request = jcapy_pb2.CommandRequest(
                command_str=command_str,
                context=context or {}
            )
            return self.stub.ExecuteCommand(request)
        except grpc.RpcError as e:
            logger.error(f"gRPC Error: {e}")
            return jcapy_pb2.CommandResponse(
                status="failure",
                message=f"RPC error: {e.details() if hasattr(e, 'details') else str(e)}"
            )

    def get_status(self) -> jcapy_pb2.StatusResponse:
        """Get daemon status."""
        if not self._connected and not self.connect():
            return jcapy_pb2.StatusResponse(status="disconnected")

        try:
            return self.stub.GetStatus(jcapy_pb2.StatusRequest())
        except grpc.RpcError as e:
            logger.error(f"gRPC Error: {e}")
            return jcapy_pb2.StatusResponse(status="error")

    def stream_logs(self, log_callback: Callable[[jcapy_pb2.LogEntry], None], filter_str: str = ""):
        """Stream logs from the daemon and pass to callback."""
        if not self._connected and not self.connect():
            return

        try:
            request = jcapy_pb2.LogRequest(filter=filter_str)
            for log_entry in self.stub.StreamLogs(request):
                log_callback(log_entry)
        except grpc.RpcError as e:
            # Cancelled or stream closed is expected on disconnect
            if e.code() != grpc.StatusCode.CANCELLED:
                logger.error(f"Log stream error: {e}")

    def close(self):
        """Close the connection."""
        if self.channel:
            self.channel.close()
            self.channel = None
            self.stub = None
            self._connected = False
