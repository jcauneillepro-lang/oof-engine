"""
engine_audit.py — self-audit pass that runs after every brief generation.

Two layers:
  1. lint_brief() — fast, deterministic, regex-based CRAFT rule checks
     (banned phrases, TBD markers, page-number consistency, etc.)
  2. critic_brief() — slow, semantic, Haiku LLM pass that reads the brief
     end-to-end and scores against CRAFT rules + the Mechanic.

Both produce structured issues. audit_brief() orchestrates and returns
a single scored report consumed by the engine's /api/generate endpoint
and surfaced in the preview UI.

The audit is meant to catch what bulk-generation misses:
  - Banned consulting-pitch phrases ("moves", "plays", "horizons")
  - [TBD] markers (good — surface to user)
  - Mixed chrome / page numbering
  - Duplicate slide titles
  - Empty slide bodies
  - Tone-register leaks
  - Missing closer / cover

Designed to add ~2-4s + ~$0.02 per brief. Default ON. Skip with audit=false.
"""
from __future__ import annotations
import json
import os
import re
from dataclasses import dataclass, asdict
from typing import Optional

from anthropic import Anthropic


# ============================================================
# CRAFT rule sets — kept here for lint speed
# ============================================================

BANNED_PHRASES = [
    # Consulting-pitch register (CRAFT Rule 6)
    "moves this quarter",
    "three moves",
    "the three moves",
    "the rest is evidence",
    "the plays",
    "the horizons",
    "the levers",
    "let's unpack",
    "low-hanging fruit",
    "double-click",
    "blue-sky",
    "boil the ocean",
    "circle back",
    "in the weeds",
    "north star",  # consulting cliché
]

INVENTION_REDFLAGS = [
    # Statements that suggest invented data
    r"\bapollo\b",  # Apollo cautionary tale
    r"\bmckinsey insights\b",  # often invented citation
    r"\bproprietary data\b",  # often fabricated framing
]


@dataclass
class AuditIssue:
    severity: str  # "block" | "warn" | "info"
    rule: str  # e.g. "CRAFT 6 · Tone register"
    location: str  # slide reference or generic
    message: str
    suggestion: str = ""

    def dict(self):
        return asdict(self)


# ============================================================
# LINT PASS · fast regex/heuristic checks
# ============================================================

