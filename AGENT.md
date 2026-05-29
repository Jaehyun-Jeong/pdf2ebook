# AGENT.md — cross-iteration memory

Things future iterations need to know. The loop appends here; humans curate.

## Architecture / where things are

- `pdf2ereader.py` — the whole tool. Key functions:
  - `page_content_bbox()` / `stable_crop_boxes()` — margin detection (even/odd,
    outlier-trimmed). Crop is solid; leave it unless evidence says otherwise.
  - `detect_column_split()` — whitespace-gutter heuristic for 2-column pages.
  - `slice_fit_width()` — **prime suspect for occluded text.** Cuts by geometry,
    not by line gaps. This is where most readability bugs live.
  - `emit_region()` — places a clip onto a device-sized page (aspect-fit,
    centered). Centering causes inconsistent vertical position page-to-page.
  - `run_crop()` / `run_split()` — the three modes (crop / fitw / 2col).
  - `choose_mode()` — auto mode: 2col if >=50% pages two-column, else crop if
    estimated on-device font >= --min-font (8.5pt) else fitw.
- `render_samples.py` — render output pages to `diag/*.png` for visual checks.
- Device target: 6" => 257.3 x 347.5 pt (`kindle6` preset, the default).

## How to verify (do this every iteration)

1. `.venv/bin/python pdf2ereader.py "papers/<file>.pdf" -o "papers/ereader/<file>.pdf"`
2. `.venv/bin/python render_samples.py "papers/ereader/<file>.pdf" diag 150`
3. **Read** the `diag/*.png` files and judge against PROMPT.md's acceptance bar.

## Gotchas discovered

- Inputs have Windows `:Zone.Identifier` sidecar files. Glob only real `*.pdf`
  (use `find papers -iname '*.pdf'`), never the sidecars.
- fitw/2col re-embed source pages per slice → output can be large (MIT ~13MB).
  Acceptable, but the slice-overlap duplication makes it worse; fixing overlap
  helps size too.
- Initial visual diagnosis (current outputs):
  - MonoBite (2col): tiny font on the title/abstract page; figures sliced;
    sentences cut at page breaks. **Worst case — always re-check.**
  - MIT & LeCun (fitw): text legible but lines cut at slice boundaries.

## Conventions to follow

- Keep text vector/selectable (no rasterizing). Verify `get_text()` non-empty.
- One behavior change per commit; message references the fix_plan item.
- Don't touch the crop logic to fix a slicing bug — fix the slicer.
