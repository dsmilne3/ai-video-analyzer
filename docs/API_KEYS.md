# API Key Configuration Guide

This guide explains how to securely configure API keys for the video evaluator.

## Why API Keys Are Required

**API keys are required** for the core qualitative analysis and feedback generation features. The system uses LLM APIs (OpenAI or Anthropic) to:

- Evaluate video transcripts against rubrics with intelligent scoring
- Generate detailed qualitative feedback with specific strengths and improvement suggestions
- Provide adaptive tone (congratulatory/supportive) based on performance

Without API keys, the system falls back to basic heuristic methods that provide conservative, but less accurate scoring and generic feedback.

## Quick Setup

### 1. Create Your .env File

```bash
# Option A: If .env doesn't exist yet
cp .env.example .env

# Option B: If .env already exists (e.g., from running run_gpu.sh)
# Just edit the existing .env file and add the API keys below
# Your GPU settings will be preserved
```

### 2. Add Your API Keys

Edit `.env` to include your actual keys (add these lines if they're not already there):

```bash
# OpenAI API Key (required for OpenAI provider)
OPENAI_API_KEY=sk-proj-abc123xyz...

# Anthropic API Key (required for Anthropic provider)
ANTHROPIC_API_KEY=sk-ant-xyz789abc...
```

### 3. Secure the File (Recommended)

```bash
chmod 600 .env
```

**Note**: If you've already run `./run_gpu.sh`, your `.env` file may already exist with GPU configuration variables. Simply add the API keys above to your existing `.env` file - don't overwrite it!

This ensures only you can read/write the file.

### 4. Test Your Configuration

```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); \
print('✓ OpenAI key loaded' if os.getenv('OPENAI_API_KEY') else '✗ No OpenAI key'); \
print('✓ Anthropic key loaded' if os.getenv('ANTHROPIC_API_KEY') else '✗ No Anthropic key')"
```

## Getting API Keys

### OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Create a new secret key
3. Copy the key (starts with `sk-proj-...`)
4. Add to `.env` as `OPENAI_API_KEY`

### Anthropic API Key

1. Go to https://console.anthropic.com/settings/keys
2. Create a new API key
3. Copy the key (starts with `sk-ant-...`)
4. Add to `.env` as `ANTHROPIC_API_KEY`

## How Keys Are Loaded

The system supports **two methods** for configuring API keys, with environment variables taking precedence:

### Method 1: .env File (Recommended)
Keys in `.env` file are automatically loaded when the app starts.

### Method 2: Environment Variables
You can also set keys directly in your shell environment:

```bash
# For current session only
export OPENAI_API_KEY=sk-proj-your-key-here
export ANTHROPIC_API_KEY=sk-ant-your-key-here

# For permanent setup, add to your shell profile (~/.zshrc, ~/.bashrc, etc.)
echo 'export OPENAI_API_KEY=sk-proj-your-key-here' >> ~/.zshrc
echo 'export ANTHROPIC_API_KEY=sk-ant-your-key-here' >> ~/.zshrc
```

### Precedence Rules
1. **Environment variables** override `.env` file values
2. If neither exists, the app falls back to heuristic evaluation (limited functionality)
3. **Restart required**: After changing environment variables, restart Streamlit

The system automatically loads API keys from environment variables based on the provider:

- **OpenAI provider** → Looks for `OPENAI_API_KEY`
- **Anthropic provider** → Looks for `ANTHROPIC_API_KEY`

Example code:

```python
from src.video_evaluator import VideoEvaluator, AIProvider

# API key automatically loaded from .env
evaluator = VideoEvaluator(provider=AIProvider.OPENAI)

# Process a video
result = evaluator.process("demo.mp4")
```

## Running Tests

### Without API Keys (Mock Mode - Limited Functionality)

```bash
python -m pytest tests/test_evaluator.py -v
```

Tests will run using mock evaluations with basic heuristic scoring (no qualitative analysis).

### With API Keys (Full Functionality)

```bash
# Ensure .env exists with your keys
python -m pytest tests/test_evaluator.py -v
```

With API keys configured, tests use real API calls for comprehensive evaluation and feedback generation.

## Security Best Practices

✅ **DO:**

- Keep `.env` file in `.gitignore` (already configured)
- Set file permissions to 600: `chmod 600 .env`
- Use different keys for development and production
- Rotate keys periodically
- Use `.env.example` as a template (safe to commit)

❌ **DON'T:**

- Commit `.env` to git
- Share your `.env` file
- Hard-code keys in source code
- Use `export` in your shell (keys end up in history)
- Share screenshots with visible API keys

## Troubleshooting

### "No API key found" Error

1. Check that `.env` exists in project root
2. Verify keys are set correctly in `.env`
3. Ensure no extra spaces around the `=` sign
4. Run the test command from step 4 above

### Keys Not Loading

```bash
# Check if python-dotenv is installed
pip list | grep python-dotenv

# Verify .env location
ls -la .env

# Test loading manually
python -c "from dotenv import load_dotenv; print(load_dotenv())"
```

### Permission Denied

```bash
# Fix file permissions
chmod 600 .env
```

## Environment Variables Reference

| Variable            | Purpose                      | Required For                  |
| ------------------- | ---------------------------- | ----------------------------- |
| `OPENAI_API_KEY`    | OpenAI API authentication    | OpenAI provider (recommended) |
| `ANTHROPIC_API_KEY` | Anthropic API authentication | Anthropic provider            |

**Note**: At least one API key is required for qualitative analysis features. Without API keys, the system uses heuristic fallback methods with limited functionality.

## Example .env File

```bash
# Complete example .env file
OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwxyz123456789
ANTHROPIC_API_KEY=sk-ant-xyz789abcdefghijklmnopqrstuvwxyz123456
```

Remember: This file should NEVER be committed to git!
