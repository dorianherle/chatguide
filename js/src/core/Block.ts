import { Task } from './Task';

export class Block {
  tasks: Task[];

  constructor(tasks: Task[]) {
    this.tasks = tasks;
  }

  get taskIds(): string[] {
    return this.tasks.map(t => t.id);
  }

  isComplete(): boolean {
    return this.tasks.every(t => t.isCompleted());
  }

  getPendingTasks(): Task[] {
    return this.tasks.filter(t => !t.isCompleted());
  }

  getTask(taskId: string): Task | undefined {
    return this.tasks.find(t => t.id === taskId);
  }

  toDict(): Record<string, any> {
    return {
      tasks: this.tasks.map(t => t.toDict()),
      status: this.isComplete() ? 'completed' : 'pending',
    };
  }
}

