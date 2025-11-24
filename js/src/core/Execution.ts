export class ExecutionState {
  private _currentTask?: string;
  private _completed: string[] = [];
  private _pendingTools: Array<Record<string, any>> = [];
  private _status: 'idle' | 'processing' | 'awaiting_input' | 'complete' = 'idle';

  get currentTask(): string | undefined {
    return this._currentTask;
  }

  set currentTask(taskId: string | undefined) {
    this._currentTask = taskId;
  }

  get completed(): string[] {
    return [...this._completed];
  }

  get status(): string {
    return this._status;
  }

  set status(value: string) {
    this._status = value as any;
  }

  markComplete(taskId: string): void {
    if (!this._completed.includes(taskId)) {
      this._completed.push(taskId);
    }
  }

  isCompleted(taskId: string): boolean {
    return this._completed.includes(taskId);
  }

  progress(totalTasks: number): {
    completed: number;
    total: number;
    percent: number;
    current_task?: string;
  } {
    const completedCount = this._completed.length;
    const percent = totalTasks > 0 ? Math.floor((completedCount / totalTasks) * 100) : 0;

    return {
      completed: completedCount,
      total: totalTasks,
      percent,
      current_task: this._currentTask,
    };
  }

  addPendingTool(tool: Record<string, any>): void {
    this._pendingTools.push(tool);
  }

  getPendingTools(): Array<Record<string, any>> {
    return [...this._pendingTools];
  }

  clearPendingTools(): void {
    this._pendingTools = [];
  }

  toDict(): Record<string, any> {
    return {
      current_task: this._currentTask,
      completed: [...this._completed],
      pending_tools: [...this._pendingTools],
      status: this._status,
    };
  }

  static fromDict(data: Record<string, any>): ExecutionState {
    const state = new ExecutionState();
    state._currentTask = data.current_task;
    state._completed = data.completed || [];
    state._pendingTools = data.pending_tools || [];
    state._status = data.status || 'idle';
    return state;
  }
}