def lint_brief(html: str, source: str = "") -> dict:
    """Run deterministic CRAFT checks on generated brief HTML.
    Returns dict with issues, counters, and lint-level grade."""
    issues: list[AuditIssue] = []

    # ----- Rule 6 · Tone register · banned phrases -----
    html_lower = html.lower()
    banned_hits = []
    for phrase in BANNED_PHRASES:
        n = html_lower.count(phrase.lower())
        if n > 0:
            banned_hits.append((phrase, n))
            issues.append(AuditIssue(
                severity="block",
                rule="CRAFT 6 · Tone register",
                location=f"{n}× in brief",
                message=f'Banned consulting-pitch phrase: "{phrase}"',
                suggestion="Rewrite to research/executive-memo register"
            ))

    # ----- Invention red-flags -----
    for pattern in INVENTION_REDFLAGS:
        matches = re.findall(pattern, html_lower)
        if matches:
            issues.append(AuditIssue(
                severity="block",
                rule="NO_INVENTION",
                location=f"{len(matches)}× in brief",
                message=f'Likely-invented term detected: "{matches[0]}"',
                suggestion="Verify the source contains this term verbatim; replace with [TBD] if not"
            ))

    # ----- Rule 7 · TBD markers (these are GOOD — surface to user) -----
    tbd_count = len(re.findall(r"\[\s*TBD\s*\]|\[\s*INSERT[^\]]*\]|\[\s*source[^\]]*\]",
                                html, flags=re.IGNORECASE))
    if tbd_count > 0:
        issues.append(AuditIssue(
            severity="info",
            rule="NO_INVENTION · honest placeholder",
            location=f"{tbd_count} placeholder(s)",
            message=f"Brief contains {tbd_count} `[TBD]` markers — honest about source gaps",
            suggestion="Provide the missing data and re-generate, or accept as final"
        ))

    # ----- Rule 3 · Page numbering consistency -----
    # Look for page numbers like "01 / 28" or "1 of 28" and check totals match
    page_patterns = re.findall(r"(\d{1,2})\s*/\s*(\d{1,3})", html)
    totals = {tot for _, tot in page_patterns}
    if len(totals) > 1:
        issues.append(AuditIssue(
            severity="block",
            rule="CRAFT 3 · Single visual grammar",
            location=f"{len(page_patterns)} page tokens",
            message=f"Mixed page-number totals found: {sorted(totals)}",
            suggestion="Sweep all page tokens to one consistent total"
        ))

    # ----- Slide count -----
    slide_count = html.count('<section class="slide"')
    if slide_count == 0:
        # try simpler match
        slide_count = html.count('class="slide')

    # ----- Rule 4 · Duplicate slide titles (h1) -----
    titles = re.findall(r"<h1[^>]*>(.*?)</h1>", html, flags=re.DOTALL)
    titles = [re.sub(r"<[^>]+>", "", t).strip() for t in titles]
    titles = [t for t in titles if t]
    duplicates = {}
    for t in titles:
        duplicates[t] = duplicates.get(t, 0) + 1
    repeated = {t: n for t, n in duplicates.items() if n > 1}
    if repeated:
        for title, n in repeated.items():
            issues.append(AuditIssue(
                severity="warn",
                rule="CRAFT 4 · Duplication audit",
                location=f"{n}× repeated",
                message=f'Slide title repeated: "{title[:60]}"',
                suggestion="Distinguish the slides or merge them"
            ))

    # ----- Rule 5 · Cover + closer presence -----
    has_cover = "cover" in html_lower or "kicker" in html_lower
    has_closer = "closer" in html_lower or "closing" in html_lower
    if not has_cover:
        issues.append(AuditIssue(
            severity="warn",
            rule="CRAFT · arc bookends",
            location="brief structure",
            message="No cover slide detected (cover/kicker class missing)",
            suggestion="Brief should open with a cover"
        ))
    if not has_closer:
        issues.append(AuditIssue(
            severity="warn",
            rule="CRAFT · arc bookends",
            location="brief structure",
            message="No closer slide detected",
            suggestion="Brief should close with a verdict / next-step slide"
        ))

    # ----- Rule 14 · Magenta vinyl mark check (it's out per JB) -----
    if "vinyl" in html_lower and "OOF" in html:
        issues.append(AuditIssue(
            severity="warn",
            rule="Design rules · wordmark only",
            location="brand mark",
            message="Vinyl OOF mark referenced — should use wordmark only",
            suggestion="Remove vinyl reference, use 'OOF.Engine' wordmark"
        ))

    # Compute lint-level severity counts
    block_count = sum(1 for i in issues if i.severity == "block")
    warn_count = sum(1 for i in issues if i.severity == "warn")
    info_count = sum(1 for i in issues if i.severity == "info")

    # Lint score (deterministic part): start at 10, deduct
    lint_score = 10.0
    lint_score -= 1.5 * block_count  # major
    lint_score -= 0.5 * warn_count   # minor
    lint_score = max(0.0, min(10.0, lint_score))

    return {
        "issues": [i.dict() for i in issues],
        "counts": {
            "block": block_count,
            "warn": warn_count,
            "info": info_count,
        },
        "stats": {
            "slide_count": slide_count,
            "title_count": len(titles),
            "tbd_markers": tbd_count,
            "page_tokens": len(page_patterns),
            "html_kb": round(len(html) / 1024, 1),
        },
        "lint_score": round(lint_score, 1),
    }


# ============================================================
# CRITIC PASS · Claude reads the brief and scores against CRAFT
# ============================================================

CRITIC_SYSTEM = """You are the OOF Engine's self-audit critic. You read a
generated brief and grade it against the CRAFT standard.

Score honestly. Inflation defeats the system. A brief that scores 7 is not
shippable per CRAFT Part 7. Only 8.5+ is shippable. Most first-pass briefs
should score 7-8; flag the specific gap that's holding it back.

Score on 6 dimensions, each 0-10:
- argument_clarity: can the reader state the argument after one read?
- design_impact: does the design carry the meaning, or compete with it?
- tone_of_voice: is the register consistent end-to-end? consulting-pitch leaks?
- data_integrity: every number traceable to the source? [TBD] markers honest?
- editorial_discipline: does every slide earn its place? duplication?
- production_craft: chrome, page numbers, spacing, alignment — tight?

Then identify up to 5 specific issues with severity (block/warn/info),
slide reference if possible, and suggested fix.

Return ONLY valid JSON. No commentary. Schema:
{
  "scores": {
    "argument_clarity": 8.5,
    "design_impact": 7.5,
    "tone_of_voice": 9.0,
    "data_integrity": 9.5,
    "editorial_discipline": 7.0,
    "production_craft": 8.0
  },
  "overall": 8.25,
  "shippable": false,
  "ship_blocker": "Editorial discipline 7.0 — two slides argue same point",
  "top_issues": [
    {
      "severity": "block|warn|info",
      "dimension": "editorial_discipline",
      "location": "slide 5 + slide 7",
      "message": "...",
      "suggestion": "..."
    }
  ],
  "what_works": ["...", "..."]
}"""


