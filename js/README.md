# ChatGuide JavaScript/TypeScript

TypeScript implementation of ChatGuide for Netlify/serverless deployment.

## Installation

```bash
npm install
```

## Build

```bash
npm run build
```

## Development

```bash
npm run dev  # Watch mode
```

## Usage

```typescript
import { ChatGuide } from './src/ChatGuide';

const guide = new ChatGuide({
  apiKey: process.env.GEMINI_API_KEY,
  config: 'configs/config.yaml',
  language: 'en',
});

// Start conversation
const reply = await guide.chat();
console.log(reply.assistant_reply);

// User responds
guide.addUserMessage("I'm John");
const reply2 = await guide.chat();
console.log(reply2.assistant_reply);

// Check progress
console.log(guide.getProgress());
```

## Structure

- `src/core/` - Core data structures (State, Context, Execution, Audit, Task, Block)
- `src/` - Main ChatGuide class and utilities
- `src/builders/` - Prompt building logic
- `src/io/` - LLM integration (Gemini API)
- `src/utils/` - Config loader, response parser

## Differences from Python Version

- Uses `@google/generative-ai` instead of `google-genai`
- Uses `js-yaml` instead of `pyyaml`
- Uses `zod` for schema validation instead of `pydantic`
- File system operations use Node.js `fs` module
- Designed for serverless/Netlify Functions environment

