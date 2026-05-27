# Production Craft Standard

**This is the standing quality floor for every artifact the OOF Engine produces
or any artifact I touch.** It overrides convenience. If a deliverable doesn't
meet these rules, it is not finished.

This standard sits alongside `NO_INVENTION.md`. Zero-invention is about WHAT
goes into the work; CRAFT is about HOW that work gets refined and verified
before delivery.

---

## Part 1 · The Mechanic

The Mechanic is how we think about composition. Every brief — and every
artifact in the OOF system — follows it.

1. **Argument before slides.** One sentence the brief is making. If you can't say it in one breath, the brief isn't ready. Write the sentence first, then the slides.
2. **Anchor an arc at the front.** Three-act or Effie five-act. The arc is the deck's spine. Every slide is a beat inside it.
3. **Bookend with the same shape.** The arc that opens the deck returns at the end with the verdict filled in. Three-act diamond opens → three-act diamond closes. Chevron opens → chevron returns.
4. **Every slide is a beat.** Not a free-floating finding. If a slide doesn't earn its place in the arc, it gets cut, merged, or moved to appendix.
5. **v23 vocabulary expresses the beat.** Chevron / chip / panel / KPI tile / waterfall / hero number. The shape carries the meaning. Shapes are not decoration.
6. **Density earns the slide.** Empty bottom = fill with substance the source supports, or cut the slide. White space is a deliberate choice, never a leftover.
7. **One chrome, one numbering, one tone, end-to-end.** Two of any of these = visible deck = process failure.
8. **Editorial judgment beats feature-completism.** Cut, reorder, merge. A 28-slide deck arguing one thing beats a 36-slide deck listing findings.
9. **Craft.** Rounded shapes, not cartoonish geometry. Spacing tight but breathing. One accent colour per card. Same diamond opens and closes.

**Quality, in operating terms:** the ELT reads it once and gets the argument.
Numbers are bulletproof. The design carries the meaning instead of competing
with it. The tone is grown-up — opinionated, evidence-backed, not pitchy.

---

## Part 2 · The Ten Rules

### 1 · Slide-by-slide render check
Every output slide is visually verified, not just text-validated.
- HTML briefs: render to PNG and inspect for overlaps, escaped elements, empty space.
- PPTX briefs: render via LibreOffice or screenshot every slide.
- Bulk text operations that "look done" are not done until each slide has been seen.

### 2 · Numeric cross-check (the Hero-Number rule)
Every standalone number on a slide must be traceable to the source.
- **Bulk regex catches `r=0.929` patterns. It misses the bare `0.929` hero stat in a 72pt callout.**
- Hand-verify every hero number, every percentage, every total, every count.
- When refreshing a wave of data, build a CHANGE-LOG of old→new values BEFORE editing. Sweep against the change-log; do not rely on contextual regex alone.
- If a number's lineage is unclear, mark `[TBD]` and surface it in the handoff.

### 3 · Single visual grammar
A deck has one chrome, one numbering scheme, one tone register, one set of card styles.
- Two of any of these is a visible deck.
- Mixed grammars are a process failure — they mean two sources got stapled together without reconciliation.
- Sweep before delivery: chrome / page numbers / typography / card patterns.

### 4 · Duplication audit
Before delivery, list every slide and the point it makes in one phrase.
- Two slides making the same point = collapse, kill, or distinguish.
- 4 slides about acquiescence × 3 facets (definition / method / before-after) = OK.
- Same facet twice = not OK.
- Run this audit at the END, not when adding slides.

### 5 · Empty-space audit
Any slide with >25% empty area at the bottom is incomplete.
- Either fill with substance the source supports
- Or cut the slide
- Or shrink the slide's vertical space deliberately
- Empty bottom is never a passive choice.

### 6 · Tone register lock
Pick one register and state it at the top of the brief:
- **Research report** — observational, hedged, evidence-cited
- **Executive memo** — verdict-first, prose-heavy, opinionated
- **Consulting pitch** — **banned in OOF work.** Words like "moves", "plays", "horizons", "levers" leak the register.
- **Academic** — formal, full citations, longer
Sweep for leaks before delivery.

