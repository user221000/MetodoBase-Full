"""
orchestrator/pipeline.py — Multi-agent pipeline orchestrator.

Flow: Architect → Product → Engineer → QA → (optional) Engineer Fixes

Each agent receives only the relevant data from prior stages.
"""

import json
import logging
import os
import time
from pathlib import Path

from orchestrator.run_agent import run_agent

logger = logging.getLogger(__name__)


def run_pipeline(input_text: str) -> dict:
    """
    Run the full multi-agent pipeline.

    Args:
        input_text: Initial context or feature request

    Returns:
        Combined pipeline result with all stages
    """
    logger.info("MULTI-AGENT PIPELINE — Starting")

    # ── Step 1: Architect ──
    logger.info("[1/4] Running Architect agent...")
    architect = run_agent(
        "architect",
        f"Analyze the following and provide your architectural assessment:\n\n{input_text}",
    )
    logger.info("  → Found %d problems, %d plan steps",
                len(architect.get('problems', [])),
                len(architect.get('plan', [])))

    # ── Step 2: Product ──
    logger.info("[2/4] Running Product agent...")
    product_input = "\n".join([
        "Based on the architect's analysis, propose product improvements.",
        "",
        "Architect's identified problems:",
        json.dumps(architect.get("problems", []), indent=2),
        "",
        "Architect's proposed plan:",
        json.dumps(architect.get("plan", []), indent=2),
        "",
        "Original request:",
        input_text,
    ])
    product = run_agent("product", product_input)
    logger.info("  → Proposed %d features, %d UI changes",
                len(product.get('features', [])),
                len(product.get('ui_changes', [])))

    # ── Step 3: Engineer ──
    logger.info("[3/4] Running Engineer agent...")
    engineer_input = "\n".join([
        "Implement the following spec exactly as described.",
        "",
        "Architecture plan:",
        json.dumps(architect.get("plan", []), indent=2),
        "",
        "Do NOT touch these files:",
        json.dumps(architect.get("do_not_touch", []), indent=2),
        "",
        "Product priorities:",
        json.dumps(product.get("priorities", []), indent=2),
        "",
        "Features to implement:",
        json.dumps(product.get("features", []), indent=2),
        "",
        "UI changes:",
        json.dumps(product.get("ui_changes", []), indent=2),
    ])
    engineer = run_agent("engineer", engineer_input)
    logger.info("  → Modified %d files, removed %d legacy items",
                len(engineer.get('files_modified', [])),
                len(engineer.get('removed_legacy', [])))

    # ── Step 4: QA ──
    logger.info("[4/4] Running QA agent...")
    code_preview = engineer.get("code", "")
    if isinstance(code_preview, str):
        code_preview = code_preview[:3000]
    else:
        code_preview = json.dumps(code_preview, indent=2)[:3000]

    qa_input = "\n".join([
        "Test the following implementation rigorously.",
        "",
        "Original spec (architect plan):",
        json.dumps(architect.get("plan", []), indent=2),
        "",
        "Files modified by engineer:",
        json.dumps(engineer.get("files_modified", []), indent=2),
        "",
        "Engineer's implementation:",
        code_preview,
        "",
        "Files that must NOT have been touched:",
        json.dumps(architect.get("do_not_touch", []), indent=2),
    ])
    qa = run_agent("qa", qa_input)
    logger.info("  → Passed: %d, Failed: %d, Critical: %d",
                qa.get('tests_passed', 0),
                qa.get('tests_failed', 0),
                len(qa.get('critical_issues', [])))

    # ── Step 5: Optional Engineer Fixes ──
    fix_output = None
    has_critical = bool(qa.get("critical_issues"))

    if has_critical:
        logger.info("[5/5] Critical issues found — running Engineer fixes...")
        fix_input = "\n".join([
            "Fix the following critical issues found by QA. Apply ONLY the requested fixes.",
            "",
            "Critical issues:",
            json.dumps(qa["critical_issues"], indent=2),
            "",
            "Fix instructions from QA:",
            json.dumps(qa.get("fix_instructions", []), indent=2),
            "",
            "Previous implementation context:",
            json.dumps(engineer.get("files_modified", []), indent=2),
        ])
        fix_output = run_agent("engineer", fix_input)
        logger.info("  → Fixed %d files", len(fix_output.get('files_modified', [])))
    else:
        logger.info("[5/5] No critical issues — skipping fix pass.")

    # ── Assemble result ──
    result = {
        "pipeline_status": "completed_with_fixes" if has_critical else "clean",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "stages": {
            "architect": architect,
            "product": product,
            "engineer": engineer,
            "qa": qa,
            "engineer_fixes": fix_output,
        },
        "summary": {
            "problems_found": len(architect.get("problems", [])),
            "features_proposed": len(product.get("features", [])),
            "files_modified": len(engineer.get("files_modified", [])),
            "tests_passed": qa.get("tests_passed", 0),
            "tests_failed": qa.get("tests_failed", 0),
            "critical_issues": len(qa.get("critical_issues", [])),
            "fixes_applied": len(fix_output.get("files_modified", [])) if fix_output else 0,
        },
    }

    logger.info("PIPELINE COMPLETE")
    s = result["summary"]
    logger.info("  Status:     %s", result['pipeline_status'])
    logger.info("  Problems:   %d", s['problems_found'])
    logger.info("  Features:   %d", s['features_proposed'])
    logger.info("  Files:      %d", s['files_modified'])
    logger.info("  QA passed:  %d", s['tests_passed'])
    logger.info("  QA failed:  %d", s['tests_failed'])
    logger.info("  Critical:   %d", s['critical_issues'])
    logger.info("  Fixes:      %d", s['fixes_applied'])

    return result
