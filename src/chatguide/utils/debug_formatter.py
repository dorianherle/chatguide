"""Debug output formatter - beautiful console display."""

from typing import Dict, Any


class ResponseFormatter:
    """Formats AI responses beautifully."""
    
    @staticmethod
    def format_reply(reply, show_tasks: bool = True) -> str:
        """Format ChatGuideReply beautifully.
        
        Args:
            reply: ChatGuideReply object
            show_tasks: If True, show task breakdown
        """
        lines = []
        lines.append("")
        lines.append("=" * 70)
        lines.append("  AI RESPONSE")
        lines.append("=" * 70)
        
        # Assistant reply (full, no truncation)
        lines.append("")
        lines.append("MESSAGE:")
        lines.append(reply.assistant_reply)
        
        if show_tasks:
            # Batch tasks
            if reply.tasks:
                lines.append("")
                lines.append("BATCH TASKS:")
                for task in reply.tasks:
                    if task.result:
                        result_preview = task.result if len(task.result) <= 50 else task.result[:47] + "..."
                        lines.append(f"  [x] {task.task_id} = \"{result_preview}\"")
                    else:
                        lines.append(f"  [ ] {task.task_id} = (empty)")
            
            # Persistent tasks
            if reply.persistent_tasks:
                lines.append("")
                lines.append("PERSISTENT TASKS:")
                for task in reply.persistent_tasks:
                    if task.result:
                        result_preview = task.result if len(task.result) <= 50 else task.result[:47] + "..."
                        lines.append(f"  [*] {task.task_id} = \"{result_preview}\"")
        
        lines.append("")
        lines.append("=" * 70)
        
        return "\n".join(lines)


class DebugFormatter:
    """Formats debug information in a readable, beautiful way."""
    
    @staticmethod
    def format_state(state_dict: Dict[str, Any], show_prompt: bool = False, 
                     prompt: str = "") -> str:
        """Format state dictionary into beautiful output.
        
        Args:
            state_dict: Output from state.to_dict()
            show_prompt: If True, include full prompt
            prompt: The prompt text
        """
        flow = state_dict['flow']
        tasks = state_dict['tasks']
        conv = state_dict['conversation']
        tones = state_dict.get('tones', {'active': []})
        routes = state_dict.get('routes', {})
        parts = state_dict['participants']
        
        lines = []
        lines.append("")
        lines.append("=" * 70)
        lines.append("  CHATGUIDE DEBUG STATE")
        lines.append("=" * 70)
        
        # Flow
        lines.append("")
        lines.append("FLOW:")
        lines.append(f"  Batches:  {len(flow['batches'])} total")
        lines.append(f"  Current:  {flow['current_index']} -> {flow['batches'][flow['current_index']] if flow['current_index'] < len(flow['batches']) else 'FINISHED'}")
        
        next_batch = flow['batches'][flow['current_index'] + 1] if flow['current_index'] + 1 < len(flow['batches']) else None
        if next_batch:
            lines.append(f"  Next:     {flow['current_index'] + 1} -> {next_batch}")
        
        if flow['persistent']:
            lines.append(f"  Persistent: {', '.join(flow['persistent'])}")
        
        # Tracker
        lines.append("")
        lines.append("TRACKER:")
        
        # Status breakdown
        completed = [k for k, v in tasks['status'].items() if v == 'completed']
        pending = [k for k, v in tasks['status'].items() if v == 'pending']
        failed = [k for k, v in tasks['status'].items() if v == 'failed']
        active = [k for k, v in tasks['status'].items() if v == 'active']
        
        if completed:
            lines.append(f"  Completed: {', '.join(completed)}")
        if pending:
            lines.append(f"  Pending:   {', '.join(pending)}")
        if failed:
            lines.append(f"  Failed:    {', '.join(failed)}")
        if active:
            lines.append(f"  Active:    {', '.join(active)}")
        
        # Results
        if tasks['results']:
            lines.append("")
            lines.append("  Results:")
            for k, v in tasks['results'].items():
                if k not in ['detect_info_updates']:
                    display_v = v if len(v) <= 40 else v[:37] + "..."
                    lines.append(f"    {k} = \"{display_v}\"")
        
        # Attempts (only show > 0)
        attempts = {k: v for k, v in tasks['attempts'].items() if v > 0}
        if attempts:
            lines.append("")
            lines.append(f"  Attempts: {', '.join([f'{k}={v}' for k, v in attempts.items()])}")
        
        # Conversation
        lines.append("")
        lines.append("CONVERSATION:")
        memory_preview = conv['memory'][:60] + "..." if len(conv['memory']) > 60 else conv['memory']
        lines.append(f"  Memory: \"{memory_preview}\"")
        lines.append(f"  History: {len(conv['history'])} messages")
        
        if conv['history']:
            lines.append("  Recent:")
            for msg in conv['history'][-3:]:  # Last 3 messages
                preview = msg if len(msg) <= 60 else msg[:57] + "..."
                lines.append(f"    {preview}")
        
        # Tones & Turn info
        lines.append("")
        lines.append("CONVERSATION:")
        lines.append(f"  Tones: {', '.join(tones['active'])}")
        lines.append(f"  Turn:  {conv['turn_count']}")
        
        # Participants
        lines.append("")
        lines.append("PARTICIPANTS:")
        lines.append(f"  Bot:  {parts['chatbot']}")
        lines.append(f"  User: {parts['user']}")
        
        lines.append("")
        lines.append("=" * 70)
        
        # Optional prompt
        if show_prompt and prompt:
            lines.append("")
            lines.append("FULL PROMPT:")
            lines.append("-" * 70)
            lines.append(prompt)
            lines.append("-" * 70)
        
        return "\n".join(lines)
    
    @staticmethod
    def format_compact(state_dict: Dict[str, Any]) -> str:
        """Compact one-line debug output."""
        flow = state_dict['flow']
        tones = state_dict.get('tones', {'active': []})
        tasks = state_dict['tasks']
        conv = state_dict['conversation']
        
        current = state_dict.get('current_tasks', [])
        completed_count = sum(1 for s in tasks['status'].values() if s == 'completed')
        
        return (f"Turn {conv['turn_count']} | "
                f"Batch {flow['current_index']}/{len(flow['batches'])} | "
                f"Current: {', '.join(current) if current else 'none'} | "
                f"Completed: {completed_count}")

