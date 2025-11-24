export interface TaskData {
  id: string;
  description: string;
  expects: string[];
  tools: Array<Record<string, any>>;
  silent: boolean;
  status?: string;
  result?: Record<string, any>;
}

export class Task {
  id: string;
  description: string;
  expects: string[] = [];
  tools: Array<Record<string, any>> = [];
  silent: boolean = false;
  status: 'pending' | 'in_progress' | 'completed' = 'pending';
  result?: Record<string, any>;

  constructor(data: TaskData) {
    this.id = data.id;
    this.description = data.description;
    this.expects = data.expects || [];
    this.tools = data.tools || [];
    this.silent = data.silent || false;
    this.status = (data.status as any) || 'pending';
    this.result = data.result;
  }

  complete(key: string, value: any): void {
    this.status = 'completed';
    this.result = { key, value };
  }

  isCompleted(): boolean {
    return this.status === 'completed';
  }

  toDict(): Record<string, any> {
    return {
      id: this.id,
      description: this.description,
      expects: this.expects,
      tools: this.tools,
      silent: this.silent,
      status: this.status,
      result: this.result,
    };
  }
}

