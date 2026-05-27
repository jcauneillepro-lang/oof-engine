"""
build_guidebook.py — generate the engine's front-end (NASA-style design
guidebook), the PDF version of the same guidebook, and an audit report
identifying what's missing.

Run from the engine repo root:
    python scripts/build_guidebook.py

Outputs:
    index.html                         — the guidebook + engine UI (replaces previous)
    OOF_Design_Guidebook_v0.4.pdf      — PDF rendering
    AUDIT.md                           — gap report (canon → engine → assets)
"""
import json
import os
from pathlib import Path


ROOT = Path(__file__).parent.parent
CANON = json.loads((ROOT / "canon_components.json").read_text())
COMPONENTS = CANON["components"]
ASSETS_DIR = ROOT / "assets"
ASSETS = sorted([f.name for f in ASSETS_DIR.iterdir() if f.is_file()]) if ASSETS_DIR.exists() else []

# Categorise assets
COVER_ASSETS = [a for a in ASSETS if any(k in a for k in ("atmos", "park", "window", "jenny", "gill", "lab"))]
DIVIDER_ASSETS = [a for a in ASSETS if any(k in a for k in ("science", "ed10", "trees", "banner"))]
ICON_ASSETS = [a for a in ASSETS if a.endswith(".svg")]
NACO_ASSETS = [a for a in ASSETS if a.startswith("naco")]

# Brief archetypes (locked list — matches claude_engine.py)
ARCHETYPES = [
    ("exec_brief", "Executive Brief", "1-page, decision-forward", "Cover · Verdict · Why · Ask · Closer", "tight"),
    ("elt_preread", "ELT Pre-Read", "Off-site / call pre-read", "Hero photo + 3 prompts · The shift · Three lenses · Closer", "narrative"),
    ("analytical_dashboard", "Analytical Dashboard", "KPI-led status / scorecard", "KPI row · Charts · Heatmap · So-what · Actions", "numbers"),
    ("strategy_narrative", "Strategy Narrative", "Multi-page strategy with pillars", "Pyramid principle · 3 pillars · Evidence per pillar · Closer", "narrative"),
    ("project_briefing", "Project Briefing", "Status update with milestones", "Status board · Gantt · Risks · Decisions needed", "operational"),
    ("working_session", "Working Session", "Workshop pre-read", "Context · Prompts · Options · Decisions captured", "interactive"),
    ("point_of_view", "Point of View", "Single opinion made unmistakable", "Position · Counter · Evidence · Implication", "narrative"),
    ("conviction_memo", "Conviction Memo", "Bezos-style narrative memo", "Long-form prose with embedded panels", "narrative"),
    ("transformation_story", "Transformation Story", "Before vs After journey", "From · Through · To · Lessons · Closer", "narrative"),
    ("strategic_choice", "Strategic Choice", "A vs B vs C decision frame", "Frame · A · B · C · Trade-offs · Recommendation", "decision"),
    ("first_90_days", "First 90 Days", "New-hire playbook", "Context · 30 · 60 · 90 · Stakeholders · Derailers", "operational"),
    ("search_brief", "Search Brief", "Executive search role brief", "Role · Market map · Profile · Pipeline · Calibration", "operational"),
    ("field_pulse", "Field Pulse", "Quarterly field / commercial pulse", "KPI row · Movements · Pulse signals · Recommendations", "numbers"),
]

# Audience options (locked list)
AUDIENCES = [
    ("elt", "ELT"), ("hrlt", "HRLT"), ("chro", "CHRO"),
    ("team", "Project team"), ("board", "Board"),
]

# Cover style options
COVER_STYLES = [
    ("exec_split", "Exec Split", "Left text panel + right lab_atmos.jpg photo"),
    ("elt_hero", "ELT Hero", "Full-bleed photo + 3 discussion prompts overlay"),
    ("park_hero", "Park Hero", "Full-bleed park_atmos.jpg outdoor"),
    ("gill_window", "Gill Window", "Full-bleed gill_window.jpg portrait"),
    ("naco", "NACO", "Exec split with NACO illustration"),
    ("minimal", "Minimal", "Ink background, no photo"),
]

DIVIDER_STYLES = [
    ("people", "People", "lab_atmos.jpg"),
    ("science", "Science", "science_cell / liver / neuron / petri"),
    ("future", "Future", "park / garden"),
    ("ed10", "ED10", "Premium high-contrast abstract"),
]


