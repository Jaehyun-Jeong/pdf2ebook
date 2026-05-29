# Ralph Loop — Objective

Improve `pdf2ereader.py` until every PDF in `papers/` converts to a **perfectly
readable** 6" e-reader PDF: body font large enough to read comfortably, **no
text cut off or occluded** at page breaks, figures/tables kept intact (never
sliced through), and a clean, consistent layout. Verify by **rendering output
pages to images and looking at them** — not by trusting the code.

## The one rule

Each iteration, do **one** thing. Pick the single highest-value item from
`fix_plan.md`, do it, verify it *visually*, commit it, update the plan. Then stop.

## Environment

- Python: use `.venv/bin/python` (PyMuPDF is installed there).
- Convert:  `.venv/bin/python pdf2ereader.py "<input.pdf>" -o "<out.pdf>"`
- Render to inspect:  `.venv/bin/python render_samples.py "<out.pdf>" diag 150`
  then **Read the PNGs in `diag/`** to see the actual result.
- Test papers live in `papers/`; write outputs to `papers/ereader/`.
- The hardest case is `MonoBite_*` (two-column, figures) — the user flagged it
  for tiny font and occluded sentences. Always re-check it.

## Workflow each iteration

1. Read `AGENT.md` for accumulated context and gotchas.
2. Read `fix_plan.md`. Pick the **top unchecked** item.
3. Make the one change to `pdf2ereader.py` (or a helper).
4. **Verify visually**: reconvert the affected paper(s), run `render_samples.py`,
   and **Read the resulting PNGs**. Confirm the specific defect is gone and you
   did not introduce a new one (cut lines, overlap, shrunk text, sliced figure).
   Also sanity-check text is preserved (page count > 0, `get_text()` non-empty).
5. If it's better, commit with a message referencing the item. If it's worse or
   broke something, `git checkout -- pdf2ereader.py` and note why in AGENT.md.
6. Update `fix_plan.md`: check off done, add any new defects you saw in the PNGs.
7. Append anything future-you needs to know to `AGENT.md`.

## What "perfect" means (acceptance bar)

- Body text renders at roughly >= 8.5pt-equivalent on a 257x347pt page.
- No sentence/line is cut horizontally at a page boundary.
- No figure, table, or equation is split across pages or down the middle.
- No duplicated/overlapping text bands from slice overlap.
- Reading order is correct (left column fully, then right column).

## Guardrails

- One thing per iteration. Resist scope creep.
- Never trust the code over the rendered image. Always look.
- If a change breaks conversion, revert it rather than pile on fixes.
- Keep `fix_plan.md` ordered by priority; the top item is always next.
- Never edit `loop.sh` or `PROMPT.md` from inside the loop.

## Stopping

The loop runs until you stop it. When `fix_plan.md` is all checked and the
rendered pages of every paper in `papers/` meet the acceptance bar, stop.
