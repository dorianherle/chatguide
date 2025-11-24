import * as yaml from 'js-yaml';
import * as fs from 'fs';
import * as path from 'path';
import { State } from '../core/State';
import { Plan } from '../Plan';
import { TaskDefinition } from '../schemas';

let langTemplates: Record<string, any> | null = null;

function loadLanguageTemplates(): Record<string, any> {
  if (langTemplates) return langTemplates;

  try {
    // Try multiple possible paths
    const possiblePaths = [
      path.join(__dirname, '../core/core_prompt.yaml'),
      path.join(process.cwd(), 'js/src/core/core_prompt.yaml'),
      path.join(process.cwd(), 'src/core/core_prompt.yaml'),
    ];

    let content: string | null = null;
    for (const templatePath of possiblePaths) {
      try {
        content = fs.readFileSync(templatePath, 'utf-8');
        break;
      } catch {
        // Try next path
      }
    }

    if (content) {
      langTemplates = yaml.load(content) as Record<string, any>;
    } else {
      // Fallback empty templates
      langTemplates = {};
    }
  } catch {
    // Fallback if file not found
    langTemplates = {};
  }

  return langTemplates || {};
}

function getLang(key: string, language: string, defaultVal: string = ''): string {
  const templates = loadLanguageTemplates();
  const langData = templates[language] || templates.en || {};
  return langData[key] || defaultVal;
}

export class PromptBuilder {
  constructor(
    private state: State,
    private plan: Plan,
    private tasks: Record<string, TaskDefinition>,
    private tone: string[],
    private toneDefinitions: Record<string, string>,
    private guardrails: string,
    private conversationHistory: Array<{ role: string; content: string }>,
    private language: string = 'en',
    private completedTasks: string[] = []
  ) {}

  build(): string {
    const currentBlock = this.plan.getCurrentBlock();
    const taskIds = currentBlock?.taskIds || [];

    return `${getLang('language_instruction', this.language, 'Speak naturally.')}

${getLang('chat_history_header', this.language, 'CONVERSATION HISTORY:')}
${this.formatHistory()}

${getLang('current_state_header', this.language, 'CURRENT STATE:')}
${this.formatState()}

${getLang('guardrails_header', this.language, 'GUARDRAILS:')}
${this.guardrails}

${getLang('current_tasks_header', this.language, 'CURRENT TASKS:')}
${this.formatTasks(taskIds)}

${getLang('tone_header', this.language, 'TONE:')}
${this.formatTone()}

${getLang('output_format_header', this.language, 'OUTPUT FORMAT:')}
Respond with JSON matching this schema:
{
  "assistant_reply": "Your natural response to the user",
  "task_results": [
    {
      "task_id": "task_name",
      "key": "state_variable_name",
      "value": "extracted_value"
    }
  ],
  "tools": [
    {
      "tool": "tool_id",
      "options": ["option1", "option2"]
    }
  ]
}

CRITICAL RULES:
1. Respond naturally in assistant_reply
2. Each task_result extracts ONE piece of data: task_id, key (state variable), value. DO NOT include duplicate entries with the same key.
3. EXTRACTION PRIORITY - CHECK USER'S LAST MESSAGE FIRST:
   - BEFORE asking any question, CHECK if the user's last message (in CHAT HISTORY) already answers the CURRENT TASK
   - If user's last message contains the answer:
     a) EXTRACT IT in task_results IMMEDIATELY
     b) DO NOT repeat the question for that task
     c) Acknowledge briefly and ask the NEXT task question
   - Examples: 
     * Current task: get_age, User says "13" -> Extract age='13', say "Thanks! And where are you from?"
     * Current task: get_origin, User says "Germany" -> Extract origin='Germany', say "Got it! Now, [next question]"
     * Current task: get_name, User says "John" -> Extract user_name='John', say "Nice to meet you, John! How old are you?"
   - For numbers: Extract ANY number, even standalone digits like "12", "25", "100"
   - For text: Extract the relevant information even if it's just a single word
   - Only ask the CURRENT TASK question if the user has NOT provided an answer yet
4. Only include tools if explicitly defined in current task
5. STRICTLY follow the tone guidelines above - they define how you should speak
6. If tone says "excited" or "exclamation marks", you MUST use them!
7. If multiple tasks are listed, ALWAYS work on the task marked ">>> CURRENT TASK (ASK THIS FIRST) <<<"
8. When user signals readiness ("ok", "yes", "sure"), ask the question for the CURRENT TASK

===============================================================================`.trim();
  }

  private formatHistory(): string {
    if (!this.conversationHistory.length) {
      return getLang('none', this.language, '(No messages yet)');
    }

    const lines = this.conversationHistory.slice(-10).map(msg => {
      return `${msg.role}: ${msg.content}`;
    });

    return lines.join('\n');
  }

  private formatState(): string {
    const stateDict = this.state.toDict();
    if (!Object.keys(stateDict).length) {
      return getLang('none', this.language, '(Empty)');
    }

    const lines = Object.entries(stateDict).map(([key, value]) => {
      return `- ${key}: ${value}`;
    });

    return lines.join('\n');
  }

  private formatTasks(taskIds: string[]): string {
    if (!taskIds.length) {
      return getLang('none', this.language, '(None)');
    }

    const currentBlock = this.plan.getCurrentBlock();
    let currentTaskId: string | undefined;

    if (currentBlock) {
      const pending = currentBlock.getPendingTasks();
      if (pending.length > 0) {
        currentTaskId = pending[0].id;
      }
    }

    const lines: string[] = [];
    const pendingTasks: string[] = [];

    for (const taskId of taskIds) {
      const task = this.tasks[taskId];
      if (!task) continue;

      if (this.completedTasks.includes(taskId)) continue;

      pendingTasks.push(taskId);

      const isCurrent = taskId === currentTaskId;
      const prefix = isCurrent ? '>>> CURRENT TASK (ASK THIS FIRST) <<<' : '';
      lines.push(`\nTask: ${taskId} ${prefix}`);
      lines.push(`Description: ${task.description}`);

      if (task.expects.length > 0) {
        lines.push(`Expected to collect: ${task.expects.join(', ')}`);
        // Add explicit examples for age extraction
        if (task.expects.includes('age')) {
          lines.push("EXAMPLES: User says '12' -> extract age='12'. User says '100' -> extract age='100'. User says 'I am 25' -> extract age='25'. Extract ANY number!");
        }
      }

      if (task.tools.length > 0) {
        lines.push('Available tools:');
        for (const toolDef of task.tools) {
          const toolId = toolDef.tool || 'unknown';
          lines.push(`  - ${toolId}`);
        }
      }
    }

    if (pendingTasks.length > 1 && currentTaskId) {
      lines.unshift(
        `IMPORTANT: You have ${pendingTasks.length} tasks in this block. Focus on asking about '${currentTaskId}' FIRST (it's marked above). Only move to other tasks after completing this one.`
      );
    }

    return lines.join('\n');
  }

  private formatTone(): string {
    if (!this.tone.length) {
      return 'Natural and helpful';
    }

    const descriptions = this.tone.map(toneId => {
      return this.toneDefinitions[toneId] || toneId;
    });

    return descriptions.join(' ');
  }
}

