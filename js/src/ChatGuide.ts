import { State } from './core/State';
import { Context } from './core/Context';
import { ExecutionState } from './core/Execution';
import { AuditLog } from './core/Audit';
import { Plan } from './Plan';
import { Block } from './core/Block';
import { Task } from './core/Task';
import { Adjustments, Adjustment } from './Adjustments';
import { TaskDefinition, ChatGuideReply } from './schemas';
import { PromptBuilder } from './builders/PromptBuilder';
import { runLLM } from './io/llm';
import { parseLLMResponse } from './utils/responseParser';
import {
  loadConfigFile,
  parseState,
  parsePlan,
  parseTasks,
  parseTones,
  parseGuardrails,
  parseAdjustments,
  parseTone,
  ConfigData,
} from './utils/configLoader';
// Note: fs/path imports removed for browser compatibility
// Config loading happens via configLoader which handles file system

export interface ChatGuideOptions {
  apiKey?: string;
  config?: string;
  debug?: boolean;
  language?: string;
}

export class ChatGuide {
  // Core 4-layer architecture
  audit: AuditLog;
  state: State;
  context: Context;
  execution: ExecutionState;
  plan: Plan;
  adjustments: Adjustments;

  // Configuration
  apiKey?: string;
  debug: boolean;
  language: string;
  tone: string[] = [];
  toneDefinitions: Record<string, string> = {};
  guardrails: string = '';

  // Tracking
  private _lastFiredAdjustments: string[] = [];
  private _lastResponse?: ChatGuideReply;
  private _errors: Array<Record<string, any>> = [];

  // Metrics
  private _metrics: Record<string, any> = {
    llm_calls: 0,
    tokens_used: 0,
    total_duration_ms: 0,
    task_completions: 0,
    errors: 0,
  };

  constructor(options: ChatGuideOptions = {}) {
    this.audit = new AuditLog();
    this.state = new State(undefined, this.audit);
    this.context = new Context();
    this.execution = new ExecutionState();
    this.plan = new Plan();
    this.adjustments = new Adjustments();

    this.apiKey = options.apiKey;
    this.debug = options.debug || false;
    this.language = options.language || 'en';

    if (options.config) {
      this.loadConfig(options.config);
    }
  }

  loadConfig(configPath: string): void {
    const data = loadConfigFile(configPath);

    // Parse initial state
    const initialState = parseState(data);
    this.state = new State(initialState, this.audit);

    // Parse plan and create blocks
    const planData = parsePlan(data);
    const tasksMap = parseTasks(data);
    const blocks: Block[] = [];

    for (const blockTasks of planData) {
      const taskObjects = blockTasks.map(taskId => {
        const taskDef = tasksMap[taskId];
        if (!taskDef) {
          throw new Error(`Task ${taskId} not found in config`);
        }
        return new Task({
          id: taskId,
          description: taskDef.description,
          expects: taskDef.expects,
          tools: taskDef.tools,
          silent: taskDef.silent,
        });
      });
      blocks.push(new Block(taskObjects));
    }

    this.plan = new Plan(blocks);

    // Parse other config
    this.tone = parseTone(data);
    this.toneDefinitions = parseTones(data);
    this.guardrails = parseGuardrails(data);
    this.adjustments = new Adjustments(parseAdjustments(data));

    // Set language if specified
    if (data.language) {
      this.language = data.language;
    }
  }