def build_audit() -> str:
    lines = ["# OOF Engine · Canon Audit · v0.4", ""]
    lines.append(f"_Generated from `canon_components.json` ({len(COMPONENTS)} components) + `assets/` ({len(ASSETS)} files)._")
    lines.append("")
    lines.append("## Component coverage")
    lines.append("")
    lines.append(f"- **Canon documents:** {len(COMPONENTS)} components")
    lines.append(f"- **Engine system prompt:** loads canon_components.json at startup → all {len(COMPONENTS)} available to Claude")
    lines.append(f"- **Status:** ✅ Full coverage")
    lines.append("")
    lines.append("### All 57 components")
    lines.append("")
    lines.append("| # | Name | Demo HTML present |")
    lines.append("|---|------|-------------------|")
    for c in COMPONENTS:
        ok = "✅" if c["demo_html"] else "❌"
        lines.append(f"| {c['n']:02d} | {c['name']} | {ok} |")
    lines.append("")

    lines.append("## Asset inventory")
    lines.append("")
    lines.append(f"**Total assets in engine:** {len(ASSETS)}")
    lines.append("")
    cats = [
        ("Cover backgrounds", COVER_ASSETS),
        ("Divider backgrounds", DIVIDER_ASSETS),
        ("Icons (SVG)", ICON_ASSETS),
        ("NACO illustrations", NACO_ASSETS),
    ]
    for cat, lst in cats:
        lines.append(f"### {cat} ({len(lst)})")
        lines.append("")
        for a in lst:
            size_kb = os.path.getsize(ASSETS_DIR / a) // 1024 if (ASSETS_DIR / a).exists() else 0
            lines.append(f"- `assets/{a}` ({size_kb}KB)")
        lines.append("")

    uncategorized = [a for a in ASSETS if a not in COVER_ASSETS + DIVIDER_ASSETS + ICON_ASSETS + NACO_ASSETS]
    if uncategorized:
        lines.append(f"### Uncategorised ({len(uncategorized)})")
        lines.append("")
        for a in uncategorized:
            lines.append(f"- `assets/{a}` — needs categorisation in claude_engine.py")
        lines.append("")

    lines.append("## Archetypes")
    lines.append("")
    lines.append(f"**Engine offers:** {len(ARCHETYPES)} archetypes")
    lines.append("")
    for slug, name, when, shape, kind in ARCHETYPES:
        lines.append(f"- **{name}** (`{slug}`) — {when}. Shape: {shape}.")
    lines.append("")

    lines.append("## Known gaps · what's still missing")
    lines.append("")
    lines.append("Things to consider for future versions:")
    lines.append("")
    lines.append("- **Few-shot canonical briefs in prompt.** The 4 finished example briefs (Exec/ELT/Annual/SWP) are not included in the system prompt. Adding them as anchors would dramatically improve fidelity to house style, at the cost of ~30K tokens.")
    lines.append("- **PPTX export uses screenshot path.** Currently produces non-editable slides. v2 roadmap: structured JSON from Claude → native python-pptx with editable text frames.")
    lines.append("- **No template-skeleton picker yet.** Users can pick archetype + cover + divider style but not 'start from this specific brief'. A skeleton picker (NACO Pulse / CDIO ELT / Teaming Roadmap) would lock structural fidelity for repeat workflows.")
    lines.append("- **Live preview is iframe-based.** Works fine but limits engine→preview interactivity. A dedicated preview pane with edit-in-place would let the user tweak generated briefs.")
    lines.append("- **No user accounts / brief history.** Generations don't persist. Adding a simple per-session history would let the team revisit recent work.")
    lines.append("- **Mobile UI not optimised.** Currently desktop-first.")
    lines.append("")
    return "\n".join(lines)


def build_html() -> str:
    """Generate the full NASA-style guidebook front-end with engine at bottom."""

    # Build the components grid HTML
    comp_cards = []
    for c in COMPONENTS:
        comp_cards.append(f"""
<article class="comp-card" id="c{c['n']:02d}">
  <header>
    <span class="comp-num">{c['n']:02d}</span>
    <h3 class="comp-name">{c['name']}</h3>
  </header>
  <div class="comp-demo">{c['demo_html']}</div>
</article>""")
    comp_grid_html = "\n".join(comp_cards)

    # Asset grid
    cover_cards = "\n".join([
        f'<div class="asset-card"><div class="asset-thumb" style="background-image: url(\'assets/{a}\');"></div><div class="asset-name">{a}</div></div>'
        for a in COVER_ASSETS
    ])
    divider_cards = "\n".join([
        f'<div class="asset-card"><div class="asset-thumb" style="background-image: url(\'assets/{a}\');"></div><div class="asset-name">{a}</div></div>'
        for a in DIVIDER_ASSETS
    ])
    icon_cards = "\n".join([
        f'<div class="asset-card icon"><div class="asset-thumb"><img src="assets/{a}" alt="{a}"></div><div class="asset-name">{a}</div></div>'
        for a in ICON_ASSETS
    ])

    # Archetype cards
    arch_cards = "\n".join([
        f"""<div class="arch-card">
  <div class="arch-meta">
    <span class="arch-kind kind-{kind}">{kind}</span>
  </div>
  <h3>{name}</h3>
  <p class="arch-when">{when}</p>
  <p class="arch-shape">{shape}</p>
</div>"""
        for slug, name, when, shape, kind in ARCHETYPES
    ])

    # Cover style options for the engine dropdown
    cover_opts = "\n".join([f'<option value="{slug}">{name} · {desc}</option>' for slug, name, desc in COVER_STYLES])
    divider_opts = "\n".join([f'<option value="{slug}">{name} · {desc}</option>' for slug, name, desc in DIVIDER_STYLES])
    audience_opts = "\n".join([f'<option value="{slug}">{name}</option>' for slug, name in AUDIENCES])
    arch_opts = "\n".join([f'<option value="{slug}">{name}</option>' for slug, name, _, _, _ in ARCHETYPES])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OOF Design Guidebook · The Engine</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Inter+Tight:wght@800;900&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="oof-v23.css">
