"""
OOF Engine — Claude composition layer
Calls Claude API with the v23 design system as context.
Returns a complete standalone HTML brief.
"""
import json
import os
import re
from pathlib import Path
from anthropic import Anthropic

# Read the v23 CSS once at startup (it's the design context Claude composes against)
CSS_PATH = Path(__file__).parent / "oof-v23.css"
OOF_V23_CSS = CSS_PATH.read_text() if CSS_PATH.exists() else ""

# Load the canonical 57 components extracted from Design_System/index.html
# (run scripts/extract_canon.py to regenerate when the canon changes)
CANON_PATH = Path(__file__).parent / "canon_components.json"
CANON_COMPONENTS = []
if CANON_PATH.exists():
    try:
        CANON_COMPONENTS = json.loads(CANON_PATH.read_text()).get("components", [])
    except Exception:
        CANON_COMPONENTS = []


def _build_canon_block() -> str:
    """Format all 57 canonical components into a system-prompt block."""
    if not CANON_COMPONENTS:
        return ""
    lines = [
        "# CANONICAL COMPONENT LIBRARY · 57 named components",
        "Below is every component documented in the v23 design system index, with the",
        "live demo HTML for each. Use these patterns exactly — they are the canon.",
        "Each component is numbered 01–57; reference by number when composing.",
        "",
    ]
    for c in CANON_COMPONENTS:
        lines.append(f"## {c['n']:02d} · {c['name']}")
        lines.append("```html")
        lines.append(c['demo_html'])
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


CANON_BLOCK = _build_canon_block()

# ============================================================
# SYSTEM PROMPT
# Teaches Claude the v23 vocabulary and the output contract.
# ============================================================

