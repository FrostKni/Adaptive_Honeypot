# 🤖 AI Provider Configuration Guide

This guide explains how to configure and use different AI providers (OpenAI, Anthropic, Google Gemini) with the Adaptive Honeypot system.

## 📋 Supported AI Providers

### 1. OpenAI (GPT Models)
- **Models**: GPT-4, GPT-4 Turbo, GPT-3.5 Turbo
- **Best for**: High-quality analysis, complex reasoning
- **Cost**: ~$0.01-0.03 per analysis
- **Speed**: 1-3 seconds

### 2. Anthropic (Claude Models)
- **Models**: Claude 3 Opus, Claude 3 Sonnet, Claude 3 Haiku
- **Best for**: Detailed analysis, safety-focused responses
- **Cost**: ~$0.015-0.075 per analysis
- **Speed**: 1-3 seconds

### 3. Google Gemini
- **Models**: Gemini Pro, Gemini 1.5 Pro, Gemini 1.5 Flash
- **Best for**: Fast analysis, cost-effective, multimodal capabilities
- **Cost**: Free tier available, then ~$0.0005-0.007 per analysis
- **Speed**: 0.5-2 seconds

---

## 🔑 Getting API Keys

### OpenAI API Key
1. Go to https://platform.openai.com/
2. Sign up or log in
3. Navigate to API Keys section
4. Click "Create new secret key"
5. Copy the key (starts with `sk-`)

### Anthropic API Key
1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys
4. Generate a new key
5. Copy the key

### Google Gemini API Key
1. Go to https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Select or create a Google Cloud project
5. Copy the API key

---

## ⚙️ Configuration

### Step 1: Edit .env File

```bash
# Copy the example file
cp .env.example .env

# Edit the file
nano .env
```

### Step 2: Configure Your Chosen Provider

#### Option A: Using OpenAI (GPT-4)
```bash
# AI Configuration
OPENAI_API_KEY=sk-your-actual-openai-key-here
AI_PROVIDER=openai
AI_MODEL=gpt-4

# Alternative OpenAI models:
# AI_MODEL=gpt-4-turbo        # Faster, cheaper
# AI_MODEL=gpt-3.5-turbo      # Fastest, cheapest
```

#### Option B: Using Anthropic (Claude)
```bash
# AI Configuration
ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-key-here
AI_PROVIDER=anthropic
AI_MODEL=claude-3-sonnet-20240229

# Alternative Anthropic models:
# AI_MODEL=claude-3-opus-20240229    # Most capable
# AI_MODEL=claude-3-haiku-20240307   # Fastest, cheapest
```

#### Option C: Using Google Gemini (Recommended for Cost)
```bash
# AI Configuration
GEMINI_API_KEY=your-actual-gemini-key-here
AI_PROVIDER=gemini
AI_MODEL=gemini-1.5-pro

# Alternative Gemini models:
# AI_MODEL=gemini-pro           # Standard model
# AI_MODEL=gemini-1.5-flash     # Fastest, cheapest
```

---

## 🚀 Quick Start Examples

### Example 1: Using Gemini (Free Tier)
```bash
# .env configuration
GEMINI_API_KEY=AIzaSyD...your-key-here
AI_PROVIDER=gemini
AI_MODEL=gemini-1.5-flash

# Start the system
./start.sh
```

### Example 2: Using OpenAI GPT-4
```bash
# .env configuration
OPENAI_API_KEY=sk-proj-...your-key-here
AI_PROVIDER=openai
AI_MODEL=gpt-4

# Start the system
./start.sh
```

### Example 3: Using Claude 3
```bash
# .env configuration
ANTHROPIC_API_KEY=sk-ant-...your-key-here
AI_PROVIDER=anthropic
AI_MODEL=claude-3-sonnet-20240229

# Start the system
./start.sh
```

---

## 📊 Model Comparison

| Provider | Model | Speed | Cost/Analysis | Quality | Free Tier |
|----------|-------|-------|---------------|---------|-----------|
| **Gemini** | gemini-1.5-flash | ⚡⚡⚡ | $0.0005 | ⭐⭐⭐⭐ | ✅ Yes |
| **Gemini** | gemini-1.5-pro | ⚡⚡ | $0.007 | ⭐⭐⭐⭐⭐ | ✅ Yes |
| **OpenAI** | gpt-3.5-turbo | ⚡⚡⚡ | $0.002 | ⭐⭐⭐ | ❌ No |
| **OpenAI** | gpt-4 | ⚡ | $0.03 | ⭐⭐⭐⭐⭐ | ❌ No |
| **OpenAI** | gpt-4-turbo | ⚡⚡ | $0.01 | ⭐⭐⭐⭐⭐ | ❌ No |
| **Anthropic** | claude-3-haiku | ⚡⚡⚡ | $0.0015 | ⭐⭐⭐⭐ | ❌ No |
| **Anthropic** | claude-3-sonnet | ⚡⚡ | $0.015 | ⭐⭐⭐⭐⭐ | ❌ No |
| **Anthropic** | claude-3-opus | ⚡ | $0.075 | ⭐⭐⭐⭐⭐ | ❌ No |

### Recommendations

**For Testing/Development:**
- Use **Gemini 1.5 Flash** (free tier, fast, good quality)

**For Production (Budget):**
- Use **Gemini 1.5 Pro** (best value, excellent quality)

**For Production (Premium):**
- Use **GPT-4 Turbo** or **Claude 3 Sonnet** (highest quality)

---

## 🔧 Advanced Configuration

### Switching Providers at Runtime