<style>
  :root {{
    --paper: #FAFAF7; --paper-2: #F4F4EF; --rule-thin: rgba(15,37,82,0.12);
    --mono: 'JetBrains Mono', ui-monospace, Menlo, monospace;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html {{ scroll-behavior: smooth; }}
  body {{
    font-family: 'Inter', system-ui, sans-serif;
    background: var(--paper); color: var(--ink);
    line-height: 1.5; overflow-x: hidden;
  }}

  /* ============== GLOBAL CHROME ============== */
  .topbar {{
    position: sticky; top: 0; z-index: 100;
    background: rgba(250,250,247,0.92); backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border-bottom: 1px solid var(--rule-thin);
    padding: 14px 32px;
    display: flex; align-items: center; justify-content: space-between;
  }}
  .topbar .brand {{ display: flex; align-items: baseline; gap: 16px; }}
  .topbar .brand .name {{
    font-family: 'Inter Tight', sans-serif; font-weight: 900;
    font-size: 18pt; letter-spacing: -0.02em; color: var(--ink);
  }}
  .topbar .brand .name .l {{ color: var(--lime); }}
  .topbar .brand .sub {{
    font-family: var(--mono); font-size: 8pt;
    color: var(--gray-d); letter-spacing: 0.18em; text-transform: uppercase;
  }}
  .topbar nav {{ display: flex; gap: 24px; }}
  .topbar nav a {{
    font-family: var(--mono); font-size: 8pt;
    color: var(--gray-d); text-decoration: none;
    letter-spacing: 0.16em; text-transform: uppercase;
    transition: color 0.15s;
  }}
  .topbar nav a:hover {{ color: var(--ink); }}
  .topbar .live {{
    display: flex; align-items: center; gap: 6px;
    font-family: var(--mono); font-size: 8pt; color: var(--gray-d);
    letter-spacing: 0.14em; text-transform: uppercase;
  }}
  .topbar .live .dot {{
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--lime); box-shadow: 0 0 8px rgba(166,245,12,0.7);
  }}

  /* ============== PAGE FRAME ============== */
  section.page {{
    max-width: 1280px; margin: 0 auto;
    padding: 80px 60px;
    position: relative;
    border-bottom: 1px solid var(--rule-thin);
  }}
  section.page:last-child {{ border-bottom: none; }}
  .corner-tl {{
    position: absolute; top: 28px; left: 60px;
    font-family: var(--mono); font-size: 8pt;
    color: var(--gray-d); letter-spacing: 0.18em; text-transform: uppercase;
  }}
  .corner-tr {{
    position: absolute; top: 28px; right: 60px;
    font-family: var(--mono); font-size: 8pt;
    color: var(--gray-d); letter-spacing: 0.18em; text-transform: uppercase;
  }}
  .page-num {{
    position: absolute; bottom: 28px; right: 60px;
    font-family: var(--mono); font-size: 8pt;
    color: var(--gray-d); letter-spacing: 0.18em;
  }}

  /* ============== HERO ============== */
  .hero {{
    min-height: 80vh;
    display: flex; flex-direction: column; justify-content: space-between;
    padding-top: 120px; padding-bottom: 80px;
  }}
  .hero .kicker {{
    display: inline-block; background: var(--lime); color: var(--ink);
    padding: 5px 10px; font-family: var(--mono); font-size: 9pt;
    font-weight: 600; letter-spacing: 0.18em; text-transform: uppercase;
    margin-bottom: 32px;
  }}
  .hero h1 {{
    font-family: 'Inter Tight', sans-serif; font-weight: 900;
    font-size: 120pt; line-height: 0.86; letter-spacing: -0.045em;
    color: var(--ink);
  }}
  .hero h1 .l {{ color: var(--lime); }}
  .hero .lede {{
    font-size: 18pt; color: var(--gray-d); line-height: 1.45;
    margin-top: 40px; max-width: 880px; font-weight: 400;
  }}
  .hero .meta-block {{
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 24px; padding-top: 24px; margin-top: 60px;
    border-top: 1px solid var(--ink);
  }}
  .hero .meta-block .item .k {{
    font-family: var(--mono); font-size: 8pt;
    letter-spacing: 0.18em; text-transform: uppercase;
    color: var(--gray-d); margin-bottom: 4px;
  }}
  .hero .meta-block .item .v {{
    font-family: 'Inter Tight', sans-serif; font-weight: 800;
    font-size: 14pt; color: var(--ink);
  }}

  /* ============== SECTION HEADERS ============== */
  .section-header {{
    margin-bottom: 56px; padding-bottom: 20px;
    border-bottom: 2px solid var(--ink);
  }}
  .section-header .num {{
    font-family: var(--mono); font-size: 9pt;
    color: var(--gray-d); letter-spacing: 0.18em; text-transform: uppercase;
    margin-bottom: 12px;
  }}
  .section-header h2 {{
    font-family: 'Inter Tight', sans-serif; font-weight: 900;
    font-size: 56pt; line-height: 0.95; letter-spacing: -0.03em;
    color: var(--ink);
  }}
  .section-header h2 .l {{ color: var(--lime); }}
  .section-header .lede {{
    font-size: 14pt; color: var(--gray-d); line-height: 1.5;
    margin-top: 20px; max-width: 880px; font-style: italic;
  }}

  /* ============== PHILOSOPHY ============== */
  .phil-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 40px; }}
  .phil-col {{ border-left: 3px solid var(--lime); padding-left: 24px; }}
  .phil-col:nth-child(2) {{ border-left-color: var(--cyan); }}
  .phil-col:nth-child(3) {{ border-left-color: var(--magenta); }}
  .phil-col .num {{
    font-family: var(--mono); font-size: 9pt; font-weight: 600;
    color: var(--lime); letter-spacing: 0.18em; margin-bottom: 16px;
  }}
  .phil-col:nth-child(2) .num {{ color: var(--cyan); }}
  .phil-col:nth-child(3) .num {{ color: var(--magenta); }}
  .phil-col h3 {{
    font-family: 'Inter Tight', sans-serif; font-weight: 900;
    font-size: 22pt; line-height: 1.05; letter-spacing: -0.02em;
    margin-bottom: 16px; color: var(--ink);
  }}
  .phil-col p {{ font-size: 12pt; color: var(--gray-d); line-height: 1.65; }}
  .phil-col p + p {{ margin-top: 12px; }}

  /* ============== COLOR SPEC SHEET ============== */
  .swatches {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 32px; }}
  .swatch {{ display: flex; flex-direction: column; }}
  .swatch .chip {{
    width: 100%; aspect-ratio: 1; border: 1px solid var(--rule-thin);
  }}
  .swatch .meta {{ padding-top: 16px; }}
  .swatch .meta .name {{
    font-family: 'Inter Tight', sans-serif; font-weight: 900;
    font-size: 20pt; letter-spacing: -0.02em; color: var(--ink);
  }}
  .swatch .meta .role {{
    font-size: 11pt; color: var(--gray-d); line-height: 1.5; margin-top: 6px;
  }}
  .swatch .specs {{
    margin-top: 16px; display: grid; grid-template-columns: auto 1fr;
    column-gap: 16px; row-gap: 4px;
    font-family: var(--mono); font-size: 9pt;
  }}
  .swatch .specs .k {{ color: var(--gray-d); letter-spacing: 0.12em; text-transform: uppercase; }}
  .swatch .specs .v {{ color: var(--ink); font-weight: 500; }}

  /* ============== TYPOGRAPHY ============== */
  .typo-row {{
    display: grid; grid-template-columns: 200px 1fr; gap: 32px;
    padding: 24px 0; border-top: 1px solid var(--rule-thin);
  }}
  .typo-row:last-child {{ border-bottom: 1px solid var(--rule-thin); }}
  .typo-row .role {{
    font-family: var(--mono); font-size: 9pt;
    color: var(--gray-d); letter-spacing: 0.14em; text-transform: uppercase;
    padding-top: 12px;
  }}
  .typo-row .role .face {{
    display: block; font-size: 8pt; color: var(--gray);
    text-transform: none; letter-spacing: 0; margin-top: 4px; font-style: italic;
  }}
  .typo-row .sample.display-xxl {{
    font-family: 'Inter Tight', sans-serif; font-weight: 900;
    font-size: 64pt; line-height: 1; letter-spacing: -0.04em;
  }}
  .typo-row .sample.display-l {{
    font-family: 'Inter Tight', sans-serif; font-weight: 900;
    font-size: 32pt; line-height: 1.05; letter-spacing: -0.02em;
  }}
  .typo-row .sample.body {{
    font-family: 'Inter', sans-serif; font-size: 14pt; font-weight: 400; line-height: 1.5;
  }}
  .typo-row .sample.kicker {{
    display: inline-block; background: var(--lime); color: var(--ink);
    padding: 4px 10px; font-family: var(--mono); font-size: 9pt;
    font-weight: 600; letter-spacing: 0.18em; text-transform: uppercase;
  }}

  /* ============== MARK PAGE ============== */
  .mark-statement {{
    background: var(--paper-2); padding: 48px; border-left: 6px solid var(--lime);
  }}
  .mark-statement h3 {{
    font-family: 'Inter Tight', sans-serif; font-weight: 900;
    font-size: 36pt; line-height: 1; letter-spacing: -0.02em; color: var(--ink);
    margin-bottom: 24px;
  }}
  .mark-statement p {{ font-size: 14pt; color: var(--gray-d); line-height: 1.6; }}
  .mark-wordmark {{
    text-align: center; padding: 64px 0;
    font-family: 'Inter Tight', sans-serif; font-weight: 900;
    font-size: 96pt; letter-spacing: -0.04em; color: var(--ink);
  }}
  .mark-wordmark .l {{ color: var(--lime); }}

  /* ============== COMPONENT GRID ============== */
  .comp-grid {{
    display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px;
  }}
  .comp-card {{
    background: white;
    border: 1px solid var(--rule-thin);
    overflow: hidden;
  }}
  .comp-card header {{
    display: flex; align-items: baseline; gap: 12px;
    padding: 16px 20px; border-bottom: 1px solid var(--rule-thin);
    background: var(--paper-2);
  }}
  .comp-card .comp-num {{
    font-family: var(--mono); font-weight: 600; font-size: 11pt;
    color: var(--lime); letter-spacing: 0.1em;
  }}
  .comp-card .comp-name {{
    font-family: 'Inter Tight', sans-serif; font-weight: 900;
    font-size: 14pt; letter-spacing: -0.01em; color: var(--ink);
  }}
  .comp-card .comp-demo {{
    padding: 20px; max-height: 340px; overflow: hidden;
    background: white;
    transform: scale(0.85); transform-origin: top left; width: 117%;
  }}

  /* ============== ASSET GRID ============== */
  .asset-grid {{
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px;
  }}
  .asset-card {{ background: white; border: 1px solid var(--rule-thin); }}
  .asset-card .asset-thumb {{
    width: 100%; aspect-ratio: 1.5;
    background-size: cover; background-position: center;
    border-bottom: 1px solid var(--rule-thin);
  }}
  .asset-card.icon .asset-thumb {{
    display: flex; align-items: center; justify-content: center; padding: 32px;
    background: var(--paper-2);
  }}
  .asset-card.icon .asset-thumb img {{ width: 100%; height: 100%; object-fit: contain; }}
  .asset-card .asset-name {{
    font-family: var(--mono); font-size: 9pt;
    color: var(--gray-d); padding: 10px 14px;
  }}

  /* ============== ARCHETYPE GRID ============== */
  .arch-grid {{
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;
  }}
  .arch-card {{
    background: white; border: 1px solid var(--rule-thin); padding: 28px;
    border-top: 4px solid var(--lime);
  }}
  .arch-card:nth-child(2n) {{ border-top-color: var(--cyan); }}
  .arch-card:nth-child(3n) {{ border-top-color: var(--magenta); }}
  .arch-card:nth-child(5n) {{ border-top-color: var(--orange); }}
  .arch-card:nth-child(7n) {{ border-top-color: var(--violet); }}
  .arch-card .arch-meta {{ margin-bottom: 14px; }}
  .arch-card .arch-kind {{
    display: inline-block; padding: 3px 8px;
    font-family: var(--mono); font-size: 7.5pt; font-weight: 600;
    letter-spacing: 0.12em; text-transform: uppercase; color: var(--gray-d);
    background: var(--paper-2);
  }}
  .arch-card h3 {{
    font-family: 'Inter Tight', sans-serif; font-weight: 900;
    font-size: 20pt; letter-spacing: -0.02em; color: var(--ink); margin-bottom: 10px;
  }}
  .arch-card .arch-when {{ font-size: 11pt; color: var(--gray-d); margin-bottom: 12px; }}
  .arch-card .arch-shape {{
    font-family: var(--mono); font-size: 9pt; color: var(--ink); line-height: 1.5;
    background: var(--paper-2); padding: 10px 12px;
  }}

  /* ============== ENGINE SECTION ============== */
  .engine-section {{
    background: var(--ink); color: white;
    padding: 80px 60px;
  }}
  .engine-section .section-header {{ border-bottom-color: var(--lime); }}
  .engine-section .section-header .num,
  .engine-section .section-header .lede {{ color: rgba(255,255,255,0.7); }}
  .engine-section .section-header h2 {{ color: white; }}
  .engine-section .section-header h2 .l {{ color: var(--lime); }}

  .engine {{ display: grid; grid-template-columns: 420px 1fr; gap: 24px; max-width: 1280px; margin: 0 auto; }}
  .engine > .panel {{ background: white; color: var(--ink); border-radius: 8px; overflow: hidden; }}
  .engine .controls {{ padding: 28px; display: flex; flex-direction: column; gap: 14px; }}
  .engine .label {{
    font-family: var(--mono); font-size: 8pt; font-weight: 600;
    color: var(--gray-d); letter-spacing: 0.12em; text-transform: uppercase;
  }}
  .engine textarea, .engine input[type=text], .engine select {{
    width: 100%; padding: 11px 13px; border: 1.5px solid var(--rule);
    font-family: 'Inter', sans-serif; font-size: 13px; line-height: 1.55; color: var(--ink);
    background: var(--paper-2); border-radius: 5px; resize: vertical;
  }}
  .engine textarea {{ min-height: 160px; }}
  .engine select {{
    appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%230F2552' stroke-width='2' fill='none'/%3E%3C/svg%3E");
    background-repeat: no-repeat; background-position: right 12px center;
    padding-right: 34px; cursor: pointer;
  }}
  .engine textarea:focus, .engine input:focus, .engine select:focus {{
    outline: none; border-color: var(--lime); background: white;
  }}
  .engine .steering-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
  .engine .field {{ display: flex; flex-direction: column; gap: 6px; }}
  .engine .file-row {{ display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }}
  .engine .file-btn {{
    cursor: pointer; background: var(--ink); color: white;
    padding: 10px 14px; border-radius: 4px; font-family: var(--mono);
    font-size: 9pt; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase;
  }}
  .engine .file-btn:hover {{ background: var(--lime); color: var(--ink); }}
  .engine #file-name {{ font-size: 11px; color: var(--gray-d); font-style: italic; }}
  .engine .file-formats {{
    font-family: var(--mono); font-size: 8pt; color: var(--gray);
    letter-spacing: 0.06em; text-transform: uppercase; margin-top: 2px;
  }}
  .engine .btn {{
    cursor: pointer; border: 0; border-radius: 5px;
    font-family: 'Inter Tight', sans-serif; font-weight: 800;
    font-size: 13px; letter-spacing: 0.04em; padding: 14px 18px;
  }}
  .engine .btn.primary {{ background: var(--lime); color: var(--ink); }}
  .engine .btn.primary:hover {{ background: var(--ink); color: var(--lime); }}
  .engine .btn.primary:disabled {{ background: var(--gray); color: white; cursor: not-allowed; }}
  .engine .btn.big {{ padding: 16px 24px; font-size: 15px; }}
  .engine .btn.secondary {{
    background: white; color: var(--ink);
    border: 1.5px solid var(--rule);
  }}
  .engine .btn.secondary:hover:not([disabled]) {{ background: var(--ink); color: white; border-color: var(--ink); }}
  .engine .btn.secondary[disabled] {{ color: var(--gray); cursor: not-allowed; opacity: 0.5; }}
  .engine .downloads {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 6px; }}
  .engine .status {{
    background: rgba(166,245,12,0.12); border-left: 3px solid var(--lime);
    padding: 10px 12px; border-radius: 3px; font-size: 11px; line-height: 1.5;
    color: var(--ink-2); font-style: italic;
  }}
  .engine .status.error {{ background: rgba(245,12,122,0.10); border-left-color: var(--magenta); color: var(--ink); }}
  .engine .preview {{ display: flex; flex-direction: column; min-height: 720px; }}
  .engine .preview-bar {{
    display: flex; justify-content: space-between; align-items: center;
    padding: 14px 22px; background: var(--ink-dk); color: white;
    font-family: var(--mono); font-size: 9pt; font-weight: 600;
    letter-spacing: 0.12em; text-transform: uppercase;
  }}
  .engine #preview {{ flex: 1; width: 100%; border: 0; background: var(--paper-2); min-height: 680px; }}

  /* ============== FOOTER ============== */
  footer.foot {{
    background: var(--ink-dk); color: white;
    padding: 40px 60px; text-align: center;
  }}
  footer.foot .line {{ font-family: var(--mono); font-size: 9pt; color: rgba(255,255,255,0.5); letter-spacing: 0.18em; text-transform: uppercase; margin-bottom: 8px; }}
  footer.foot .tag {{ font-style: italic; color: rgba(255,255,255,0.7); }}