  async chat(options: {
    model?: string;
    apiKey?: string;
    temperature?: number;
    maxTokens?: number;
  } = {}): Promise<ChatGuideReply> {
    const {
      model = 'gemini-2.0-flash-exp',
      apiKey,
      temperature = 0.7,
      maxTokens = 4000,
    } = options;

    const apiKeyToUse = apiKey || this.apiKey;
    if (!apiKeyToUse) {
      throw new Error('API key is required');
    }

    // Build prompt
    const tasksMap = this._getTasksMap();
    const completedTaskIds = this.plan
      .getAllTasks()
      .filter(t => t.isCompleted())
      .map(t => t.id);

    const promptBuilder = new PromptBuilder(
      this.state,
      this.plan,
      tasksMap,
      this.tone,
      this.toneDefinitions,
      this.guardrails,
      this.context.getHistoryDict(),
      this.language,
      completedTaskIds
    );

    const prompt = promptBuilder.build();

    // Call LLM
    const startTime = Date.now();
    const rawResponse = await runLLM(prompt, {
      model,
      apiKey: apiKeyToUse,
      temperature,
      maxTokens,
    });

    this._metrics.llm_calls++;
    this._metrics.total_duration_ms += Date.now() - startTime;

    console.log('\n=== LLM RESPONSE ===');
    console.log('Assistant reply:', rawResponse.assistant_reply);
    console.log('Task results:', JSON.stringify(rawResponse.task_results, null, 2));
    console.log('===================\n');

    // Process reply
    await this._processReply(rawResponse);

    // Handle silent tasks - if we have silent tasks that were just completed, re-call
    const currentBlock = this.plan.getCurrentBlock();
    if (currentBlock) {
      const silentTasks = currentBlock.tasks.filter(t => t.silent && !t.isCompleted());
      if (silentTasks.length > 0 && rawResponse.task_results.length > 0) {
        // Check if any silent tasks were just completed
        const justCompletedSilent = rawResponse.task_results.some(tr => {
          const task = currentBlock.getTask(tr.task_id || '');
          return task && task.silent;
        });
        
        if (justCompletedSilent) {
          // Re-call if we have silent tasks that need processing
          return this.chat(options);
        }
      }
    }

    this._lastResponse = rawResponse;
    return rawResponse;
  }

  private async _processReply(reply: ChatGuideReply): Promise<void> {
    const currentBlock = this.plan.getCurrentBlock();
    const currentTaskId = this.getCurrentTask();

    console.log('=== PROCESSING REPLY ===');
    console.log('Current task ID:', currentTaskId);
    console.log('Task results:', JSON.stringify(reply.task_results, null, 2));
    console.log('Current block tasks:', currentBlock?.tasks.map(t => ({
      id: t.id,
      expects: t.expects,
      completed: t.isCompleted(),
      status: t.status
    })));

    // Update state with task results (deduplicate by key)
    const seenKeys = new Set<string>();
    const uniqueTaskResults: typeof reply.task_results = [];
    for (const taskResult of reply.task_results) {
      if (!seenKeys.has(taskResult.key)) {
        seenKeys.add(taskResult.key);
        uniqueTaskResults.push(taskResult);
      }
    }
    
    for (const taskResult of uniqueTaskResults) {
      // Skip empty values
      if (!taskResult.value || taskResult.value.trim() === '') {
        console.log('Skipping empty task result:', taskResult);
        continue;
      }

      console.log('Processing task result:', taskResult);
      this.state.set(taskResult.key, taskResult.value, currentTaskId);

      // Find and mark task as complete
      let taskToComplete: Task | undefined;
      
      if (currentBlock) {
        // First try to match by task_id if provided
        if (taskResult.task_id) {
          taskToComplete = currentBlock.getTask(taskResult.task_id);
          console.log('Matched by task_id:', taskResult.task_id, '->', taskToComplete?.id);
        }
        
        // If not found, try to match by expected key in ALL tasks (not just pending)
        // This handles cases where task might need to be updated
        if (!taskToComplete) {
          for (const task of currentBlock.tasks) {
            if (task.expects.includes(taskResult.key)) {
              taskToComplete = task;
              console.log('Matched by expects key:', taskResult.key, '->', task.id);
              break;
            }
          }
        }
        
        // Also try matching by task ID if key matches task ID
        if (!taskToComplete) {
          for (const task of currentBlock.tasks) {
            if (task.id === taskResult.key) {
              taskToComplete = task;
              console.log('Matched by task ID:', taskResult.key, '->', task.id);
              break;
            }
          }
        }
        
        // Mark as complete (update even if already completed)
        if (taskToComplete) {
          const wasCompleted = taskToComplete.isCompleted();
          if (!wasCompleted) {
            taskToComplete.complete(taskResult.key, taskResult.value);
            this._metrics.task_completions++;
            this.execution.markComplete(taskToComplete.id);
            console.log('✅ Marked task as complete:', taskToComplete.id);
          } else {
            // Task already completed, but update the result value
            taskToComplete.complete(taskResult.key, taskResult.value);
            console.log('⚠️ Task already completed, updating value:', taskToComplete.id);
          }
        } else {
          console.log('❌ Could not find task to complete for:', taskResult);
        }
      }
    }

    console.log('After processing - Current task:', this.getCurrentTask());
    console.log('Block complete?', currentBlock?.isComplete());
    console.log('Execution completed tasks:', this.execution.completed);

    // Auto-complete tasks with no expectations
    if (currentBlock) {
      for (const task of currentBlock.tasks) {
        if (!task.expects.length && !task.isCompleted()) {
          task.complete('auto', true);
          this._metrics.task_completions++;
          this.execution.markComplete(task.id);
        }
      }
    }

    // Evaluate adjustments
    const firedAdjustments = this.adjustments.evaluate(this.state, this.plan, this.tone);
    this._lastFiredAdjustments = firedAdjustments;

    // Add assistant message to history
    this.addAssistantMessage(reply.assistant_reply);

    // Check if current block is complete
    if (currentBlock && currentBlock.isComplete()) {
      console.log('✅ Block complete, advancing plan');
      this.plan.advance();
      console.log('New current block index:', this.plan.currentIndex);
    } else {
      console.log('⏸️ Block not complete yet');
    }
    console.log('=== END PROCESSING ===\n');
  }

