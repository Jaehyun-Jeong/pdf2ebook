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

## iter 2026-05-29 (header/footer furniture — fix #3 DONE)
- Double-check (6 parallel inspectors over a dense render sample) found REAL
  defects beyond font: HIGH — blank trailing page (only "84"), orphaned eq band
  on one page; MED — section heading duplicated below the page number (p035 "3.3
  Learning the Marginal Vector Field", p056 "4.3 Score Matching").
- ROOT CAUSE: source has a running header at y0≈44.4 (5.6% — section num+name on
  every page) and a centered page-number footer at y≈710-723 (89.7%). The crop's
  trimmed-union includes both bands, so region_blocks extracted them as text
  atoms and _Flow placed them → duplicated heading bands + isolated page-number
  pages. (Body runs y≈82.8→700, i.e. 10.5%→88%.)
- FIX: new _is_furniture() drops (a) any text line with y0 < 7% of source page
  height (running header) and (b) pure-number lines (arabic/roman) in the top OR
  bottom margin (page numbers); applied in region_blocks before merge/flow. The
  numeric gate protects footnotes (y≈85%, non-numeric); 7% top band sits safely
  above the 10.5% body start so no real first line or section heading is lost
  (real headings live mid-body, e.g. src p18 y613). Verified: pages 158->148,
  blank 0, lone-number pages 3->0, font 6.54pt unchanged, eq/fig/TOC/title intact.
- NOTE: get_text on the OUTPUT still reports the dropped furniture text — it
  lives in the clipped show_pdf_page XObject layer (not visible). Trust the
  RENDER, not get_text, when checking for visible duplicates/blanks.

## iter 2026-05-29 (near-empty page — callout-box fill — fix #6 DONE)
- Double-check via parallel vision inspectors (workflow) called all 32 sampled
  pages CLEAN — but the METRIC caught output p75 at <1.5% ink (the one blank).
  LESSON: vision agents rationalize whitespace as "section end"; trust the metric
  for near-empty pages. p75 held only a lead-in line + 1 equation while p76
  CONTINUED the same derivation = a real stranded-content defect, not a section end.
- ROOT CAUSE (instrumented /tmp/diag_flow.py + diag_pages.py): this MIT textbook
  renders Remark/Definition/Example callouts as a big vector FILL rect behind the
  text (e.g. src p43 fill 98% crop-w x 72% crop-h). region_blocks added that fill
  to `figs`; the text-absorb step folded all 57 enclosed prose lines into it ->
  one 518.6pt block -> _Flow.add oversized branch placed it ALONE on its own page,
  scaled to ~4.6pt (smaller than 6.5pt body!), and stranded the previous page.
  6 such boxes doc-wide (src p17,21,32,43,48,62; ALL 0 images, 57-108 lines).
- FIX: region_blocks drops a drawing rect with w>=0.9*region.w AND h>=0.45*region.h
  AND >=6 enclosed text lines (background tint, not a figure). The enclosed prose
  then flows at body size; the shade still shows through per-line show_pdf_page
  clips so design is preserved (NO reflow — line positions unchanged). Verified:
  blank 1->0, min cov 0.4%->1.95%, font 6.54pt unchanged, Figure 14 (p73) intact.
- NOTE for next double-check: p54 (Example 23 short box, ~1.95% cov) is a SMALL
  callout below the 0.45-height threshold — kept whole as a unit, legit section
  end, NOT a defect (was low-cov before this fix too). Don't chase it.

## FONT CEILING (important — stops chasing an impossible target)
- MIT body = genuine FULL-WIDTH single column: prose lines ~497pt, crop ~508pt.
  Landscape long edge 347.5pt → max whole-line scale 335.5/508 = 0.66 → 6.6pt.
  TOP/BOTTOM split keeps line width → NO font gain. LEFT/RIGHT split would give
  ~13pt but CUTS every line = banned defect. Margins buy only +0.2pt. So ~6.6pt
  IS the design-preserving ceiling; the old "split MIT to 9-10pt" goal is
  geometrically impossible without reflow (banned). Treat font axis as DONE.

## iter 2026-05-29 (detached equation numbers — fix_plan #5 DONE)
- Double-check pass 2 (page set 20/40/60/90/110/130) was NOT clean: out p130
  showed eq numbers (115)-(118) stacked detached in the right-margin dead space
  below their equation; #5 had predicted this for 125/126/127. So we did NOT stop.
- ROOT CAUSE (instrumented region_blocks on src p73): display-eq labels "(n)" sit
  at x0=531.7, a ~25pt alignment gap past the eq body's right edge (~506) — wider
  than the text merge reach (infl_x=16) — so they never fused. Each flowed as a
  lone atom AFTER the (often multi-row, tall-integral-chained) merged equation
  block, so all the numbers stacked below the equation. WORSE: when the eq block's
  OWN merged bbox already reached x=554 (the margin), the number showed through the
  block's clip AND flowed separately => DUPLICATED numbers (seen p129/p130 first try).
- FIX: region_blocks sets aside any lone "(n)"/"(n.m)" line (EQNUM_RE) whose x0 is
  in the right 25% of the region, then re-attaches each to the block straddling the
  number's vertical centre whose left edge is at/left of it (pick the WIDEST such
  block), via bbox union — the number rides in that block's clip at its true 2D
  position (NO reflow). TWO bugs found & fixed mid-iter: (a) sequential absorption
  grew the block past later numbers -> compute all targets against the UNMUTATED
  block list first; (b) the original `br.x1 <= num.x0` left-guard rejected tall eq
  blocks already touching the margin (leaving the number to duplicate) -> guard is
  now `num.x0 >= br.x0 - 2` (number not LEFT of the block), so a no-op union still
  consumes the stray atom. Verified: out p124-127 eq 115-131 each on its own row,
  0 detached/duplicated; TOC page numbers ("3"/"4", no parens) NOT misattached;
  eq (70)/Remark 29/Figure 14/Summary 45 intact. Metric pages 149->142 (~7 stranded
  number-lines collapsed back), font 6.54pt unchanged, blank 0, cov med 96.3%.