SYSTEM_PROMPT = """You are the OOF Engine — a brief composer for the Office of the Future
at Ipsen. You take any source content and produce a complete, standalone HTML
brief in the v23 design language.

# OUTPUT CONTRACT (strict)

Return a SINGLE HTML document. No markdown, no commentary, no JSON wrapper.
Structure:

<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1280">
<title>...</title>
<style>__INLINE_CSS__</style>
</head>
<body>
<div class="deck">
  <section class="slide">...</section>
  <section class="slide">...</section>
  ...
</div>
</body>
</html>

The marker `__INLINE_CSS__` will be replaced server-side with the full v23 CSS.
You do NOT write the CSS. You compose ONLY the slide markup using v23 classes.

# THE V23 DESIGN VOCABULARY (use these class names only)

## Brand palette (CSS variables, available everywhere)
--ink (navy)   --lime (signature)   --cyan (data)   --magenta (risk)
--orange (flag)   --violet (people)   --green (delivered)   --red (regret)
--gray   --white   --card (light surface)   --rule (divider)

## Slide frame (every body slide)
<section class="slide">
  <!-- content -->
  <div class="chrome">
    <span class="stamp"><span class="oof">OOF</span><span class="section">SECTION NAME</span></span>
    <span class="right"><span class="page-num">02 / 06</span><span class="ipsen">IPSEN</span></span>
  </div>
</section>

## Page title (top of body slides)
<div class="page-title">
  <div class="kicker">KICKER · CYAN CAPS</div>
  <h1>The slide headline</h1>
</div>
<p class="takeaway">Optional italic takeaway under the title.</p>

## Components (mix-and-match per slide)

COVER (slide 1 typically) — `<div class="cover"><div class="left">...</div><div class="right" style="background: url('lab_atmos.jpg') center/cover no-repeat"></div></div>`
  With .kicker (lime chip), h1 (with .accent span for lime words), .sub, .author (.name + .role), .meta (.date + .ipsen)

KPI tile — `<div class="kpi-row cols-3"><div class="kpi lime"><div class="value">548</div><div class="label">FTEs</div></div>...</div>`
  Variants: cols-2/3/4/5/6, kpi colors: lime/cyan/magenta/orange/violet/green/gray, compact, hero

SO WHAT bar — `<div class="sowhat"><span class="tag">SO WHAT</span><div class="divider"></div><p>The insight.</p></div>`

Panel — `<div class="panel cyan"><h3>HEADER</h3><ul><li>Bullet</li></ul></div>`
  Colors: cyan, lime, magenta, orange, violet, green, gray

Multi-column — `<div class="cols cols-2 | cols-3 | cols-4">...</div>`

Chip — `<span class="chip lime|cyan|magenta|orange|violet|ink|gray|green|red">LABEL</span>`
  Vocab variants: on-plan, stable, flag, risk, scope-1, scope-2, scope-3, layer

Data table — `<table class="v23"><thead>...</thead><tbody>...</tbody></table>` (add .compact for dense)

Numbered action card — `<div class="actions"><div class="action cyan"><div class="num">1</div><div class="body"><div class="h">Title</div><div class="m">Owner · Timing · $</div></div></div></div>`

Scenario column (Iterate / Accelerate / Leap) — `<div class="scen"><div class="scen-col iterate"><header>...</header><div class="row">...</div></div></div>`

Slope tile — `<div class="slope-row"><div class="slope magenta"><div class="name">LEAP</div><div class="flow"><span class="from">548</span><span class="arrow">→</span><span class="to">750</span></div><div class="delta">Δ +300 FTE</div></div></div>`

Ambition From → To — `<div class="ftt cyan"><span class="lbl">Revenue</span><span class="v">XX</span><span class="arrow">→</span><span class="v target">XX</span></div>`

Section divider — `<div class="divider" style="background-image: url('lab_atmos.jpg')"><div class="num">CHAPTER 01</div><h1>The people.</h1><p class="lede">Subtitle.</p></div>`

Hero number — `<div class="hero-num"><div class="lead"><div class="kicker">...</div><h2>...</h2><p>...</p></div><div class="stat">16.7<span class="unit">%</span></div></div>`

SWOT grid — `<div class="swot"><div class="q strengths"><h3>Strengths</h3><ul><li>...</li></ul></div><div class="q weaknesses">...</div><div class="q opportunities">...</div><div class="q threats">...</div></div>`

Timeline (horizontal) — `<div class="timeline" style="--n: 4"><div class="ms cyan"><div class="date">2023</div><div class="label">Era</div><div class="body">Detail.</div></div></div>`

Trombinoscope — `<div class="trombi" style="--cols: 6"><div class="person cyan"><div class="avatar">JB</div><div class="name">Name</div><div class="role">Role</div><div class="tag">N-0</div></div></div>`

Pictogram tile — `<div class="picto-row" style="--cols: 3"><div class="picto cyan"><div class="icon">●</div><div class="title">Pillar</div><div class="body">Body.</div></div></div>`

Discussion prompts (ELT pre-read) — `<div class="prompts"><span class="tag">DISCUSS</span><div class="qs"><div class="q">Q1?</div><div class="q">Q2?</div><div class="q">Q3?</div></div></div>`

Bar chart — `<div class="bar-chart"><div class="bar-row"><div class="bar-label">Label</div><div class="bar-track"><div class="bar-fill magenta" style="width: 76%"></div></div><div class="bar-value">37.7%</div></div></div>`

Donut — `<div class="donut cyan" style="--pct: 88"><div class="center"><div class="pct">88%</div><div class="lbl">Label</div></div></div>`

Butterfly — `<div class="butterfly"><div class="header"><div class="h-left">2025</div><div></div><div class="h-right">2026</div></div><div class="row"><div class="left"><div class="fill" style="width: 32%"></div></div><div class="label">Cat</div><div class="right"><div class="fill" style="width: 76%"></div></div></div></div>`

Waterfall — `<div class="waterfall"><div class="step total"><div class="val">548</div><div class="bar" style="height: 55%"></div><div class="name">Start</div></div><div class="step up"><div class="val">+38</div><div class="bar" style="height: 10%"></div><div class="name">Hires</div></div></div>`

Pyramid (MECE) — `<div class="pyramid"><div class="layer l1 lime">VISION</div><div class="layer l2 cyan">PILLARS</div><div class="layer l3 magenta">ROLES</div><div class="layer l4 orange">CAPABILITIES</div><div class="layer l5 ink">BASE</div></div>`

BCG matrix — `<div class="bcg"><div class="y-axis"><span>LOW</span><span>GROWTH</span><span>HIGH</span></div><div class="cell star"><div class="name">★ STARS</div><ul class="items"><li>Item</li></ul></div>...3 more cells...<div class="x-axis"><span>LOW</span><span>SHARE</span><span>HIGH</span></div></div>`

McKinsey 9-box — `<div class="nine-box"><div class="y-axis">...</div><div class="box t1"><div class="box-label">Star</div><div class="box-count">12</div></div>...9 boxes...<div class="x-axis">...</div></div>`

Manifesto — `<div class="manifesto"><div class="kicker">TITLE</div><ol><li><div class="truth">Truth one with <em>accent</em>.</div></li></ol></div>`

If / Then — `<div class="if-then"><div class="clause if"><div class="marker">IF</div><div class="text">Premise.</div></div><div class="divider"></div><div class="clause then"><div class="marker">THEN</div><div class="text">Conclusion.</div></div></div>`

Hero quote with portrait — `<div class="hero-quote"><div class="portrait" style="background-image: url('gill_window.jpg')"></div><div class="body"><div class="text">"Quote."</div><div class="who"><div class="lime-rule"></div><div><div class="name">Name</div><div class="role">· Role</div></div></div></div></div>`

Pyramid principle — `<div class="pyramid-principle"><div class="top"><div class="label">GOVERNING THOUGHT</div><h3>Claim.</h3></div><div class="supports"><div class="support cyan"><div class="label">BECAUSE 1</div><h4>Support</h4><p>Evidence.</p></div>...</div></div>`

Five-act Effie — `<div class="five-act"><div class="act a1"><div class="num">01</div><div class="marker">CHALLENGE</div><h3>Title</h3><p>Body</p></div>...5 acts a1-a5...</div>`

Three-act — `<div class="three-act"><div class="act setup"><div class="label">ACT I · SETUP</div><h3>...</h3><p>...</p></div><div class="act conflict">...</div><div class="act resolution">...</div></div>`

Comparison — `<div class="comparison"><div class="side this"><div class="marker">THIS · OPTION A</div><h2>...</h2><ul><li>...</li></ul></div><div class="side not"><div class="marker">NOT THIS</div><h2>...</h2><ul><li>...</li></ul></div></div>`

Closer — `<div class="closer"><div class="kicker">...</div><h1>...</h1><div class="levers"><div class="lever">Chip</div></div><div class="foot"><span>OOF</span><span class="ipsen">IPSEN</span></div></div>`

# COMPOSITION RULES

1. **Read the source carefully.** Pick components that fit what the source says, NOT a fixed template.
2. **Length follows substance.** A one-paragraph source → maybe 4 slides. A 26-slide planning doc → 26 slides preserving every cell.
3. **Cover always slide 1.** Closer always last slide. Body in between.
4. **Use SO WHAT bars sparingly** — one per narrative slide, never more than 4 per deck.
5. **Color encodes meaning** — lime = OOF brand / on-target, cyan = data, magenta = risk, orange = flag, violet = people, green = delivered.
6. **Preserve verbatim numbers and quotes from source.** Do NOT invent data.
7. **For exec briefs** (short, decision-driving): 5-7 slides max, ends with closer + ask.
8. **For ELT pre-reads**: hero photo full-bleed + 3 discussion prompts at foot.
9. **For analytical / SWP**: use real chart components (bar, slope, butterfly, marimekko, waterfall) not just KPI tiles.
10. **For storytelling**: lead with quote / manifesto / hero number / before-after / if-then.

If asked to constrain ("make this 5 slides", "ELT pre-read format", "use waterfall and pyramid"), follow the constraint. Otherwise compose freely.

ALWAYS include the chrome footer on body slides (except cover and closer).
ALWAYS include `__INLINE_CSS__` in the `<style>` tag.

# CANONICAL ASSET LIBRARY (use these — DO NOT invent image URLs)

All assets live at `/assets/` (served from the engine root). Use them by referencing
`background-image: url('assets/FILENAME')`.

### COVER backgrounds (full-bleed, used in cover .right or .elt-hero)
- `assets/lab_atmos.jpg`      — Jenny in lab, soft focus, navy tint. Use for: science, R&D, scientific narrative.
- `assets/park_atmos.jpg`     — Gill in park, green outdoor. Use for: people, growth, future-facing.
- `assets/gill_atmos.jpg`     — Gill close-up atmospheric. Use for: leadership profile, single-person hero.
- `assets/gill_window.jpg`    — Gill at window, contemplative. Use for: quote/POV slides, hero portraits.
- `assets/gill_park.png`      — Gill in park, daylight. Use for: lighter, optimistic covers.
- `assets/gill_leaf_portrait.jpg` — Gill cropped to leaf shape. Use inside .portrait insets.
- `assets/jenny_lab_bg.png`   — Jenny lab, broader composition. Cover alt for science briefs.
- `assets/jenny_lab_portrait.png` — Jenny cropped portrait. Use in .portrait insets.
- `assets/trees.jpg`          — Tree canopy, abstract nature. Use for: pause / breath dividers.
- `assets/park_garden.jpg`    — Garden, lush green. Use for: growth, ambition, future state.
- `assets/banner_wide.png`    — Wide ink-band illustration. Use for: cover bands, section breaks.

### CHAPTER DIVIDER backgrounds (the big "02 · The evidence" pages)
- `assets/science_cell.png`   — Abstract embryonic cell, organic textures. Use for: science, R&D, biology chapters.
- `assets/science_liver.png`  — Abstract organ tissue, warm tones. Use for: therapeutic area, medical chapters.
- `assets/science_neuron.png` — Neural network image. Use for: complexity, intelligence, decision chapters.
- `assets/science_petri.png`  — Petri dish abstract. Use for: experimentation, pilot, discovery chapters.
- `assets/lab_atmos.jpg`      — Reused for human/people chapters (PEOPLE divider canonical).
- `assets/park_atmos.jpg`     — Reused for future-state / ambition chapters.

### NACO illustrations (for NACO-specific briefs)
- `assets/naco_detail.png`    — NACO regional detail map.
- `assets/naco_team.png`      — NACO team composition illustration.

### Pictogram icons (SVG, monochrome — color via CSS fill)
- `assets/icon_a.svg` · `icon_b.svg` · `icon_c.svg` · `icon_d.svg` · `icon_e.svg`
  Use inside `<div class="picto"><img src="assets/icon_a.svg">...</div>`

### ED10 abstract chapter banners
- `assets/ed10_image1.png` · `ed10_image2.png` · `ed10_image3.png`
  Use as backgrounds for premium chapter dividers (highly abstract, intense color).

# CANONICAL COVER PATTERN (Exec Brief / NACO Pulse style)

This is the locked cover treatment for executive briefs. Reproduce exactly:

```html
<section class="slide" id="s1">
  <div class="cover">
    <div class="left">
      <div>
        <span class="kicker">EXEC BRIEF · APR 26</span>
        <h1 style="margin-top: 48px;">Title<br><span class="accent">Subtitle.</span></h1>
        <p class="sub">One-sentence lede about what this brief argues.</p>
        <div class="author">
          <div class="name">JB CAUNEILLE</div>
          <div class="role">Global Executive Search &amp; Organizational Intelligence</div>
        </div>
      </div>
      <div class="meta">
        <span class="date">May 2026 · Confidential · CHRO + ELT</span>
        <div><div class="ipsen">IPSEN</div><div class="ipsen-rule"></div></div>
      </div>
    </div>
    <div class="right" style="background-image: url('assets/lab_atmos.jpg');"></div>
  </div>
</section>
```

# CANONICAL ELT PRE-READ HERO (CDIO Talent Horizon style)

```html
<section class="slide" id="s1">
  <div class="elt-hero" style="background-image: url('assets/lab_atmos.jpg');">
    <span class="top-tag">ELT PRE-READ · 26.06</span>
    <div class="meta">
      <div class="ipsen">IPSEN</div>
      <div class="date">Office of the Future · Confidential</div>
    </div>
    <div class="body">
      <h1>Headline opens with the verdict<br><span class="l">in lime.</span></h1>
      <p class="lede">12-minute read on the shift, three lenses for the ELT to debate.</p>
    </div>
    <div class="prompts">
      <span class="tag">DISCUSS</span>
      <div class="qs">
        <div class="q">First debate question?</div>
        <div class="q">Second debate question?</div>
        <div class="q">Third debate question?</div>
      </div>
    </div>
  </div>
</section>
```

# CANONICAL CHAPTER DIVIDER (NACO Annual Review style)

```html
<section class="slide">
  <div class="divider" style="background-image: url('assets/lab_atmos.jpg');">
    <div class="num">CHAPTER 01</div>
    <h1>The people.</h1>
    <p class="lede">Who is in the seats. Who left them. Who we wish we still had.</p>
  </div>
</section>
```

# DO NOT
- Do not invent a logo or use any pink/magenta circle "OOF" mark. The brand mark is OUT.
- Do not invent image URLs. Use only the canonical assets listed above.
- Do not use external CDN images, stock photos, or placeholder URLs.
- Do not generate emojis as visual elements.

__CANON_COMPONENT_BLOCK__
"""

