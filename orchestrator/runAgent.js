const fs = require("fs");
const path = require("path");
const { parseJSON } = require("../utils/parseJSON");
const { logAgentOutput } = require("../utils/logger");

const AGENTS_DIR = path.join(__dirname, "..", "agents");
const MAX_RETRIES = 2;

/**
 * Run a single agent: load its prompt, call the LLM, parse JSON response.
 * @param {string} role - Agent name (architect|product|engineer|qa)
 * @param {string} userInput - The user message / context to send
 * @returns {Promise<object>} Parsed JSON from the agent
 */
async function runAgent(role, userInput) {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    throw new Error("OPENAI_API_KEY environment variable is not set");
  }

  const baseUrl = process.env.OPENAI_BASE_URL || "https://api.openai.com/v1";
  const model = process.env.OPENAI_MODEL || "gpt-4o";

  const promptPath = path.join(AGENTS_DIR, `${role}.prompt.txt`);
  if (!fs.existsSync(promptPath)) {
    throw new Error(`Prompt file not found: ${promptPath}`);
  }

  const systemPrompt = fs.readFileSync(promptPath, "utf-8").trim();

  let lastError = null;

  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    try {
      const response = await fetch(`${baseUrl}/chat/completions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${apiKey}`,
        },
        body: JSON.stringify({
          model,
          temperature: 0.2,
          messages: [
            { role: "system", content: systemPrompt },
            { role: "user", content: userInput },
          ],
          response_format: { type: "json_object" },
        }),
      });

      if (!response.ok) {
        const errorBody = await response.text();
        throw new Error(
          `API returned ${response.status}: ${errorBody.slice(0, 500)}`
        );
      }

      const data = await response.json();
      const content = data.choices?.[0]?.message?.content;

      if (!content) {
        throw new Error("Empty response from LLM");
      }

      const parsed = parseJSON(content);

      await logAgentOutput(role, {
        attempt: attempt + 1,
        model,
        input: userInput.slice(0, 200),
        output: parsed,
        timestamp: new Date().toISOString(),
      });

      return parsed;
    } catch (err) {
      lastError = err;
      const isLastAttempt = attempt === MAX_RETRIES;
      console.error(
        `[${role}] Attempt ${attempt + 1}/${MAX_RETRIES + 1} failed: ${err.message}`
      );
      if (!isLastAttempt) {
        const delay = 1000 * (attempt + 1);
        await new Promise((resolve) => setTimeout(resolve, delay));
      }
    }
  }

  throw new Error(
    `Agent "${role}" failed after ${MAX_RETRIES + 1} attempts: ${lastError?.message}`
  );
}

module.exports = { runAgent };
