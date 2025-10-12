"""Route action executor - mutates state via direct access or method calls."""


class RouteExecutor:
    """Executes route actions by mutating state containers."""
    
    def __init__(self, chatguide):
        self.guide = chatguide
        self.state = chatguide.state
        self.config = chatguide.config
    
    def execute(self, route: dict) -> bool:
        """Execute a route action.
        
        Supports two formats:
        1. Direct field assignment: action="set", path="interaction.tones", value=[...]
        2. Method calls: action="flow.advance", force=true
        """
        action = route.get("action")
        if not action:
            return False
        
        # Direct field assignment
        if action == "set":
            return self._set_field(route)
        
        # Append to field (for lists/strings)
        if action == "append":
            return self._append_field(route)
        
        # Special actions
        if action == "process_corrections":
            return self._process_corrections(route)
        
        # Method call (container.method)
        if '.' in action:
            container, method = action.split('.', 1)
            return self._call_method(container, method, route)
        
        return False
    
    def _set_field(self, route: dict) -> bool:
        """Set a field value directly.
        
        Example:
            action: "set"
            path: "interaction.tones"
            value: ["friendly", "playful"]
            
        Or with dynamic evaluation:
            value: "task_results.get('get_name')"  # Will be evaluated
        """
        path = route.get("path", "")
        value = route.get("value")
        
        if not path or value is None:
            return False
        
        # If value is a string expression, try to evaluate it
        if isinstance(value, str) and ("task_results" in value or "turn_count" in value):
            try:
                eval_context = {
                    "__builtins__": {},
                    "task_results": self.state.tracker.results,
                    "turn_count": self.state.interaction.turn_count,
                    "batch_index": self.state.flow.current_index,
                }
                value = eval(value, eval_context)
            except Exception:
                pass  # Keep original value if eval fails
        
        # Parse path (e.g., "interaction.tones")
        parts = path.split('.')
        obj = self.state
        
        # Navigate to parent
        for part in parts[:-1]:
            obj = getattr(obj, part, None)
            if obj is None:
                return False
        
        # Set final attribute
        try:
            setattr(obj, parts[-1], value)
            if self.state.debug:
                print(f"Set {path} = {value}")
            return True
        except Exception:
            return False
    
    def _append_field(self, route: dict) -> bool:
        """Append to a field (list or string).
        
        Example:
            action: "append"
            path: "conversation.memory"
            value: "\\nUser is VIP"
        """
        path = route.get("path", "")
        value = route.get("value")
        
        if not path or value is None:
            return False
        
        # Navigate to target
        parts = path.split('.')
        obj = self.state
        for part in parts[:-1]:
            obj = getattr(obj, part, None)
            if obj is None:
                return False
        
        # Append
        try:
            current = getattr(obj, parts[-1])
            if isinstance(current, list):
                current.append(value)
            elif isinstance(current, str):
                setattr(obj, parts[-1], current + value)
            else:
                return False
            
            if self.state.debug:
                print(f"Appended to {path}")
            return True
        except Exception:
            return False
    
    def _call_method(self, container: str, method: str, route: dict) -> bool:
        """Call a method on a container.
        
        Example:
            action: "flow.advance"
            force: true
            target: 2
        """
        containers = {
            'flow': self.state.flow,
            'tracker': self.state.tracker,
            'conversation': self.state.conversation,
            'interaction': self.state.interaction,
            'participants': self.state.participants
        }
        
        cont = containers.get(container)
        if not cont or not hasattr(cont, method):
            return False
        
        # Get method
        method_fn = getattr(cont, method)
        
        # Extract params (exclude 'action' and 'condition')
        params = {k: v for k, v in route.items() 
                  if k not in ['action', 'condition']}
        
        try:
            method_fn(**params)
            return True
        except Exception as e:
            if self.state.debug:
                print(f"Route execution error: {e}")
            return False
    
    def _process_corrections(self, route: dict) -> bool:
        """Parse and apply corrections from detect_info_updates.
        
        Parses strings like:
            "update: get_name = John, update: get_age = 32"
        
        And updates tracker.results accordingly.
        Note: History name updates happen via the separate route that sets participants.user.
        """
        correction_text = self.state.tracker.results.get('detect_info_updates', '')
        if not correction_text or 'update:' not in correction_text:
            return False
        
        # Split by "update:" to get individual corrections
        updates = correction_text.split('update:')
        
        for update in updates:
            update = update.strip()
            if not update or '=' not in update:
                continue
            
            # Parse "task_id = value" (update: prefix already removed)
            try:
                # Remove any leading comma from split
                update = update.lstrip(',').strip()
                
                # Split by '='
                task_id, value = update.split('=', 1)
                task_id = task_id.strip()
                value = value.strip().rstrip(',')  # Remove trailing comma too
                
                # Update the tracker
                old_value = self.state.tracker.results.get(task_id, "NOT_SET")
                self.state.tracker.results[task_id] = value
                
                if self.state.debug:
                    print(f"Correction applied: {task_id} '{old_value}' -> '{value}'", flush=True)
            except Exception as e:
                if self.state.debug:
                    print(f"Failed to parse correction: '{update}' - {e}", flush=True)
        
        return True
