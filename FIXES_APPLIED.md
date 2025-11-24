# ChatGuide Extraction Bug Fixes

## Issue
The LLM was not extracting user responses correctly, particularly:
1. Standalone numbers like "13" for age
2. Single words like "Germany" for origin
3. The bot would re-ask questions even after user provided answers

## Root Cause
**Conflicting prompt instructions** - The guardrails had:
```yaml
flow: "Always ask the question, never just acknowledge"
```

This conflicted with the extraction requirement, causing the LLM to prioritize asking questions over extracting data.

## Fixes Applied

### 1. Python Changes

#### `configs/config.yaml`
- **Removed** conflicting guardrails about "always ask the question"
- **Added** `extraction_priority` guardrail emphasizing immediate extraction
- **Updated** `flow` guardrail to check CHAT HISTORY and avoid re-asking

#### `python/src/chatguide/builders/prompt.py`
- **Rewrote** CRITICAL RULES section with clear extraction priority
- **Added** explicit instruction: "CHECK USER'S LAST MESSAGE FIRST"
- **Added** concrete examples showing extraction flow
- **Added** age-specific extraction examples in task formatting

#### `python/src/chatguide/utils/response_parser.py`
- **Added** deduplication logic to filter duplicate task_results by key
- **Handles** the `task_id` field that LLM includes (but schema doesn't use)

#### `python/src/chatguide/chatguide.py`
- **Added** deduplication in `_process_reply` method as backup

### 2. JavaScript/TypeScript Changes

#### `js/src/builders/PromptBuilder.ts`
- **Updated** CRITICAL RULES section matching Python version
- **Added** extraction priority instructions
- **Added** age-specific extraction examples

#### `js/src/utils/responseParser.ts`
- **Added** deduplication logic for task_results
- **Handles** task_id field from LLM responses

#### `js/src/ChatGuide.ts`
- **Added** deduplication in `_processReply` method

## Testing

### Before Fix
```
You: 13
Bot: Okay Dorian, how old are you?
[Extracted Data] (no data extracted)

You: Germany  
Bot: Okay Dorian, how old are you?
[Extracted Data] (no data extracted)
```

### After Fix
```
You: 13
Bot: Thanks, Dorian! And what is your country of origin?
[Extracted Data]
  - age: 13

You: Germany
Bot: Thanks, Dorian! And what is your country of origin?
[Extracted Data]
  - origin: Germany
```

## Key Learnings

1. **Prompt clarity is critical** - LLMs need explicit priority guidance when multiple instructions could conflict
2. **Check-then-extract pattern** - Teaching the LLM to check chat history first prevents re-asking
3. **Concrete examples help** - Specific examples like "User says '13' -> extract age='13'" are more effective than general instructions
4. **Multiple layers of deduplication** - Parser + processing loop catches duplicates from any source
5. **Task filtering works** - Completed tasks are correctly removed from prompt, reducing confusion

## Files Changed

### Python
- `configs/config.yaml`
- `python/src/chatguide/builders/prompt.py`
- `python/src/chatguide/utils/response_parser.py`
- `python/src/chatguide/chatguide.py`

### JavaScript
- `js/src/builders/PromptBuilder.ts`
- `js/src/utils/responseParser.ts`
- `js/src/ChatGuide.ts`

### Shared Config
- `configs/config.yaml` (used by both Python and JS)

## Debug Scripts Created

Located in `python/`:
- `debug_raw_response.py` - Shows raw LLM responses
- `debug_prompt_test.py` - Shows exact prompts sent to LLM
- `debug_test.py` - Full conversation flow testing
- `simple_test.py` - Quick extraction test
- `check_age_prompt.py` - Age-specific prompt inspection
- `test_completed_filtering.py` - Verifies completed tasks are filtered
- `DEBUG_README.md` - Documentation for debug scripts

