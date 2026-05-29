# Fixes log

Running log of printing problems found and fixed by the Ralph loop. Newest last.
Format: `iter N (<commit>): FIXED <problem> — <how> — verified by <metric/render>.`

## Diagnosed (not yet fixed) — found in double-check pass 2026-05-29

- MIT: equation (68) split across p128→p129 (tall matrix bracket fragmented).
  Cause: equation atoms not clustered → _Flow breaks them at page edge.
- MIT: body font only 6.5pt (too small). Needs wide-page top/bottom split to
  enlarge without reflow.

(Loop iterations append their FIXED lines below.)
