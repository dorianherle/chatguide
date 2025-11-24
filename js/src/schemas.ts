import { z } from 'zod';

export const TaskResultSchema = z.object({
  task_id: z.string().optional(),
  key: z.string(),
  value: z.string(),
});

export const ToolCallSchema = z.object({
  tool: z.string(),
  options: z.array(z.string()).optional(),
});

export const ChatGuideReplySchema = z.object({
  assistant_reply: z.string(),
  task_results: z.array(TaskResultSchema).default([]),
  tools: z.array(ToolCallSchema).default([]),
});

export type TaskResult = z.infer<typeof TaskResultSchema>;
export type ToolCall = z.infer<typeof ToolCallSchema>;
export type ChatGuideReply = z.infer<typeof ChatGuideReplySchema>;

export interface TaskDefinition {
  description: string;
  expects: string[];
  tools: Array<Record<string, any>>;
  silent: boolean;
}

