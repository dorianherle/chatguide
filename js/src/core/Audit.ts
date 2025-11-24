export interface AuditEntry {
  timestamp: string;
  key: string;
  old_value: any;
  new_value: any;
  source_task?: string;
}

export class AuditLog {
  private _entries: AuditEntry[] = [];

  log(key: string, oldValue: any, newValue: any, sourceTask?: string): void {
    this._entries.push({
      timestamp: new Date().toISOString(),
      key,
      old_value: oldValue,
      new_value: newValue,
      source_task: sourceTask,
    });
  }

  search(options?: {
    key?: string;
    task?: string;
    since?: string;
  }): AuditEntry[] {
    let results = [...this._entries];

    if (options?.key) {
      results = results.filter(e => e.key === options.key);
    }
    if (options?.task) {
      results = results.filter(e => e.source_task === options.task);
    }
    if (options?.since) {
      results = results.filter(e => e.timestamp >= options.since!);
    }

    return results;
  }

  getLatest(key: string): AuditEntry | undefined {
    const entries = this._entries.filter(e => e.key === key);
    return entries.length > 0 ? entries[entries.length - 1] : undefined;
  }

  toList(): AuditEntry[] {
    return [...this._entries];
  }

  static fromList(data: AuditEntry[]): AuditLog {
    const log = new AuditLog();
    log._entries = [...data];
    return log;
  }
}

