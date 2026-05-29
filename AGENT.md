# AGENT.md — cross-iteration memory

Things future iterations need to know. The loop appends here; humans curate.

## Architecture / where things are

- `pdf2ereader.py` — the whole tool. Key functions:
  - `page_content_bbox()` / `stable_crop_boxes()` — margin detection (even/odd,
    outlier-trimmed). Solid; leave alone unless evidence says otherwise.
  - `region_atoms()` — indivisible units (text *lines*, images, drawings) in a
    region. The granularity that page breaks must respect.
  - `pack_slices()` — groups atoms into screen-height slices, cutting only
    between atoms (no line ever bisected, no overlap). Oversized atom (big
    figure) goes alone and is scaled down whole.
  - `two_col_regions()` + `estimate_gutter()` + `_merge_y_bands()` — 2-col layout:
    full-width spans become their own full-width region; column bands split
    left-then-right. This is what fixed MonoBite's tiny font.
  - `emit_region()` — places a clip on a device page, width-fit, top-aligned,
    6pt margin (`PAGE_MARGIN`).
  - `run_crop()` / `run_split()` — the three modes. `choose_mode()` — auto.
- `render_samples.py` — render output pages to `diag/*.png` for visual checks.
- Device target: 6" => 257.3 x 347.5 pt (`kindle6` preset, default).

## How to verify (do this EVERY iteration — do not skip)

1. `.venv/bin/python pdf2ereader.py "papers/<file>.pdf" -o /tmp/test.pdf`
2. `.venv/bin/python render_samples.py /tmp/test.pdf diag 150`
3. **Read** the `diag/*.png` and judge against PROMPT.md's acceptance bar.
4. Check text preserved: `get_text()` non-empty, page_count > 0.
Only commit after the render actually looks right. Never claim a result you
have not rendered and viewed this iteration.

## Gotchas discovered

- Inputs have Windows `:Zone.Identifier` sidecars. Glob real `*.pdf` only.
- Edits fail silently if `old_string` indentation doesn't match — the file uses
  4-space indent, no tabs. After any edit, run `ast.parse` AND actually convert
  a paper; a parse-OK file can still NameError at runtime.
- fitw/2col re-embed source pages per slice → large output (MIT ~21MB). Fine for
  USB; under the 200MB Send-to-Kindle limit.
- A full-width text line is ~535pt wide; fitting it to a 257pt screen is ~0.48x
  (small). That's why full-width title bands are small — inherent, not a bug.
  Column-width body text fills the screen and is readable.

## Iteration log (verified, real)

- iter1 (b918f76): region_atoms + pack_slices — fixes cut/occluded lines.
- iter2 (03c9f1f): two_col_regions band-segmentation — fixes 2-col tiny font.
- iter3: emit_region top-align + 6pt margin — consistency/prettiness.

## Conventions

- Keep text vector/selectable (no rasterizing).
- One behavior change per commit; message references the fix_plan item.
- Don't touch crop logic to fix a slicing bug — fix the slicer.

## iter4 note (atom-stacking)
- run_split split path now: region_blocks() (tag text/fig, merge ONLY fig atoms)
  + emit_stacked() (flow blocks, gap cap 6pt, new page when full, oversized fig
  alone). Metric improved LeCun/MonoBite blanks & density; MIT pages 84->178
  (text now width-filled = bigger, likely more readable).
- KEY REMAINING INSIGHT: emit_stacked resets state per region per source page,
  so every source page leaves a partial last device page -> most remaining blank
  pages. fix_plan #1 = one continuous flow across the whole doc. That's the big
  remaining win to "fill the empty pages".
- pack_slices / screen_height_src / emit_region are now UNUSED by the split path
  (kept for reference / crop mode uses none of them). Safe to remove later.

## Restart 2026-05-29 (objective: larger font + stable printing)
- Double-check found 2 real defects in delivered MIT: (1) eq (68) split across
  p128->p129 (tall equation fragmented at page edge); (2) font only 6.5pt.
- LeCun 8.1pt, MonoBite 9.7pt, all 0 blank / 0 clipped. fix_plan #1=eq integrity
  (cluster equation atoms), #2=top/bottom split MIT wide pages for bigger font.
