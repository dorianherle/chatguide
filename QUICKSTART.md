# Quick Start - Local Chat

## Setup (3 steps)

1. **Install & Build:**
   ```bash
   cd js
   npm install
   npm run build
   ```

2. **Create `.env` file in root directory:**
   ```
   GEMINI_API_KEY=your_api_key_here
   PORT=3000
   ```

3. **Start server:**
   ```bash
   npm start
   ```

4. **Open browser:**
   ```
   http://localhost:3000
   ```

## YAML Config ✅

**Yes, your YAML config works perfectly with JS!**

The JavaScript version supports all the core features:
- ✅ `plan` - Task blocks
- ✅ `tasks` - Task definitions  
- ✅ `guardrails` - Conversation rules
- ✅ `tones` - Tone definitions
- ✅ `language` - Language setting

Your `configs/config.yaml` will work as-is!

## What's Included

- Simple Express server (`js/server.js`)
- Beautiful chat UI (`js/public/index.html`)
- Session management (in-memory)
- Progress tracking
- Uses your `.env` file for API key

