# Ralph Loop — Objective

Make `pdf2ereader.py` produce e-reader PDFs with **no wasted space**: eliminate
near-empty pages and large empty regions within a page, while keeping the best
possible human readability (big-enough text, nothing cut mid-line, figures
whole). Verify by **rendering output pages and looking at them** — never trust
the code over the image.

## The one rule

Each iteration, do **one** thing. Pick the single top item from `fix_plan.md`,
do it, verify it *visually* and with the coverage metric, commit it, update the
plan. Then stop.

## Why pages are empty right now (root cause)

The split modes (`fitw`, `2col`) currently render each slice as a rectangular
clip of the *source* page (`emit_region` + `pack_slices`). Sparse source pages
(title page, a lone trailing line + page number, a short last slice) become
near-empty output pages, and big vertical gaps in the source are reproduced as
blank bands. The fix is to stop copying rectangular slices and instead **flow
content blocks onto output pages with collapsed whitespace.**

## The fix (top of fix_plan)

Replace `pack_slices` + `emit_region` (in the split path of `run_split`) with an
**atom-stacking emitter**:

1. `region_atoms(page, region)` already returns indivisible units. Tag each as
   text-line vs figure (image/drawing).
2. **Merge** nearby figure atoms into one composite figure block (so a figure
   built from many sub-drawings is never split). Leave text lines separate so
   they can flow across pages.
3. **Stack** blocks top-to-bottom onto device pages: scale to fill the width
   (`scale = (dev_w - 2*margin) / region.width`); place each block at a running
   y with a SMALL gap (preserve a little inter-paragraph spacing, but CAP large
   source gaps — e.g. `gap = min(source_gap*scale, ~6pt)`); start a new page
   when the next block won't fit. A block taller than a page gets its own page,
   scaled down whole.
4. Preserve each block's horizontal offset within the region so centered titles
   stay centered and columns stay aligned.

Watch out: do NOT merge adjacent *text lines* into one block — that turns a whole
column into one giant block that scales to one tiny page. Only merge figure
atoms. (This was a real bug in a prior attempt that produced 112 pages.)

## Environment

- Python: `.venv/bin/python` (PyMuPDF installed).
- Convert:  `.venv/bin/python pdf2ereader.py "<in.pdf>" -o /tmp/out.pdf`
- Render:   `.venv/bin/python render_samples.py /tmp/out.pdf diag 150` then Read `diag/*.png`.
- Coverage metric (text-based, robust if image display is flaky):
  for each output page compute content-bbox area / page area; report median
  coverage and count of pages under 15% (those are the "empty" pages). The goal
  is median coverage UP and blank-page count → 0, WITHOUT shrinking text.
- Test papers: `papers/*.pdf`. Hardest: `MonoBite_*` (2-col, many figures).

## Workflow each iteration

1. Read `AGENT.md` and `fix_plan.md`. Pick the top unchecked item.
2. Make the one change to `pdf2ereader.py`.
3. `ast.parse` it AND actually convert a paper (a parse-OK file can still
   NameError at runtime — always run a real conversion).
4. Verify: run the coverage metric (blank-page count should drop, text not
   shrink) AND render + Read a few pages (a dense body page, the title page, a
   former blank page). Confirm no cut lines, figures whole, text readable.
5. Better? Commit referencing the item. Worse/broken? `git checkout -- pdf2ereader.py`.
6. Update `fix_plan.md` (check off, add new findings) and `AGENT.md` (gotchas).

## Acceptance bar

- No output page under ~15% content coverage (no near-empty pages).
- No large empty band inside a page (source gaps collapsed).
- Body text still fills the width at readable size; nothing cut mid-line;
  figures/tables/equations intact and whole.
- Reading order correct (2-col: left column, then right).

## Guardrails

- One thing per iteration. Verify before committing. Never claim a result you
  did not render and view this iteration.
- If image display is dropping output, fall back to the coverage metric to gate
  commits, and note in AGENT.md that visual confirmation is pending.
- Never edit `loop.sh` or `PROMPT.md` from inside the loop.

## Stopping

Stop when the acceptance bar is met on all three papers and `fix_plan.md` is
clear.
