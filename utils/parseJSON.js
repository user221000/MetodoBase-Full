/**
 * Safe JSON parser with controlled error handling.
 * Strips markdown fences and trailing commas before parsing.
 *
 * @param {string} raw - Raw string from LLM response
 * @returns {object} Parsed JSON object
 * @throws {Error} If parsing fails after cleanup
 */
function parseJSON(raw) {
  if (typeof raw !== "string" || raw.trim().length === 0) {
    throw new Error("parseJSON: received empty or non-string input");
  }

  let cleaned = raw.trim();

  // Strip markdown code fences (```json ... ``` or ``` ... ```)
  cleaned = cleaned.replace(/^```(?:json)?\s*\n?/i, "").replace(/\n?```\s*$/, "");
  cleaned = cleaned.trim();

  // Remove trailing commas before closing brackets/braces
  cleaned = cleaned.replace(/,\s*([}\]])/g, "$1");

  try {
    return JSON.parse(cleaned);
  } catch (firstError) {
    // Try extracting first JSON object from the string
    const objectMatch = cleaned.match(/\{[\s\S]*\}/);
    if (objectMatch) {
      try {
        const extracted = objectMatch[0].replace(/,\s*([}\]])/g, "$1");
        return JSON.parse(extracted);
      } catch (_) {
        // fall through
      }
    }

    throw new Error(
      `parseJSON: failed to parse LLM response. ` +
        `First 200 chars: "${raw.slice(0, 200)}". ` +
        `Error: ${firstError.message}`
    );
  }
}

module.exports = { parseJSON };
