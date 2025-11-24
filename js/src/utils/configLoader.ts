import * as yaml from 'js-yaml';
import * as fs from 'fs';
import * as path from 'path';
import { TaskDefinition } from '../schemas';
import { Adjustment } from '../Adjustments';

export interface ConfigData {
  state?: Record<string, any>;
  plan?: string[][];
  tasks?: Record<string, any>;
  tools?: Record<string, any>;
  adjustments?: Array<Record<string, any>>;
  tone?: string[];
  tones?: Record<string, string>;
  guardrails?: string | Record<string, string> | string[];
  language?: string;
}

export function loadConfigFile(filePath: string): ConfigData {
  // Try multiple possible paths
  const possiblePaths = [
    filePath,
    path.join(process.cwd(), filePath),
    path.join(process.cwd(), 'configs', path.basename(filePath)),
    path.join(__dirname, '../../..', filePath),
  ];

  let content: string | null = null;
  for (const configPath of possiblePaths) {
    try {
      content = fs.readFileSync(configPath, 'utf-8');
      break;
    } catch {
      // Try next path
    }
  }

  if (!content) {
    throw new Error(`Config file not found: ${filePath}`);
  }

  return yaml.load(content) as ConfigData;
}

export function parseState(data: ConfigData): Record<string, any> {
  return data.state || {};
}

export function parsePlan(data: ConfigData): string[][] {
  return data.plan || [];
}

export function parseTasks(data: ConfigData): Record<string, TaskDefinition> {
  const tasks: Record<string, TaskDefinition> = {};
  const tasksData = data.tasks || {};

  for (const [taskId, taskData] of Object.entries(tasksData)) {
    tasks[taskId] = {
      description: taskData.description || '',
      expects: taskData.expects || [],
      tools: taskData.tools || [],
      silent: taskData.silent || false,
    };
  }

  return tasks;
}

export function parseTools(data: ConfigData): Record<string, any> {
  return data.tools || {};
}

export function parseAdjustments(data: ConfigData): Adjustment[] {
  const adjustments: Adjustment[] = [];
  const adjustmentsData = data.adjustments || [];

  for (const adjData of adjustmentsData) {
    const name = adjData.name || 'unnamed';
    const condition = adjData.when || adjData.condition || 'false';
    const actions = adjData.actions || [];

    const formattedActions = actions.map((action: any) => {
      if (typeof action === 'string') {
        return parseActionString(action);
      }
      return action;
    });

    adjustments.push(new Adjustment(name, condition, formattedActions));
  }

  return adjustments;
}

function parseActionString(actionStr: string): Record<string, any> {
  const match = actionStr.match(/^(\w+)\.(\w+)\((.*)\)$/);
  if (!match) return {};

  const [, obj, method, argsStr] = match;
  const actionType = `${obj}.${method}`;
  const result: Record<string, any> = { type: actionType };

  if (argsStr) {
    try {
      const trimmed = argsStr.trim();
      if (trimmed.startsWith('[') || trimmed.startsWith('{')) {
        const evaluated = JSON.parse(trimmed);
        if (actionType === 'tone.set') {
          result.tones = evaluated;
        } else if (actionType === 'plan.insert_block' || actionType === 'plan.replace_block') {
          result.tasks = evaluated;
        }
      } else {
        result.index = parseInt(trimmed, 10);
      }
    } catch {
      // Ignore parse errors
    }
  }

  return result;
}

export function parseTone(data: ConfigData): string[] {
  return data.tone || [];
}

export function parseTones(data: ConfigData): Record<string, string> {
  const tones: Record<string, string> = {};
  const tonesData = data.tones || {};

  for (const [toneId, toneData] of Object.entries(tonesData)) {
    if (typeof toneData === 'string') {
      tones[toneId] = toneData;
    } else if (typeof toneData === 'object' && toneData !== null) {
      const toneObj = toneData as any;
      tones[toneId] = toneObj.description || '';
    }
  }

  return tones;
}

export function parseGuardrails(data: ConfigData): string {
  const guardrails = data.guardrails;
  if (!guardrails) return '';

  if (typeof guardrails === 'string') {
    return guardrails;
  }
  if (Array.isArray(guardrails)) {
    return guardrails.map(g => `- ${g}`).join('\n');
  }
  if (typeof guardrails === 'object') {
    return Object.entries(guardrails)
      .map(([key, value]) => `- ${key}: ${value}`)
      .join('\n');
  }

  return String(guardrails);
}

