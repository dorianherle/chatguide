import { GoogleGenerativeAI } from '@google/generative-ai';
import { ChatGuideReply, ChatGuideReplySchema } from '../schemas';

export interface LLMOptions {
  model?: string;
  apiKey?: string;
  temperature?: number;
  maxTokens?: number;
  extraConfig?: Record<string, any>;
}

export async function runLLM(
  prompt: string,
  options: LLMOptions = {}
): Promise<ChatGuideReply> {
  const {
    model = 'gemini-2.0-flash-exp',
    apiKey,
    temperature = 0.7,
    maxTokens = 4000,
    extraConfig = {},
  } = options;

  if (!apiKey) {
    throw new Error('API key is required');
  }

  const genAI = new GoogleGenerativeAI(apiKey);
  const genModel = genAI.getGenerativeModel({
    model,
    generationConfig: {
      temperature,
      maxOutputTokens: maxTokens,
      responseMimeType: 'application/json',
      ...extraConfig,
    },
  });

  try {
    const result = await genModel.generateContent(prompt);
    const response = await result.response;
    const text = response.text();

    // Parse JSON response
    const parsed = JSON.parse(text);

    // Validate with schema
    return ChatGuideReplySchema.parse(parsed);
  } catch (error: any) {
    throw new Error(`LLM call failed: ${error.message}`);
  }
}