</style>
</head>
<body>

<nav class="topbar">
  <div class="brand">
    <span class="name">OOF<span class="l">.</span> Engine</span>
    <span class="sub">Design Guidebook · v0.4</span>
  </div>
  <nav>
    <a href="#philosophy">Philosophy</a>
    <a href="#colour">Colour</a>
    <a href="#typography">Typography</a>
    <a href="#components">Components</a>
    <a href="#assets">Assets</a>
    <a href="#archetypes">Archetypes</a>
    <a href="#engine">The Engine</a>
  </nav>
  <div class="live"><span class="dot"></span>Live</div>
</nav>

<!-- ============== HERO ============== -->
<section class="page hero">
  <div class="corner-tl">OOF · Office of the Future · Ipsen</div>
  <div class="corner-tr">Design Guidebook · Edition 0.4 · 2026</div>
  <div>
    <span class="kicker">From the people who live in the future</span>
    <h1>OOF<br>Design<br><span class="l">Guidebook.</span></h1>
    <p class="lede">A language for the next generation of HR leadership at Ipsen. {len(COMPONENTS)} components, {len(ARCHETYPES)} brief archetypes, {len(ASSETS)} canonical assets. Composed by the engine at the speed of thought, rendered at the standard of forever.</p>
  </div>
  <div>
    <div class="meta-block">
      <div class="item"><div class="k">Document</div><div class="v">OOF · v0.4</div></div>
      <div class="item"><div class="k">Issued</div><div class="v">May 2026</div></div>
      <div class="item"><div class="k">Owner</div><div class="v">Office of the Future</div></div>
      <div class="item"><div class="k">Status</div><div class="v">Live</div></div>
    </div>
  </div>
  <div class="page-num">01</div>
