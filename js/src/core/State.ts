import { AuditLog } from './Audit';

export class State {
  private _data: Record<string, any> = {};
  private _auditLog?: AuditLog;

  constructor(initial?: Record<string, any>, auditLog?: AuditLog) {
    this._data = initial || {};
    this._auditLog = auditLog;
  }

  get(key: string, defaultVal?: any): any {
    return this._data[key] ?? defaultVal;
  }

  set(key: string, value: any, sourceTask?: string): void {
    const oldValue = this._data[key];
    this._data[key] = value;

    if (this._auditLog && oldValue !== value) {
      this._auditLog.log(key, oldValue, value, sourceTask);
    }
  }

  update(data: Record<string, any>, sourceTask?: string): void {
    for (const [key, value] of Object.entries(data)) {
      this.set(key, value, sourceTask);
    }
  }

  getTyped<T>(key: string, type: new (...args: any[]) => T, defaultVal?: T): T | undefined {
    const val = this._data[key];
    if (val === undefined || val === null) return defaultVal;
    if (val instanceof type) return val;
    try {
      return new type(val);
    } catch {
      return defaultVal;
    }
  }

  resolveTemplate(template: any): any {
    if (typeof template === 'string') {
      return template.replace(/\{\{(\w+)\}\}/g, (_, key) => {
        return this.get(key, '');
      });
    }
    if (Array.isArray(template)) {
      return template.map(item => this.resolveTemplate(item));
    }
    if (typeof template === 'object' && template !== null) {
      const resolved: Record<string, any> = {};
      for (const [k, v] of Object.entries(template)) {
        resolved[k] = this.resolveTemplate(v);
      }
      return resolved;
    }
    return template;
  }

  get variables(): Record<string, any> {
    return { ...this._data };
  }

  toDict(): Record<string, any> {
    return { ...this._data };
  }
}

