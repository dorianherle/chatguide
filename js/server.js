const express = require('express');
const path = require('path');
const dotenv = require('dotenv');
const { ChatGuide } = require('./dist/ChatGuide');

// Load .env from root directory
dotenv.config({ path: path.join(__dirname, '..', '.env') });

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Session storage (in-memory, for production use Redis/database)
const sessions = new Map();

app.post('/api/chat', async (req, res) => {
  try {
    const { message, sessionId, action = 'chat' } = req.body;
    const apiKey = process.env.GEMINI_API_KEY;

    if (!apiKey) {
      return res.status(500).json({ error: 'GEMINI_API_KEY not found in .env file' });
    }

    // Get or create session
    let session = sessionId ? sessions.get(sessionId) : null;

    if (action === 'reset' || !session) {
      // Initialize new ChatGuide
      const guide = new ChatGuide({
        apiKey,
        config: path.join(__dirname, '../configs/config.yaml'),
        language: 'en',
      });

      const reply = await guide.chat();
      const newSessionId = sessionId || `session_${Date.now()}`;

      session = {
        chatGuide: guide.dump(),
        sessionId: newSessionId,
      };
      sessions.set(newSessionId, session);

      return res.json({
        reply: reply.assistant_reply,
        sessionId: newSessionId,
        progress: guide.getProgress(),
        finished: guide.isFinished(),
      });
    }

    // Restore ChatGuide from session
    const guide = new ChatGuide({
      apiKey,
      config: path.join(__dirname, '../configs/config.yaml'),
      language: 'en',
    });

    // Restore entire state using restoreFromDump
    const sessionData = session.chatGuide;
    guide.restoreFromDump(sessionData);

    if (action === 'init') {
      const reply = await guide.chat();
      session.chatGuide = guide.dump();
      sessions.set(session.sessionId, session);

      return res.json({
        reply: reply.assistant_reply,
        sessionId: session.sessionId,
        progress: guide.getProgress(),
        finished: guide.isFinished(),
      });
    }

    if (!message) {
      return res.status(400).json({ error: 'Message is required' });
    }

    // Add user message and get response
    guide.addUserMessage(message);
    const reply = await guide.chat();

    // Debug logging
    if (process.env.DEBUG) {
      console.log('Task results:', JSON.stringify(reply.task_results, null, 2));
      console.log('Current task:', guide.getCurrentTask());
      console.log('Progress:', guide.getProgress());
      console.log('State:', guide.state.toDict());
    }

    // Save session
    session.chatGuide = guide.dump();
    sessions.set(session.sessionId, session);

    res.json({
      reply: reply.assistant_reply,
      sessionId: session.sessionId,
      progress: guide.getProgress(),
      finished: guide.isFinished(),
      taskResults: reply.task_results,
    });
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({ error: error.message || 'Internal server error' });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`🚀 Server running on http://localhost:${PORT}`);
  console.log(`📝 Make sure GEMINI_API_KEY is set in .env file`);
});