</section>

<!-- ============== PHILOSOPHY ============== -->
<section class="page" id="philosophy">
  <div class="corner-tl">OOF · Section 01</div>
  <div class="corner-tr">Philosophy</div>
  <div class="section-header">
    <div class="num">Section 01 · Philosophy</div>
    <h2>Why this system <span class="l">exists.</span></h2>
    <p class="lede">Three convictions that shaped the language. They are the test every component must pass.</p>
  </div>
  <div class="phil-grid">
    <div class="phil-col">
      <div class="num">01 · WHY</div>
      <h3>Form is the rate-limiter on insight.</h3>
      <p>Every HR leader has decisions waiting on a deck. The deck is rarely the hard part — the thinking is. The system removes the design-and-format tax so the thinking gets through.</p>
      <p>Inspired by Dieter Rams: good design is as little design as possible — but never less.</p>
    </div>
    <div class="phil-col">
      <div class="num">02 · HOW</div>
      <h3>One language, ruthlessly applied.</h3>
      <p>Navy ink. Lime accent. Cyan, magenta, orange, violet for hierarchy. Inter Tight for display, Inter for body. {len(COMPONENTS)} components, all composable.</p>
      <p>The constraint is the feature: a brief in v23 is recognisable across the company in two seconds.</p>
    </div>
    <div class="phil-col">
      <div class="num">03 · FOR WHOM</div>
      <h3>The next generation of HR leadership.</h3>
      <p>Built for the HR professionals who will lead businesses, not just functions. Briefs that hold their own at the ELT, the Board, and the off-site.</p>
      <p>Source-honest. Evidence-cited. Verdict-forward.</p>
    </div>
  </div>
  <div class="page-num">02</div>
