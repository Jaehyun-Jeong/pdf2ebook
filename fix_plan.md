# Fix Plan

One item per line. Ordered by priority — top item is what the next loop does.
Seeded from a visual diagnosis of the current outputs (rendered at 150 dpi).

## To do

- [ ] **Stop slicing through text lines.** `slice_fit_width()` cuts at fixed
      geometric y-positions with a 4% overlap, so cuts land in the middle of a
      line → half-cut letters / occluded sentences at every page break. Snap
      each slice boundary to a whitespace gap *between* text lines: collect line
      bboxes via `page.get_text("dict")` (or a horizontal pixel projection
      profile), and choose the largest blank band near the target cut height.
- [ ] **Keep figures/tables whole.** Detect blocks that are images/drawings (or
      full-width regions) and never cut through them. If a figure is taller than
      one screen, scale it to fit a single page on its own rather than slicing.
- [ ] **Fix tiny font on column-detection-miss pages.** When `detect_column_split`
      returns None on a clearly multi-column paper (e.g. title/abstract page),
      the whole wide page is fit by min-scale → tiny. Fall back to fit-to-width
      (slice vertically) instead of min-scale fit for any page wider than the
      device aspect.
- [ ] **Remove duplicate text bands.** The 4% slice overlap repeats a strip of
      text on consecutive pages. Once cuts snap to line gaps, drop the overlap
      (or make it exactly one blank gap) so nothing is shown twice.
- [ ] **Two-column reading order + full-width spans.** In `2col`, emit left
      column (all its slices) then right column. Detect elements that span both
      columns (wide figures, section headers, abstract) and emit them as their
      own full-width page in reading order, not split down the gutter.
- [ ] **Consistent margins / prettiness.** Small uniform margin, content
      top-aligned (not vertically centered) so successive pages line up; avoid
      large letterbox bands.
- [ ] **Re-verify all three papers** (MonoBite, MIT, LeCun) end-to-end against
      the acceptance bar in PROMPT.md and record per-paper status in AGENT.md.

## Done

(checked items move here)
