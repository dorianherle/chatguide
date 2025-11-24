# Debug Scripts for ChatGuide

These scripts help diagnose issues with data extraction and conversation flow.

## Scripts

### 1. `debug_test.py` - Complete Conversation Test
Shows the full conversation flow with detailed state after each turn.

**Run:**
```bash
python debug_test.py
```

**Shows:**
- User input
- Assistant reply
- Extracted data
- Current state
- Task completion status
- Execution state
- Plan progress

### 2. `debug_prompt_test.py` - Prompt Inspection
Shows the EXACT prompt sent to the LLM at each step.

**Run:**
```bash
python debug_prompt_test.py
```

**Shows:**
- The full prompt before each LLM call
- Which tasks are current vs completed
- Chat history as seen by LLM
- Current state as seen by LLM
- Task descriptions and examples

**Use this to check:**
- Is `get_origin` marked as the current task?
- Are `get_name` and `get_age` marked completed?
- Is the chat history correct?
- Are the extraction examples showing?

### 3. `debug_raw_response.py` - Raw LLM Response Analysis
Shows the RAW unprocessed LLM response for the "Germany" case.

**Run:**
```bash
python debug_raw_response.py
```

**Shows:**
- Raw JSON from LLM before parsing
- Parsed response structure
- Task status before/after processing
- State before/after processing
- Diagnosis of what went wrong

**Use this to check:**
- Did the LLM include `origin` in `task_results`?
- What keys did the LLM extract?
- Was the value extracted correctly?
- Was the task marked as completed?
- Was the state updated?

## Typical Workflow

1. **Run `debug_prompt_test.py` first** to see if the prompt is correct
2. **Run `debug_raw_response.py`** to see what the LLM actually returned
3. **Run `debug_test.py`** to see the full flow

## What to Look For

### If "Germany" is not extracted:

1. **Check the prompt** (`debug_prompt_test.py`):
   - Is `get_origin` the current task?
   - Is the description clear?
   - Are examples shown?

2. **Check the LLM response** (`debug_raw_response.py`):
   - Does `task_results` contain an entry with `key: "origin"`?
   - Is the value "Germany"?
   - Is it being filtered out during parsing?

3. **Check task completion logic** (`debug_raw_response.py`):
   - Is the task being marked as completed?
   - Is the state being updated?

## Common Issues

### Issue: LLM doesn't extract the data
**Solution:** Check the task description in `config.yaml` and prompt examples

### Issue: LLM extracts but task not marked complete
**Solution:** Check `expects` field matches the `key` in task_results

### Issue: Duplicate extractions
**Solution:** Check deduplication logic in `response_parser.py`

### Issue: Bot repeats the same question
**Solution:** Check if task is being marked as completed and block is advancing