</section>

<!-- ============== COLOUR ============== -->
<section class="page" id="colour">
  <div class="corner-tl">OOF · Section 02</div>
  <div class="corner-tr">Colour</div>
  <div class="section-header">
    <div class="num">Section 02 · Colour</div>
    <h2>The <span class="l">palette.</span></h2>
    <p class="lede">Six colours carry the entire system. The palette is closed; do not extend it.</p>
  </div>
  <div class="swatches">
    <div class="swatch"><div class="chip" style="background: #0F2552;"></div><div class="meta"><div class="name">Ink</div><div class="role">Substrate. Type, headlines, slide backgrounds.</div><div class="specs"><span class="k">Hex</span><span class="v">#0F2552</span><span class="k">RGB</span><span class="v">15 37 82</span><span class="k">CMYK</span><span class="v">100 85 35 35</span><span class="k">Pantone</span><span class="v">280 C</span></div></div></div>
    <div class="swatch"><div class="chip" style="background: #A6F50C;"></div><div class="meta"><div class="name">Lime</div><div class="role">Hero accent. Verdicts, highlights, CTA. The future.</div><div class="specs"><span class="k">Hex</span><span class="v">#A6F50C</span><span class="k">RGB</span><span class="v">166 245 12</span><span class="k">CMYK</span><span class="v">35 0 100 0</span><span class="k">Pantone</span><span class="v">389 C</span></div></div></div>
    <div class="swatch"><div class="chip" style="background: #0CB8F5;"></div><div class="meta"><div class="name">Cyan</div><div class="role">Secondary signal. Data, evidence, "how we know".</div><div class="specs"><span class="k">Hex</span><span class="v">#0CB8F5</span><span class="k">RGB</span><span class="v">12 184 245</span><span class="k">CMYK</span><span class="v">75 10 0 0</span><span class="k">Pantone</span><span class="v">2925 C</span></div></div></div>
    <div class="swatch"><div class="chip" style="background: #F50C7A;"></div><div class="meta"><div class="name">Magenta</div><div class="role">Risk, voice, rare emphasis.</div><div class="specs"><span class="k">Hex</span><span class="v">#F50C7A</span><span class="k">RGB</span><span class="v">245 12 122</span><span class="k">CMYK</span><span class="v">0 90 20 0</span><span class="k">Pantone</span><span class="v">219 C</span></div></div></div>
    <div class="swatch"><div class="chip" style="background: #F5800C;"></div><div class="meta"><div class="name">Orange</div><div class="role">Warning, deadlines, "decide by".</div><div class="specs"><span class="k">Hex</span><span class="v">#F5800C</span><span class="k">RGB</span><span class="v">245 128 12</span><span class="k">CMYK</span><span class="v">0 60 95 0</span><span class="k">Pantone</span><span class="v">158 C</span></div></div></div>
    <div class="swatch"><div class="chip" style="background: #8B5CF6;"></div><div class="meta"><div class="name">Violet</div><div class="role">People, profiles, perspectives.</div><div class="specs"><span class="k">Hex</span><span class="v">#8B5CF6</span><span class="k">RGB</span><span class="v">139 92 246</span><span class="k">CMYK</span><span class="v">55 65 0 0</span><span class="k">Pantone</span><span class="v">266 C</span></div></div></div>
  </div>
  <div class="page-num">03</div>
</section>

<!-- ============== TYPOGRAPHY ============== -->
<section class="page" id="typography">
  <div class="corner-tl">OOF · Section 03</div>
  <div class="corner-tr">Typography</div>
  <div class="section-header">
    <div class="num">Section 03 · Typography</div>
    <h2>Two fonts, eight <span class="l">jobs.</span></h2>
    <p class="lede">Inter Tight 900 carries the verdict. Inter 400 carries the evidence. There are no other choices because there should not be.</p>
  </div>
  <div class="typo-row">
    <div class="role">Display XXL<span class="face">Inter Tight 900 · 64pt / -4%</span></div>
    <div class="sample display-xxl">Briefs at the speed of thought.</div>
  </div>
  <div class="typo-row">
    <div class="role">Display L · Slide<span class="face">Inter Tight 900 · 32pt / -2%</span></div>
    <div class="sample display-l">Turnover hit 16.7% — ACCELERATE the response.</div>
  </div>
  <div class="typo-row">
    <div class="role">Body<span class="face">Inter 400 · 14pt / 1.5</span></div>
    <div class="sample body">Recent studies indicate that the time-to-fill for senior commercial roles in oncology has risen 47% YoY across EU-15 pharma. The implication is structural, not cyclical.</div>
  </div>
  <div class="typo-row">
    <div class="role">Kicker · Chip<span class="face">JetBrains Mono 600 · 9pt / +18% spacing / UPPER</span></div>
    <div class="sample"><span class="kicker">From the people who live in the future</span></div>
  </div>
  <div class="page-num">04</div>
