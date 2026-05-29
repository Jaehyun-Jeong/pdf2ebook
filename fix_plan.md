# Fix Plan

One item per line, top = next. Larger font + stable printing, design preserved
(no reflow). Verify every change by metric + render. Commit only verified wins.

## Double-check findings (this restart)

Current delivered fonts: MIT 6.5pt (too small), LeCun 8.1pt, MonoBite 9.7pt;
all 0 blank pages, 0 off-page/clipped pages. Two printing defects found:

## To do

(empty — acceptance met; see STOP below)

## STOP — acceptance met (2026-05-29)

- [x] **#4 Re-verify against acceptance — DONE, two consecutive clean passes.**
      Fresh double-check (no code change this iter): regenerated /tmp/mit.pdf and
      rendered TWO independent page-sets — pass1 {0,12,40,70,100,130}, pass2
      {6,25,55,85,115,141}. BOTH clean: equations intact, eq numbers attached,
      figures whole (Fig 8 dual-image, DiT diagram), callout boxes (Thm 3, Ex 4,
      Key Idea 2/3, Remark 32, Summary 45) flow at body size, TOC + references
      clean, no duplicated header/footer, no trailing furniture page, correct
      reading order. Metric: 142 pages, font 6.54pt (at the ~6.6pt design-preserving
      ceiling), 0 blank, coverage median 96.3% / min 52.23% (p100 = clean paragraph
      end, not stranded). Font axis already resolved as not-further-achievable
      without banned reflow (see below). => Two consecutive clean double-checks +
      clean metric => STOP. Loop objective complete.

## Resolved / not-actionable

- **#2 MIT font (was "split to 9-10pt") — NOT ACHIEVABLE without reflow.**
  MEASURED: MIT body is a genuine FULL-WIDTH single column — prose lines reach
  ~497pt, crop ~508pt. On the landscape long edge (347.5pt) the max whole-line
  scale is 335.5/508 = 0.66 → 6.6pt. A TOP/BOTTOM split does NOT change line
  width → same 0.66 → NO font gain. A LEFT/RIGHT split WOULD enlarge (~13pt) but
  cuts every text line horizontally = a banned printing defect (PROMPT's own
  "no text line cut at a boundary" rule). Tighter margins buy only 6.6→6.8pt.
  CONCLUSION: 6.6pt IS the design-preserving ceiling for MIT; the 9-10pt target
  presumed a split that geometry forbids. Font is therefore "as large as design
  preservation allows" — acceptance met on the font axis. (Recorded in AGENT.md.)

## Done

(moved here as completed; see FIXES.md for the running fix log)
- [x] #5 detached/duplicated equation numbers (pending-commit): right-margin "(n)"
      labels (e.g. 115-131 on src p73) sat ~25pt beyond the eq body — wider than
      the infl_x=16 merge reach — so they flowed stacked below their (tall, merged)
      equation block, and where the block bbox already touched the margin they ALSO
      duplicated. FIX: region_blocks sets aside EQNUM_RE lines in the right 25%
      margin and re-attaches each (bbox union) to the widest block straddling its
      y-centre, targets chosen against unmutated blocks. Verified: eq 115-131 each
      on its own row, 0 stacked/duplicated, no TOC false-match; pages 149->142,
      font 6.54pt unchanged, blank 0. See FIXES.md.
- [x] empty pages eliminated, occluded text fixed, 2col tiny font fixed, landscape
      for wide single-column (prior iters 1-6; see git log).
- [x] #1 display equations no longer scattered (84a16a9): anisotropic text merge
      (infl_x=16, infl_y=1) fuses each equation row into one intact block; verified
      on MIT eq (68)/(69). pages 179->158, clipped 124->89, no blowup.
- [x] #6 near-empty page from page-scale background-fill callout boxes: src p43's
      shaded "Remark 29" box (vector fill 98% w × 72% h) absorbed all 57 enclosed
      prose lines → one 518.6pt block → oversized branch placed it ALONE on p76
      scaled to ~4.6pt and stranded p75 (<1.5% ink). FIX: region_blocks drops a
      drawing rect spanning >=0.9 crop width AND >=0.45 height AND enclosing >=6
      text lines (background tint, not a figure). 6 such boxes doc-wide all now
      flow at body size. Verified: blank pages 1->0, min coverage 0.4%->1.95%,
      font 6.54pt unchanged, Figure 14 intact, p75/76 dense + correct order.
- [x] #3 running-header + page-number furniture removed (_is_furniture in
      region_blocks): killed duplicated heading bands (3.3/4.3 repeated below the
      page number) AND the blank trailing "84" page + lone page-number pages.
      pages 158->148, blank 0, lone-number pages 3->0, font 6.54pt unchanged,
      equations/figures/TOC/title intact. See FIXES.md.

## Known pitfalls

- Reflow is BANNED (destroys design). Use crop/fitw/2col + landscape only.
- Only merge FIGURE atoms was the old rule; #1 deliberately extends clustering to
  equation text atoms — be careful NOT to merge whole prose columns into one block
  (that caused a 112-page blowup before). Cluster only by tight overlap/adjacency.
- A parse-OK file can still NameError — always run a real conversion.
- Image render + temp-file writes drop/corrupt intermittently here. Re-run the
  metric; if a temp file looks like binary garbage, regenerate it. Gate commits on
  metric when images won't display, and note "visual pending".
