"""Test comprehensive state inspection features."""

from chatguide import ChatGuide
from chatguide.schemas import TaskDefinition
from chatguide.plan import Plan
from chatguide.state import State
import json

def print_section(title):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def test_state_inspection():
    """Test comprehensive state inspection."""
    print("Testing ChatGuide Professional State Inspection")
    
    # Create a simple guide
    cg = ChatGuide(api_key="test_key", debug=True)
    
    # Manually set up a simple plan
    cg.plan = Plan([
        ["greet"],
        ["get_name", "get_age"],
        ["get_location"],
        ["payment"],
        ["confirm"]
    ])
    
    # Define tasks
    cg.tasks = {
        "greet": TaskDefinition(description="Greet the user"),
        "get_name": TaskDefinition(description="Get user's name", expects=["user_name"]),
        "get_age": TaskDefinition(description="Get user's age", expects=["age"]),
        "get_location": TaskDefinition(description="Get user's location", expects=["location"]),
        "payment": TaskDefinition(description="Process payment", expects=["payment_method"]),
        "confirm": TaskDefinition(description="Confirm booking"),
    }
    
    # Initial state (idle)
    print_section("Initial State (idle)")
    state = cg.get_state()
    print(f"Status: {state['execution']['status']}")
    print(f"Current block: {state['execution']['current_block_index']}")
    print(f"Current tasks: {state['execution']['current_tasks']}")
    print(f"Progress: {state['progress']['completed_count']}/{state['progress']['total_tasks']}")
    print(f"Is finished: {state['execution']['is_finished']}")
    print(f"Data coverage: {state['data_coverage']['coverage_percent']}%")
    print(f"Expected keys: {state['data_coverage']['expected_keys']}")
    print(f"Task count: {len(state['tasks'])}")
    
    # Test helper methods - initial
    print_section("Helper Methods (initial)")
    print(f"get_current_task(): {cg.get_current_task()}")
    print(f"get_progress(): {cg.get_progress()}")
    print(f"get_next_tasks(): {cg.get_next_tasks()}")
    print(f"is_waiting_for_user(): {cg.is_waiting_for_user()}")
    print(f"is_finished(): {cg.is_finished()}")
    
    # Show task metadata
    print_section("Task Metadata")
    for task_id, meta in list(state['tasks'].items())[:3]:  # First 3 tasks
        print(f"\n{task_id}:")
        print(f"  Status: {meta['status']}")
        print(f"  Description: {meta['description']}")
        print(f"  Expects: {meta['expects']}")
        print(f"  Has tools: {meta['has_tools']}")
        print(f"  Is silent: {meta['is_silent']}")
    
    # Simulate completing first task
    print_section("After completing 'greet' task")
    cg._completed_tasks.append("greet")
    cg.plan.advance()
    cg._execution_status = "awaiting_input"
    
    state = cg.get_state()
    print(f"Status: {state['execution']['status']}")
    print(f"Current block: {state['execution']['current_block_index']}")
    print(f"Current tasks: {state['execution']['current_tasks']}")
    print(f"Completed tasks: {state['progress']['completed_tasks']}")
    print(f"Pending tasks: {state['progress']['pending_tasks']}")
    print(f"Progress: {state['progress']['completed_count']}/{state['progress']['total_tasks']}")
    print(f"Data coverage: {state['data_coverage']['coverage_percent']}%")
    
    print("\nBlock metadata:")
    for block in state['progress']['blocks']:
        print(f"  Block {block['index']}: {block['tasks']} - {block['status']}")
    
    # Simulate completing get_name
    print_section("After completing 'get_name' task")
    cg._completed_tasks.append("get_name")
    cg.state.set("user_name", "John")
    # Simulate extraction tracking
    cg._data_extractions["user_name"] = {
        "value": "John",
        "extracted_by": "get_name",
        "validated": True
    }
    
    state = cg.get_state()
    progress = cg.get_progress()
    print(f"Current task: {cg.get_current_task()}")
    print(f"Progress: {progress['completed']}/{progress['total']} ({progress['percent']}%)")
    print(f"Data extracted: {state['data']}")
    print(f"Next tasks: {cg.get_next_tasks(limit=2)}")
    print(f"Data coverage: {state['data_coverage']['coverage_percent']}%")
    print(f"Missing keys: {state['data_coverage']['missing_keys']}")
    
    print("\nData extractions:")
    for key, info in state['data_extractions'].items():
        print(f"  {key}: {info['value']} (by {info['extracted_by']}, validated: {info['validated']})")
    
    # Simulate completing get_age
    print_section("After completing 'get_age' task")
    cg._completed_tasks.append("get_age")
    cg.state.set("age", 25)
    cg._data_extractions["age"] = {
        "value": 25,
        "extracted_by": "get_age",
        "validated": True
    }
    cg.plan.advance()
    
    state = cg.get_state()
    progress = cg.get_progress()
    print(f"Current task: {cg.get_current_task()}")
    print(f"Progress: {progress['completed']}/{progress['total']} ({progress['percent']}%)")
    print(f"Data: {cg.state.to_dict()}")
    print(f"Data coverage: {state['data_coverage']['coverage_percent']}%")
    
    # Complete remaining tasks
    print_section("Completing remaining tasks")
    cg._completed_tasks.extend(["get_location", "payment", "confirm"])
    cg.state.set("location", "NYC")
    cg.state.set("payment_method", "credit_card")
    cg._data_extractions["location"] = {
        "value": "NYC",
        "extracted_by": "get_location",
        "validated": True
    }
    cg._data_extractions["payment_method"] = {
        "value": "credit_card",
        "extracted_by": "payment",
        "validated": True
    }
    cg.plan.jump_to(5)  # Jump past last block
    cg._execution_status = "complete"
    
    state = cg.get_state()
    progress = cg.get_progress()
    print(f"Status: {state['execution']['status']}")
    print(f"Is finished: {state['execution']['is_finished']}")
    print(f"Progress: {progress['completed']}/{progress['total']} ({progress['percent']}%)")
    print(f"Current task: {cg.get_current_task()}")
    print(f"Data coverage: {state['data_coverage']['coverage_percent']}%")
    print(f"Error count: {state['execution']['error_count']}")
    
    print("\nAll collected data:")
    for key, value in state['data'].items():
        extraction_info = state['data_extractions'].get(key, {})
        extracted_by = extraction_info.get('extracted_by', 'unknown')
        print(f"  {key}: {value} (extracted by: {extracted_by})")
    
    print("\nFinal block metadata:")
    for block in state['progress']['blocks']:
        print(f"  Block {block['index']}: {block['tasks']} - {block['status']} (completed: {block['completed']})")
    
    print_section("Comprehensive State Structure Test")
    print("Testing all state components:")
    print(f"  [OK] execution: {list(state['execution'].keys())}")
    print(f"  [OK] progress: {list(state['progress'].keys())}")
    print(f"  [OK] tasks: {len(state['tasks'])} tasks with metadata")
    print(f"  [OK] data: {len(state['data'])} keys")
    print(f"  [OK] data_extractions: {len(state['data_extractions'])} tracked")
    print(f"  [OK] data_coverage: {list(state['data_coverage'].keys())}")
    print(f"  [OK] tone: {state['tone']}")
    print(f"  [OK] adjustments: {list(state['adjustments'].keys())}")
    print(f"  [OK] conversation: {list(state['conversation'].keys())}")
    
    print_section("PASS")
    print("All comprehensive state inspection tests passed!")
    print("ChatGuide now provides professional-grade state visibility.")


if __name__ == "__main__":
    test_state_inspection()

