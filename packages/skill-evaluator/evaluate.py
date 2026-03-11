#!/usr/bin/env python3
"""Skill Evaluator — assess Claude Code skills (SKILL.md) across multiple dimensions."""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml
import tiktoken

from rubrics import RUBRICS


# ---------------------------------------------------------------------------
# Tier 1: Deterministic Checks
# ---------------------------------------------------------------------------

def check_skill_md_exists(skill_dir: Path) -> dict:
    """SKILL.md must be present."""
    exists = (skill_dir / "SKILL.md").is_file()
    return {
        "check": "SKILL.md exists",
        "passed": exists,
        "score": 1 if exists else 0,
        "detail": "" if exists else "SKILL.md not found — this is a hard requirement.",
    }


def check_kebab_case(skill_dir: Path) -> dict:
    """Directory name must be kebab-case."""
    name = skill_dir.resolve().name
    pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    passed = bool(re.match(pattern, name))
    return {
        "check": "kebab-case directory",
        "passed": passed,
        "score": 1 if passed else 0,
        "detail": "" if passed else f"Directory name '{name}' does not match kebab-case pattern.",
    }


def check_yaml_frontmatter(skill_dir: Path) -> dict:
    """SKILL.md should have YAML frontmatter with name and description."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return {
            "check": "YAML frontmatter",
            "passed": False,
            "score": 0,
            "detail": "SKILL.md not found.",
        }

    content = skill_md.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return {
            "check": "YAML frontmatter",
            "passed": False,
            "score": 0,
            "detail": "No YAML frontmatter block found (file does not start with ---).",
        }

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {
            "check": "YAML frontmatter",
            "passed": False,
            "score": 0,
            "detail": "Malformed frontmatter — missing closing ---.",
        }

    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        return {
            "check": "YAML frontmatter",
            "passed": False,
            "score": 0,
            "detail": f"YAML parse error: {e}",
        }

    if not isinstance(fm, dict):
        return {
            "check": "YAML frontmatter",
            "passed": False,
            "score": 0,
            "detail": "Frontmatter is not a YAML mapping.",
        }

    missing = [f for f in ("name", "description") if f not in fm]
    passed = len(missing) == 0
    return {
        "check": "YAML frontmatter",
        "passed": passed,
        "score": 1 if passed else 0,
        "detail": "" if passed else f"Missing frontmatter fields: {', '.join(missing)}.",
    }


def check_metadata_json(skill_dir: Path) -> dict:
    """If metadata.json exists, validate it has name, description, and tags."""
    meta_path = skill_dir / "metadata.json"
    if not meta_path.is_file():
        return {
            "check": "metadata.json",
            "passed": True,
            "score": 1,
            "detail": "metadata.json not present (optional).",
        }

    try:
        data = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return {
            "check": "metadata.json",
            "passed": False,
            "score": 0,
            "detail": f"Invalid JSON: {e}",
        }

    if not isinstance(data, dict):
        return {
            "check": "metadata.json",
            "passed": False,
            "score": 0,
            "detail": "metadata.json root is not an object.",
        }

    missing = [f for f in ("name", "description", "tags") if f not in data]
    passed = len(missing) == 0
    return {
        "check": "metadata.json",
        "passed": passed,
        "score": 1 if passed else 0,
        "detail": "" if passed else f"Missing fields: {', '.join(missing)}.",
    }


def check_length_efficiency(skill_dir: Path) -> dict:
    """Token count and instruction-to-boilerplate ratio."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return {
            "check": "length/efficiency",
            "passed": False,
            "score": 0,
            "detail": "SKILL.md not found.",
        }

    content = skill_md.read_text(encoding="utf-8")
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(content)
    token_count = len(tokens)

    # Count code-block lines vs total lines as a rough boilerplate proxy
    lines = content.split("\n")
    total_lines = len(lines)
    code_lines = 0
    in_code = False
    for line in lines:
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            code_lines += 1

    instruction_lines = total_lines - code_lines
    ratio = instruction_lines / max(code_lines, 1)

    if token_count > 15000:
        return {
            "check": "length/efficiency",
            "passed": False,
            "score": 0,
            "detail": f"{token_count} tokens (>15k limit). Instruction/code ratio: {ratio:.1f}.",
        }

    return {
        "check": "length/efficiency",
        "passed": True,
        "score": 1,
        "detail": f"{token_count} tokens. Instruction/code ratio: {ratio:.1f}.",
    }


