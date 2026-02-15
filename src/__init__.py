"""Workflow Engine - Execution engine for multi-agent workflows."""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid


class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentType(Enum):
    NVIDIA_GPU = "nvidia"
    AWS_TRAINIUM = "trainium"
    GOOGLE_TPU = "tpu"
    CPU = "cpu"


class Protocol(Enum):
    MCP = "mcp"
    A2A = "a2a"
    CUSTOM = "custom"
    HTTP = "http"


@dataclass
class WorkflowStep:
    step_id: str
    name: str
    action: str
    agent_id: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.PENDING
    result: Any = None
    error: Optional[str] = None


@dataclass
class Workflow:
    workflow_id: str
    name: str
    steps: Dict[str, WorkflowStep] = field(default_factory=dict)
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)


class WorkflowEngine:
    """Execution engine for multi-agent workflows."""
    
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.executors: Dict[str, Callable] = {}
    
    def create_workflow(self, name: str) -> Workflow:
        wf = Workflow(workflow_id=str(uuid.uuid4()), name=name)
        self.workflows[wf.workflow_id] = wf
        return wf
    
    def add_step(self, workflow_id: str, step_id: str, name: str, action: str, dependencies: List[str] = None) -> WorkflowStep:
        wf = self.workflows.get(workflow_id)
        if not wf:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        step = WorkflowStep(step_id=step_id, name=name, action=action, dependencies=dependencies or [])
        wf.steps[step_id] = step
        return step
    
    def register_executor(self, action: str, executor: Callable) -> None:
        self.executors[action] = executor
    
    async def run(self, workflow_id: str) -> Dict[str, Any]:
        wf = self.workflows.get(workflow_id)
        if not wf:
            return {"error": "Workflow not found"}
        
        wf.status = WorkflowStatus.RUNNING
        
        completed = set()
        failed = False
        
        while len(completed) < len(wf.steps) and not failed:
            ready = []
            
            for step_id, step in wf.steps.items():
                if step_id in completed or step.status in (WorkflowStatus.RUNNING, WorkflowStatus.COMPLETED, WorkflowStatus.FAILED):
                    continue
                
                deps_met = all(dep in completed for dep in step.dependencies)
                if deps_met:
                    ready.append(step)
            
            if not ready:
                if len(completed) < len(wf.steps):
                    wf.status = WorkflowStatus.FAILED
                    failed = True
                break
            
            for step in ready:
                step.status = WorkflowStatus.RUNNING
                
                executor = self.executors.get(step.action)
                if executor:
                    try:
                        step.result = await executor(step)
                        step.status = WorkflowStatus.COMPLETED
                    except Exception as e:
                        step.status = WorkflowStatus.FAILED
                        step.error = str(e)
                        failed = True
                        break
                else:
                    step.status = WorkflowStatus.COMPLETED
                
                completed.add(step.step_id)
        
        wf.status = WorkflowStatus.COMPLETED if not failed else WorkflowStatus.FAILED
        
        return {"workflow_id": workflow_id, "status": wf.status.value, "steps": {s.step_id: s.status.value for s in wf.steps.values()}}
    
    def get_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        wf = self.workflows.get(workflow_id)
        if not wf:
            return None
        
        return {"workflow_id": wf.workflow_id, "name": wf.name, "status": wf.status.value, "steps": len(wf.steps)}


__all__ = ["WorkflowEngine", "Workflow", "WorkflowStep", "WorkflowStatus", "AgentType", "Protocol"]
