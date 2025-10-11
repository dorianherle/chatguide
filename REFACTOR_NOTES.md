# ChatGuide V2 Refactor

## Problems with V1

1. **Implicit task completion** - Empty string vs non-empty, no validation
2. **Scattered state machine** - Task progression logic spread across multiple methods
3. **No output validation** - Model could return anything
4. **Routes fire after generation** - Model doesn't know what's coming
5. **No max attempts** - Tasks could loop forever

## V2 Improvements

### 1. Explicit Task Output Specifications

**V1:**
```yaml
tasks:
  get_origin: "Find out where the user is from."
```

**V2:**
```yaml
tasks:
  get_origin:
    description: "Find out where the user is from (country/region)."
    output:
      type: "string"
      allow_empty: false
    max_attempts: 5
```

**Benefits:**
- Model knows exactly what format to return
- Framework validates output automatically
- Tasks fail after max attempts instead of infinite loops

### 2. Centralized State Machine

**V1:** State scattered across:
- `current_batch_idx`
- `completed_tasks` dict
- `task_turn_counts` dict
- Logic in `update_task_progress()`, `get_current_tasks()`, etc.

**V2:** Explicit `StateMachine` class:
```python
class StateMachine:
    def get_current_tasks() -> List[str]
    def mark_completed(task_id: str)
    def mark_failed(task_id: str)
    def advance() -> bool
    def is_finished() -> bool
```

**Benefits:**
- All state logic in one place
- Clear state transitions
- Easy to debug and extend

### 3. Output Validation

**V2 adds validation layer:**
```python
def validate_task_result(task_id: str, result: str) -> bool:
    # Validates against output specification
    # - enum: checks against valid values
    # - regex: matches pattern
    # - string: accepts any non-empty (if allow_empty=false)
```

**Examples:**
```yaml
# Enum validation
get_emotion:
  output:
    type: "enum"
    validation: "happy, sad, angry, anxious, neutral"

# Regex validation  
speak_in_language:
  output:
    type: "regex"
    validation: "^[a-z]{2}$"  # 2-letter language code
```

### 4. Max Attempts & Task Failure

Tasks now have `max_attempts` - after which they're marked as **failed** and state advances anyway.

This prevents infinite loops like the one in your example where `offer_language` couldn't complete.

### 5. Cleaner Prompt

**V1:** 10 numbered rules + implicit completion criteria

**V2:** Simplified rules + explicit output specs per task
```
##CURRENT BATCH TASKS:
- get_origin: Find out where the user is from. | OUTPUT: non-empty string (attempt 1/5)
- offer_language: Ask if user wants origin language. | OUTPUT: one of [de, fr, es, it, no] (attempt 1/5)
```

## Migration Guide

### Running V2

```bash
# V1 (existing)
streamlit run streamlit_app.py

# V2 (new)
streamlit run streamlit_app_v2.py
```

### Converting Config

**V1 format (still supported):**
```yaml
tasks:
  get_name: "Ask for the user's name."
```

**V2 format (recommended):**
```yaml
tasks:
  get_name:
    description: "Ask for the user's name."
    output:
      type: "string"
      allow_empty: false
    max_attempts: 5
```

### Code Changes

**V1:**
```python
from chatguide import ChatGuide
guide = ChatGuide()
guide.load_from_file("config.yaml")
```

**V2:**
```python
from chatguide_v2 import ChatGuideV2
guide = ChatGuideV2()
guide.load_from_file("config_v2.yaml")
```

API is mostly compatible - main difference is internal structure.

## What This Fixes

The horrible conversation loop you showed:
```
> Would you like to chat in German?
> yes
> Would you like to chat in German?
> yes
> Would you like to chat in German?
```

**V1 Problem:**
- `offer_language` completed with vague "yes"
- Route added `speak_in_language` as persistent task
- `speak_in_language` couldn't complete (no language code)
- Loop forever

**V2 Solution:**
```yaml
offer_language:
  output:
    type: "enum"
    validation: "de, fr, es, it, no"
    allow_empty: false
  max_attempts: 5
```

Model MUST return a valid language code or "no" - no vague responses allowed. Task fails after 5 attempts if model can't figure it out.

## Next Steps

Test V2 with the same conversation and confirm it doesn't loop.