- NEXT: #4 re-verify. Pass 2 was dirty this iter, so the two-consecutive-clean
  counter resets; next loop must double-check from scratch before any STOP.

## iter 2026-05-29 (re-verify #4 — STOP, acceptance met)
- No code change. Fresh from-scratch double-check after last iter's dirty pass 2.
  Regenerated /tmp/mit.pdf (142 pp, 6.54pt, 0 blank, cov med 96.3% min 52.23%).
  Rendered TWO independent page-sets and Read every page:
  pass1 {0,12,40,70,100,130}, pass2 {6,25,55,85,115,141}. BOTH fully clean —
  equations intact w/ attached numbers, figures whole, all callout boxes flow at
  body size, TOC + refs clean, no header/footer dup, no trailing furniture page,
  correct order. p100 ~half-white = legit paragraph/section end (min-cov page),
  NOT stranded (ends mid-sentence-complete with a period; design preserved = can't
  fill without banned reflow). => two consecutive clean double-checks + clean
  metric + font at the geometric 6.6pt ceiling => STOP. All fix_plan items done.
  If the loop re-fires: re-run metric + render two page-sets; only reopen if a
  NEW defect appears or the input set changes.

## iter 2026-05-29 (restart double-check NOT clean — word-tag eq labels fixed)
- Restart required a fresh double-check (prior session had STOPped). Ran a workflow
  of 12 parallel vision inspectors over TWO independent page-sets (A {3,18,48,78,
  108,138}, B {10,33,60,95,120,135}). 11/12 clean; ONE real defect: out p134
  "(reconstruction sampler)" / "(generative sampler)" floating detached below
  their r^recon/r^gen equations. So the loop REOPENED (did NOT stay stopped).
- ROOT CAUSE: the #5 detached-label fix only set aside NUMERIC labels (EQNUM_RE)
  whose x0 > region.x0+0.75*width. On src p80 these are right-ALIGNED WORD tags on
  the SAME y-band as their equation, but long words => left edge x0≈409/427 (vs
  numeric labels ≈532). They failed BOTH the numeric regex and the 0.75 gate, so
  flowed as lone atoms detached below the equation.
- FIX (one change): broadened the set-aside to any lone fully-parenthesised line
  (EQTAG_RE = ^\(.+\)$) and relaxed the gate 0.75->0.65 of region width. 0.65 puts
  the threshold at x0≈386 (catches 409/427) while left-anchored prose (x0≈58, ~10%
  in) and left-anchored heading parentheticals like Remark 42's "(What Happens...)"
  never match. Re-attachment is the SAME #5 band-union machinery (no reflow).
- Verified: out p134 both tags right-aligned ON their rows (gone); numeric regress
  p124 eq 115-118 + inline "(for all f...)" tags still attached/no-dup; p133 ELBO/
  Remark 42 unchanged. Metric 142->141 pages (2 stranded tag-lines collapse back),
  6.54pt, blank 0, cov med 96.4%. papers/ereader/ regenerated.
- COUNTER RESET: this restart's double-check was DIRTY (found a defect), so the
  two-consecutive-clean counter is 0. NEXT loop: double-check from scratch (render
  2 fresh page-sets, Read every page) before any STOP.

