# OpenHands Workflow Automation Guide

This guide covers workflow automation and task orchestration patterns for OpenHands systems.

## Table of Contents
1. [Workflow Engine](#workflow-engine)
2. [Task Orchestration](#task-orchestration)
3. [State Machines](#state-machines)
4. [Event-Driven Workflows](#event-driven-workflows)

## Workflow Engine

### 1. Workflow Definition

Implementation of workflow engine:

```python
from enum import Enum
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import asyncio
import json

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class Task:
    """Workflow task definition"""
    id: str
    name: str
    handler: str
    dependencies: List[str]
    params: Dict[str, Any]
    retry_policy: Optional[dict] = None
    timeout: Optional[int] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None

class WorkflowEngine:
    """Engine for workflow execution"""
    
    def __init__(self):
        self.workflows: Dict[str, dict] = {}
        self.task_handlers: Dict[str, Callable] = {}
        self.active_workflows: Dict[str, dict] = {}
        
    def register_workflow(
        self,
        name: str,
        definition: dict
    ):
        """Register workflow definition"""
        # Validate workflow
        self._validate_workflow(definition)
        self.workflows[name] = definition
        
    def register_task_handler(
        self,
        name: str,
        handler: Callable
    ):
        """Register task handler"""
        self.task_handlers[name] = handler
        
    async def start_workflow(
        self,
        workflow_name: str,
        params: Dict[str, Any]
    ) -> str:
        """Start workflow execution"""
        if workflow_name not in self.workflows:
            raise ValueError(f"Unknown workflow: {workflow_name}")
            
        # Create workflow instance
        instance_id = str(uuid.uuid4())
        workflow = self.workflows[workflow_name].copy()
        workflow['params'] = params
        workflow['status'] = TaskStatus.RUNNING
        workflow['tasks'] = {
            task['id']: Task(**task)
            for task in workflow['tasks']
        }
        
        self.active_workflows[instance_id] = workflow
        
        # Start execution
        asyncio.create_task(
            self._execute_workflow(instance_id)
        )
        
        return instance_id
        
    async def _execute_workflow(self, instance_id: str):
        """Execute workflow instance"""
        workflow = self.active_workflows[instance_id]
        tasks = workflow['tasks']
        
        try:
            # Execute tasks in dependency order
            while any(task.status == TaskStatus.PENDING
                     for task in tasks.values()):
                # Find ready tasks
                ready_tasks = [
                    task for task in tasks.values()
                    if self._is_task_ready(task, tasks)
                ]
                
                # Execute ready tasks
                await asyncio.gather(*[
                    self._execute_task(instance_id, task)
                    for task in ready_tasks
                ])
                
            # Check workflow completion
            if any(task.status == TaskStatus.FAILED
                   for task in tasks.values()):
                workflow['status'] = TaskStatus.FAILED
            else:
                workflow['status'] = TaskStatus.COMPLETED
                
        except Exception as e:
            workflow['status'] = TaskStatus.FAILED
            workflow['error'] = str(e)
            
    async def _execute_task(
        self,
        instance_id: str,
        task: Task
    ):
        """Execute single task"""
        workflow = self.active_workflows[instance_id]
        
        try:
            # Get handler
            handler = self.task_handlers.get(task.handler)
            if not handler:
                raise ValueError(
                    f"Unknown task handler: {task.handler}"
                )
                
            # Execute task
            task.status = TaskStatus.RUNNING
            task.result = await asyncio.wait_for(
                handler(task.params, workflow['params']),
                timeout=task.timeout
            )
            task.status = TaskStatus.COMPLETED
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            
            # Handle retry
            if task.retry_policy:
                await self._handle_retry(instance_id, task)
                
    def _is_task_ready(
        self,
        task: Task,
        all_tasks: Dict[str, Task]
    ) -> bool:
        """Check if task is ready for execution"""
        if task.status != TaskStatus.PENDING:
            return False
            
        # Check dependencies
        for dep_id in task.dependencies:
            dep_task = all_tasks.get(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
                
        return True
```

### 2. Task Handlers

Implementation of task handlers:

```python
class TaskHandlers:
    """Collection of task handlers"""
    
    def __init__(self, llm_manager: LLMManager):
        self.llm_manager = llm_manager
        
    async def process_text(
        self,
        params: dict,
        workflow_params: dict
    ) -> dict:
        """Process text using LLM"""
        text = params.get('text')
        if not text:
            raise ValueError("No text provided")
            
        response = await self.llm_manager.generate(
            text,
            params.get('model', 'gpt-4'),
            **params.get('model_params', {})
        )
        
        return {
            'processed_text': response,
            'model_used': params.get('model')
        }
        
    async def analyze_sentiment(
        self,
        params: dict,
        workflow_params: dict
    ) -> dict:
        """Analyze text sentiment"""
        text = params.get('text')
        if not text:
            raise ValueError("No text provided")
            
        # Use sentiment analysis model
        sentiment = await self._analyze_sentiment(text)
        
        return {
            'sentiment': sentiment,
            'confidence': sentiment['confidence']
        }
        
    async def generate_summary(
        self,
        params: dict,
        workflow_params: dict
    ) -> dict:
        """Generate text summary"""
        text = params.get('text')
        if not text:
            raise ValueError("No text provided")
            
        prompt = f"Please summarize this text:\n{text}"
        summary = await self.llm_manager.generate(
            prompt,
            params.get('model', 'gpt-4')
        )
        
        return {
            'summary': summary,
            'length': len(summary.split())
        }
```

## Task Orchestration

### 1. Task Scheduler

Implementation of task scheduler:

```python
class TaskScheduler:
    """Schedule and manage task execution"""
    
    def __init__(self):
        self.schedules: Dict[str, dict] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.task_results: Dict[str, Any] = {}
        
    async def schedule_task(
        self,
        task_id: str,
        handler: Callable,
        schedule: dict,
        params: Dict[str, Any]
    ):
        """Schedule task execution"""
        self.schedules[task_id] = {
            'handler': handler,
            'schedule': schedule,
            'params': params,
            'next_run': self._calculate_next_run(schedule)
        }
        
        # Start scheduling
        self.running_tasks[task_id] = asyncio.create_task(
            self._run_scheduled_task(task_id)
        )
        
    async def cancel_task(self, task_id: str):
        """Cancel scheduled task"""
        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
            del self.running_tasks[task_id]
            del self.schedules[task_id]
            
    async def get_task_result(
        self,
        task_id: str
    ) -> Optional[Any]:
        """Get task execution result"""
        return self.task_results.get(task_id)
        
    async def _run_scheduled_task(self, task_id: str):
        """Run scheduled task"""
        schedule = self.schedules[task_id]
        
        while True:
            try:
                # Wait until next run
                now = datetime.now()
                next_run = schedule['next_run']
                if next_run > now:
                    await asyncio.sleep(
                        (next_run - now).total_seconds()
                    )
                    
                # Execute task
                result = await schedule['handler'](
                    schedule['params']
                )
                self.task_results[task_id] = result
                
                # Calculate next run
                schedule['next_run'] = self._calculate_next_run(
                    schedule['schedule']
                )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    f"Task {task_id} execution failed: {e}"
                )
                await asyncio.sleep(60)  # Retry after 1 minute
```

## State Machines

### 1. State Machine Engine

Implementation of state machine:

```python
class State:
    """State machine state"""
    
    def __init__(
        self,
        name: str,
        handlers: Dict[str, Callable]
    ):
        self.name = name
        self.handlers = handlers
        
    async def handle_event(
        self,
        event: str,
        context: dict
    ) -> Optional[str]:
        """Handle event in this state"""
        handler = self.handlers.get(event)
        if handler:
            return await handler(context)
        return None

class StateMachine:
    """State machine implementation"""
    
    def __init__(self):
        self.states: Dict[str, State] = {}
        self.transitions: Dict[str, Dict[str, str]] = {}
        self.current_state: Optional[str] = None
        self.context: Dict[str, Any] = {}
        
    def add_state(
        self,
        name: str,
        handlers: Dict[str, Callable]
    ):
        """Add state to machine"""
        self.states[name] = State(name, handlers)
        self.transitions[name] = {}
        
    def add_transition(
        self,
        from_state: str,
        to_state: str,
        event: str
    ):
        """Add state transition"""
        if from_state not in self.states:
            raise ValueError(f"Unknown state: {from_state}")
        if to_state not in self.states:
            raise ValueError(f"Unknown state: {to_state}")
            
        self.transitions[from_state][event] = to_state
        
    def set_initial_state(self, state: str):
        """Set initial state"""
        if state not in self.states:
            raise ValueError(f"Unknown state: {state}")
        self.current_state = state
        
    async def handle_event(
        self,
        event: str,
        context_update: Optional[dict] = None
    ):
        """Handle event"""
        if not self.current_state:
            raise ValueError("No current state")
            
        # Update context
        if context_update:
            self.context.update(context_update)
            
        # Handle event in current state
        state = self.states[self.current_state]
        result = await state.handle_event(event, self.context)
        
        # Check for transition
        next_state = self.transitions[self.current_state].get(
            event
        )
        if next_state:
            self.current_state = next_state
            
        return result
```

## Event-Driven Workflows

### 1. Event Router

Implementation of event-driven workflow router:

```python
class EventRouter:
    """Route events to workflows"""
    
    def __init__(
        self,
        workflow_engine: WorkflowEngine
    ):
        self.workflow_engine = workflow_engine
        self.routes: Dict[str, List[dict]] = {}
        
    def add_route(
        self,
        event_type: str,
        workflow: str,
        params_mapper: Callable
    ):
        """Add event route"""
        if event_type not in self.routes:
            self.routes[event_type] = []
            
        self.routes[event_type].append({
            'workflow': workflow,
            'params_mapper': params_mapper
        })
        
    async def route_event(self, event: dict):
        """Route event to workflows"""
        event_type = event.get('type')
        if not event_type:
            raise ValueError("Event has no type")
            
        routes = self.routes.get(event_type, [])
        for route in routes:
            # Map event to workflow params
            params = await route['params_mapper'](event)
            
            # Start workflow
            await self.workflow_engine.start_workflow(
                route['workflow'],
                params
            )

class EventProcessor:
    """Process workflow events"""
    
    def __init__(
        self,
        event_router: EventRouter
    ):
        self.event_router = event_router
        self.processors: Dict[str, Callable] = {}
        
    def register_processor(
        self,
        event_type: str,
        processor: Callable
    ):
        """Register event processor"""
        self.processors[event_type] = processor
        
    async def process_event(self, event: dict):
        """Process and route event"""
        event_type = event.get('type')
        if not event_type:
            raise ValueError("Event has no type")
            
        # Process event
        processor = self.processors.get(event_type)
        if processor:
            event = await processor(event)
            
        # Route event
        await self.event_router.route_event(event)
```

Remember to:
- Define clear workflow patterns
- Handle task dependencies
- Implement proper error handling
- Monitor workflow execution
- Manage state transitions
- Handle event routing
- Document workflow patterns