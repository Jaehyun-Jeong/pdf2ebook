# Fix Plan

One item per line, top = next. Larger font + stable printing, design preserved
(no reflow). Verify every change by metric + render. Commit only verified wins.

## Double-check findings (this restart)

Current delivered fonts: MIT 6.5pt (too small), LeCun 8.1pt, MonoBite 9.7pt;
all 0 blank pages, 0 off-page/clipped pages. Two printing defects found:

## To do

- [ ] **#1 MIT equations split across page boundaries (PRINTING DEFECT).**
      Rendered MIT p128→p129: equation (68) `TimeEmb(t) = [ ... ]^T` is fragmented
      — its tall matrix bracket starts at the bottom of p128 and the rows continue
      on p129. Root cause: an equation is many separate atoms (bracket pieces,
      matrix rows that are 'text', the eq number) that `region_blocks` does NOT
      cluster together, so `_Flow` breaks them at the page edge. Fix: cluster ALL
      atoms (text + fig) belonging to one equation/figure into a single block
      (e.g. merge atoms whose x-ranges overlap and are vertically adjacent, not
      just fig-fig). A block taller than the page already gets its own page scaled
      whole — so once clustered, the equation stays intact. Verify on MIT p128.
- [ ] **#2 MIT font too small (6.5pt).** Landscape fit of MIT's wide single
      column only reaches 6.5pt. To enlarge WITHOUT reflow, split each wide
      single-column page into TOP/BOTTOM sub-pages (vertical halves), each fitting
      the screen width → ~1.5-2x font (~9-10pt). Must NOT cut a text line or an
      equation: split only at whitespace between blocks (the _Flow already groups
      by atoms, so increasing effective width per sub-page is the lever). Keep
      reading order. Verify font goes up AND #1 stays fixed (no new splits).
- [ ] **#3 Minor: residual blank/clipped pages.** Metric pass-1: MIT blank=3,
      LeCun blank=2 + clipped_pages=1. Investigate the 1 LeCun clipped page
      (content bbox past page edge) and the handful of blanks; likely oversized-
      block pages or end-of-section. Low priority vs #1/#2.
- [ ] **#4 Re-verify all three** against acceptance: font as large as design
      allows, zero splits/blanks/clipping, MonoBite unchanged.

## Done

(moved here as completed; see FIXES.md for the running fix log)
- [x] empty pages eliminated, occluded text fixed, 2col tiny font fixed, landscape
      for wide single-column (prior iters 1-6; see git log).

## Known pitfalls

- Reflow is BANNED (destroys design). Use crop/fitw/2col + landscape only.
- Only merge FIGURE atoms was the old rule; #1 deliberately extends clustering to
  equation text atoms — be careful NOT to merge whole prose columns into one block
  (that caused a 112-page blowup before). Cluster only by tight overlap/adjacency.
- A parse-OK file can still NameError — always run a real conversion.
- Image render + temp-file writes drop/corrupt intermittently here. Re-run the
  metric; if a temp file looks like binary garbage, regenerate it. Gate commits on
  metric when images won't display, and note "visual pending".
