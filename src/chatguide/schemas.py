"""Pydantic schemas for ChatGuide data structures."""

from pydantic import BaseModel
from typing import List


class Task(BaseModel):
    """Task definition."""
    key: str
    description: str


class TaskResult(BaseModel):
    """Result from a completed task."""
    task_id: str
    result: str


class ChatGuideReply(BaseModel):
    """LLM response envelope."""
    tasks: List[TaskResult]
    persistent_tasks: List[TaskResult] = []
    assistant_reply: str
