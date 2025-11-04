"""Comprehensive test suite for ChatGuide - validates all 10/10 features."""

import pytest
import json
import os
from pathlib import Path
from chatguide import ChatGuide
from chatguide.schemas import TaskDefinition
from chatguide.plan import Plan
from chatguide.state import State


class TestStateManagement:
    """Test core state functionality."""
    
    def test_state_get_set(self):
        state = State()
        state.set("user_name", "John")
        assert state.get("user_name") == "John"
        assert state.get("missing", "default") == "default"
    
    def test_state_update(self):
        state = State()
        state.update({"name": "Alice", "age": 30})
        assert state.get("name") == "Alice"
        assert state.get("age") == 30
    
    def test_template_resolution(self):
        state = State({"name": "Bob", "room": 305})
        result = state.resolve_template("Hello {{name}}, room {{room}}")
        assert result == "Hello Bob, room 305"
    
    def test_template_dict(self):
        state = State({"city": "NYC", "country": "USA"})
        template = {"location": "{{city}}, {{country}}"}
        result = state.resolve_template(template)
        assert result == {"location": "NYC, USA"}


class TestPlanManipulation:
    """Test plan and flow control."""
    
    def test_plan_creation(self):
        plan = Plan([["task1"], ["task2", "task3"]])
        assert len(plan._blocks) == 2
        assert plan.current_index == 0
    
    def test_plan_advance(self):
        plan = Plan([["task1"], ["task2"]])
        plan.advance()
        assert plan.current_index == 1
        assert plan.get_current_block() == ["task2"]
    
    def test_plan_jump(self):
        plan = Plan([["task1"], ["task2"], ["task3"]])
        plan.jump_to(2)
        assert plan.current_index == 2
    
    def test_plan_insert_block(self):
        plan = Plan([["task1"], ["task3"]])
        plan.insert_block(1, ["task2"])
        assert plan._blocks == [["task1"], ["task2"], ["task3"]]
    
    def test_plan_is_finished(self):
        plan = Plan([["task1"]])
        assert not plan.is_finished()
        plan.advance()
        assert plan.is_finished()


class TestComprehensiveState:
    """Test professional state inspection features."""
    
    def test_get_state_structure(self):
        cg = ChatGuide(api_key="test")
        cg.plan = Plan([["greet"], ["get_name", "get_age"]])
        cg.tasks = {
            "greet": TaskDefinition(description="Greet user"),
            "get_name": TaskDefinition(description="Get name", expects=["user_name"]),
            "get_age": TaskDefinition(description="Get age", expects=["age"])
        }
        
        state = cg.get_state()
        
        # Check all required keys
        assert "execution" in state
        assert "progress" in state
        assert "tasks" in state
        assert "data" in state
        assert "data_extractions" in state
        assert "data_coverage" in state
        assert "tone" in state
        assert "adjustments" in state
        assert "conversation" in state
    
    def test_task_metadata(self):
        cg = ChatGuide(api_key="test")
        cg.tasks = {
            "get_name": TaskDefinition(description="Get name", expects=["user_name"], silent=False)
        }
        
        state = cg.get_state()
        task_meta = state['tasks']['get_name']
        
        assert task_meta['description'] == "Get name"
        assert task_meta['expects'] == ["user_name"]
        assert task_meta['is_silent'] == False
        assert 'status' in task_meta
    
    def test_data_coverage(self):
        cg = ChatGuide(api_key="test")
        cg.tasks = {
            "get_name": TaskDefinition(description="Get name", expects=["user_name"]),
            "get_age": TaskDefinition(description="Get age", expects=["age"])
        }
        cg.state.set("user_name", "John")
        
        state = cg.get_state()
        coverage = state['data_coverage']
        
        assert "user_name" in coverage['collected_keys']
        assert "age" in coverage['missing_keys']
        assert coverage['coverage_percent'] == 50


