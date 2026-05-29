# Fixes log

Running log of printing problems found and fixed by the Ralph loop. Newest last.
Format: `iter N (<commit>): FIXED <problem> — <how> — verified by <metric/render>.`

## Diagnosed (not yet fixed) — found in double-check pass 2026-05-29

- MIT: equation (68) split across p128→p129 (tall matrix bracket fragmented).
  Cause: equation atoms not clustered → _Flow breaks them at page edge.
- MIT: body font only 6.5pt (too small). Needs wide-page top/bottom split to
  enlarge without reflow.

(Loop iterations append their FIXED lines below.)

iter (84a16a9): FIXED MIT display equations scattered vertically (eq 68/69 on
src p41) — _merge_rects made anisotropic (infl_x=16, infl_y=1) so all atoms on
one equation row fuse into a single block placed intact, while stacked prose
lines stay separate — verified by render (eq 68/69 now one clean line each) +
metric (pages 179->158, clipped 124->89, blank 0->1 trailing page-number page,
font 6.5pt unchanged, no blowup).
