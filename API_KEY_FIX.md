# 🔑 API Key Configuration Fix

## Problem
The orchestrator was trying to initialize OpenAI even when using Gemini, causing:
```
OpenAIError: The api_key client option must be set
```

## What Was Fixed

1. **Updated `core/orchestrator.py`**:
   - Now reads `AI_PROVIDER` and `AI_MODEL` from environment
   - Passes them to AIAnalyzer

2. **Updated `ai/analyzer.py`**:
   - Gracefully handles missing API keys
   - Falls back to rule-based analysis if no API key
   - Only initializes the client for the selected provider

3. **Updated `docker-compose.yml`**:
   - Uses `env_file` to properly load environment variables
   - Ensures all env vars are available in container

4. **Created `check_config.sh`**:
   - Validates your .env configuration
   - Checks API keys are set correctly

## How to Fix

### Step 1: Check Your .env File
```bash
./check_config.sh
```

### Step 2: Ensure Correct Configuration

For **Gemini** (your case):
```bash
# Edit .env
nano .env

# Make sure these are set:
AI_PROVIDER=gemini
AI_MODEL=gemini-1.5-pro
GEMINI_API_KEY=your_actual_gemini_key_here

# These can be empty or commented out:
# OPENAI_API_KEY=
# ANTHROPIC_API_KEY=
```

For **OpenAI**:
```bash
AI_PROVIDER=openai
AI_MODEL=gpt-4
OPENAI_API_KEY=sk-your-key-here
```

For **Anthropic**:
```bash
AI_PROVIDER=anthropic
AI_MODEL=claude-3-sonnet-20240229
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### Step 3: Restart Orchestrator
```bash
# Stop current container
docker-compose down orchestrator

# Rebuild with new configuration
docker-compose up -d --build orchestrator

# Check logs
docker-compose logs -f orchestrator
```

## Verify It's Working

### Check Logs
```bash
docker-compose logs orchestrator | grep -i "ai\|gemini\|provider"
```

You should see:
```
INFO: Using AI provider: gemini
INFO: AI model: gemini-1.5-pro
```

### Test API
```bash
curl http://localhost:8000/status
```

## Example .env File

### For Gemini (Recommended)
```bash
# AI Configuration
GEMINI_API_KEY=AIzaSyD...your-actual-key
AI_PROVIDER=gemini
AI_MODEL=gemini-1.5-pro

# Optional (can be empty)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# Adaptive Settings
ADAPTATION_THRESHOLD=5
ANALYSIS_INTERVAL=60
MAX_HONEYPOTS=10

# Database
DATABASE_URL=sqlite+aiosqlite:///./honeypot.db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# API
API_HOST=0.0.0.0
API_PORT=8000

# Honeypot Network
HONEYPOT_NETWORK=honeypot_net
HONEYPOT_SUBNET=172.25.0.0/16

# Logging
LOG_LEVEL=INFO
LOG_DIR=./logs
```

## Fallback Behavior

If no API key is configured, the system will:
1. Log a warning
2. Use rule-based analysis instead of AI
3. Continue operating normally

This means the system can run without AI, but won't have intelligent adaptation.

## Common Issues

### Issue 1: "API key not found"
**Solution**: Check .env file exists and has correct key name
```bash
cat .env | grep GEMINI_API_KEY
```

### Issue 2: "Environment variable not loaded"
**Solution**: Restart container to reload env vars
```bash
docker-compose restart orchestrator
```

### Issue 3: "Wrong provider initialized"
**Solution**: Check AI_PROVIDER is set correctly
```bash
grep AI_PROVIDER .env
```

### Issue 4: "Still trying to use OpenAI"
**Solution**: Rebuild container to apply code changes
```bash
docker-compose up -d --build orchestrator
```

## Testing Different Providers

### Test Gemini
```bash
# Set in .env
AI_PROVIDER=gemini
GEMINI_API_KEY=your_key

# Restart
docker-compose restart orchestrator
```

### Test OpenAI
```bash
# Set in .env
AI_PROVIDER=openai
OPENAI_API_KEY=your_key

# Restart
docker-compose restart orchestrator
```

### Test Without AI (Fallback)
```bash
# Remove or comment out all API keys
# AI_PROVIDER=gemini
# GEMINI_API_KEY=

# Restart
docker-compose restart orchestrator

# System will use rule-based analysis
```

## Quick Commands

```bash
# Check configuration
./check_config.sh

# Restart with new config
docker-compose up -d --build orchestrator

# View logs
docker-compose logs -f orchestrator

# Check status
curl http://localhost:8000/status
```

## Summary

✅ System now reads AI_PROVIDER from environment
✅ Only initializes the selected AI provider
✅ Gracefully handles missing API keys
✅ Falls back to rule-based analysis if needed
✅ Properly loads environment variables in Docker

Your Gemini configuration should now work correctly!
