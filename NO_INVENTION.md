# Zero Invention Rule

**This is the highest-priority rule in the OOF Engine.** It overrides every
other instruction in the system prompt, every archetype, every component, every
steering hint, every operator request.

## What the rule says

The engine may **never** fabricate any of the following:

- Names of people, products, programmes, platforms, brands, methodologies, frameworks
- Numbers, percentages, deltas, dates, currencies, sample sizes, growth rates
- Quotes, attributions, citations, study findings, research conclusions
- Org charts, role titles, reporting lines, headcounts, BU names
- Initials standing in for real people (no "JB · CHRO" placeholders for unknown leaders)
- Statistics ("47% YoY", "16.7%", "+1.9 pt") unless they appear verbatim in the source

## What the engine may use

- Verbatim content from the source provided in the request
- The client's own frameworks and taxonomies (only when explicitly given)
- Placeholder language clearly marked: `[TBD]`, `[INSERT HERE]`, `[source: gap]`

## What to do when source data is missing

If a slide pattern would require content the source does not contain, the engine
must do one of:

1. **Use `[TBD]` or `[INSERT HERE]` as literal placeholder text** in the slide
2. **Skip that slide entirely** and substitute a different pattern that the source can support
3. **Return an early-exit note in the brief** saying:
   _"Source does not contain X — cannot build slide Y without it. Please provide
   X or remove Y from scope."_

A slide with `[TBD]` markers is **correct**.
A slide with invented data is **broken**, even if it looks polished.

## The Apollo cautionary tale

A previous build of the engine invented a platform called "Apollo" that did not
exist at Ipsen. It read as plausible. It was wrong. Never again. If the engine
would need to invent a name or number to complete a slide, it does not include
that slide.

## Where the rule lives

- **`claude_engine.py`** — top of `SYSTEM_PROMPT` (loaded at every Claude call)
- **`NO_INVENTION.md`** — this file (canonical statement)
- **`README.md`** — first section (reader awareness)
- **Skill prompts** (e.g. `ipsen-strategic-brief`) — `data_integrity.md` reference
- **Build scripts** — never embed example data that isn't from the canon

## How to verify the engine is honouring the rule

Quick test: generate a brief from a source that contains a topic but no numbers.
The output should show `[TBD]` markers where numbers would have gone, not
invented percentages. If you see plausible-looking statistics with no source
citation, the rule is being violated.
