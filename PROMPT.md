# Ralph Loop — Objective (retargeted 2026-05-29)

**Maximize the MIT e-reader body font toward 8pt on the 6" device, preserving
the EXACT original design (no reflow, no line cuts).** The user wants 8pt and the
same design. Squeeze every design-preserving geometric lever first; only stop
once the font sits at its true measured maximum AND printing is defect-free.

## Honest constraint (do not ignore, do not hide)

MEASURED: MIT body is a genuine full-width single column — body/prose lines reach
~497pt; the trimmed crop is ~508pt. The 6" landscape long edge is 347.5pt. So the
absolute whole-line scale ceiling is `usable_width / line_width`. At the current
6pt device margin: 335.5/497 ≈ 0.675 → ~6.75pt. With margins driven to ~0:
347.5/497 ≈ 0.70 → ~7.0pt. **A true 8pt would need ~398pt of screen width — the
6" device does not have it.** 8pt is therefore only reachable by reflow (banned)
or a wider device (user chose to stay 6"). So:

- The target is 8pt; the REALISTIC ceiling on 6" is ~7pt. Push to that ceiling.
- DO NOT stop at 6.54pt citing the old "6.6pt ceiling" until you have actually
  implemented and verified the margin/crop levers below. The prior loop declared
  the ceiling WITHOUT minimizing device margins or cropping to the true text bbox.
- When you reach the true geometric max, STOP and DOCUMENT the achieved font and
  the exact reason 8pt is unreachable on 6" (one short paragraph in FIXES.md).
  Never claim 8pt if the render/metric does not show it.

## The font levers to exhaust (each = one iteration, verify before commit)

1. **Minimize device margin.** `PAGE_MARGIN` is currently 6pt; the content is
   width-fit, so every margin point shrinks the font. Try 2pt (or 0–1pt) and
   re-measure. Verify nothing touches/!clips the page edge.
2. **Crop to the TRUE text bbox, not the inflated crop.** If `stable_crop_boxes`
   leaves slack beyond the real text column (crop 508 vs text 497), fitting to the
   true column raises scale. Verify no real glyph is trimmed.
3. **Per-region width-fit (if not already).** Don't let a single rare wide element
   (a full-width display equation, a wide figure, a header band) force the WHOLE
   page to a smaller scale than the body prose needs. Fit narrow body regions to
   the screen on their own where it doesn't break reading order. Verify wide
   elements are NOT clipped (scale them whole if oversized).

After each: re-measure median on-device body font and confirm it went UP with
zero new defects. Stop when further levers yield <0.1pt or would break design.

## What "stable printing" means (unchanged — no regressions)

No text line cut at a page/sub-page boundary; no equation/figure/table split; no
near-empty pages; no duplicated bands; no content clipped off the edge; correct
reading order. The equation-integrity, furniture-strip, and callout-box fixes are
DONE — do not regress them (see AGENT.md / fix_plan.md "Done").

## Environment

- Python: `.venv/bin/python` (PyMuPDF). Input: `papers/MIT_flow_matching_diffusion.pdf`.
- Convert (design-preserving only — crop / fitw / 2col, NEVER reflow):
  `.venv/bin/python pdf2ereader.py "papers/MIT_flow_matching_diffusion.pdf" --mode fitw -o /tmp/out.pdf`
- Render to inspect: `.venv/bin/python render_samples.py /tmp/out.pdf diag 150`
  then **Read** `diag/*.png`.
- Metric: per output page compute content-bbox coverage AND median on-device font
  size (pt); scan for blank pages (<15% coverage). Goal: median body font UP toward
  ~7pt, blank pages 0, coverage healthy, zero clipped pages.
- Deliverable: regenerate `papers/ereader/MIT_flow_matching_diffusion.ereader.pdf`
  from the improved tool on the iteration that lands the best font.

## Workflow each iteration

1. Read `AGENT.md` and `fix_plan.md`.
2. Pick the top item in `fix_plan.md` "To do". Make ONE change to `pdf2ereader.py`.
3. `ast.parse` AND run a real conversion (a parse-OK file can still NameError).
4. Verify: metric (font UP, no new blanks/clips) + render and Read a dense body
   page, an equation page, a figure page. Confirm font rose and nothing broke.
5. Better → commit referencing the item + append a "FIXED: ..." line to FIXES.md.
   Worse/broken → `git checkout -- pdf2ereader.py`, note why in AGENT.md.
6. Update `fix_plan.md` and `AGENT.md`. Regenerate the deliverable on the best iter.

## Acceptance / stopping

Stop when the median body font is at its true geometric maximum on the 6" device
(all three levers exhausted; further change yields <0.1pt or would break design),
printing defects are zero, AND two consecutive double-check passes find nothing
new. Record the achieved font and — if it is below 8pt — the exact geometric
reason 8pt is impossible on 6" without reflow.

## Guardrails

- One change per iteration. Verify before commit. Never claim a font you did not
  measure AND render this iteration.
- Reflow is BANNED. Line-cutting (left/right split of a text column) is BANNED.
- Never edit `loop.sh` or `PROMPT.md` from inside the loop.
- If image display drops, gate commits on the metric and note "visual pending".