### 7 · Inconsistency surfacing
When inconsistencies are found during a pass, name them in the deliverable handoff.
- Never silently leave a known issue.
- Format: _"Known: X is inconsistent because Y. Fix is Z. Did not fix because [reason]."_
- The handoff should make every known gap visible.

### 8 · Render-verify after each structural change
Don't save-and-hope. Visually confirm after each structural edit:
- Slide deletion → page numbers + chapter rails reconciled?
- Slide reorder → narrative still flows?
- Text replacement → did it preserve formatting + line breaks?
- New shape added → does it overlap existing shapes?

### 9 · Slow before fast
A 10-minute deep read of the source beats 30 minutes of bulk operations.
- The first pass is reading + mapping.
- The second pass is editing.
- The third pass is verifying.
- Bulk regex is the LAST pass, not the first.

### 10 · Honest gap report on every handoff
Every delivery includes:
- What was done
- What was caught
- What was missed (and why)
- What still needs human eyes
- Self-grade out of 10 across argument / design / tone / data / discipline / craft

No silent ship.

---

## Part 3 · The Design Rules

### Light backgrounds
OOF artifacts use light cream / paper / white substrate. Dark backgrounds are
permitted only for cover / divider / closer slides where they earn the contrast.
Default body slides = light. Reason: JB preference, also reads better in print.

### Wordmark, no logo
The OOF identity is the wordmark "OOF.Engine" or "OOF · Office of the Future"
in Inter Tight 900. **No pink vinyl disc. No symbol mark.** The wordmark works
at any size, any colour, any background.

### Rounded, not cartoonish
Geometric primitives — circles, rounded rectangles, chevrons — are used at
SCALE with restraint. Sharp-edged stand-in shapes (hard checkmarks, numbered
bubbles trying to look like icons) read as decorative and weaken the slide.
If a shape isn't doing semantic work, it doesn't earn its place.

### One accent per card
A card carries one colour band on top (4-8px lime, cyan, magenta, orange, or violet).
Body is white on light background. No multi-coloured cards. No left-border-accent
trope. Top band is the convention.

### Palette is closed
Six colours carry the entire system:
- **Ink** #0F2552 — substrate
- **Lime** #A6F50C — hero accent, verdict, future
- **Cyan** #0CB8F5 — data, evidence
- **Magenta** #F50C7A — risk, voice, rare emphasis
- **Orange** #F5800C — warning, deadlines
- **Violet** #8B5CF6 — people, profiles, perspectives

Do not add to the palette. Do not invent gradients. Do not soften the lime.

### Typography is closed
Two fonts:
- **Inter Tight 900** — display, headlines, verdicts
- **Inter 400** — body, supporting text
- **JetBrains Mono 600** (or system mono) — corner stamps, page numbers, technical specs

No font-switching for hierarchy. Hierarchy is size + colour + weight, not face.

### Voice rules (from ipsen-strategic-brief skill)
- US English ("behavior" not "behaviour")
- Phase in Roman numerals (Phase I, Phase II)
- Dates: "1 January 2026"
- "Ipsen" sentence-case inline; caps "IPSEN" reserved for the brand mark
- First-person plural ("we"), not corporate "the team"
- No em-dashes in body text; bullets or periods
- Title-case in titles is wrong; sentence case correct

---

## Part 4 · The Deference Protocol

When working on canonical artifacts (Design_System/index.html, the live engine,
the v23 CSS, established briefs) — **edit before add, ask before swap.**

1. **READ before WRITE.** Understand what the artifact is doing before changing it.
2. **EDIT before ADD.** Make existing content sharper before adding new content.
3. **ASK before SWAP.** If a structural change is proposed (new layout, new section, dropped slide), surface the proposal and wait for explicit consent.
4. **OPINE freely.** Recommend, push back, propose alternatives. The protocol is about consent on execution, not about silence on judgment.
5. **NEVER substitute silently.** If something can't be done as asked, say so and propose the alternative — do not deliver a different thing under the same name.
6. **NEVER touch the design language without permission.** Design is the team's vocabulary. Changes propagate.

