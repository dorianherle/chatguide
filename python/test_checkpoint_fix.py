"""Test that checkpoint restore properly syncs execution._completed."""
import sys
sys.path.insert(0, 'src')

from chatguide import ChatGuide
from chatguide.core import ExecutionState

print('=== Testing checkpoint restore for execution._completed ===')

# Create a mock checkpoint with completed tasks
checkpoint = {
    'version': '1.0',
    'timestamp': '2025-01-01T00:00:00',
    'session_id': 'test_session',
    'session_metadata': {},
    'state': {'user_name': 'John', 'age': '25'},
    'plan': {
        'blocks': [['greet'], ['get_name', 'get_age'], ['confirm']],
        'current_index': 2
    },
    'tone': [],
    'completed_tasks': ['greet', 'get_name', 'get_age'],
    'execution_status': 'awaiting_input',
    'errors': [],
    'retry_count': 0,
    'context': {'session_id': 'test_session', 'metadata': {}, 'history': [], 'created_at': '2025-01-01T00:00:00'},
    'fired_adjustments': [],
    'metrics': {},
    'config': {
        'tasks': {
            'greet': {'description': 'Greet user', 'expects': [], 'tools': [], 'silent': False},
            'get_name': {'description': 'Get name', 'expects': ['user_name'], 'tools': [], 'silent': False},
            'get_age': {'description': 'Get age', 'expects': ['age'], 'tools': [], 'silent': False},
            'confirm': {'description': 'Confirm', 'expects': [], 'tools': [], 'silent': False}
        },
        'tone_definitions': {},
        'guardrails': '',
        'language': 'en'
    }
}

# Restore from checkpoint
cg = ChatGuide.from_checkpoint(checkpoint, api_key='test_key')

# Check execution._completed is properly restored
print(f'execution._completed: {cg.execution._completed}')
print('Expected: ["greet", "get_name", "get_age"]')

# Verify task statuses
print('\nTask statuses:')
for task in cg.plan.get_all_tasks():
    print(f'  Task {task.id}: status={task.status}, is_completed={task.is_completed()}')

# Verify consistency
task_completed = [t.id for t in cg.plan.get_all_tasks() if t.is_completed()]
exec_completed = cg.execution._completed

print(f'\nTask status completed: {task_completed}')
print(f'Execution completed: {exec_completed}')

is_consistent = set(task_completed) == set(exec_completed)
print(f'Are they consistent? {is_consistent}')

if is_consistent and set(exec_completed) == {'greet', 'get_name', 'get_age'}:
    print('\n✅ PASS: Checkpoint restore correctly syncs execution._completed')
else:
    print('\n❌ FAIL: Checkpoint restore does NOT sync execution._completed')
    sys.exit(1)