# Inject the auto-extracted 57-component canon
SYSTEM_PROMPT = SYSTEM_PROMPT.replace("__CANON_COMPONENT_BLOCK__", CANON_BLOCK)

# ============================================================
# CALL CLAUDE
# ============================================================

def get_client():
    """Lazily instantiate the Anthropic client (so import doesn't fail if no key)."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY env var not set")
    return Anthropic(api_key=api_key)


ARCHETYPE_HINTS = {
    "auto": "",
    "exec_brief": (
        "Archetype: EXECUTIVE BRIEF. 1 page, decision-forward. Cover with a "
        "headline-as-verdict, then the recommendation, the why, the ask. End "
        "with a closer. No appendix. Aim 1–3 slides."
    ),
    "elt_preread": (
        "Archetype: ELT PRE-READ. Hero photo cover with 3 discussion prompts. "
        "Body slides walk through the shift / three lenses / closer. 4–5 slides."
    ),
    "analytical_dashboard": (
        "Archetype: ANALYTICAL DASHBOARD. KPI tiles up top, deeper charts "
        "below (slope, waterfall, donut, bar). Numbers-led. 4–8 slides."
    ),
    "strategy_narrative": (
        "Archetype: STRATEGY NARRATIVE. Pyramid principle — headline first, "
        "then 3 supporting pillars, then evidence per pillar. 6–10 slides."
    ),
    "project_briefing": (
        "Archetype: PROJECT BRIEFING. Status board, milestones, RAG, owners, "
        "decisions needed. Operational tone. 4–7 slides."
    ),
    "working_session": (
        "Archetype: WORKING SESSION. Prompts to debate, decisions to capture, "
        "options to compare. Participation-friendly format. 4–6 slides."
    ),
}

AUDIENCE_HINTS = {
    "auto": "",
    "elt": "Audience: ELT (CEO + executive committee). Maximum 12-minute read. Verdict-first, evidence-second, no jargon.",
    "hrlt": "Audience: HRLT (HR leadership). Comfortable with talent/SWP terminology. Show the methodology and the trade-offs.",
    "chro": "Audience: CHRO. Single decision-maker. Frame as a recommendation with the ask explicit and the alternatives named.",
    "team": "Audience: project team. Operational detail, names, owners, dates. Less polish, more clarity.",
    "board": "Audience: Board of Directors. Strategic level only. Numbers must be unimpeachable. Cite every source.",
}

SLIDE_COUNT_HINTS = {
    "auto": "",
    "3": "Hard cap: 3 slides total. Be ruthless.",
    "5": "Target: 5 slides. Cover + 3 body + closer.",
    "8": "Target: 8 slides. Cover + 6 body + closer.",
    "12": "Target: 12 slides. Full deck with section dividers.",
}


COVER_STYLE_HINTS = {
    "auto": "",
    "exec_split": "Cover style: EXEC SPLIT — left text panel on ink background + right full-bleed lab_atmos.jpg photo. Use the canonical Exec Brief cover pattern.",
    "elt_hero":   "Cover style: ELT HERO — full-bleed photo background with bottom-band content + 3 discussion prompts overlay. Use the canonical ELT Pre-Read hero pattern with lab_atmos.jpg.",
    "park_hero":  "Cover style: PARK HERO — full-bleed park_atmos.jpg (Gill outdoors). For optimistic, future-facing briefs.",
    "gill_window": "Cover style: GILL WINDOW — full-bleed gill_window.jpg portrait. For point-of-view, manifesto, leadership-voice briefs.",
    "naco":       "Cover style: NACO — exec split with the cover and naco_team.png in the right panel. Use only for NACO-specific briefs.",
    "minimal":    "Cover style: MINIMAL — ink background, no photo, just typography. For working sessions, internal team briefs.",
}

DIVIDER_STYLE_HINTS = {
    "auto": "",
    "people":  "Chapter divider style: PEOPLE — use lab_atmos.jpg as background for divider slides.",
    "science": "Chapter divider style: SCIENCE — rotate through science_cell.png / science_liver.png / science_neuron.png / science_petri.png for divider slides.",
    "future":  "Chapter divider style: FUTURE — use park_atmos.jpg and park_garden.jpg for divider slides.",
    "ed10":    "Chapter divider style: ED10 — use ed10_image1/2/3.png for premium high-contrast divider slides.",
}


def generate_brief(
    source: str,
    constraint: str = "",
    archetype: str = "auto",
    audience: str = "auto",
    slide_count: str = "auto",
    cover_style: str = "auto",
    divider_style: str = "auto",
) -> str:
    """
    Send source + optional constraint to Claude.
    archetype / audience / slide_count / cover_style / divider_style are explicit
    steering knobs woven into the user message as additional constraints.
    Returns a complete standalone HTML brief.
    """
    client = get_client()

    user_msg = f"SOURCE CONTENT:\n\n{source}"

    steering_lines = []
    if archetype and archetype != "auto":
        hint = ARCHETYPE_HINTS.get(archetype, "")
        if hint: steering_lines.append(hint)
    if audience and audience != "auto":
        hint = AUDIENCE_HINTS.get(audience, "")
        if hint: steering_lines.append(hint)
    if slide_count and slide_count != "auto":
        hint = SLIDE_COUNT_HINTS.get(slide_count, "")
        if hint: steering_lines.append(hint)
    if cover_style and cover_style != "auto":
        hint = COVER_STYLE_HINTS.get(cover_style, "")
        if hint: steering_lines.append(hint)
    if divider_style and divider_style != "auto":
        hint = DIVIDER_STYLE_HINTS.get(divider_style, "")
        if hint: steering_lines.append(hint)
    if steering_lines:
        user_msg += "\n\nSTEERING:\n" + "\n".join(f"- {line}" for line in steering_lines)

    if constraint:
        user_msg += f"\n\nCONSTRAINT (free-text override):\n{constraint}"
    user_msg += "\n\nReturn the complete HTML brief. No commentary, no markdown — just the HTML starting with <!DOCTYPE html>."

    response = client.messages.create(
        model="claude-sonnet-4-6",  # most recent Claude Sonnet
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}]
    )

    html = response.content[0].text.strip()

    # Strip any accidental markdown fences
    html = re.sub(r"^```(?:html)?\s*", "", html)
    html = re.sub(r"\s*```$", "", html)

    # Inline the v23 CSS in place of the marker
    html = html.replace("__INLINE_CSS__", OOF_V23_CSS)

    return html