---

## Part 5 · The Engine application

When Claude generates a brief through the OOF Engine:

- These rules are part of the system prompt's quality contract.
- Every output is composed against these rules AND against the v23 component vocabulary.
- The engine should return a brief AND a self-audit (Part 6, future v0.5).
- The user can re-run with stricter rules if any are violated.

When I (or anyone) edits a deck or design artifact:

- Same rules, no exceptions.
- The handoff message includes the gap report.
- Inconsistencies are surfaced, not buried.
- Bulk operations are explicit (named) and followed by render-verify.

---

## Part 6 · The Cautionary Tales (standing tests)

These are the named failures we test every output against.

### Apollo · data invention
A previous build invented a platform called "Apollo" at Ipsen. It didn't exist.
The slide read as plausible. It was wrong.
**Fix:** `NO_INVENTION.md`. Hardcoded zero-invention rule.

### Three Moves This Quarter · tone leak
A previous build left the consulting-pitch phrase "Three moves this quarter.
The rest is evidence." on the closer slide of a research brief.
**Fix:** Rule 6 above. Words like "moves" / "plays" / "horizons" / "levers" are
banned in research-register OOF work.

### The Bulk-Regex Miss · numeric blind spot
A previous build's bulk regex caught `r=0.929` but missed the bare `0.929` hero
stat in a 72pt callout. The slide carried stale data while looking refreshed.
**Fix:** Rule 2 above. Hand-verify every hero number. Build a CHANGE-LOG of
old→new values when refreshing a wave; sweep against it.

### The Mixed-Grammar Deck · two-source stapling
A previous build inherited a 36-slide deck assembled from two source decks with
different chrome and different page-numbering schemes (`NN/23` mixed with `NN/35`),
never reconciled. The deck shipped with two visual languages.
**Fix:** Rule 3 above. Single visual grammar end-to-end. Sweep chrome and page
numbers before delivery.

### The Substitute Manual · silent swap
When weasyprint couldn't render the canonical Design_System/index.html, a
previous build wrote a NEW intro doc instead of fixing the render — and shipped
it under the same name. The user reasonably objected.
**Fix:** Part 4 above. Never substitute silently. If something can't be done as
asked, say so and propose the alternative.

### The Cartoonish Closer · decorative geometry
A previous build added numbered bubbles, hard checkmark squares, and stand-in
photo blobs to a closer slide that already had a clean argument. "Awful and say
nothing." Shapes were doing decoration, not semantic work.
**Fix:** Design Rules above. Rounded, not cartoonish. If a shape isn't doing
semantic work, it doesn't earn its place.

### The Fluff Addition · feature-completism over editorial judgment
A previous build added 7 "demo" slides to a brief — pyramid, 9-box, trombinoscope,
waterfall, etc. — without asking what the existing deck was already arguing.
Some duplicated content already present; one slide contained 32 invented
people names (Apollo error). All 7 were dropped.
**Fix:** Mechanic rule 8 — editorial judgment beats feature-completism.
Read the artifact before changing it. Earn the change.

---

## Part 7 · The Grading Schema

Every handoff includes a self-grade out of 10 across six dimensions:

| Dimension | What it measures |
|---|---|
| **Argument clarity** | Can the reader state the argument after one read? |
| **Design impact** | Does the design carry the meaning, or compete with it? |
| **Tone of voice** | Is the register consistent end-to-end? No leaks? |
| **Data integrity** | Is every number traceable to the source? |
| **Editorial discipline** | Does every slide earn its place? |
| **Production craft** | Page numbers, chrome, spacing, alignment — is it tight? |

**8.5+ overall = shippable.** Below 8 = not yet finished.
The grade is honest. Inflation defeats the schema.
