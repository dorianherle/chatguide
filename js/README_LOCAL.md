# ChatGuide - Local Development

Simple local chat interface using the JavaScript/TypeScript implementation.

## Setup

1. **Install dependencies:**
   ```bash
   cd js
   npm install
   ```

2. **Build TypeScript:**
   ```bash
   npm run build
   ```

3. **Create `.env` file in root directory:**
   ```bash
   GEMINI_API_KEY=your_api_key_here
   PORT=3000
   ```

4. **Start server:**
   ```bash
   npm start
   ```

5. **Open browser:**
   ```
   http://localhost:3000
   ```

## YAML Config Compatibility

✅ **Yes, your YAML config works with JS!**

The JavaScript version supports:
- ✅ `plan` - Task blocks
- ✅ `tasks` - Task definitions with descriptions, expects, tools, silent
- ✅ `guardrails` - Conversation rules
- ✅ `tones` - Tone definitions
- ✅ `tone` - Initial tone
- ✅ `language` - Language setting
- ✅ `state` - Initial state

**Note:** The `routes` section in your config is Python-specific and uses a different system. The JS version uses `adjustments` (similar concept but different syntax). For basic conversations, you don't need routes - the core flow works fine!

## Features

- 🚀 Simple Express server
- 💬 Real-time chat interface
- 📊 Progress tracking
- 💾 Session persistence (in-memory)
- 🎨 Beautiful UI

## Development

Watch mode for TypeScript:
```bash
npm run dev  # In one terminal
npm start    # In another terminal
```

