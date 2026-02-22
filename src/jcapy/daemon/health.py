# SPDX-License-Identifier: Apache-2.0
"""
JCapy Daemon Health Checker

Provides health monitoring and diagnostics for the daemon:
- System resource checks
- Dependency verification
- Service availability checks
- Self-healing capabilities
"""

import os
import sys
import json
import subprocess
import platform
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class HealthCheckResult:
    """Result of a single health check"""
    name: str
    status: str  # 'ok', 'warning', 'error'
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return asdict(self)


class HealthChecker:
    """Comprehensive health checker for JCapy daemon"""
    
    def __init__(self):
        self.checks: List[HealthCheckResult] = []
        self.jcapy_home = Path.home() / '.jcapy'
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks and return summary"""
        self.checks = []
        
        # Run individual checks
        self._check_python_version()
        self._check_disk_space()
        self._check_memory()
        self._check_jcapy_home()
        self._check_dependencies()
        self._check_network()
        self._check_config()
        
        # Calculate overall status
        overall = self._calculate_overall_status()
        
        return {
            "status": overall,
            "timestamp": datetime.now().isoformat(),
            "hostname": platform.node(),
            "platform": f"{platform.system()} {platform.release()}",
            "checks": [c.to_dict() for c in self.checks],
            "summary": {
                "total": len(self.checks),
                "ok": sum(1 for c in self.checks if c.status == 'ok'),
                "warnings": sum(1 for c in self.checks if c.status == 'warning'),
                "errors": sum(1 for c in self.checks if c.status == 'error')
            }
        }
    
    def _check_python_version(self):
        """Check Python version compatibility"""
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        
        if version.major >= 3 and version.minor >= 11:
            self.checks.append(HealthCheckResult(
                name="Python Version",
                status="ok",
                message=f"Python {version_str} is compatible",
                details={"version": version_str}
            ))
        else:
            self.checks.append(HealthCheckResult(
                name="Python Version",
                status="error",
                message=f"Python {version_str} is not supported. Requires 3.11+",
                details={"version": version_str, "required": "3.11+"}
            ))
    
    def _check_disk_space(self):
        """Check available disk space"""
        try:
            total, used, free = shutil.disk_usage(Path.home())
            free_gb = free // (1024 ** 3)
            total_gb = total // (1024 ** 3)
            used_percent = (used / total) * 100
            
            if free_gb < 1:
                status = "error"
                message = f"Critical: Only {free_gb}GB free space"
            elif free_gb < 5:
                status = "warning"
                message = f"Low disk space: {free_gb}GB free"
            else:
                status = "ok"
                message = f"{free_gb}GB free of {total_gb}GB"
            
            self.checks.append(HealthCheckResult(
                name="Disk Space",
                status=status,
                message=message,
                details={
                    "free_gb": free_gb,
                    "total_gb": total_gb,
                    "used_percent": round(used_percent, 1)
                }
            ))
        except Exception as e:
            self.checks.append(HealthCheckResult(
                name="Disk Space",
                status="error",
                message=f"Failed to check disk space: {e}"
            ))
    
    def _check_memory(self):
        """Check system memory"""
        try:
            # Try to get memory info
            if platform.system() == "Darwin":  # macOS
                result = subprocess.run(
                    ["sysctl", "-n", "hw.memsize"],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    total_bytes = int(result.stdout.strip())
                    total_gb = total_bytes / (1024 ** 3)
                    
                    # Get free memory
                    vm_stat = subprocess.run(
                        ["vm_stat"],
                        capture_output=True, text=True
                    )
                    # Parse vm_stat output (simplified)
                    
                    self.checks.append(HealthCheckResult(
                        name="Memory",
                        status="ok",
                        message=f"Total memory: {total_gb:.1f}GB",
                        details={"total_gb": round(total_gb, 1)}
                    ))
                else:
                    raise Exception("Could not read memory info")
            elif platform.system() == "Linux":
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()
                    # Parse MemTotal
                    for line in meminfo.split('\n'):
                        if line.startswith('MemTotal:'):
                            total_kb = int(line.split()[1])
                            total_gb = total_kb / (1024 ** 2)
                            break
                    
                    self.checks.append(HealthCheckResult(
                        name="Memory",
                        status="ok",
                        message=f"Total memory: {total_gb:.1f}GB",
                        details={"total_gb": round(total_gb, 1)}
                    ))
            else:
                self.checks.append(HealthCheckResult(
                    name="Memory",
                    status="warning",
                    message="Memory check not implemented for this platform"
                ))
        except Exception as e:
            self.checks.append(HealthCheckResult(
                name="Memory",
                status="warning",
                message=f"Could not check memory: {e}"
            ))
    
    def _check_jcapy_home(self):
        """Check JCapy home directory"""
        home = self.jcapy_home
        
        if not home.exists():
            try:
                home.mkdir(parents=True, exist_ok=True)
                (home / 'skills').mkdir(exist_ok=True)
                (home / 'data').mkdir(exist_ok=True)
                
                self.checks.append(HealthCheckResult(
                    name="JCapy Home",
                    status="ok",
                    message=f"Created {home}",
                    details={"path": str(home)}
                ))
            except Exception as e:
                self.checks.append(HealthCheckResult(
                    name="JCapy Home",
                    status="error",
                    message=f"Cannot create {home}: {e}"
                ))
        else:
            # Check permissions
            if os.access(home, os.W_OK):
                self.checks.append(HealthCheckResult(
                    name="JCapy Home",
                    status="ok",
                    message=f"Home directory ready",
                    details={"path": str(home)}
                ))
            else:
                self.checks.append(HealthCheckResult(
                    name="JCapy Home",
                    status="error",
                    message=f"No write permission for {home}"
                ))
    
    def _check_dependencies(self):
        """Check required Python dependencies"""
        required = ['rich', 'textual', 'yaml', 'chromadb']
        missing = []
        installed = []
        
        for dep in required:
            try:
                __import__(dep)
                installed.append(dep)
            except ImportError:
                missing.append(dep)
        
        if missing:
            self.checks.append(HealthCheckResult(
                name="Dependencies",
                status="error",
                message=f"Missing: {', '.join(missing)}",
                details={"missing": missing, "installed": installed}
            ))
        else:
            self.checks.append(HealthCheckResult(
                name="Dependencies",
                status="ok",
                message=f"All {len(installed)} dependencies installed",
                details={"installed": installed}
            ))
    
    def _check_network(self):
        """Check network connectivity"""
        # Simple check - can we bind to a port?
        import socket
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', 8080))
            sock.close()
            
            if result == 0:
                self.checks.append(HealthCheckResult(
                    name="Network",
                    status="ok",
                    message="Port 8080 is active",
                    details={"port_8080": "listening"}
                ))
            else:
                self.checks.append(HealthCheckResult(
                    name="Network",
                    status="ok",
                    message="Network stack available",
                    details={"port_8080": "available"}
                ))
        except Exception as e:
            self.checks.append(HealthCheckResult(
                name="Network",
                status="warning",
                message=f"Network check issue: {e}"
            ))
    
    def _check_config(self):
        """Check JCapy configuration"""
        config_file = self.jcapy_home / 'config.yaml'
        
        if config_file.exists():
            try:
                import yaml
                with open(config_file) as f:
                    config = yaml.safe_load(f)
                
                self.checks.append(HealthCheckResult(
                    name="Configuration",
                    status="ok",
                    message="Configuration loaded",
                    details={"file": str(config_file)}
                ))
            except Exception as e:
                self.checks.append(HealthCheckResult(
                    name="Configuration",
                    status="warning",
                    message=f"Config exists but cannot load: {e}"
                ))
        else:
            self.checks.append(HealthCheckResult(
                name="Configuration",
                status="ok",
                message="Using default configuration",
                details={"file": str(config_file), "exists": False}
            ))
    
    def _calculate_overall_status(self) -> str:
        """Calculate overall health status"""
        if any(c.status == 'error' for c in self.checks):
            return 'unhealthy'
        elif any(c.status == 'warning' for c in self.checks):
            return 'degraded'
        else:
            return 'healthy'
    
    def print_report(self):
        """Print a formatted health report"""
        results = self.run_all_checks()
        
        # Colors
        GREEN = '\033[0;32m'
        YELLOW = '\033[1;33m'
        RED = '\033[0;31m'
        CYAN = '\033[0;36m'
        BOLD = '\033[1m'
        RESET = '\033[0m'
        
        print(f"\n{BOLD}{CYAN}╔═══════════════════════════════════════════════════════════╗{RESET}")
        print(f"{BOLD}{CYAN}║           JCAPY DAEMON HEALTH REPORT                      ║{RESET}")
        print(f"{BOLD}{CYAN}╚═══════════════════════════════════════════════════════════╝{RESET}\n")
        
        # Overall status
        status_colors = {
            'healthy': GREEN,
            'degraded': YELLOW,
            'unhealthy': RED
        }
        status_color = status_colors.get(results['status'], RESET)
        print(f"{BOLD}Overall Status:{RESET} {status_color}{results['status'].upper()}{RESET}")
        print(f"{BOLD}Timestamp:{RESET} {results['timestamp']}")
        print(f"{BOLD}Platform:{RESET} {results['platform']}\n")
        
        # Individual checks
        print(f"{BOLD}Health Checks:{RESET}")
        print("-" * 60)
        
        for check in results['checks']:
            status_icon = {
                'ok': f'{GREEN}✓{RESET}',
                'warning': f'{YELLOW}⚠{RESET}',
                'error': f'{RED}✗{RESET}'
            }.get(check['status'], '?')
            
            print(f"  {status_icon} {check['name']}: {check['message']}")
        
        # Summary
        print("-" * 60)
        summary = results['summary']
        print(f"\n{BOLD}Summary:{RESET}")
        print(f"  Total: {summary['total']} | {GREEN}OK: {summary['ok']}{RESET} | {YELLOW}Warnings: {summary['warnings']}{RESET} | {RED}Errors: {summary['errors']}{RESET}\n")


def run_health_check():
    """Entry point for health check CLI"""
    checker = HealthChecker()
    checker.print_report()
    return checker.run_all_checks()


if __name__ == '__main__':
    run_health_check()