class TestHelperMethods:
    """Test helper methods for easy access."""
    
    def test_get_current_task(self):
        cg = ChatGuide(api_key="test")
        cg.plan = Plan([["task1", "task2"]])
        
        # Initially first task
        assert cg.get_current_task() == "task1"
        
        # After completing first task
        cg._completed_tasks.append("task1")
        assert cg.get_current_task() == "task2"
    
    def test_get_progress(self):
        cg = ChatGuide(api_key="test")
        cg.plan = Plan([["task1"], ["task2"], ["task3"], ["task4"]])
        cg._completed_tasks = ["task1", "task2"]
        
        progress = cg.get_progress()
        assert progress['completed'] == 2
        assert progress['total'] == 4
        assert progress['percent'] == 50
    
    def test_get_next_tasks(self):
        cg = ChatGuide(api_key="test")
        cg.plan = Plan([["task1"], ["task2"], ["task3"]])
        cg._completed_tasks = ["task1"]
        
        next_tasks = cg.get_next_tasks(limit=2)
        assert "task2" in next_tasks
        assert len(next_tasks) <= 2
    
    def test_is_waiting_for_user(self):
        cg = ChatGuide(api_key="test")
        cg._execution_status = "awaiting_input"
        assert cg.is_waiting_for_user() == True
        
        cg._execution_status = "processing"
        assert cg.is_waiting_for_user() == False


class TestSessionPersistence:
    """Test checkpoint/resume functionality."""
    
    def test_checkpoint_creation(self):
        cg = ChatGuide(api_key="test")
        cg.state.set("user_name", "Alice")
        cg._completed_tasks = ["greet"]
        cg._session_id = "test_session"
        
        checkpoint = cg.checkpoint()
        
        assert checkpoint['state']['user_name'] == "Alice"
        assert "greet" in checkpoint['completed_tasks']
        assert checkpoint['session_id'] == "test_session"
        assert 'version' in checkpoint
        assert 'timestamp' in checkpoint
    
    def test_checkpoint_save_load(self, tmp_path):
        # Create and save checkpoint
        cg1 = ChatGuide(api_key="test")
        cg1.state.set("city", "NYC")
        cg1._completed_tasks = ["task1"]
        cg1._session_id = "session123"
        
        checkpoint_path = tmp_path / "test_checkpoint.json"
        cg1.save_checkpoint(str(checkpoint_path))
        
        assert checkpoint_path.exists()
        
        # Load checkpoint
        cg2 = ChatGuide.load_checkpoint(str(checkpoint_path), api_key="test")
        
        assert cg2.state.get("city") == "NYC"
        assert "task1" in cg2._completed_tasks
        assert cg2._session_id == "session123"
    
    def test_from_checkpoint(self):
        checkpoint = {
            "version": "1.0",
            "timestamp": "2025-01-01T00:00:00",
            "session_id": "test",
            "state": {"name": "Bob"},
            "plan": {"blocks": [["task1"]], "current_index": 0},
            "tone": ["professional"],
            "completed_tasks": [],
            "execution_status": "idle",
            "data_extractions": {},
            "errors": [],
            "retry_count": 0,
            "conversation_history": [],
            "fired_adjustments": [],
            "metrics": {"llm_calls": 0}
        }
        
        cg = ChatGuide.from_checkpoint(checkpoint, api_key="test")
        assert cg.state.get("name") == "Bob"
        assert cg._session_id == "test"


class TestStreamingCallbacks:
    """Test real-time streaming support."""
    
    def test_add_stream_callback(self):
        cg = ChatGuide(api_key="test")
        
        events = []
        def callback(event):
            events.append(event)
        
        cg.add_stream_callback(callback)
        assert len(cg._stream_callbacks) == 1
    
    def test_emit_event(self):
        cg = ChatGuide(api_key="test")
        
        received_events = []
        def callback(event):
            received_events.append(event)
        
        cg.add_stream_callback(callback)
        cg._emit_event({"type": "test", "data": "value"})
        
        assert len(received_events) == 1
        assert received_events[0]['type'] == "test"


class TestMetricsTelemetry:
    """Test metrics tracking."""
    
    def test_initial_metrics(self):
        cg = ChatGuide(api_key="test")
        metrics = cg.get_metrics()
        
        assert metrics['llm_calls'] == 0
        assert metrics['task_completions'] == 0
        assert metrics['errors'] == 0
    
    def test_reset_metrics(self):
        cg = ChatGuide(api_key="test")
        cg._metrics['llm_calls'] = 5
        cg._metrics['errors'] = 2
        
        cg.reset_metrics()
        
        assert cg._metrics['llm_calls'] == 0
        assert cg._metrics['errors'] == 0


