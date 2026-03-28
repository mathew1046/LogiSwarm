# Using OpenCode Go Models

This guide explains how to configure LogiSwarm to use **OpenCode Go** models instead of Anthropic Claude.

## Overview

OpenCode Go provides access to various LLM models through an OpenAI-compatible API. LogiSwarm now supports this provider alongside Anthropic Claude.

## Configuration

### 1. Get Your API Key

Sign up at [opencode.ai](https://opencode.ai) and obtain your API key.

### 2. Update Environment Variables

Edit your `.env` file:

```bash
# Use OpenCode Go instead of Anthropic
LLM_API_KEY=your-opencode-api-key-here
LLM_BASE_URL=https://opencode.ai/zen/go/v1
LLM_MODEL_NAME=minimax-m2.5
```

### 3. Install Dependencies

The `openai` Python package is now included in the backend dependencies:

```bash
cd backend
pip install openai>=1.12.0
```

### 4. Restart Services

```bash
docker-compose restart backend
# or
cd backend && uvicorn app.main:app --reload
```

## Available Models

OpenCode Go supports various models. Check their documentation for the latest list:

| Model | Use Case | Recommended For |
|-------|----------|----------------|
| `minimax-m2.5` | General purpose | Good balance of performance and cost |
| `deepseek-coder` | Code generation | Technical analysis |
| Other models | Check OpenCode Go docs | Various specialized tasks |

## How It Works

The LLM core automatically detects OpenAI-compatible providers by checking the `base_url`:

```python
# Auto-detection logic
if "opencode.ai" in base_url.lower():
    # Use OpenAI client format
    client = OpenAI(api_key=api_key, base_url=base_url)
```

### Request Format

LogiSwarm converts prompts to OpenAI-compatible format:

```python
response = client.chat.completions.create(
    model="minimax-m2.5",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.3,
    max_tokens=800,
)
```

### Response Parsing

The response is parsed and converted to match Anthropic's structured output format:

```json
{
  "disruption_probability": 0.75,
  "severity": "HIGH",
  "affected_routes": ["route_1", "route_2"],
  "recommended_actions": ["reroute_via_cape"],
  "confidence": 0.82,
  "reasoning": "Weather pattern indicates..."
}
```

## Testing

Test your configuration:

```bash
cd backend
python -c "
import os
from app.agents.llm_core import ClaudeReasoningCore
import asyncio

os.environ['LLM_API_KEY'] = 'your-key'
os.environ['LLM_BASE_URL'] = 'https://opencode.ai/zen/go/v1'

async def test():
    core = ClaudeReasoningCore(
        model_name='minimax-m2.5',
        agent_id='test'
    )
    result = await core.reason({
        'system_prompt': 'You are a supply chain analyst.',
        'events': [{'type': 'weather_alert', 'severity': 'high'}],
        'memory_episodes': []
    })
    print(result)

asyncio.run(test())
"
```

## Troubleshooting

### API Key Issues

```bash
# Verify key is set
echo $LLM_API_KEY

# Test with curl
curl https://opencode.ai/zen/go/v1/chat/completions \
  -H "Authorization: Bearer $LLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"minimax-m2.5","messages":[{"role":"user","content":"hi"}]}'
```

### Model Not Found

Check that your model name is correct:

```bash
# List available models
curl https://opencode.ai/zen/go/v1/models \
  -H "Authorization: Bearer $LLM_API_KEY"
```

### Fallback Behavior

If OpenCode Go calls fail, the system will:
1. Log the error
2. Return a fallback assessment with zero confidence
3. Continue operating without LLM reasoning

## Performance Considerations

| Metric | Anthropic Claude | OpenCode Go |
|--------|------------------|-------------|
| Latency | ~2-4s | Varies by model |
| Rate limits | Check provider docs | Check provider docs |
| Cost | Provider dependent | Provider dependent |

## Switching Back to Anthropic

Simply revert your `.env`:

```bash
LLM_API_KEY=your-anthropic-key
LLM_BASE_URL=https://api.anthropic.com
LLM_MODEL_NAME=claude-sonnet-4-6
```

No code changes needed!

## Advanced: Dual Provider Setup

You can configure a fallback provider:

```bash
# Primary: Anthropic
LLM_API_KEY=anthropic-key
LLM_BASE_URL=https://api.anthropic.com
LLM_MODEL_NAME=claude-sonnet-4-6

# Fallback: OpenCode Go (automatically used on rate limits/timeouts)
LLM_FALLBACK_MODEL=minimax-m2.5
```

The system will automatically fall back to the configured fallback model when the primary provider fails.