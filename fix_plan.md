# Fix Plan

One item per line, top = next. Gate every change on the coverage metric
(blank-page count must drop, text must not shrink) AND render + look when image
display works. Commit only verified improvements.

## To do

- [ ] **Visual confirmation pass** (when image display is reliable): for each
      paper render a dense body page, the title page, a figure page, and a 2-col
      page with a mid-page figure. Confirm text readable, nothing cut, figures
      whole, reading order L→R. Metric is already green (blanks ~0); this is the
      eyeball sign-off.
- [ ] **Tune gaps if needed** — `_Flow.INTRA_GAP` (6pt) / `REGION_GAP` (5pt). If
      pages look cramped or too airy after the visual pass, adjust.
- [ ] **Optional cleanup** — remove now-unused `pack_slices`,
      `screen_height_src`, `emit_stacked`, `emit_region` (the continuous `_Flow`
      replaced them in the split path; crop mode uses none).

## Done

- [x] **Occluded / cut sentences** — region_atoms + pack_slices. (ba45f17 iter1)
- [x] **Tiny font on 2-col** — two_col_regions band-segmentation. (d122f9e iter2)
- [x] **Top-align + margin** — emit_region top-align. (3759cd9 iter3)
- [x] **Collapse whitespace within a page** — region_blocks + emit_stacked. (iter4)
- [x] **#1 EMPTY PAGES ELIMINATED — continuous cross-page flow** — `_Flow`
      streams blocks across the whole document; a new device page starts only
      when full, not per source page. Metric: blank(<15%) pages LeCun 44→0,
      MonoBite 12→1, MIT 0→0; median coverage 88–100%; page counts DOWN
      (LeCun 124→72, MIT 178→138); text preserved. (iter5)

## Known pitfalls

- Only merge FIGURE atoms; merging text lines makes a column one giant tiny block.
- A parse-OK file can still NameError — always run a real conversion.
- Image render output drops intermittently here; gate on the coverage metric and
  note when visual confirmation is pending.