class TestMiddlewareHooks:
    """Test middleware and plugin system."""
    
    def test_add_middleware(self):
        cg = ChatGuide(api_key="test")
        
        def middleware(context):
            context['modified'] = True
            return context
        
        cg.add_middleware(middleware)
        assert len(cg._middleware) == 1
    
    def test_add_task_hook(self):
        cg = ChatGuide(api_key="test")
        
        hook_calls = []
        def hook(task_id, value):
            hook_calls.append((task_id, value))
        
        cg.add_task_hook("get_name", hook)
        assert "get_name" in cg._task_hooks
        
        # Test hook execution
        cg._run_task_hooks("get_name", "Alice")
        assert len(hook_calls) == 1
        assert hook_calls[0] == ("get_name", "Alice")
    
    def test_run_middleware(self):
        cg = ChatGuide(api_key="test")
        
        def middleware(context):
            context['phase_seen'] = context.get('phase')
            return context
        
        cg.add_middleware(middleware)
        result = cg._run_middleware("before", {"test": "data"})
        
        assert result['phase_seen'] == "before"


class TestErrorTracking:
    """Test error handling and tracking."""
    
    def test_error_storage(self):
        cg = ChatGuide(api_key="test")
        
        error = {
            "type": "tool_execution",
            "tool": "test_tool",
            "error": "Test error",
            "task": "test_task"
        }
        cg._errors.append(error)
        
        state = cg.get_state()
        assert state['execution']['error_count'] == 1
        assert len(state['execution']['errors']) == 1


class TestConfigLoading:
    """Test configuration loading."""
    
    def test_load_config_structure(self, tmp_path):
        config_content = """
state:
  user_name: null

plan:
  - [greet]
  - [get_name]

tasks:
  greet:
    description: "Welcome the user"
  
  get_name:
    description: "Ask for user's name"
    expects: ["user_name"]

tone:
  - professional
"""
        config_path = tmp_path / "test_config.yaml"
        config_path.write_text(config_content)
        
        cg = ChatGuide(api_key="test")
        cg.load_config(str(config_path))
        
        assert cg.state.get("user_name") is None
        assert len(cg.plan._blocks) == 2
        assert "greet" in cg.tasks
        assert "get_name" in cg.tasks
        assert "professional" in cg.tone


class TestIntegration:
    """Integration tests for complete workflows."""
    
    def test_full_workflow_simulation(self):
        """Simulate a complete conversation flow."""
        cg = ChatGuide(api_key="test")
        
        # Setup
        cg.plan = Plan([
            ["greet"],
            ["get_name", "get_age"],
            ["confirm"]
        ])
        
        cg.tasks = {
            "greet": TaskDefinition(description="Greet user"),
            "get_name": TaskDefinition(description="Get name", expects=["user_name"]),
            "get_age": TaskDefinition(description="Get age", expects=["age"]),
            "confirm": TaskDefinition(description="Confirm details")
        }
        
        # Initial state
        state = cg.get_state()
        assert state['execution']['current_tasks'] == ["greet"]
        assert state['progress']['completed_count'] == 0
        
        # Simulate task completion
        cg._completed_tasks.append("greet")
        cg.plan.advance()
        
        state = cg.get_state()
        assert state['execution']['current_tasks'] == ["get_name", "get_age"]
        assert state['progress']['completed_count'] == 1
        
        # Complete data collection
        cg.state.set("user_name", "Alice")
        cg.state.set("age", 25)
        cg._completed_tasks.extend(["get_name", "get_age"])
        cg.plan.advance()
        
        state = cg.get_state()
        assert state['data_coverage']['coverage_percent'] == 100
        assert state['progress']['completed_count'] == 3


def test_all_features_present():
    """Meta-test: Ensure all 10/10 features are implemented."""
    cg = ChatGuide(api_key="test")
    
    # Session persistence
    assert hasattr(cg, 'checkpoint')
    assert hasattr(cg, 'save_checkpoint')
    assert hasattr(ChatGuide, 'load_checkpoint')
    assert hasattr(ChatGuide, 'from_checkpoint')
    
    # Streaming
    assert hasattr(cg, 'add_stream_callback')
    assert hasattr(cg, '_emit_event')
    
    # Metrics
    assert hasattr(cg, 'get_metrics')
    assert hasattr(cg, 'reset_metrics')
    
    # Middleware
    assert hasattr(cg, 'add_middleware')
    assert hasattr(cg, 'add_task_hook')
    
    # State inspection
    assert hasattr(cg, 'get_state')
    assert hasattr(cg, 'get_current_task')
    assert hasattr(cg, 'get_progress')
    assert hasattr(cg, 'get_next_tasks')
    assert hasattr(cg, 'is_waiting_for_user')
    
    # Logging
    assert hasattr(cg, 'logger')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