You can change providers without rebuilding containers:

```bash
# Stop the system
docker-compose down

# Edit .env file
nano .env
# Change AI_PROVIDER and AI_MODEL

# Restart
docker-compose up -d
```

### Using Multiple Providers (Fallback)

The system automatically falls back to rule-based analysis if AI fails. You can configure multiple keys:

```bash
# Configure all three providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIza...

# Primary provider
AI_PROVIDER=gemini
AI_MODEL=gemini-1.5-pro
```

If Gemini fails, you can manually switch to another provider.

---

## 🧪 Testing AI Providers

### Test Gemini Connection
```bash
# Test API key
curl "https://generativelanguage.googleapis.com/v1/models?key=YOUR_GEMINI_KEY"
```

### Test OpenAI Connection
```bash
# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_OPENAI_KEY"
```

### Test Anthropic Connection
```bash
# Test API key
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: YOUR_ANTHROPIC_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-haiku-20240307","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'
```

---

## 💡 Best Practices

### 1. API Key Security
```bash
# Never commit .env to git
echo ".env" >> .gitignore

# Use environment variables in production
export GEMINI_API_KEY="your-key"

# Rotate keys regularly
```

### 2. Cost Optimization
```bash
# Use cheaper models for testing
AI_MODEL=gemini-1.5-flash  # Gemini
AI_MODEL=gpt-3.5-turbo     # OpenAI
AI_MODEL=claude-3-haiku-20240307  # Anthropic

# Increase analysis interval to reduce API calls
ANALYSIS_INTERVAL=120  # Analyze every 2 minutes instead of 1
```

### 3. Rate Limiting
```bash
# Gemini Free Tier Limits:
# - 60 requests per minute
# - 1,500 requests per day

# OpenAI Limits (Tier 1):
# - 3,500 requests per minute
# - 200,000 requests per day

# Anthropic Limits (Tier 1):
# - 50 requests per minute
# - 1,000 requests per day
```

---

## 🐛 Troubleshooting

### Error: "API key not found"
```bash
# Check if key is set
grep GEMINI_API_KEY .env

# Restart containers after changing .env
docker-compose restart
```

### Error: "Rate limit exceeded"
```bash
# Increase analysis interval
ANALYSIS_INTERVAL=180  # 3 minutes

# Reduce adaptation threshold
ADAPTATION_THRESHOLD=10  # Trigger less frequently
```

### Error: "Invalid API key"
```bash
# Verify key format
# Gemini: Should start with "AIza"
# OpenAI: Should start with "sk-"
# Anthropic: Should start with "sk-ant-"

# Regenerate key from provider dashboard
```

### Error: "Model not found"
```bash
# Check model name spelling
# Gemini: gemini-1.5-pro (not gemini-1.5-pro-latest)
# OpenAI: gpt-4 (not gpt4)
# Anthropic: claude-3-sonnet-20240229 (exact date required)
```

---

## 📈 Performance Tuning

### For High-Volume Environments
```bash
# Use fastest models
AI_PROVIDER=gemini
AI_MODEL=gemini-1.5-flash

# Increase thresholds
ADAPTATION_THRESHOLD=20
ANALYSIS_INTERVAL=300
```

### For Maximum Accuracy
```bash
# Use most capable models
AI_PROVIDER=openai
AI_MODEL=gpt-4

# Decrease thresholds for more frequent analysis
ADAPTATION_THRESHOLD=3
ANALYSIS_INTERVAL=30
```

---

## 🎯 Example Configurations

### Configuration 1: Budget-Friendly (Gemini Free)
```bash
GEMINI_API_KEY=your_key_here
AI_PROVIDER=gemini
AI_MODEL=gemini-1.5-flash
ADAPTATION_THRESHOLD=10
ANALYSIS_INTERVAL=120
MAX_HONEYPOTS=5
```

### Configuration 2: Balanced (Gemini Pro)
```bash
GEMINI_API_KEY=your_key_here
AI_PROVIDER=gemini
AI_MODEL=gemini-1.5-pro
ADAPTATION_THRESHOLD=5
ANALYSIS_INTERVAL=60
MAX_HONEYPOTS=10
```

### Configuration 3: Premium (GPT-4)
```bash
OPENAI_API_KEY=your_key_here
AI_PROVIDER=openai
AI_MODEL=gpt-4-turbo
ADAPTATION_THRESHOLD=3
ANALYSIS_INTERVAL=30
MAX_HONEYPOTS=15
```

---

## 📚 Additional Resources

### Gemini
- API Documentation: https://ai.google.dev/docs
- Pricing: https://ai.google.dev/pricing
- Models: https://ai.google.dev/models/gemini

### OpenAI
- API Documentation: https://platform.openai.com/docs
- Pricing: https://openai.com/pricing
- Models: https://platform.openai.com/docs/models

### Anthropic
- API Documentation: https://docs.anthropic.com/
- Pricing: https://www.anthropic.com/pricing
- Models: https://docs.anthropic.com/claude/docs/models-overview

---

## ✅ Quick Checklist

- [ ] Obtained API key from chosen provider
- [ ] Added API key to .env file
- [ ] Set AI_PROVIDER correctly
- [ ] Set AI_MODEL to valid model name
- [ ] Tested API connection
- [ ] Started the system
- [ ] Verified AI analysis is working
- [ ] Monitored costs/usage

---

**Recommendation**: Start with **Google Gemini 1.5 Flash** for testing (free tier), then upgrade to **Gemini 1.5 Pro** or **GPT-4 Turbo** for production based on your budget and quality requirements.
