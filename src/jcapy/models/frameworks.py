from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

class ResultStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    WARNING = "warning"

@dataclass
class FrameworkResult:
    """Result of a framework/skill operation."""
    status: ResultStatus
    message: str
    path: Optional[str] = None
    payload: Optional[Dict[str, Any]] = field(default_factory=dict)