## iter 2026-05-29 (re-verify after word-tag fix — STOP, acceptance met)
- No code change. Fresh from-scratch double-check required because the word-tag
  fix (f1be6fb) had reset the two-consecutive-clean counter. Regenerated
  /tmp/mit.pdf (141 pp, 6.54pt, 0 blank, cov med 96.4% / min 52.23%). Ran a
  14-parallel-inspector workflow over TWO independent page-sets — A {0,14,35,60,
  90,120,140}, B {7,28,50,75,105,130,138}: BOTH fully clean, zero defects.
  Additionally Read p134 directly (the previously-detached word-tag page):
  "(reconstruction sampler)"/"(generative sampler)" now right-aligned ON their
  equation rows — fix holds. => two consecutive clean double-checks + clean
  metric + font at the geometric 6.6pt ceiling => STOP. All fix_plan items done.
  If the loop re-fires: re-run metric + render two fresh page-sets; only reopen
  if a NEW defect appears or the input set (papers/) changes.

- ENV WARNING: this session intermittently corrupts tool output, temp files, and
  even file-read display (saw binary garbage in a .txt; saw garbled line numbers
  in a source Read). The SOURCE ON DISK is fine (ast.parse OK). Do risky edits in
  a fresh/stable loop iteration; always re-run metric and re-render to confirm;
  regenerate any temp file that looks corrupted. Did NOT attempt #1/#2 inline due
  to this — left for a clean loop iteration.

## Retarget 2026-05-29 (objective: maximize font toward 8pt on 6", same design)

- User reviewed the delivered PDF, says 6.54pt is too small, wants **8pt at the
  EXACT same design** and explicitly chose to STAY on the 6" device (declined a
  wider-device option that would make 8pt trivial).
- HARD GEOMETRY (re-measured this retarget): src is US-Letter 612x792, body font
  10pt, body/prose lines up to ~497pt wide, crop ~508pt. 6" landscape long edge =
  347.5pt. 8pt needs scale 0.80 → ~398pt screen width → IMPOSSIBLE on 6" without
  reflow (banned) or line-cutting (banned). True ceiling ~7pt.
- BUT the prior STOP ("6.6pt ceiling") was declared WITHOUT exhausting the font
  levers. New fix_plan To-do drives three real levers: (1) minimize PAGE_MARGIN
  6pt→~2pt, (2) crop to true text bbox not the 508pt crop, (3) per-region
  width-fit so a rare wide element doesn't shrink the whole page. Expect ~6.54 →
  ~7pt. Do these BEFORE any STOP; then document achieved font + why 8pt is
  unreachable on 6". Never claim 8pt unless metric+render show it.