def check_prerequisites(skill_dir: Path) -> dict:
    """Keyword scan to classify prerequisite scope (broad vs niche)."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return {
            "check": "prerequisites",
            "passed": True,
            "score": 1,
            "detail": "SKILL.md not found.",
        }

    content = skill_md.read_text(encoding="utf-8").lower()
    markers = {
        "aws": r"\baws\b",
        "gcp": r"\bgcp\b|\bgoogle cloud\b",
        "azure": r"\bazure\b",
        "docker": r"\bdocker\b",
        "kubernetes": r"\bkubernetes\b|\bk8s\b",
        "database": r"\bpostgres\b|\bmysql\b|\bmongodb\b|\bdynamodb\b|\bredis\b",
        "terraform": r"\bterraform\b",
    }

    found = [name for name, pat in markers.items() if re.search(pat, content)]

    if len(found) >= 3:
        detail = f"Broad prerequisites detected ({', '.join(found)}). May limit audience."
        passed = True  # informational, not a failure
    elif found:
        detail = f"Niche prerequisites: {', '.join(found)}."
        passed = True
    else:
        detail = "No heavy external prerequisites detected."
        passed = True

    return {
        "check": "prerequisites",
        "passed": passed,
        "score": 1,
        "detail": detail,
    }


def check_security_patterns(skill_dir: Path) -> dict:
    """Scan for dangerous patterns and check for a security section."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return {
            "check": "security patterns",
            "passed": False,
            "score": 0,
            "detail": "SKILL.md not found.",
        }

    content = skill_md.read_text(encoding="utf-8")

    dangerous_patterns = [
        (r"rm\s+-rf\s+/(?!\S)", "rm -rf / (root deletion)"),
        (r"--no-verify", "--no-verify (skip git hooks)"),
        (r"\bsudo\b", "sudo usage"),
        (r"\beval\s*\(", "eval() call"),
        (r"\|\s*(?:bash|sh|zsh)\b", "pipe to shell"),
        (r"(?i)ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions", "prompt injection phrase"),
        (r"(?i)you\s+are\s+now\s+(?:a|an)\b", "prompt injection phrase"),
    ]

    findings = []
    for pat, label in dangerous_patterns:
        matches = re.findall(pat, content)
        if matches:
            findings.append(f"{label} ({len(matches)}x)")

    # Check for external URLs
    urls = re.findall(r"https?://[^\s\)>\"]+", content)
    unique_domains = set()
    for url in urls:
        match = re.match(r"https?://([^/\s]+)", url)
        if match:
            unique_domains.add(match.group(1))

    # Check for security section
    has_security_section = bool(re.search(r"(?i)^#+\s*.*security", content, re.MULTILINE))

    details = []
    if findings:
        details.append(f"Dangerous patterns: {'; '.join(findings)}")
    if unique_domains:
        details.append(f"External domains ({len(unique_domains)}): {', '.join(sorted(unique_domains)[:10])}")
    if has_security_section:
        details.append("Has security section.")
    else:
        details.append("No security section found.")

    # Pass if no dangerous patterns found (or they're inside security guidance context)
    # and a security section exists
    passed = len(findings) == 0 or has_security_section
    score = 1 if passed else 0

    return {
        "check": "security patterns",
        "passed": passed,
        "score": score,
        "detail": " | ".join(details),
    }


