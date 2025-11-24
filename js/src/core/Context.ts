export interface Message {
  role: string;
  content: string;
  timestamp: string;
}

export class Context {
  sessionId?: string;
  metadata: Record<string, any> = {};
  private _history: Message[] = [];
  createdAt: string;

  constructor(sessionId?: string, metadata?: Record<string, any>) {
    this.sessionId = sessionId;
    this.metadata = metadata || {};
    this.createdAt = new Date().toISOString();
  }

  get history(): Message[] {
    return [...this._history];
  }

  addMessage(role: string, content: string): void {
    this._history.push({
      role,
      content,
      timestamp: new Date().toISOString(),
    });
  }

  getHistoryDict(): Array<{ role: string; content: string }> {
    return this._history.map(msg => ({
      role: msg.role,
      content: msg.content,
    }));
  }

  toDict(): Record<string, any> {
    return {
      session_id: this.sessionId,
      metadata: this.metadata,
      history: this._history,
      created_at: this.createdAt,
    };
  }

  static fromDict(data: Record<string, any>): Context {
    const ctx = new Context(data.session_id, data.metadata);
    ctx.createdAt = data.created_at || new Date().toISOString();
    ctx._history = (data.history || []).map((msg: any) => ({
      role: msg.role,
      content: msg.content,
      timestamp: msg.timestamp || new Date().toISOString(),
    }));
    return ctx;
  }
}

