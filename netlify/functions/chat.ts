import { Handler, HandlerEvent, HandlerContext } from '@netlify/functions';
import { ChatGuide } from '../../js/dist/ChatGuide';
import * as path from 'path';
import * as fs from 'fs';

// Session storage (in production, use a database or Redis)
const sessions = new Map<string, any>();

interface ChatRequest {
  message?: string;
  sessionId?: string;
  action?: 'init' | 'chat' | 'reset';
}

export const handler: Handler = async (event: HandlerEvent, context: HandlerContext) => {
  // CORS headers
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Content-Type': 'application/json',
  };

  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 200, headers, body: '' };
  }

  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      headers,
      body: JSON.stringify({ error: 'Method not allowed' }),
    };
  }

  try {
    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
      return {
        statusCode: 500,
        headers,
        body: JSON.stringify({ error: 'GEMINI_API_KEY not configured' }),
      };
    }

    const body: ChatRequest = JSON.parse(event.body || '{}');
    const { message, sessionId, action = 'chat' } = body;

    // Get or create session
    let session = sessionId ? sessions.get(sessionId) : null;
    let chatGuide: ChatGuide;

    if (action === 'reset' || !session) {
      // Initialize new ChatGuide instance
      const configPath = path.join(process.cwd(), 'configs', 'config.yaml');
      
      chatGuide = new ChatGuide({
        apiKey,
        config: configPath,
        language: 'en',
      });

      // Get initial greeting
      const reply = await chatGuide.chat();
      
      const newSessionId = sessionId || `session_${Date.now()}`;
      session = {
        chatGuide: chatGuide.dump(),
        sessionId: newSessionId,
      };
      
      sessions.set(newSessionId, session);

      return {
        statusCode: 200,
        headers,
        body: JSON.stringify({
          reply: reply.assistant_reply,
          sessionId: newSessionId,
          progress: chatGuide.getProgress(),
          finished: chatGuide.isFinished(),
        }),
      };
    }

    // Restore ChatGuide from session
    const configPath = path.join(process.cwd(), 'configs', 'config.yaml');
    chatGuide = new ChatGuide({
      apiKey,
      config: configPath,
      language: 'en',
    });

    // Restore state from session
    const sessionData = session.chatGuide;
    if (sessionData.variables) {
      for (const [key, value] of Object.entries(sessionData.variables)) {
        chatGuide.state.set(key, value);
      }
    }

    if (sessionData.context) {
      chatGuide.context = require('../../js/dist/core/Context').Context.fromDict(sessionData.context);
    }

    if (sessionData.execution) {
      chatGuide.execution = require('../../js/dist/core/Execution').ExecutionState.fromDict(sessionData.execution);
    }

    if (action === 'init') {
      const reply = await chatGuide.chat();
      session.chatGuide = chatGuide.dump();
      sessions.set(session.sessionId, session);

      return {
        statusCode: 200,
        headers,
        body: JSON.stringify({
          reply: reply.assistant_reply,
          sessionId: session.sessionId,
          progress: chatGuide.getProgress(),
          finished: chatGuide.isFinished(),
        }),
      };
    }

    if (!message) {
      return {
        statusCode: 400,
        headers,
        body: JSON.stringify({ error: 'Message is required' }),
      };
    }

    // Add user message and get response
    chatGuide.addUserMessage(message);
    const reply = await chatGuide.chat();

    // Save session
    session.chatGuide = chatGuide.dump();
    sessions.set(session.sessionId, session);

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        reply: reply.assistant_reply,
        sessionId: session.sessionId,
        progress: chatGuide.getProgress(),
        finished: chatGuide.isFinished(),
        taskResults: reply.task_results,
      }),
    };
  } catch (error: any) {
    console.error('Error:', error);
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ error: error.message || 'Internal server error' }),
    };
  }
};