  addUserMessage(message: string): void {
    this.context.addMessage('user', message);
  }

  addAssistantMessage(message: string): void {
    this.context.addMessage('assistant', message);
  }

  getCurrentTask(): string | undefined {
    if (this.plan.isFinished()) {
      return undefined;
    }

    const currentBlock = this.plan.getCurrentBlock();
    if (!currentBlock) {
      return undefined;
    }

    const pending = currentBlock.getPendingTasks();
    return pending.length > 0 ? pending[0].id : undefined;
  }

  getProgress(): {
    completed: number;
    total: number;
    percent: number;
    current_task?: string;
  } {
    const allTasks = this.plan.getAllTasks();
    const total = allTasks.length;
    const completed = allTasks.filter(t => t.isCompleted()).length;
    const percent = total > 0 ? Math.floor((completed / total) * 100) : 0;

    return {
      completed,
      total,
      percent,
      current_task: this.getCurrentTask(),
    };
  }

  isFinished(): boolean {
    return this.plan.isFinished();
  }

  isWaitingForUser(): boolean {
    return !this.isFinished() && this.execution.status === 'awaiting_input';
  }

  dump(): Record<string, any> {
    return {
      variables: this.state.variables,
      context: this.context.toDict(),
      execution: this.execution.toDict(),
      audit: this.audit.toList(),
    };
  }

  restoreFromDump(dumpData: Record<string, any>): void {
    // Restore state
    if (dumpData.variables) {
      for (const [key, value] of Object.entries(dumpData.variables)) {
        this.state.set(key, value);
      }
    }

    // Restore context
    if (dumpData.context) {
      this.context = Context.fromDict(dumpData.context);
    }

    // Restore execution
    if (dumpData.execution) {
      this.execution = ExecutionState.fromDict(dumpData.execution);
      
      // CRITICAL: Restore task completion status from execution state
      const completedTaskIds = this.execution.completed;
      for (const taskId of completedTaskIds) {
        const task = this.plan.getTask(taskId);
        if (task && !task.isCompleted()) {
          // Mark task as completed (we don't have the original result, so use a placeholder)
          task.complete('restored', 'restored');
        }
      }

      // Restore plan current index from execution state
      // The execution state tracks completed tasks, so we need to find
      // the first incomplete block and set that as current
      const blocks = (this.plan as any)._blocks;
      let foundIncomplete = false;
      for (let i = 0; i < blocks.length; i++) {
        const block = blocks[i];
        if (!block.isComplete()) {
          (this.plan as any)._currentIndex = i;
          foundIncomplete = true;
          break;
        }
      }
      // If all blocks are complete, set to end
      if (!foundIncomplete) {
        (this.plan as any)._currentIndex = blocks.length;
      }
    }

    // Restore audit
    if (dumpData.audit) {
      this.audit = AuditLog.fromList(dumpData.audit);
    }
  }

  private _getTasksMap(): Record<string, TaskDefinition> {
    const tasksMap: Record<string, TaskDefinition> = {};
    const allTasks = this.plan.getAllTasks();

    for (const task of allTasks) {
      tasksMap[task.id] = {
        description: task.description,
        expects: task.expects,
        tools: task.tools,
        silent: task.silent,
      };
    }

    return tasksMap;
  }
}

