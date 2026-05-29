# Fix Plan

One item per line, top = next. Verify every change by (a) the coverage metric
and (b) rendering pages and LOOKING. Commit only what you verified.

## To do

- [ ] **#1 Fill empty pages / empty space (atom-stacking emitter).** Replace
      `pack_slices` + `emit_region` in the split path of `run_split` with a
      stacking emitter that FLOWS content blocks onto device pages with collapsed
      whitespace (see PROMPT.md "The fix" for the full algorithm). Tag atoms
      text vs figure; MERGE only figure atoms into composite blocks (NOT text
      lines — merging text lines caused a 112-page blow-up before); stack blocks
      top-to-bottom, small capped gaps, new page when full, oversized block alone
      scaled whole; preserve horizontal offset within the region. Acceptance:
      zero pages under ~15% coverage, no big internal blank bands, text not
      shrunk, figures whole, lines never cut. Verify on all three papers.
- [ ] **#2 Tune spacing for readability.** Once stacking works, pick an
      inter-block gap that looks natural (not cramped, not loose) — try a small
      constant (~4-6pt device) plus a slightly larger gap when the source gap was
      large (paragraph/section breaks). Render and eyeball.
- [ ] **#3 Re-verify reading order** on a 2-col page with a mid-page figure:
      left column, right column, spanning figure at its y-position.

## Done

- [x] **Occluded / cut sentences** — `region_atoms` + `pack_slices`: cut only
      between atoms, never through a text line. (commit ba45f17 iter1)
- [x] **Tiny font on 2-col pages** — `two_col_regions` band-segmentation: full-
      width spans kept whole, column bands split L-then-R; body text fills a
      column. (commit d122f9e iter2)
- [x] **Top-align + margin** — `emit_region` top-aligns with 6pt margin.
      (commit 3759cd9 iter3) — NOTE: this is what leaves blank space on sparse
      pages; #1 replaces this path with stacking.

## Known pitfalls (from prior attempts)

- Merging adjacent TEXT lines → whole column becomes one giant block → scaled to
  one tiny page. Only merge FIGURE atoms.
- A parse-OK file can still NameError at runtime — always run a real conversion,
  not just ast.parse.
- Tool output / image display has been intermittently dropping in this repo;
  gate commits on the text-based coverage metric when images won't render.
