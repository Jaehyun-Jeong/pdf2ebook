# Fix Plan

One item per line, top = next. Gate every change on the coverage metric
(blank-page count must drop, text must not shrink) AND render + look when the
image display is working. Commit only verified improvements.

## To do

- [ ] **#1 Flow content CONTINUOUSLY across source pages (kills remaining
      blanks).** Right now `run_split` calls `emit_stacked` per region per source
      page, so each source page's leftover starts a fresh device page → ~1 partial
      page per source page (that's the bulk of the remaining 35 blanks in LeCun).
      Fix: collect blocks for the WHOLE document in reading order (per page:
      full-width spans / left col / right col via the existing region logic),
      then flow them through ONE continuous emit_stacked state so a new device
      page starts only when full — not at every source-page boundary. Expected:
      blank-page count → ~1 (only the very last page). Keep figures whole and
      reading order correct. Verify with coverage metric (blank<15% near 0).
- [ ] **#2 Check the MIT page growth (84→178).** With stacking, MIT text is now
      width-filled (bigger/more readable) which is good, but confirm visually it
      isn't *too* large / wasteful, and that #1 brings the page count back down by
      removing per-page partial pages. Re-measure after #1.
- [ ] **#3 Visual pass when image display works:** render a dense body page, a
      former-blank page, a figure page, and a 2-col page with a mid-page figure
      for each paper. Confirm: text readable, nothing cut, figures whole, reading
      order L→R. (Algorithm guarantees no cut lines, but eyeball figures/order.)
- [ ] **#4 Tune gap (currently 6pt cap).** If pages look cramped or loose after
      #1, adjust `max_gap` in `emit_stacked` and the small intra-paragraph gap.

## Done

- [x] **Occluded / cut sentences** — region_atoms + pack_slices. (ba45f17 iter1)
- [x] **Tiny font on 2-col** — two_col_regions band-segmentation. (d122f9e iter2)
- [x] **Top-align + margin** — emit_region top-align. (3759cd9 iter3)
- [x] **Atom-stacking emitter (collapse whitespace within a page)** —
      region_blocks + emit_stacked replace pack_slices+emit_region in the split
      path. Metric: LeCun blank 44→35, MonoBite 12→9, density up. (iter4)
      Remaining blanks are per-source-page partials → item #1.

## Known pitfalls

- Only merge FIGURE atoms; merging text lines makes a column one giant tiny block.
- A parse-OK file can still NameError — always run a real conversion.
- Image render output drops intermittently in this session; gate on the
  text-based coverage metric and note when visual confirmation is pending.
- emit_stacked currently resets per region/page — that's the #1 thing to change.
