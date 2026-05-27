# OOF Engine

A small backend that takes any source content, calls Claude, and returns a v23-designed brief in HTML / PDF / PPTX.

## ⚠ ZERO INVENTION RULE — read this first

The engine never fabricates names, numbers, quotes, percentages, dates, org
charts, or any data the source does not contain. When data is missing, the
output uses `[TBD]` / `[INSERT HERE]` placeholders or skips the slide.

This rule overrides every other instruction. See [`NO_INVENTION.md`](NO_INVENTION.md)
for the full statement and the Apollo cautionary tale.

## Architecture

```
┌────────────────┐         ┌──────────────────────┐         ┌────────────┐
│  Frontend      │  POST   │  Flask backend       │  HTTPS  │  Claude    │
│  (static HTML) │ ──────► │  /api/generate       │ ──────► │  API       │
│  paste · upload│         │  /api/export/pdf     │         │            │
│  preview · DL  │ ◄────── │  /api/export/pptx    │ ◄────── │  Sonnet 4  │
└────────────────┘  HTML   └──────────────────────┘  HTML   └────────────┘
                              │
                              ├── claude_engine.py  · LLM call + v23 system prompt
                              ├── pptx_export.py    · weasyprint + python-pptx
                              └── frontend/oof-v23.css  · 57-component design system
```

## Local development

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# macOS · install poppler for PDF→PNG conversion
brew install poppler
# Set API key
export ANTHROPIC_API_KEY=sk-ant-...
# Run
python app.py
# Open http://localhost:8000
```

## Deploy to Render

1. **Push this folder to a new GitHub repo** (any name, e.g. `oof-engine`).
2. **Render dashboard → New → Web Service → Connect this repo**.
3. **Render auto-detects `render.yaml`.** Confirm.
4. **Add environment variable** `ANTHROPIC_API_KEY` in the Render dashboard (Settings → Environment).
5. **Deploy.** Build takes ~3 min (poppler + python deps). First request takes ~10s as Claude responds.

Your engine is live at `https://oof-engine.onrender.com` (or whatever Render names it).

## What the engine does

**POST `/api/generate`** — `{source: "...", constraint: "..."}` → `{html: "..."}`
Claude reads your source, composes a brief using the 57-component v23 vocabulary, returns standalone HTML with the CSS inlined.

**POST `/api/export/pdf`** — `{html: "..."}` → PDF binary
weasyprint renders the HTML to PDF server-side. Honors print styles (1280×720, page-break-after on .slide).

**POST `/api/export/pptx`** — `{html: "..."}` → PPTX binary
weasyprint → PDF → split to per-slide PNG → python-pptx wraps each PNG as a full-bleed slide. Visually perfect, not text-editable. (v2 roadmap: structured JSON from Claude → native python-pptx with editable text frames.)

## Roadmap

- **v2 editable PPTX** — extend the system prompt to also return structured JSON (slide-by-slide component tree). Python-pptx builds native shapes/text. Editable in PowerPoint.
- **File parsing on upload** — accept .pptx/.docx/.pdf directly. Parse to text server-side (python-pptx for ppt, python-docx for docx, pdfplumber for pdf). Frontend just uploads, backend extracts.
- **Auth + history** — basic API key on the frontend, store generated briefs server-side, "regenerate from history" button.
- **Team brand kits** — each customer gets a CSS variant (`oof-v23-acme.css`) with their colors. Frontend picks at generation time.

## Files

- `backend/app.py` — Flask app, three routes + static frontend serving
- `backend/claude_engine.py` — system prompt + Claude API call
- `backend/pptx_export.py` — PDF + PPTX export logic
- `backend/requirements.txt` — pinned deps
- `frontend/index.html` — the engine UI
- `frontend/oof-v23.css` — design system (57 components)
- `frontend/assets/` — cover photos
- `render.yaml` — Render deployment config
- `.gitignore` — Python + IDE noise