TIER1_CHECKS = [
    check_skill_md_exists,
    check_kebab_case,
    check_yaml_frontmatter,
    check_metadata_json,
    check_length_efficiency,
    check_prerequisites,
    check_security_patterns,
]


def run_tier1(skill_dir: Path) -> list[dict]:
    return [check(skill_dir) for check in TIER1_CHECKS]


# ---------------------------------------------------------------------------
# Tier 2: LLM-as-Judge
# ---------------------------------------------------------------------------

def judge_dimension(
    skill_content: str,
    metadata: dict | None,
    dimension: str,
    rubric: dict,
    model: str,
) -> dict:
    """Use `claude -p` to score a single dimension."""
    scale_text = "\n".join(f"  {k}: {v}" for k, v in rubric["scale"].items())
    meta_text = ""
    if metadata:
        meta_text = f"\n\nMetadata:\n```json\n{json.dumps(metadata, indent=2)}\n```"

    system_prompt = (
        "You are a skill quality evaluator for Claude Code agent skills. "
        "You assess SKILL.md files that serve as prompts/instructions for an AI coding assistant. "
        "Be rigorous but fair. Evaluate based on the rubric provided."
    )

    user_prompt = (
        f"Evaluate the following skill on the **{dimension}** dimension.\n\n"
        f"## Rubric\n\n"
        f"Question: {rubric['question']}\n\n"
        f"Rating scale:\n{scale_text}\n\n"
        f"## Skill Content\n\n"
        f"```markdown\n{skill_content}\n```"
        f"{meta_text}\n\n"
        f"Think step-by-step about your evaluation, then provide your final score.\n\n"
        f"Respond with ONLY a JSON object in this exact format:\n"
        f'{{"reasoning": "your analysis here", "score": N, "dimension": "{dimension}"}}\n\n'
        f"where N is an integer from 1 to 5."
    )

    cmd = [
        "claude", "-p",
        "--model", model,
        "--system-prompt", system_prompt,
        "--output-format", "text",
        "--allowedTools", "",
    ]

    proc = subprocess.run(
        cmd,
        input=user_prompt,
        capture_output=True,
        text=True,
        timeout=120,
    )

    if proc.returncode != 0:
        return {
            "reasoning": f"claude -p failed: {proc.stderr.strip()}",
            "score": 0,
            "dimension": dimension,
        }

    text = proc.stdout.strip()

    # Extract JSON from the response (handle markdown code fences)
    json_match = re.search(r"\{[^{}]*\"reasoning\"[^{}]*\}", text, re.DOTALL)
    if json_match:
        text = json_match.group(0)

    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        result = {"reasoning": text, "score": 0, "dimension": dimension}

    result["dimension"] = dimension
    return result


def run_tier2(skill_dir: Path, model: str) -> list[dict]:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return [{"dimension": d, "score": 0, "reasoning": "SKILL.md not found."} for d in RUBRICS]

    skill_content = skill_md.read_text(encoding="utf-8")

    metadata = None
    meta_path = skill_dir / "metadata.json"
    if meta_path.is_file():
        try:
            metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass

    results = []
    total = len(RUBRICS)
    for i, (dimension, rubric) in enumerate(RUBRICS.items(), 1):
        print(f"  Judging {dimension} ({i}/{total})...", file=sys.stderr, flush=True)
        result = judge_dimension(skill_content, metadata, dimension, rubric, model)
        results.append(result)

    return results


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def compute_grade(avg: float) -> str:
    if avg >= 4.5:
        return "A"
    if avg >= 4.0:
        return "A-"
    if avg >= 3.5:
        return "B+"
    if avg >= 3.0:
        return "B"
    if avg >= 2.5:
        return "C"
    if avg >= 2.0:
        return "D"
    return "F"


