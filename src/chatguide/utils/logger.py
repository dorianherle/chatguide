"""Structured logging for ChatGuide."""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime


class ChatGuideLogger:
    """Structured logger for ChatGuide with configurable output."""
    
    def __init__(self, name: str = "chatguide", level: int = logging.INFO, 
                 format_type: str = "json", output_file: Optional[str] = None):
        """Initialize logger.
        
        Args:
            name: Logger name
            level: Logging level (DEBUG, INFO, WARNING, ERROR)
            format_type: "json" or "text"
            output_file: Optional file path for log output
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.format_type = format_type
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        
        if format_type == "json":
            console_handler.setFormatter(JSONFormatter())
        else:
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
        
        self.logger.addHandler(console_handler)
        
        # File handler if specified
        if output_file:
            file_handler = logging.FileHandler(output_file)
            file_handler.setLevel(level)
            if format_type == "json":
                file_handler.setFormatter(JSONFormatter())
            else:
                file_handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                ))
            self.logger.addHandler(file_handler)
    
    def log_event(self, event_type: str, data: Dict[str, Any], level: str = "info"):
        """Log a structured event.
        
        Args:
            event_type: Type of event (e.g., "task_complete", "error")
            data: Event data
            level: Log level (debug, info, warning, error)
        """
        log_data = {
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            **data
        }
        
        log_func = getattr(self.logger, level.lower())
        if self.format_type == "json":
            log_func(json.dumps(log_data))
        else:
            log_func(f"[{event_type}] {json.dumps(data)}")
    
    def task_start(self, task_id: str, description: str):
        """Log task start."""
        self.log_event("task_start", {"task_id": task_id, "description": description})
    
    def task_complete(self, task_id: str, key: str, value: Any):
        """Log task completion."""
        self.log_event("task_complete", {"task_id": task_id, "key": key, "value": str(value)})
    
    def tool_call(self, tool: str, args: Dict[str, Any]):
        """Log tool execution."""
        self.log_event("tool_call", {"tool": tool, "args": args})
    
    def adjustment_fired(self, name: str, actions: list):
        """Log adjustment firing."""
        self.log_event("adjustment_fired", {"name": name, "actions": actions})
    
    def error(self, error_type: str, error: str, context: Dict[str, Any]):
        """Log error."""
        self.log_event("error", {"error_type": error_type, "error": error, **context}, level="error")
    
    def llm_response(self, reply: str, was_silent: bool, task_results: list):
        """Log LLM response."""
        self.log_event("llm_response", {
            "reply_length": len(reply),
            "was_silent": was_silent,
            "task_results": task_results
        })
    
    def checkpoint_saved(self, path: str, session_id: Optional[str]):
        """Log checkpoint save."""
        self.log_event("checkpoint_saved", {"path": path, "session_id": session_id})
    
    def checkpoint_loaded(self, path: str, session_id: Optional[str]):
        """Log checkpoint load."""
        self.log_event("checkpoint_loaded", {"path": path, "session_id": session_id})


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logs."""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

