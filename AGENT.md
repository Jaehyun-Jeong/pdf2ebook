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

- ENV WARNING: this session intermittently corrupts tool output, temp files, and
  even file-read display (saw binary garbage in a .txt; saw garbled line numbers
  in a source Read). The SOURCE ON DISK is fine (ast.parse OK). Do risky edits in
  a fresh/stable loop iteration; always re-run metric and re-render to confirm;
  regenerate any temp file that looks corrupted. Did NOT attempt #1/#2 inline due
  to this — left for a clean loop iteration.
