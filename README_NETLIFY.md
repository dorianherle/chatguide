# ChatGuide - Netlify Deployment

This is a monorepo containing both Python and JavaScript/TypeScript implementations of ChatGuide.

## Structure

```
chatguide/
├── python/          # Python implementation (original)
├── js/              # TypeScript/JavaScript implementation
├── configs/         # Shared YAML configuration files
├── netlify/         # Netlify deployment files
│   ├── functions/   # Netlify Functions (serverless)
│   └── public/      # Frontend static files
└── netlify.toml     # Netlify configuration
```

## Quick Start - Netlify Deployment

1. **Install dependencies:**
   ```bash
   cd js
   npm install
   ```

2. **Build TypeScript:**
   ```bash
   npm run build
   ```

3. **Set environment variable in Netlify:**
   - Go to Netlify dashboard → Site settings → Environment variables
   - Add: `GEMINI_API_KEY` = your API key

4. **Deploy:**
   - Connect your GitHub repo to Netlify
   - Netlify will auto-detect `netlify.toml` and deploy

## Local Development

1. **Install Netlify CLI:**
   ```bash
   npm install -g netlify-cli
   ```

2. **Run locally:**
   ```bash
   netlify dev
   ```

3. **Access:**
   - Frontend: http://localhost:8888
   - Functions: http://localhost:8888/.netlify/functions/chat

## Configuration

Edit `configs/config.yaml` to customize your conversation flow. The same config works for both Python and JavaScript versions.

## Architecture

- **Frontend**: Pure HTML/CSS/JS (no framework needed)
- **Backend**: Netlify Functions (serverless Node.js)
- **LLM**: Google Gemini API
- **State Management**: In-memory sessions (for production, use Redis/database)

## Features

- ✅ State-driven conversation flow
- ✅ Progress tracking
- ✅ Session persistence
- ✅ Multi-language support
- ✅ Real-time chat interface

## Python vs JavaScript

Both implementations share the same core logic:
- **Python**: Full-featured library with Streamlit demo
- **JavaScript**: Optimized for Netlify/serverless deployment

The JavaScript version is a direct port maintaining API compatibility.

