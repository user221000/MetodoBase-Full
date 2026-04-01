const { runAgent } = require("./runAgent");

/**
 * Run the full multi-agent pipeline:
 *   Architect → Product → Engineer → QA → (optional) Engineer Fixes
 *
 * @param {string} input - Initial context or feature request
 * @returns {Promise<object>} Combined pipeline result
 */
async function runPipeline(input) {
  console.log("\n══════════════════════════════════════");
  console.log("  MULTI-AGENT PIPELINE — Starting");
  console.log("══════════════════════════════════════\n");

  // ── Step 1: Architect ──
  console.log("[1/4] Running Architect agent...");
  const architectOutput = await runAgent(
    "architect",
    `Analyze the following and provide your architectural assessment:\n\n${input}`
  );
  console.log(
    `  → Found ${architectOutput.problems?.length || 0} problems, ${architectOutput.plan?.length || 0} plan steps`
  );

  // ── Step 2: Product ──
  console.log("[2/4] Running Product agent...");
  const productInput = [
    "Based on the architect's analysis, propose product improvements.",
    "",
    "Architect's identified problems:",
    JSON.stringify(architectOutput.problems, null, 2),
    "",
    "Architect's proposed plan:",
    JSON.stringify(architectOutput.plan, null, 2),
    "",
    "Original request:",
    input,
  ].join("\n");

  const productOutput = await runAgent("product", productInput);
  console.log(
    `  → Proposed ${productOutput.features?.length || 0} features, ${productOutput.ui_changes?.length || 0} UI changes`
  );

  // ── Step 3: Engineer ──
  console.log("[3/4] Running Engineer agent...");
  const engineerInput = [
    "Implement the following spec exactly as described.",
    "",
    "Architecture plan:",
    JSON.stringify(architectOutput.plan, null, 2),
    "",
    "Do NOT touch these files:",
    JSON.stringify(architectOutput.do_not_touch, null, 2),
    "",
    "Product priorities:",
    JSON.stringify(productOutput.priorities, null, 2),
    "",
    "Features to implement:",
    JSON.stringify(productOutput.features, null, 2),
    "",
    "UI changes:",
    JSON.stringify(productOutput.ui_changes, null, 2),
  ].join("\n");

  const engineerOutput = await runAgent("engineer", engineerInput);
  console.log(
    `  → Modified ${engineerOutput.files_modified?.length || 0} files, removed ${engineerOutput.removed_legacy?.length || 0} legacy items`
  );

  // ── Step 4: QA ──
  console.log("[4/4] Running QA agent...");
  const qaInput = [
    "Test the following implementation rigorously.",
    "",
    "Original spec (architect plan):",
    JSON.stringify(architectOutput.plan, null, 2),
    "",
    "Files modified by engineer:",
    JSON.stringify(engineerOutput.files_modified, null, 2),
    "",
    "Engineer's implementation:",
    typeof engineerOutput.code === "string"
      ? engineerOutput.code.slice(0, 3000)
      : JSON.stringify(engineerOutput.code, null, 2).slice(0, 3000),
    "",
    "Files that must NOT have been touched:",
    JSON.stringify(architectOutput.do_not_touch, null, 2),
  ].join("\n");

  const qaOutput = await runAgent("qa", qaInput);
  console.log(
    `  → Passed: ${qaOutput.tests_passed}, Failed: ${qaOutput.tests_failed}, Critical: ${qaOutput.critical_issues?.length || 0}`
  );

  // ── Step 5: Optional Engineer Fixes ──
  let fixOutput = null;
  const hasCriticalIssues =
    qaOutput.critical_issues && qaOutput.critical_issues.length > 0;

  if (hasCriticalIssues) {
    console.log("[5/5] Critical issues found — running Engineer fixes...");
    const fixInput = [
      "Fix the following critical issues found by QA. Apply ONLY the requested fixes.",
      "",
      "Critical issues:",
      JSON.stringify(qaOutput.critical_issues, null, 2),
      "",
      "Fix instructions from QA:",
      JSON.stringify(qaOutput.fix_instructions, null, 2),
      "",
      "Previous implementation context:",
      JSON.stringify(engineerOutput.files_modified, null, 2),
    ].join("\n");

    fixOutput = await runAgent("engineer", fixInput);
    console.log(
      `  → Fixed ${fixOutput.files_modified?.length || 0} files`
    );
  } else {
    console.log("[5/5] No critical issues — skipping fix pass.");
  }

  // ── Assemble final result ──
  const result = {
    pipeline_status: hasCriticalIssues ? "completed_with_fixes" : "clean",
    timestamp: new Date().toISOString(),
    stages: {
      architect: architectOutput,
      product: productOutput,
      engineer: engineerOutput,
      qa: qaOutput,
      engineer_fixes: fixOutput,
    },
    summary: {
      problems_found: architectOutput.problems?.length || 0,
      features_proposed: productOutput.features?.length || 0,
      files_modified: engineerOutput.files_modified?.length || 0,
      tests_passed: qaOutput.tests_passed || 0,
      tests_failed: qaOutput.tests_failed || 0,
      critical_issues: qaOutput.critical_issues?.length || 0,
      fixes_applied: fixOutput?.files_modified?.length || 0,
    },
  };

  console.log("\n══════════════════════════════════════");
  console.log("  PIPELINE COMPLETE");
  console.log("══════════════════════════════════════");
  console.log(`  Status:     ${result.pipeline_status}`);
  console.log(`  Problems:   ${result.summary.problems_found}`);
  console.log(`  Features:   ${result.summary.features_proposed}`);
  console.log(`  Files:      ${result.summary.files_modified}`);
  console.log(`  QA passed:  ${result.summary.tests_passed}`);
  console.log(`  QA failed:  ${result.summary.tests_failed}`);
  console.log(`  Critical:   ${result.summary.critical_issues}`);
  console.log(`  Fixes:      ${result.summary.fixes_applied}`);
  console.log("══════════════════════════════════════\n");

  return result;
}

module.exports = { runPipeline };