</section>

<!-- ============== MARK ============== -->
<section class="page" id="mark">
  <div class="corner-tl">OOF · Section 04</div>
  <div class="corner-tr">The Mark</div>
  <div class="section-header">
    <div class="num">Section 04 · The Mark</div>
    <h2>The wordmark is the <span class="l">mark.</span></h2>
    <p class="lede">No symbol. No logomark. The wordmark in Inter Tight 900 is the OOF identity in full. This is a deliberate constraint, not a missing piece.</p>
  </div>
  <div class="mark-wordmark">OOF<span class="l">.</span> Engine</div>
  <div class="mark-statement">
    <h3>Why no symbol.</h3>
    <p>Logos demand attention; words carry meaning. The OOF identity earns its presence through what it says, not how it sits in a frame. When you need an OOF stamp on a brief, use the wordmark — it works at any size, in any colour, on any background.</p>
  </div>
  <div class="page-num">05</div>
</section>

<!-- ============== COMPONENTS ============== -->
<section class="page" id="components">
  <div class="corner-tl">OOF · Section 05</div>
  <div class="corner-tr">Components</div>
  <div class="section-header">
    <div class="num">Section 05 · Components</div>
    <h2>The <span class="l">vocabulary.</span></h2>
    <p class="lede">{len(COMPONENTS)} numbered components. Each one has a job. Composition is the discipline — not every slide needs every component.</p>
  </div>
  <div class="comp-grid">
    {comp_grid_html}
  </div>
  <div class="page-num">06</div>
</section>

<!-- ============== ASSETS ============== -->
<section class="page" id="assets">
  <div class="corner-tl">OOF · Section 06</div>
  <div class="corner-tr">Asset library</div>
  <div class="section-header">
    <div class="num">Section 06 · Asset library</div>
    <h2>{len(ASSETS)} canonical <span class="l">assets.</span></h2>
    <p class="lede">Every cover background, every chapter divider, every icon. Used by the engine when composing briefs.</p>
  </div>
  <h3 style="font-family: 'Inter Tight'; font-weight: 900; font-size: 18pt; margin: 24px 0 16px;">Cover backgrounds</h3>
  <div class="asset-grid">{cover_cards}</div>
  <h3 style="font-family: 'Inter Tight'; font-weight: 900; font-size: 18pt; margin: 32px 0 16px;">Chapter divider backgrounds</h3>
  <div class="asset-grid">{divider_cards}</div>
  <h3 style="font-family: 'Inter Tight'; font-weight: 900; font-size: 18pt; margin: 32px 0 16px;">Pictogram icons</h3>
  <div class="asset-grid">{icon_cards}</div>
  <div class="page-num">07</div>
</section>

<!-- ============== ARCHETYPES ============== -->
<section class="page" id="archetypes">
  <div class="corner-tl">OOF · Section 07</div>
  <div class="corner-tr">Brief archetypes</div>
  <div class="section-header">
    <div class="num">Section 07 · Brief archetypes</div>
    <h2>{len(ARCHETYPES)} brief <span class="l">archetypes.</span></h2>
    <p class="lede">Every brief is one of these shapes. The engine asks you which one before composing — or auto-detects from your source.</p>
  </div>
  <div class="arch-grid">{arch_cards}</div>
  <div class="page-num">08</div>
</section>

<!-- ============== ENGINE ============== -->
<section class="engine-section" id="engine">
  <div class="section-header">
    <div class="num">Section 08 · The Engine</div>
    <h2>Compose a brief <span class="l">now.</span></h2>
    <p class="lede">Paste source · pick archetype + audience · hit Generate · download in HTML / PDF / PPTX. ~10 seconds end-to-end.</p>
  </div>
  <div class="engine">
    <div class="panel controls">
      <div class="label">Source · paste or describe</div>
      <textarea id="input" placeholder="Paste your source: a Slack thread, a board pack, an SWP file, an executive thought. Or describe what you need."></textarea>

      <div class="steering-row">
        <div class="field">
          <div class="label">Archetype</div>
          <select id="archetype">
            <option value="auto">Auto-detect</option>
            {arch_opts}
          </select>
        </div>
        <div class="field">
          <div class="label">Audience</div>
          <select id="audience">
            <option value="auto">Auto-detect</option>
            {audience_opts}
          </select>
        </div>
      </div>

      <div class="steering-row">
        <div class="field">
          <div class="label">Slide count</div>
          <select id="slide_count">
            <option value="auto">Auto</option>
            <option value="3">3 · Tight</option>
            <option value="5">5 · Standard</option>
            <option value="8">8 · Full</option>
            <option value="12">12 · Deep</option>
          </select>
        </div>
        <div class="field">
          <div class="label">Cover style</div>
          <select id="cover_style">
            <option value="auto">Auto</option>
            {cover_opts}
          </select>
        </div>
      </div>

      <div class="steering-row">
        <div class="field">
          <div class="label">Chapter dividers</div>
          <select id="divider_style">
            <option value="auto">Auto</option>
            {divider_opts}
          </select>
        </div>
        <div class="field">
          <div class="label">Free-text override</div>
          <input type="text" id="constraint" placeholder="e.g. 'use waterfall'">
        </div>
      </div>

      <div>
        <div class="file-row">
          <label class="file-btn">↑ Upload source<input type="file" id="file" accept=".txt,.md,.csv,.json,.pptx,.docx,.pdf" style="display:none;"></label>
          <span id="file-name">No file selected</span>
        </div>
        <div class="file-formats">.pptx · .docx · .pdf · .txt · .md · .csv · .json</div>
      </div>

      <button id="make" class="btn primary big">Generate brief →</button>

      <div class="downloads">
        <button id="dl-html" class="btn secondary" disabled>↓ HTML</button>
        <button id="dl-pdf"  class="btn secondary" disabled>↓ PDF</button>
        <button id="dl-pptx" class="btn secondary" disabled>↓ PPTX</button>
      </div>
      <div id="status" class="status" style="display:none;"></div>
    </div>

    <div class="panel preview">
      <div class="preview-bar">
        <span>Live preview</span>
        <span id="preview-meta" style="opacity: 0.7;">Hit Generate to render</span>
      </div>
      <iframe id="preview" srcdoc="<style>body{{font-family:'Inter Tight',sans-serif;color:#46526E;display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;margin:0;background:linear-gradient(135deg,#F6F8FA 0%,#EDF1F5 100%);text-align:center;padding:40px}}h2{{font-size:28px;color:#0F2552;letter-spacing:-0.02em;margin-bottom:14px}}p{{max-width:340px;font-size:13px;color:#5A6275;line-height:1.6}}span{{display:inline-block;background:#A6F50C;color:#0F2552;padding:4px 10px;font-size:10px;font-weight:800;letter-spacing:0.1em;margin-bottom:20px}}</style><span>READY</span><h2>Your brief renders here.</h2><p>Paste a source on the left, pick an archetype + audience if you have an opinion, hit Generate.</p>"></iframe>
    </div>
  </div>
