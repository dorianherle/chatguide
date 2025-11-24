import { State } from './core/State';
import { Plan } from './Plan';

export interface AdjustmentAction {
  type: string;
  [key: string]: any;
}

export class Adjustment {
  name: string;
  condition: string;
  actions: AdjustmentAction[];
  fired: boolean = false;

  constructor(name: string, condition: string, actions: AdjustmentAction[]) {
    this.name = name;
    this.condition = condition;
    this.actions = actions;
  }

  reset(): void {
    this.fired = false;
  }
}

export class Adjustments {
  private _adjustments: Adjustment[] = [];

  constructor(adjustments?: Adjustment[]) {
    this._adjustments = adjustments || [];
  }

  add(adjustment: Adjustment): void {
    this._adjustments.push(adjustment);
  }

  evaluate(state: State, plan: Plan, tone: string[]): string[] {
    const firedNames: string[] = [];

    for (const adj of this._adjustments) {
      if (adj.fired) continue;

      try {
        // Simple condition evaluation (for Netlify, we'll use a safer approach)
        // In production, use a proper expression evaluator
        const context: any = {
          state: state.toDict(),
          plan,
          tone,
        };

        // Basic condition matching (simplified - in production use proper evaluator)
        let conditionMet = false;
        try {
          // Try to evaluate simple conditions
          const condition = adj.condition.replace(/state\.get\(['"](.*?)['"]\)/g, (_, key) => {
            return `state['${key}']`;
          });
          // This is a simplified version - in production use a proper expression parser
          conditionMet = this._evaluateCondition(condition, context);
        } catch {
          // If evaluation fails, skip
        }

        if (conditionMet) {
          this._executeActions(adj.actions, state, plan, tone);
          adj.fired = true;
          firedNames.push(adj.name);
        }
      } catch {
        // Silently skip invalid conditions
      }
    }

    return firedNames;
  }

  private _evaluateCondition(condition: string, context: any): boolean {
    // Very basic condition evaluator - in production use a proper library
    // This handles simple cases like: state['key'] == 'value'
    try {
      // Replace state access patterns
      let evalStr = condition;
      evalStr = evalStr.replace(/state\[['"](.*?)['"]\]/g, (_, key) => {
        const val = context.state[key];
        return typeof val === 'string' ? `'${val}'` : String(val);
      });

      // Evaluate (this is simplified - use a proper evaluator in production)
      return eval(evalStr);
    } catch {
      return false;
    }
  }

  private _executeActions(
    actions: AdjustmentAction[],
    state: State,
    plan: Plan,
    tone: string[]
  ): void {
    for (const action of actions) {
      const actionType = action.type;

      if (actionType === 'plan.insert_block') {
        const index = action.index || 0;
        const tasks = action.tasks || [];
        // Create block from tasks
        const { Block } = require('./core/Block');
        const { Task } = require('./core/Task');
        const taskObjs = tasks.map((t: any) => new Task(t));
        const block = new Block(taskObjs);
        plan.insertBlock(index, block);
      } else if (actionType === 'plan.remove_block') {
        const index = action.index || 0;
        plan.removeBlock(index);
      } else if (actionType === 'plan.replace_block') {
        const index = action.index || 0;
        const tasks = action.tasks || [];
        const { Block } = require('./core/Block');
        const { Task } = require('./core/Task');
        const taskObjs = tasks.map((t: any) => new Task(t));
        const block = new Block(taskObjs);
        plan.replaceBlock(index, block);
      } else if (actionType === 'plan.jump_to') {
        const index = action.index || 0;
        plan.jumpTo(index);
      } else if (actionType === 'tone.set') {
        const newTones = action.tones || [];
        tone.length = 0;
        tone.push(...newTones);
      } else if (actionType === 'tone.add') {
        const newTone = action.tone;
        if (newTone && !tone.includes(newTone)) {
          tone.push(newTone);
        }
      } else if (actionType === 'state.set') {
        const key = action.key;
        const value = action.value;
        if (key) {
          state.set(key, value);
        }
      }
    }
  }

  resetAll(): void {
    for (const adj of this._adjustments) {
      adj.reset();
    }
  }

  toDict(): Record<string, any> {
    return {
      adjustments: this._adjustments.map(adj => ({
        name: adj.name,
        condition: adj.condition,
        fired: adj.fired,
      })),
    };
  }
}