def critic_brief(html: str, source: str = "") -> dict:
    """Run a Claude Haiku critic pass on the brief HTML.
    Returns scored audit dict per the CRITIC_SYSTEM schema."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY not set; critic pass skipped"}

    client = Anthropic(api_key=api_key)

    # Trim HTML for cost — drop the inlined CSS, keep only the body markup
    body_only = html
    if "<body" in body_only:
        body_only = body_only.split("<body", 1)[1]
        body_only = body_only.split(">", 1)[1] if ">" in body_only else body_only
    if "</body>" in body_only:
        body_only = body_only.split("</body>", 1)[0]

    # Strip inline styles attributes to compress further
    body_only = re.sub(r'\sstyle="[^"]*"', '', body_only)
    # Strip class attribute values longer than 40 chars
    body_only = re.sub(r'class="([^"]{0,200})"', r'class="\1"', body_only)

    user_msg = (
        f"SOURCE CONTEXT (first 2000 chars):\n{source[:2000]}\n\n"
        f"---\n\nGENERATED BRIEF BODY:\n{body_only[:25000]}\n\n"
        f"---\n\nGrade this brief against CRAFT. Return JSON only."
    )

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            system=CRITIC_SYSTEM,
            messages=[{"role": "user", "content": user_msg}]
        )
        raw = response.content[0].text.strip()
        # Strip markdown fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {"error": f"critic returned invalid JSON: {e}", "raw": raw[:500]}
    except Exception as e:
        return {"error": f"critic call failed: {e}"}


# ============================================================
# ORCHESTRATOR
# ============================================================

def audit_brief(html: str, source: str = "", skip_critic: bool = False) -> dict:
    """Run lint + (optionally) critic, return combined audit report."""
    lint = lint_brief(html, source)

    if skip_critic:
        return {
            "lint": lint,
            "critic": None,
            "overall_score": lint["lint_score"],
            "shippable": lint["lint_score"] >= 8.5 and lint["counts"]["block"] == 0,
            "summary": _build_summary(lint, None),
        }

    critic = critic_brief(html, source)

    # Combined overall: average of lint_score and critic.overall, weighted 30/70
    if isinstance(critic, dict) and "overall" in critic:
        overall = round(0.3 * lint["lint_score"] + 0.7 * float(critic["overall"]), 1)
        shippable = (
            overall >= 8.5
            and lint["counts"]["block"] == 0
            and critic.get("shippable", False)
        )
    else:
        overall = lint["lint_score"]
        shippable = overall >= 8.5 and lint["counts"]["block"] == 0

    return {
        "lint": lint,
        "critic": critic,
        "overall_score": overall,
        "shippable": shippable,
        "summary": _build_summary(lint, critic),
    }


def _build_summary(lint: dict, critic: dict | None) -> str:
    """Build a short human-readable summary for the UI."""
    parts = []
    if lint["counts"]["block"]:
        parts.append(f"⚠ {lint['counts']['block']} block-level issue(s)")
    if lint["counts"]["warn"]:
        parts.append(f"{lint['counts']['warn']} warning(s)")
    if lint["stats"]["tbd_markers"]:
        parts.append(f"{lint['stats']['tbd_markers']} [TBD] marker(s) · honest about gaps")
    if critic and "overall" in critic:
        parts.append(f"Critic score: {critic['overall']}/10")
        if critic.get("ship_blocker"):
            parts.append(f"Blocker: {critic['ship_blocker']}")
    if not parts:
        parts.append("Clean lint + clean critic pass")
    return " · ".join(parts)
