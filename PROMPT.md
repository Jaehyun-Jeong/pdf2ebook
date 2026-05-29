# Ralph Loop — Objective

Make the e-reader output font **larger** while keeping **stable, correct
printing** (rendering/layout) — and preserve each paper's original design
(no reflow). Find printing problems, fix ONE per iteration, verify visually +
by metric, commit, and record what you fixed. Repeat until two consecutive
checks find no problem.

## The one rule

Each iteration: read state, pick the SINGLE top item in `fix_plan.md`, make one
change to `pdf2ereader.py`, verify it, commit, update the plan. Then stop.

## What "larger font + stable printing" means

- Target on-device body font ~9-10pt where possible WITHOUT reflow (reflow is
  banned — it destroys the design; see AGENT.md).
- The known hard case is **MIT** (~6.5pt landscape): its text column is too wide
  to enlarge by rotation alone. The agreed approach is to **split each wide
  single-column page into top/bottom (or left/right) sub-pages** so each sub-page
  fills the screen → roughly doubles the font, equations stay intact.
- "Stable printing" = NO printing defects:
  - no text line cut horizontally at a page/sub-page boundary,
  - no equation/figure/table split across pages,
  - no near-empty pages, no duplicated bands,
  - no content clipped off the page edge, correct reading order.

## Environment

- Python: `.venv/bin/python` (PyMuPDF installed).
- Convert (design-preserving modes only — crop / fitw / 2col, never reflow):
  `.venv/bin/python pdf2ereader.py "<in.pdf>" --mode fitw -o /tmp/out.pdf`
- Render to inspect: `.venv/bin/python render_samples.py /tmp/out.pdf diag 150`
  then **Read** `diag/*.png`.
- Metric (reliable even when image display drops): per output page compute
  content-bbox coverage and median on-device font size; also scan for blank
  pages (<15% coverage). Goal: font UP, blank pages ~0, coverage healthy.
- Papers in `papers/`. Deliverables in `papers/ereader/`.
- MonoBite is the reference (9.7pt, portrait) — keep it good; focus on MIT/LeCun.

## Workflow each iteration

1. Read `AGENT.md` and `fix_plan.md`.
2. **Double-check pass (required at restart):** before changing anything, render
   and inspect the CURRENT delivered outputs for printing problems TWICE
   (two independent looks / two papers or two page-sets). List any problem found
   in `fix_plan.md`. If two consecutive checks find nothing, STOP — done.
3. Pick the top item. Make ONE change to `pdf2ereader.py`.
4. `ast.parse` AND run a real conversion (a parse-OK file can still NameError).
5. Verify: metric (font larger, no new blanks) + render and Read pages (a dense
   body page, an equation page, a figure page). Confirm the specific defect is
   gone and nothing new broke.
6. Better → commit referencing the item, and write a one-line "FIXED: ..." note.
   Worse/broken → `git checkout -- pdf2ereader.py`, note why in AGENT.md.
7. Update `fix_plan.md` and `AGENT.md`.

## Report what you fixed

Each iteration that commits, append a line to `FIXES.md` (create if missing):
`iter N (<commit>): FIXED <problem> — <how> — verified by <metric/render>.`

## Acceptance / stopping

Stop when: body font is as large as design-preservation allows (MIT split to
~9-10pt), there are zero printing defects, AND two consecutive double-check
passes find no new problem. Keep MonoBite intact.

## Guardrails

- One change per iteration. Verify before commit. Never claim a result you did
  not render/measure this iteration.
- Reflow is banned (design must be preserved).
- Never edit `loop.sh` or `PROMPT.md` from inside the loop.
- If image display drops, gate commits on the metric and note "visual pending".
