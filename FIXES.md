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

iter (pending-commit): FIXED MIT running-header + page-number furniture leaking
into the flow — produced (a) duplicated section-heading bands (e.g. "3.3 Learning
the Marginal Vector Field" / "4.3 Score Matching" repeated below the page number)
and (b) the blank trailing "84" page + scattered lone page-number bands. Added
_is_furniture(): drops text lines in the source page's top 7% margin band
(running header) and pure-number lines in the top/bottom margin (page numbers),
applied in region_blocks before merge/flow. Real body headings (~10.5% down) and
footnotes (non-numeric) are kept. Verified by double-check render (p031/p033/p035
clean — heading once, no footers; title+TOC+Figure-7+last page intact; equations
still whole) + metric (pages 158->148, blank 0, lone-number pages 3->0, font
6.54pt unchanged — font is at its geometric ceiling, see AGENT.md).

iter (cc3c348): FIXED MIT near-empty output page (p75 <1.5% ink: stranded
1 lead-in line + 1 equation at ~85% white) — caused by src p43's shaded "Remark 29"
callout box. Its vector background-fill rect (98% crop width x 72% height) was
treated as a figure and absorbed all 57 enclosed prose lines into ONE 518.6pt
block, which tripped _Flow's oversized-figure branch -> placed alone on the next
page scaled down to ~4.6pt (SMALLER than 6.5pt body) and left the prior page
near-empty. 6 such boxes doc-wide (src p17,21,32,43,48,62; all 0 images, 57-108
lines). FIX: region_blocks now drops a drawing rect that spans >=0.9 crop width
AND >=0.45 crop height AND encloses >=6 text lines (a background tint, not a
figure) so the enclosed prose flows as normal body text — no reflow (line
positions unchanged; the box shade still shows through per-line clips). Verified
by metric (blank pages 1->0, min coverage 0.4%->1.95%, font 6.54pt unchanged,
148->149 pages) + render (p75/76 now dense body-size Remark 29 text in correct
reading order with equations intact; Figure 14 on p73 fully preserved — guard
spared the real figure).

iter (b06eb56): FIXED MIT detached/duplicated equation numbers (fix_plan
#5) — display-equation labels like (115)-(131) (src page 73) sit ~25pt past the
equation body in the right margin, wider than the text-merge reach (infl_x=16),
so they never fused into their equation block. They flowed as separate atoms AFTER
the (often tall, multi-row) merged equation block — stacking detached in the dead
space below the equation (output p128-130 before), and where the equation block's
own bbox already reached the margin the number ALSO showed through its clip =>
duplicated numbers. FIX: region_blocks now sets aside any lone "(n)"/"(n.m)" line
in the right 25% margin (EQNUM_RE) and re-attaches each to the block straddling its
vertical centre whose left edge is at/left of the number (widest such block), via a
bbox union — placed intact in the block's clip at its true position (NO reflow).
Targets are chosen against the UNMUTATED block list so several numbers on one tall
equation all attach (an earlier number growing the block must not disqualify later
ones). Verified by render (eq 115-131 across out p124-127 each on its own row, zero
stacked/duplicated numbers; title/TOC page numbers "3"/"4" NOT misattached — regex
needs parens; eq (70)/Remark 29/Figure 14/Summary 45 intact) + metric (pages
149->142 as ~7 stranded number-lines collapse back, font 6.54pt unchanged, blank 0,
coverage median 96.3% min 52.2%).
