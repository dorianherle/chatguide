import { ChatGuideReply, ChatGuideReplySchema } from '../schemas';

export function parseLLMResponse(raw: any): ChatGuideReply {
  if (!raw) {
    throw new Error('LLM returned no content');
  }

  if (typeof raw === 'string') {
    try {
      raw = JSON.parse(raw);
    } catch {
      throw new Error('Invalid JSON response from LLM');
    }
  }

  // Handle task_id field from LLM responses and deduplicate
  if (raw.task_results && Array.isArray(raw.task_results)) {
    const processedResults: any[] = [];
    const seenKeys = new Set<string>();
    
    for (const tr of raw.task_results) {
      if (tr && typeof tr === 'object') {
        const key = tr.key || '';
        // Skip duplicates and empty keys
        if (key && !seenKeys.has(key)) {
          seenKeys.add(key);
          processedResults.push({
            key: key,
            value: tr.value || ''
          });
        }
      }
    }
    raw.task_results = processedResults;
  }

  return ChatGuideReplySchema.parse(raw);
}