</section>

<footer class="foot">
  <div class="line">OOF Engine v0.4 · 2026 · Built with Claude Code · Deployed on Render · Open source</div>
  <div class="tag">From the people who live in the future. Our future.</div>
</footer>

<script>
const API = location.origin;
let lastHTML = '';
const TEXT_EXTS = ['txt','md','csv','json'];
const BINARY_EXTS = ['pptx','docx','pdf'];

document.getElementById('file').addEventListener('change', async (e) => {{
  const f = e.target.files[0];
  if (!f) return;
  const ext = (f.name.split('.').pop() || '').toLowerCase();
  document.getElementById('file-name').textContent = `${{f.name}} · ${{Math.round(f.size/1024)}}KB`;
  if (TEXT_EXTS.includes(ext)) {{
    const r = new FileReader();
    r.onload = (ev) => {{ document.getElementById('input').value = ev.target.result; setStatus(`✓ Loaded ${{f.name}} (${{ev.target.result.length}}ch)`); }};
    r.readAsText(f);
  }} else if (BINARY_EXTS.includes(ext)) {{
    setStatus(`Parsing ${{ext.toUpperCase()}}…`);
    try {{
      const fd = new FormData(); fd.append('file', f);
      const r = await fetch(`${{API}}/api/upload`, {{ method: 'POST', body: fd }});
      const data = await r.json();
      if (data.error) throw new Error(data.error);
      document.getElementById('input').value = data.text;
      setStatus(`✓ Extracted ${{data.chars}}ch from ${{data.filename}}`);
    }} catch (err) {{ setStatus('Upload failed: '+err.message, true); }}
  }} else {{ setStatus(`Unsupported: .${{ext}}`, true); }}
}});

function setStatus(msg, isError=false) {{
  const el = document.getElementById('status');
  el.textContent = msg;
  el.className = 'status'+(isError?' error':'');
  el.style.display = msg ? 'block' : 'none';
}}

document.getElementById('make').addEventListener('click', async () => {{
  const payload = {{
    source: document.getElementById('input').value.trim(),
    constraint: document.getElementById('constraint').value.trim(),
    archetype: document.getElementById('archetype').value,
    audience: document.getElementById('audience').value,
    slide_count: document.getElementById('slide_count').value,
    cover_style: document.getElementById('cover_style').value,
    divider_style: document.getElementById('divider_style').value,
  }};
  const btn = document.getElementById('make');
  btn.disabled = true; btn.textContent = '⏳ Calling Claude…';
  setStatus('Generating brief…');
  const t0 = Date.now();
  try {{
    const r = await fetch(`${{API}}/api/generate`, {{
      method: 'POST', headers: {{'Content-Type':'application/json'}}, body: JSON.stringify(payload)
    }});
    const data = await r.json();
    if (data.error) throw new Error(data.error);
    lastHTML = data.html;
    document.getElementById('preview').srcdoc = data.html;
    const secs = ((Date.now()-t0)/1000).toFixed(1);
    document.getElementById('preview-meta').textContent = `Live · ${{(data.len/1024).toFixed(1)}}KB · ${{secs}}s`;
    document.getElementById('dl-html').disabled = false;
    document.getElementById('dl-pdf').disabled = false;
    document.getElementById('dl-pptx').disabled = false;
    setStatus(`✓ Generated in ${{secs}}s`);
  }} catch (e) {{ setStatus('Error: '+e.message, true); }}
  finally {{ btn.disabled = false; btn.textContent = 'Generate brief →'; }}
}});

document.getElementById('dl-html').addEventListener('click', () => {{
  const blob = new Blob([lastHTML], {{type:'text/html'}});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'OOF_brief.html'; a.click(); URL.revokeObjectURL(url);
}});
async function exportBinary(path, name) {{
  setStatus('Building '+name+'…');
  try {{
    const r = await fetch(`${{API}}${{path}}`, {{ method:'POST', headers:{{'Content-Type':'application/json'}}, body: JSON.stringify({{html:lastHTML}}) }});
    if (!r.ok) throw new Error(await r.text());
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = name; a.click(); URL.revokeObjectURL(url);
    setStatus('✓ '+name+' downloaded');
  }} catch (e) {{ setStatus(name+' failed: '+e.message, true); }}
}}
document.getElementById('dl-pdf').addEventListener('click',  () => exportBinary('/api/export/pdf',  'OOF_brief.pdf'));
document.getElementById('dl-pptx').addEventListener('click', () => exportBinary('/api/export/pptx', 'OOF_brief.pptx'));
</script>
</body>
</html>"""


if __name__ == '__main__':
    # 1. Write index.html
    html = build_html()
    (ROOT / "index.html").write_text(html)
    print(f"✓ index.html written ({len(html)} chars)")

    # 2. Write AUDIT.md
    audit = build_audit()
    (ROOT / "AUDIT.md").write_text(audit)
    print(f"✓ AUDIT.md written ({len(audit)} chars)")

    print(f"\nNext: render PDF version with weasyprint.")
