const fs = require("fs");
const path = require("path");

const LOGS_DIR = path.join(__dirname, "..", "logs");

/**
 * Save agent output to a JSON log file.
 * Creates /logs/ directory if it doesn't exist.
 *
 * @param {string} agentName - Agent role name (architect, product, etc.)
 * @param {object} data - Data to log
 */
async function logAgentOutput(agentName, data) {
  if (!fs.existsSync(LOGS_DIR)) {
    fs.mkdirSync(LOGS_DIR, { recursive: true });
  }

  const logPath = path.join(LOGS_DIR, `${agentName}.json`);

  let existing = [];
  if (fs.existsSync(logPath)) {
    try {
      const content = fs.readFileSync(logPath, "utf-8");
      existing = JSON.parse(content);
      if (!Array.isArray(existing)) {
        existing = [existing];
      }
    } catch {
      existing = [];
    }
  }

  existing.push(data);
  fs.writeFileSync(logPath, JSON.stringify(existing, null, 2), "utf-8");
}

/**
 * Read all logs for a specific agent.
 *
 * @param {string} agentName - Agent role name
 * @returns {Array} Array of log entries
 */
function readAgentLogs(agentName) {
  const logPath = path.join(LOGS_DIR, `${agentName}.json`);
  if (!fs.existsSync(logPath)) {
    return [];
  }
  try {
    const content = fs.readFileSync(logPath, "utf-8");
    const parsed = JSON.parse(content);
    return Array.isArray(parsed) ? parsed : [parsed];
  } catch {
    return [];
  }
}

module.exports = { logAgentOutput, readAgentLogs };