def format_text_report(skill_dir: Path, tier1: list[dict] | None, tier2: list[dict] | None) -> str:
    lines = []
    lines.append("=== Skill Evaluation Report ===")
    lines.append(f"Skill: {skill_dir.resolve().name}")
    lines.append("")

    if tier1 is not None:
        lines.append("--- Tier 1: Deterministic Checks ---")
        passed_count = 0
        for r in tier1:
            status = "PASS" if r["passed"] else "FAIL"
            detail = f" — {r['detail']}" if r["detail"] else ""
            lines.append(f"[{status}] {r['check']}{detail}")
            if r["passed"]:
                passed_count += 1
        lines.append("")

    if tier2 is not None:
        lines.append("--- Tier 2: LLM-as-Judge ---")
        for r in tier2:
            reasoning_short = r.get("reasoning", "")[:120]
            if len(r.get("reasoning", "")) > 120:
                reasoning_short += "..."
            lines.append(f"{r['dimension'].capitalize():15s} {r['score']}/5 — \"{reasoning_short}\"")
        lines.append("")

    lines.append("--- Summary ---")
    parts = []
    if tier1 is not None:
        t1_passed = sum(1 for r in tier1 if r["passed"])
        parts.append(f"Tier 1: {t1_passed}/{len(tier1)} passed")
    if tier2 is not None:
        scores = [r["score"] for r in tier2 if r["score"] > 0]
        avg = sum(scores) / len(scores) if scores else 0.0
        grade = compute_grade(avg)
        parts.append(f"Tier 2: {avg:.1f}/5.0 avg")
        parts.append(f"Grade: {grade}")

    lines.append(" | ".join(parts))
    lines.append("")
    return "\n".join(lines)


def build_json_report(skill_dir: Path, tier1: list[dict] | None, tier2: list[dict] | None) -> dict:
    report: dict = {"skill": skill_dir.resolve().name}

    if tier1 is not None:
        t1_passed = sum(1 for r in tier1 if r["passed"])
        report["tier1"] = {
            "checks": tier1,
            "passed": t1_passed,
            "total": len(tier1),
        }

    if tier2 is not None:
        scores = [r["score"] for r in tier2 if r["score"] > 0]
        avg = sum(scores) / len(scores) if scores else 0.0
        report["tier2"] = {
            "dimensions": tier2,
            "average": round(avg, 2),
            "grade": compute_grade(avg),
        }

    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Evaluate a Claude Code skill directory.",
    )
    parser.add_argument("skill_dir", type=Path, help="Path to the skill directory")
    parser.add_argument(
        "--tier",
        choices=["1", "2", "all"],
        default="all",
        help="Which evaluation tiers to run (default: all)",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-20250514",
        help="Model for Tier 2 LLM judge (default: claude-sonnet-4-20250514)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON",
    )
    args = parser.parse_args()

    skill_dir = args.skill_dir.resolve()
    if not skill_dir.is_dir():
        print(f"Error: '{skill_dir}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    run_t1 = args.tier in ("1", "all")
    run_t2 = args.tier in ("2", "all")

    tier1_results = run_tier1(skill_dir) if run_t1 else None
    tier2_results = None

    # Hard gate: if SKILL.md doesn't exist, skip Tier 2
    if run_t2:
        if tier1_results and not tier1_results[0]["passed"]:
            print("SKILL.md not found — skipping Tier 2.", file=sys.stderr)
        elif not shutil.which("claude"):
            print("Error: 'claude' CLI not found on PATH — cannot run Tier 2.", file=sys.stderr)
            if not run_t1:
                sys.exit(1)
        else:
            tier2_results = run_tier2(skill_dir, args.model)

    if args.json_output:
        print(json.dumps(build_json_report(skill_dir, tier1_results, tier2_results), indent=2))
    else:
        print(format_text_report(skill_dir, tier1_results, tier2_results))

    # Exit non-zero if any Tier 1 check failed
    if tier1_results and any(not r["passed"] for r in tier1_results):
        sys.exit(1)


if __name__ == "__main__":
    main()
