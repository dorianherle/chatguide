"""Pytest configuration and fixtures for ChatGuide tests."""

import pytest
from pathlib import Path


@pytest.fixture
def sample_config():
    """Sample configuration dictionary."""
    return {
        "state": {
            "user_name": None,
            "age": None
        },
        "plan": [
            ["greet"],
            ["get_name", "get_age"],
            ["confirm"]
        ],
        "tasks": {
            "greet": {
                "description": "Welcome the user"
            },
            "get_name": {
                "description": "Ask for user's name",
                "expects": ["user_name"]
            },
            "get_age": {
                "description": "Ask for user's age",
                "expects": ["age"]
            },
            "confirm": {
                "description": "Confirm the details"
            }
        },
        "tone": ["professional"]
    }


@pytest.fixture
def test_checkpoint():
    """Sample checkpoint data."""
    return {
        "version": "1.0",
        "timestamp": "2025-01-01T00:00:00",
        "session_id": "test_session",
        "session_metadata": {},
        "state": {
            "user_name": "Alice",
            "age": 30
        },
        "plan": {
            "blocks": [["greet"], ["get_name", "get_age"]],
            "current_index": 1
        },
        "tone": ["professional"],
        "completed_tasks": ["greet"],
        "execution_status": "awaiting_input",
        "data_extractions": {
            "user_name": {
                "value": "Alice",
                "extracted_by": "get_name",
                "validated": True
            }
        },
        "errors": [],
        "retry_count": 0,
        "conversation_history": [
            {"role": "assistant", "content": "Hello!"},
            {"role": "user", "content": "Hi, I'm Alice"}
        ],
        "fired_adjustments": [],
        "metrics": {
            "llm_calls": 1,
            "tokens_used": 50,
            "total_duration_ms": 1000,
            "task_completions": 1,
            "errors": 0
        }
    }

