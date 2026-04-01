#!/usr/bin/env node

require("dotenv").config();

const fs = require("fs");
const path = require("path");
const { runPipeline } = require("./orchestrator/pipeline");

const DEFAULT_INPUT = [
  "Analyze the MetodoBase nutrition SaaS platform.",
  "The platform serves gyms and independent nutritionists.",
  "It includes: meal plan generation, PDF export, client management, dashboard, and billing.",
  "Tech stack: Python backend, PySide6 desktop UI, FastAPI web API, SQLite/PostgreSQL.",
  "",
  "Focus areas:",
  "1. Identify architectural issues and technical debt",
  "2. Propose monetizable features for gym owners",
  "3. Implement the highest-priority improvement",
  "4. Verify the implementation quality",
].join("\n");

async function main() {
  const input = process.argv[2] || DEFAULT_INPUT;

  console.log("Pipeline input:");
  console.log("─".repeat(40));
  console.log(input.slice(0, 300));
  if (input.length > 300) console.log("...");
  console.log("─".repeat(40));

  try {
    const result = await runPipeline(input);

    const logsDir = path.join(__dirname, "logs");
    if (!fs.existsSync(logsDir)) {
      fs.mkdirSync(logsDir, { recursive: true });
    }

    const resultPath = path.join(logsDir, "pipeline-result.json");
    fs.writeFileSync(resultPath, JSON.stringify(result, null, 2), "utf-8");
    console.log(`\nFull result saved to: ${resultPath}`);
  } catch (err) {
    console.error("\nPipeline failed:", err.message);
    process.exit(1);
  }
}

main();