- Equation-integrity (#1), furniture-strip (#3), callout-box (#6), eq-num/word-tag
  (#5) fixes are DONE — do not regress while chasing font.

## iter 2026-05-29 (Lever 1 — device margin 6pt→2pt — font 6.54→6.70pt)
- PAGE_MARGIN 6.0 → 2.0. Content is width-fit so each margin pt directly shrinks
  font; landscape avail_w 335.5 → 343.5pt → fit scale +2.4% → median font
  6.54 → 6.70pt (p90 6.62→6.78), pages 141 (unchanged), 0 blank, cov med 96.4→
  98.5% (min 49.59% — content sits closer to edge but well within; NO clipping).
- Verified by render+Read: p40 (eq 39-42 + Example/Prop callouts), p90 (dense
  body eq 84-86), p125 (eq 119-124), p73 (DiT figure). All intact, nothing
  clipped, comfortable L/R whitespace remains. Committed.
- NEXT: Lever 2 (crop to TRUE text bbox, not the inflated ~508 crop) and Lever 3
  (per-region width-fit so a rare wide element doesn't shrink the whole page).
  Could also push margin 2→0-1pt for ~+0.06pt but deferred (bezel safety).
- COUNTER: this is a code-change iter (not a re-verify), so the two-clean STOP
  counter is N/A until Levers 2/3 are exhausted and a fresh double-check runs.

## iter 2026-05-29 (Lever 2 — width-fit to TRUE text bbox — font 6.70→6.89pt)
- run_split now tightens each region's x-extent to the union of its real block
  rects (min x0 .. max x1) BEFORE flowing, instead of width-fitting the padded
  ~508pt crop. MIT real text column ~497-500pt, so ~8-11pt of side padding was
  being fit to screen and wasting scale. Union spans every block (incl widest
  display eq) → widest real element exactly fills width → nothing ever clipped.
- Verified: median font 6.70→6.89pt (p90 6.78→6.89), pages 141→146 (+5; larger
  scale spills ~5 regions onto one more device page — benign), 0 blank, cov med
  98.5→100.4% (min 49.59→54.48%). Rendered+Read p40 (Summary-14 box + eq 32-34),
  p73 (DiT + CLIP figs both whole), p90 (dense body), p125 (Thm-41 + eq 108/109),
  p128/p129 (eq 115-118 + heading C page boundary): all clean — eqs on own rows
  with attached numbers/word-tags, figures whole, callouts at body size, no
  line/eq split at the new breaks, no detached labels, nothing clipped. Committed.
- NEXT: Lever 3. NOTE Lever 2 already union-fits PER region, so for single-col
  MIT (one region per page) the residual Lever-3 gain only exists on pages where
  a wide display equation reaches wider than the prose and thus shrinks the whole
  page's body. Quantify how many such pages exist (and how much body font they
  lose) BEFORE implementing — may be a small/no win for MIT. Also still optional:
  push PAGE_MARGIN 2→1pt for ~+0.06pt (bezel safety tradeoff).
- COUNTER: code-change iter; two-clean STOP counter stays N/A until Lever 3 is
  resolved and a fresh from-scratch double-check runs.

## iter 2026-05-29 (Lever 3 quantified — NOT ACTIONABLE — + re-verify → STOP)
- NO code change. Lever 3 = "don't let a rare wide element force the whole page
  smaller than the body needs." Probe replicated run_split per region over all 84
  src pages (landscape avail_w=343.5, PAGE_MARGIN=2):
    * current per-page body font (10pt src × avail_w/union_width) is already
      near-UNIFORM: median 6.91, p10=p90=6.91, min 6.75, max 7.80.
    * Reason: the MIT body prose IS a genuine full-column single column reaching
      ~496.8pt on ~94% of pages → the body is itself the widest element, so there
      is no rare-wide-element-vs-narrow-body gap to exploit on the vast majority
      of pages.
    * Dropping the single widest block per page from the width → median stays
      6.91 → 6.91 (ZERO gain, < the 0.1pt stop threshold). Only 5/84 pages changed.
    * Those 5 are mostly FALSE POSITIVES: src p75's widest 496.8 block is a real
      full-width PROSE line ("This shows the third property…") — Lever 3 would
      wrongly shrink genuine body text; src p57's widest is the Figure-18 band that
      legitimately spans the column (body there = naturally-narrow Algorithm-7
      lines). Enlarging only those pages would also break cross-page body-size
      uniformity ("exact same design").
  => Lever 3 yields no median gain AND would break design uniformity / shrink real
     prose → NOT IMPLEMENTED (resolved, per PROMPT's "stop when a lever yields
     <0.1pt or would break design").
- RE-VERIFY (this iter): regenerated deliverable from HEAD (Levers 1+2) — 146 pp,
  median 6.89pt, 0 blank, cov med 100.4% / min 54.48%. Read TWO independent
  page-sets in full: A {0,18,45,72,100,128,145}, B {9,33,60,88,118,140}. BOTH
  fully CLEAN — eqs (6/7a/7b, 24/25/26, 43, 88, 111/112) on own rows with attached
  numbers/word-tags; callouts (Theorem 5, Remark 16, Summary 45, Intuition 44,
  Algorithm 6/7) flow at body size; figures whole (prob-path triptych, dog grid,
  DiT); refs/appendix-E/TOC clean; page-boundary headings not cut; correct order;
  no blanks/clips/detached labels. papers/ereader/ regenerated.
- FINAL: all three font levers exhausted (1: margin 6→2pt; 2: width-fit to true
  text bbox; 3: no-op for full-width single column). Achieved body font 6.89pt
  (6.54→6.70→6.89). 8pt is GEOMETRICALLY IMPOSSIBLE on 6": body lines ~497pt, 6"
  landscape long edge 347.5pt → max whole-line scale ~343.5/497 ≈ 0.691 → ~6.9pt;
  8pt needs scale 0.80 → ~398pt of screen width the 6" device does not have. The
  only routes to 8pt are reflow or line-cutting (both BANNED) or a wider device
  (user declined). => two consecutive clean double-checks + clean metric + all
  levers exhausted at the true geometric ceiling => STOP. Loop objective complete.

## iter 2026-05-29 (re-fire — protocol re-verify, STOP holds)
- Loop re-fired after the converged STOP. Per the re-fire protocol (re-run metric
  + render two FRESH page-sets; reopen only on a NEW defect or changed input set):
  input set unchanged (papers/ = MIT only); ast.parse OK; regenerated /tmp/mit.pdf
  = 146 pp, median 6.89pt (p10=4.82 p90=6.89), 0 blank, cov med 100.4% / min 54.48%
  — IDENTICAL to the recorded STOP metric. Rendered + Read TWO fresh independent
  page-sets (distinct from prior A/B): A2 {3,21,52,80,110,135,144}, B2 {12,40,66,
  95,125,142}. BOTH fully CLEAN — callout boxes (Summary 7/14/27, Theorem 3/41,
  Remark 21, Proposition 3) flow at body size; (i)-(viii) derivation rows + eqs
  32-34/63-65/108/109/138/139/146/147/148 on own rows with attached numbers &
  word-tags; Algorithm 5 line-items intact; Figure 1/17 whole; footnote 6 kept;
  §3/§4.3/§7.2.3/Appendix-B page-boundary headings not cut; correct order; no
  blanks/clips/detached labels. No NEW defect, input unchanged => STOP holds, no
  code change. Deliverable already current (papers/ereader/ regenerated 11:59).

## iter 2026-05-29 (re-fire #3 — protocol re-verify, STOP holds)
- Loop re-fired again post-convergence. Re-fire protocol: input unchanged
  (papers/ = MIT only, same bytes May 29 10:24); ast.parse OK; regenerated
  /tmp/mit.pdf = 146 pp, median 6.89pt (p10=4.82 p90=6.89), 0 blank, cov med
  100.4% / min 54.48% — IDENTICAL to recorded STOP metric (deterministic output).
  Rendered + Read TWO fresh page-sets distinct from all prior (14 pages total:
  {5,16,27,38,48,58,70,82,92,103,115,128,138,143}). Dispatched a 14-parallel
  vision-inspector workflow → allClean:true, defects:[]. Also Read p070 (§6.1 dense
  body, complete lines, page break between a complete lead-in and its equation =
  allowed atom break, not stranding) and p115 (Algorithm 13/14 + Figure 20 masked-
  diffusion grid whole + body, correct order) directly — both clean. No NEW defect,
  input unchanged => STOP holds, no code change. Deliverable current (papers/ereader/
  regenerated 11:59). 8pt remains geometrically impossible on 6" (body ~497pt vs
  landscape 347.5pt long edge → ceiling ~6.9pt); only reflow / line-cut (banned) or
  a wider device (user declined) could reach it.

## iter 2026-05-29 (re-fire #4 — protocol re-verify, STOP holds)
- Loop re-fired again post-convergence. Re-fire protocol: input unchanged
  (papers/ = MIT only, same bytes May 29 10:24); ast.parse OK; regenerated
  /tmp/mit.pdf = 146 pp, font median 6.89pt (p10=6.83 p90=6.89) — IDENTICAL to the
  recorded STOP metric (deterministic output, source unchanged). A naive
  text-block coverage probe flagged out-page 55 as "low-text" (14%) — FALSE
  POSITIVE: Read directly, p55 is the dense CSM-loss derivation + Algorithm-4
  caption, full of content (the crude metric undercounts large display-equation
  blocks; trust the render). Rendered + Read TWO fresh independent page-sets
  distinct from all prior (14 pages): A {2,19,37,55,74,98,122,144}, B {30,50,67,
  85,108,131}. BOTH fully CLEAN — eqs 8/9/28/50/70/80/98-100/125-131/147/148 on own
  rows with attached numbers & word-tags; callouts (Example 6/13/34, Remark 20)
  flow at body size; figures whole (Figure 13 MNIST grid, Figure 14 DiT/CLIP,
  joint-PDF plot); Algorithm 3/4 line-items intact; footnote 6 kept; TOC clean;
  correct order; no blanks/clips/detached labels. No NEW defect, input unchanged =>
  STOP holds, no code change. Deliverable current (papers/ereader/ 146pp 6.89pt,
  regenerated 11:59). 8pt remains geometrically impossible on 6" (body ~497pt vs
  landscape 347.5pt long edge → ceiling ~6.9pt); only reflow / line-cut (banned)
  or a wider device (user declined) could reach it.

## iter 2026-05-29 (re-fire #2 — protocol re-verify, STOP holds)
- Loop re-fired again post-convergence. Re-fire protocol: input set unchanged
  (papers/ = MIT only, same bytes); ast.parse OK; regenerated /tmp/mit.pdf = 146 pp,
  median 6.89pt (p10=4.82 p90=6.89), 0 blank, cov med 100.4% / min 54.48% — IDENTICAL
  to recorded STOP metric (output is deterministic, source unchanged). Rendered + Read
  a fresh spread {title/TOC p000, figure page p073, dense body p145}: TOC dotted
  leaders + page nums + link intact; DiT + CLIP figures whole; Summary-45 callout flows
  at body size with complete sentences — all clean. No NEW defect, input unchanged =>
  STOP holds, no code change. Deliverable current. 8pt remains geometrically impossible
  on 6" (body ~497pt vs landscape 347.5pt long edge → ceiling ~6.9pt); only reflow /
  line-cut (banned) or a wider device (user declined) could reach it.

## PIVOT 2026-05-29 — LaTeX-recompile pipeline (NEW objective, supersedes reformat)

User wants 8-9pt on a REAL 6" Kindle Paperwhite 10th-gen with the original design
AND intact equations — impossible by reformatting the rendered PDF (~6.9pt ceiling).
After /team-research, pivoted to recompiling the arXiv source. Authorized to break
architecture.

- Source: arXiv:2506.02070 ("Flow Matching and Diffusion Models"), downloaded to
  `latex_src/` (root `main.tex`, standard `article` class @10pt, bundled `notes.sty`,
  subfiles, biblatex/biber, bbm). gitignored: figures/, fm_guide_assets/, build
  artifacts; tracked: *.tex, *.sty, *.bib, build.sh.
- Toolchain: TeX Live 2019 via apt (pdflatex/biber/latexmk). NOTE: external installer
  (TinyTeX curl|sh) was BLOCKED by hooks/classifier — apt is the allowed path.
- KEY TRICK: a LaTeX pt is absolute. Shrinking the PAGE to the 6" panel
  (257.3x347.5pt via geometry in notes.sty) while keeping 10pt font => body renders
  ~10pt PHYSICAL on the 6" screen, design + equations identical. PROVEN: built clean,
  241pp, median body 9.96pt, theorem boxes/links/figures perfect.
- Geometry knob = the `\usepackage[paperwidth=3.573in,paperheight=4.826in,...]{geometry}`
  line in notes.sty (orig backed up as notes.sty.orig; +\emergencystretch 3em added).
- REMAINING DEFECT (the loop's job): wide display equations (multi-line align, long
  lines) overflow the right edge — ~258 Overfull \hbox (worst ~246pt), ~51/241 pages.
  Body + most equations are perfect; only wide eqs overflow. Fix via DISPLAY-only math
  shrink (cheapest), then per-eq \resizebox/breqn, then landscape for the stubborn few.
  Body font must stay >=8pt; equations must stay correct vector. See PROMPT.md/fix_plan.md.
- Build: `cd latex_src && latexmk -pdf -interaction=nonstopmode main.tex` -> main.pdf.
  Metric/render: `.venv/bin/python` + fitz, run from repo ROOT.

## iter 2026-05-29 (Lever 2a — auto-fit unnumbered align* — commit ed0a10a)
- Recompile pipeline. After Lever 1 (\small display), ~89 overfull boxes >30pt
  remained; worst ~210pt; ~40 pages with content past the right edge. RENDER (not
  the block metric — PyMuPDF block x1 undercounts math overflow) is authoritative:
  p138/p193/p94/p218 showed wide display eqs running clean off the page.
- FIX: \RenewEnviron{align*} (environ pkg) -> typeset \BODY in \aligned inside a
  measured \sbox, \resizebox to \linewidth ONLY if \wd>\linewidth (fitting ones
  untouched, keep their \small size). Emitted via \centerline (NOT \[...\] —
  in THIS preamble \[ maps to equation*, so calling it inside the redef
  re-triggers environ's equation* parser and mis-nests: "equation* ended by
  \end{align*}"). 116 align* envs covered.
- equation* (5 envs) DELIBERATELY EXCLUDED: redefining it via environ breaks on
  equation* used inside mdframed remark/summary boxes ("equation* ended by
  \end{remarkbox}") and on multi-line bodies forced into inline $...$. Low count,
  not worth the breakage; leave native.
- VERIFIED: build exit 0, 229pp (was 233; minor reflow from shrunk eqs). Overfull
  118->71, >30pt 89->48, pages-past-edge(block) 40->22, body font median 9.96pt
  UNCHANGED. Rendered p193 (q_{t2|t0} derivation): every align* row now fits the
  column, alignment at = preserved, vector+selectable, correct. p30/p24 align*
  equation parts fit. No regression on fitting align*.
- STILL OVERFLOWING (next iters, by environment, NOT regressions):
  * alignat* (7 envs) — the \blacktriangleright &&\text{...} margin annotations
    (p24 "initial guess of new state", p30 "expression for", p138 area). Lever 2b.
  * numbered align (100) + equation (35) — worst boxes incl. 210pt; p138 eq85/86,
    p94 eq63/64. Can't use \aligned (loses (n) tag). Lever 2c, hardest.
- COUNTER: code-change iter; two-clean STOP counter N/A until 2b/2c done + fresh
  double-check. Deliverable NOT regenerated yet (overflow not ~0).

## iter 2026-05-29 (Lever 2b — auto-fit alignat* — overfull 71->66)
- \RenewEnviron{alignat*}[1]{\rldisplay{$\small\displaystyle\begin{aligned}\BODY
  \end{aligned}$}} — the [1] absorbs alignat*'s mandatory {n} col-count arg (dropped),
  \aligned handles &/&&. Reuses Lever 2a's \rlfit measured-sbox + \resizebox-to-
  \linewidth (only scales rows wider than the column). 7 alignat* envs covered.
- VERIFIED: build exit 0, 229pp (unchanged), body 9.96pt unchanged. Overfull \hbox
  71->66 (>30pt 48->43), worst 210->189pt, pages-past-right-edge(block) 22->19.
  Rendered out-p23 (Heun's method alignat* w/ ► &&\text margin notes): both rows
  aligned at =, both annotations ("initial guess…", "update with average…") fit the
  column, sane && spacing, vector+selectable+correct. No regression.
- REMAINING OVERFLOW = numbered align (100) + equation (35) only — Lever 2c, hardest
  (can't use \aligned, loses the (n) tag; worst boxes ~189pt). Then Lever 3 landscape.
- COUNTER: code-change iter; two-clean STOP counter N/A until 2c done + fresh double-check.

## iter 2026-05-29 (Lever 2c equation-half — auto-fit numbered equation — overfull 66->55)
- Numbered display envs (equation/align) CANNOT be boxed (display envs error in
  restricted-horizontal/sbox), so the 2a/2b "\aligned in \resizebox via \centerline"
  trick drops the (n) tag. KEY INSIGHT for `equation`: don't box the env — \let-save
  the genuine \equation/\endequation BEFORE \RenewEnviron (avoids environ name
  recursion), then re-enter it with the body as an auto-fitted hbox:
  \RenewEnviron{equation}{\rloldequation\rlfitnum{$\small\displaystyle\BODY$}\rloldendequation}.
  \rlfitnum \resizebox-es to (\linewidth-26pt) ONLY when wider (26pt reserves the
  "(nnn)" tag); the equation env appends (n) at FULL size in the right margin.
- VERIFIED: build exit 0, 229pp, body 9.96pt unchanged. overfull 66->55 (>30pt
  43->34), pages-past-right-edge(block) 19->16. The 176pt VAE equation (eq83,
  total_vae_loss, out-p122) — 2nd-worst overall — now fits w/ full-size (83).
  Rendered out-p122 (3-line aligned VAE loss + 4 underbraces, fits, vector,
  number full-size), out-p100 (wide eq68 TimeEmb scaled+fits, narrow eq69 left
  untouched = conditional resize works), out-p110 (figure/body prose ~10pt clean).
  No regression on fitting equations.
- equation* (5 envs) still native (deliberately, per 2a notes). 
- REMAINING OVERFLOW = numbered `align` (100 envs) — now THE bulk AND all worst
  boxes (189/173/163/161/149pt). HARD: align can't be boxed and per-row scaling
  breaks &-alignment + the (n) count (\cref). Next: Lever 2c align-half — split
  BODY on \\, scale each row in an aligned-of-one with an explicit \tag mirroring
  amsmath numbering (MUST preserve equation count), OR landscape the worst few.
- COUNTER: code-change iter; two-clean STOP counter N/A until align-half done +
  fresh double-check. Deliverable NOT regenerated yet (overflow not ~0).

## iter 2026-05-29 (Lever 2c align-half SINGLE-ROW — auto-fit numbered align — overfull 55->33/pass)
- Remaining overflow after 2a/2b/2c-equation was ALL numbered `align` (100 envs;
  worst 189/173/163/161pt). align is NOT a simple begin/end like equation: it is
  built on \halign via \start@align, so it CANNOT be re-entered by \let-ing its
  begin/end (proved: "weird error", double-counts), and a multi-row body (&/\\)
  can't be boxed without destroying alignment + per-row numbers.
- SPLIT THE PROBLEM by row count. Detection: `\rl@detectbreak` appends \\\marker to
  one expansion of \BODY, grabs tokens after the FIRST \; if == marker, no real \\.
  (environ's \BODY is \edef'd w/ \unexpanded, so ONE \expandafter reveals the body.)
  Verified SINGLE/MULTI/SINGLE on standalone. Counts: 64 single-row, 36 multi-row;
  only 1 align block uses \nonumber and it's multi-row (so all 64 single-row are
  plainly numbered → safe).
- SINGLE-ROW (no \\): numerically identical to an `equation` (shared equation
  counter, one number) → route through the proven equation machinery:
  `\rloldequation\rlfitnum{$\small\displaystyle\begin{aligned}\BODY\end{aligned}$}\rloldendequation`.
  \aligned keeps any inner & alignment; \rlfitnum \resizeboxes to \linewidth-26pt
  only when wider; equation emits (n) full-size in margin. equation CENTERS it
  (cleaner than re-entering align which left-aligns at axis).
- MULTI-ROW (has \\): CLONE genuine align under a private name and call it by
  \begin/\end so \@currenvir is set up properly:
  `\expandafter\let\csname rlgenalign\endcsname\align` (+ end), then
  `\begin{rlgenalign}\BODY\end{rlgenalign}`. Standalone-verified the clone keeps
  the equation COUNT exactly (single=1, multi 2-row=2,3, next=4) and \cref labels.
- BUG FOUND+FIXED mid-iter (build exit 12): \RenewEnviron{align} clobbers \endalign,
  and amsmath's \endalignat/\endflalign are literally "\endalign" (\meaning checked)
  → the numbered alignat in part_04 (Thm 17 SDE-extension) broke with cascading
  Missing }/$/\cr at \end{alignat}. FIX: after redefining align, repoint
  `\let\endalignat\endrlgenalign` + `\let\endflalign\endrlgenalign` (saved genuine end).
- VERIFIED: build exit 0, 0 errors, 228pp, body font median 9.96pt UNCHANGED.
  overfull/pass 55->33 (>30pt 34->20), worst 189->135pt, pages-past-right-edge(block)
  16->13. Rendered+Read: p64 eq(39) (the worst 189pt \nabla\log chain) now fits the
  column, vector+correct, full-size (39); p81 eq(54) DSM loss + "(denoising score
  matching loss)" annotation fits w/ full-size (54); p146 clean body; p186 multi-row
  eqs(115-118) native — per-row numbers + = alignment intact, STILL overflow (= next
  lever, not regression); p68 alignat Thm17 (44/45) renders unbroken.
- REMAINING OVERFLOW = MULTI-ROW align (36) + numbered alignat (1) only; worst now
  135/129/120pt. Next: Lever 2c part-2 — split-and-tag per row (\\-split verified safe:
  ~0 align blocks have nested \\ matrix/cases) OR landscape the stubborn few.
- COUNTER: code-change iter; two-clean STOP counter N/A until multi-row done + fresh
  double-check. Deliverable NOT regenerated (overflow not ~0 yet).

## iter 2026-05-29 (Lever 2d — auto-fit unnumbered \[ \] displays — overfull 28->... 33->28)
- INVESTIGATION FINDING: the top item said "only multi-row align/alignat left", but
  classifying ALL 20 >30pt overflows by env showed 5 were UNNUMBERED `\[...\]`
  displays — incl. THE worst (135pt, part_05 logq/logp; also 120/98/40/39pt) — which
  the 2a notes had DELIBERATELY excluded as equation* (environ mis-scans equation*
  across mdframed boxes). These are the cheapest, lowest-risk class (no number, no
  &-alignment, single-line), so per PROMPT "global low-risk levers first" I did them
  before the harder multi-row align.
- FIX (notes.sty): do NOT touch equation* via environ. Redefine `\[`/`\]` DIRECTLY at
  \AtBeginDocument (after amsmath): `\def\[{\setbox\rldispbox\hbox\bgroup$\small\displaystyle}`
  and `\def\]{$\egroup $$\ifdim\wd\rldispbox>\linewidth\resizebox{\linewidth}{!}{\usebox
  \rldispbox}\else\usebox\rldispbox\fi$$}`. KEY: emit inside plain `$$...$$` (not
  \centerline) — `$$` centers the (possibly resized) box AND keeps the surrounding
  paragraph continuing un-indented after `\]`, exactly like native `\[...\]`;
  \centerline would force a \par and indent the continuation. \resizebox only when
  wider than \linewidth (narrow displays untouched, full size).
- SAFETY VERIFIED before applying: `\[...\]` (=equation*) forbids top-level `\\`/`&`,
  so an hbox capture is always valid; of 23 `\[...\]` blocks doc-wide, 3 contain `\\`
  but ALL nested inside array/pmatrix/cases (own alignment, valid in an hbox) —
  standalone-tested matrix+cases render correctly. Standalone-tested paragraph
  continuation: text after `\]` is NOT indented (matches native); a blank-line-
  separated new paragraph IS indented.
- VERIFIED on real build: exit 0, 228pp, body font median 9.96pt UNCHANGED. overfull
  33->28 (>30pt 20->15), worst 135.8->129.1pt (new worst is a multi-row align =
  remaining lever, NOT a regression), pages-past-right-edge(block) 13->10. Rendered+
  Read p121 (KL proof: wide logq/logp `\[...\]` now fits the column, vector+correct;
  numbered eq(81) full-size tag; short E_q[..] `\[...\]` below stays natural size) and
  p107 (DiT attention: wide `z=x..(self-attn)` (was 98pt) + `MultiHead=Concat..` (was
  120pt) both scaled to fit, while narrow `Attn(Q,K,V)` and `head_h` displays untouched
  = conditional resize correct). Body ~10pt, gray boxes + blue links intact. No regression.
- REMAINING OVERFLOW = multi-row numbered `align` (14) + `alignat` (1); worst now
  129/113/107/100/96/92pt. Next: Lever 2c part-2 (split-and-tag per row, OR landscape).
- COUNTER: code-change iter; two-clean STOP counter N/A until multi-row align done +
  fresh double-check. Deliverable NOT regenerated yet (overflow not ~0).
