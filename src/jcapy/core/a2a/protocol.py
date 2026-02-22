from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class Role(int, Enum):
    ROLE_UNSPECIFIED = 0
    ROLE_USER = 1
    ROLE_AGENT = 2

class TaskState(int, Enum):
    TASK_STATE_UNSPECIFIED = 0
    TASK_STATE_SUBMITTED = 1
    TASK_STATE_WORKING = 2
    TASK_STATE_COMPLETED = 3
    TASK_STATE_FAILED = 4
    TASK_STATE_CANCELED = 5
    TASK_STATE_INPUT_REQUIRED = 6
    TASK_STATE_REJECTED = 7
    TASK_STATE_AUTH_REQUIRED = 8

class Part(BaseModel):
    text: Optional[str] = None
    raw: Optional[bytes] = None
    url: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    filename: Optional[str] = None
    media_type: Optional[str] = None

class Message(BaseModel):
    message_id: str
    context_id: Optional[str] = None
    task_id: Optional[str] = None
    role: Role
    parts: List[Part]
    metadata: Optional[Dict[str, Any]] = None
    extensions: Optional[List[str]] = None
    reference_task_ids: Optional[List[str]] = None

class TaskStatus(BaseModel):
    state: TaskState
    message: Optional[Message] = None
    timestamp: Optional[str] = None

class Artifact(BaseModel):
    artifact_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    parts: List[Part]
    metadata: Optional[Dict[str, Any]] = None
    extensions: Optional[List[str]] = None

class Task(BaseModel):
    id: str
    context_id: str
    status: TaskStatus
    artifacts: Optional[List[Artifact]] = None
    history: Optional[List[Message]] = None
    metadata: Optional[Dict[str, Any]] = None

class SendMessageRequest(BaseModel):
    tenant: Optional[str] = None
    message: Message
    configuration: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class SendMessageResponse(BaseModel):
    task: Optional[Task] = None
    message: Optional[Message] = None

# Backward compatibility (alias) for our mock code so it doesn't break instantly
# These will be phased out in Task 2 & 3.
A2AMessage = SendMessageRequest
TaskRequest = Message
