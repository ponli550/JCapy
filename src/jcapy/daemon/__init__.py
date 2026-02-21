# SPDX-License-Identifier: Apache-2.0
"""
JCapy Daemon Module

Provides background service capabilities for JCapy:
- Web Control Plane (HTTP server)
- Health monitoring
- Session persistence
- Background task execution
"""

from jcapy.daemon.server import DaemonServer
from jcapy.daemon.health import HealthChecker

__all__ = ['DaemonServer', 'HealthChecker']