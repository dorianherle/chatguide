import { Block } from './core/Block';
import { Task } from './core/Task';

export class Plan {
  private _blocks: Block[] = [];
  private _currentIndex = 0;

  constructor(blocks?: Block[]) {
    this._blocks = blocks || [];
  }

  getCurrentBlock(): Block | undefined {
    if (this._currentIndex < this._blocks.length) {
      return this._blocks[this._currentIndex];
    }
    return undefined;
  }

  getBlock(index: number): Block | undefined {
    if (index >= 0 && index < this._blocks.length) {
      return this._blocks[index];
    }
    return undefined;
  }

  advance(): void {
    if (this._currentIndex < this._blocks.length) {
      this._currentIndex++;
    }
  }

  jumpTo(index: number): void {
    if (index >= 0 && index < this._blocks.length) {
      this._currentIndex = index;
    }
  }

  insertBlock(index: number, block: Block): void {
    this._blocks.splice(index, 0, block);
  }

  removeBlock(index: number): void {
    if (index >= 0 && index < this._blocks.length) {
      this._blocks.splice(index, 1);
      if (this._currentIndex >= this._blocks.length) {
        this._currentIndex = Math.max(0, this._blocks.length - 1);
      }
    }
  }

  replaceBlock(index: number, block: Block): void {
    if (index >= 0 && index < this._blocks.length) {
      this._blocks[index] = block;
    }
  }

  getAllTasks(): Task[] {
    const tasks: Task[] = [];
    for (const block of this._blocks) {
      tasks.push(...block.tasks);
    }
    return tasks;
  }

  getTask(taskId: string): Task | undefined {
    for (const block of this._blocks) {
      const task = block.getTask(taskId);
      if (task) return task;
    }
    return undefined;
  }

  isFinished(): boolean {
    return this._currentIndex >= this._blocks.length;
  }

  get currentIndex(): number {
    return this._currentIndex;
  }

  toDict(): Record<string, any> {
    return {
      blocks: this._blocks.map(b => b.toDict()),
      current_index: this._currentIndex,
      is_finished: this.isFinished(),
    };
  }
}

