# Multi-Agent Orchestration Pipeline

A production-ready multi-agent pipeline system built with plain Node.js and OpenAI-compatible APIs.

## Architecture

```
Input → Architect → Product → Engineer → QA → (optional) Engineer Fixes → Output
```

Each agent receives structured context from the previous stage and returns strict JSON.

## File Structure

```
agents/                  — Agent system prompts
  architect.prompt.txt
  product.prompt.txt
  engineer.prompt.txt
  qa.prompt.txt

orchestrator/            — Pipeline core
  runAgent.js            — Load prompt, call LLM, parse response, retry
  pipeline.js            — Chain agents: Architect → Product → Engineer → QA → Fixes

utils/                   — Shared utilities
  parseJSON.js           — Safe JSON parser for LLM responses
  logger.js              — Per-agent JSON logging to /logs/

run.js                   — Entry point
package.json             — Dependencies (dotenv only)
logs/                    — Auto-created at runtime
```

## Installation

```bash
npm install
```

Requires Node.js 18+ (uses native fetch).

## Configuration

Add your API key to `.env` (see `.env.example`):

```
OPENAI_API_KEY=sk-your-key-here
```

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | Yes | — | Your OpenAI API key |
| `OPENAI_BASE_URL` | No | `https://api.openai.com/v1` | For OpenAI-compatible providers |
| `OPENAI_MODEL` | No | `gpt-4o` | Model identifier |

## Running

```bash
node run.js
node run.js "Analyze the authentication module and propose improvements"
```

Pipeline stages:
1. **Architect** — Detect structural issues, produce implementation plan
2. **Product** — Propose monetizable features, prioritize by impact
3. **Engineer** — Implement the combined spec
4. **QA** — Find critical issues, provide fix instructions
5. **Engineer Fixes** — Auto-triggered only if QA finds critical issues

Result saved to `logs/pipeline-result.json`.

## Adding Agents

1. Create `agents/my-agent.prompt.txt` with a system prompt that returns JSON
2. Call from code:
   ```js
   const { runAgent } = require("./orchestrator/runAgent");
   const result = await runAgent("my-agent", "input");
   ```
3. Insert into `orchestrator/pipeline.js` to add it to the chain

## Logs

Each run appends to `logs/{agent-name}.json`. Final result: `logs/pipeline-result.json`.