## iter 2026-05-29 (eq integrity — fix_plan #1 DONE, commit 84a16a9)
- papers/ now holds ONLY MIT (LeCun/MonoBite gone). papers/ereader/ regenerated.
- Root cause of "equation split": NOT a page-boundary cut. PyMuPDF's get_text
  splits a display-equation ROW into many separate 'line' atoms (TimeEmb(t)=,
  cos(...), ···, sin(...), tall brackets) on ONE horizontal band with ~10pt gaps.
  region_blocks' `_merge_rects(texts, 1.0)` (1pt isotropic) never fused them, so
  _Flow stacked each fragment vertically -> equation scattered down the page.
- Fix: `_merge_rects` now (infl_x, infl_y); text uses (16, 1) — wide horizontal
  reach fuses a whole equation row into ONE block (placed intact, internal 2D
  layout preserved by the clip); tiny vertical keeps stacked PROSE lines separate
  (they're already single full-width atoms) so they still flow -> NO page blowup.
- Verified: eq (68)/(69) render as one clean line each; Algorithm-3 page clean;
  pages 179->158, clipped 124->89, font 6.5pt (unchanged — font size is #2).
  Only new "blank" page = trailing source page-number "84" on its own page (benign).
- NEXT (fix_plan #1 is now #2): MIT font still 6.5pt. To enlarge w/o reflow, split
  each wide single-col page into top/bottom sub-pages so each fills the screen.

## iter 2026-05-29 (header/footer furniture — fix #3 DONE)
- Double-check (6 parallel inspectors over a dense render sample) found REAL
  defects beyond font: HIGH — blank trailing page (only "84"), orphaned eq band
  on one page; MED — section heading duplicated below the page number (p035 "3.3
  Learning the Marginal Vector Field", p056 "4.3 Score Matching").
- ROOT CAUSE: source has a running header at y0≈44.4 (5.6% — section num+name on
  every page) and a centered page-number footer at y≈710-723 (89.7%). The crop's
  trimmed-union includes both bands, so region_blocks extracted them as text
  atoms and _Flow placed them → duplicated heading bands + isolated page-number
  pages. (Body runs y≈82.8→700, i.e. 10.5%→88%.)
- FIX: new _is_furniture() drops (a) any text line with y0 < 7% of source page
  height (running header) and (b) pure-number lines (arabic/roman) in the top OR
  bottom margin (page numbers); applied in region_blocks before merge/flow. The
  numeric gate protects footnotes (y≈85%, non-numeric); 7% top band sits safely
  above the 10.5% body start so no real first line or section heading is lost
  (real headings live mid-body, e.g. src p18 y613). Verified: pages 158->148,
  blank 0, lone-number pages 3->0, font 6.54pt unchanged, eq/fig/TOC/title intact.
- NOTE: get_text on the OUTPUT still reports the dropped furniture text — it
  lives in the clipped show_pdf_page XObject layer (not visible). Trust the
  RENDER, not get_text, when checking for visible duplicates/blanks.

## iter 2026-05-29 (near-empty page — callout-box fill — fix #6 DONE)
- Double-check via parallel vision inspectors (workflow) called all 32 sampled
  pages CLEAN — but the METRIC caught output p75 at <1.5% ink (the one blank).
  LESSON: vision agents rationalize whitespace as "section end"; trust the metric
  for near-empty pages. p75 held only a lead-in line + 1 equation while p76
  CONTINUED the same derivation = a real stranded-content defect, not a section end.
- ROOT CAUSE (instrumented /tmp/diag_flow.py + diag_pages.py): this MIT textbook
  renders Remark/Definition/Example callouts as a big vector FILL rect behind the
  text (e.g. src p43 fill 98% crop-w x 72% crop-h). region_blocks added that fill
  to `figs`; the text-absorb step folded all 57 enclosed prose lines into it ->
  one 518.6pt block -> _Flow.add oversized branch placed it ALONE on its own page,
  scaled to ~4.6pt (smaller than 6.5pt body!), and stranded the previous page.
  6 such boxes doc-wide (src p17,21,32,43,48,62; ALL 0 images, 57-108 lines).
- FIX: region_blocks drops a drawing rect with w>=0.9*region.w AND h>=0.45*region.h
  AND >=6 enclosed text lines (background tint, not a figure). The enclosed prose
  then flows at body size; the shade still shows through per-line show_pdf_page
  clips so design is preserved (NO reflow — line positions unchanged). Verified:
  blank 1->0, min cov 0.4%->1.95%, font 6.54pt unchanged, Figure 14 (p73) intact.
- NOTE for next double-check: p54 (Example 23 short box, ~1.95% cov) is a SMALL
  callout below the 0.45-height threshold — kept whole as a unit, legit section
  end, NOT a defect (was low-cov before this fix too). Don't chase it.

## FONT CEILING (important — stops chasing an impossible target)
- MIT body = genuine FULL-WIDTH single column: prose lines ~497pt, crop ~508pt.
  Landscape long edge 347.5pt → max whole-line scale 335.5/508 = 0.66 → 6.6pt.
  TOP/BOTTOM split keeps line width → NO font gain. LEFT/RIGHT split would give
  ~13pt but CUTS every line = banned defect. Margins buy only +0.2pt. So ~6.6pt
  IS the design-preserving ceiling; the old "split MIT to 9-10pt" goal is
  geometrically impossible without reflow (banned). Treat font axis as DONE.

## iter 2026-05-29 (detached equation numbers — fix_plan #5 DONE)
- Double-check pass 2 (page set 20/40/60/90/110/130) was NOT clean: out p130
  showed eq numbers (115)-(118) stacked detached in the right-margin dead space
  below their equation; #5 had predicted this for 125/126/127. So we did NOT stop.
- ROOT CAUSE (instrumented region_blocks on src p73): display-eq labels "(n)" sit
  at x0=531.7, a ~25pt alignment gap past the eq body's right edge (~506) — wider
  than the text merge reach (infl_x=16) — so they never fused. Each flowed as a
  lone atom AFTER the (often multi-row, tall-integral-chained) merged equation
  block, so all the numbers stacked below the equation. WORSE: when the eq block's
  OWN merged bbox already reached x=554 (the margin), the number showed through the
  block's clip AND flowed separately => DUPLICATED numbers (seen p129/p130 first try).
- FIX: region_blocks sets aside any lone "(n)"/"(n.m)" line (EQNUM_RE) whose x0 is
  in the right 25% of the region, then re-attaches each to the block straddling the
  number's vertical centre whose left edge is at/left of it (pick the WIDEST such
  block), via bbox union — the number rides in that block's clip at its true 2D
  position (NO reflow). TWO bugs found & fixed mid-iter: (a) sequential absorption
  grew the block past later numbers -> compute all targets against the UNMUTATED
  block list first; (b) the original `br.x1 <= num.x0` left-guard rejected tall eq
  blocks already touching the margin (leaving the number to duplicate) -> guard is
  now `num.x0 >= br.x0 - 2` (number not LEFT of the block), so a no-op union still
  consumes the stray atom. Verified: out p124-127 eq 115-131 each on its own row,
  0 detached/duplicated; TOC page numbers ("3"/"4", no parens) NOT misattached;
  eq (70)/Remark 29/Figure 14/Summary 45 intact. Metric pages 149->142 (~7 stranded
  number-lines collapsed back), font 6.54pt unchanged, blank 0, cov med 96.3%.
- NEXT: #4 re-verify. Pass 2 was dirty this iter, so the two-consecutive-clean
  counter resets; next loop must double-check from scratch before any STOP.

- ENV WARNING: this session intermittently corrupts tool output, temp files, and
  even file-read display (saw binary garbage in a .txt; saw garbled line numbers
  in a source Read). The SOURCE ON DISK is fine (ast.parse OK). Do risky edits in
  a fresh/stable loop iteration; always re-run metric and re-render to confirm;
  regenerate any temp file that looks corrupted. Did NOT attempt #1/#2 inline due
  to this — left for a clean loop iteration.
