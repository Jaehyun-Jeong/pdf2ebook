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

iter (d503a36): FIXED MIT detached/duplicated equation numbers (fix_plan
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

iter (detached word-tag eq labels): FIXED MIT detached equation WORD tags
"(reconstruction sampler)" / "(generative sampler)" (src p80, out p134) floating
in the right-margin dead space below their r^recon / r^gen equations. Root cause:
the #5 re-attach logic set aside only NUMERIC labels (EQNUM_RE) AND gated on
x0 > region.x0+0.75*width. These word tags are right-ALIGNED on the same y-band
as their equation, but being long words their left edge starts at x0≈409/427
(vs numeric labels at ≈532), so they (a) didn't match the numeric regex and
(b) failed the 0.75 gate — flowing detached as lone atoms below the equation.
FIX: broadened the set-aside predicate to any lone fully-parenthesised line
(new EQTAG_RE = ^\(.+\)$) and relaxed the right-margin gate 0.75->0.65 of region
width (catches x0≈409 while left-anchored prose at x0≈58 / ~10% in never matches).
The existing band re-attachment then unions each tag into the equation block
straddling its y-centre (NO reflow; placed at true position). Verified by render
(out p134 both tags now right-aligned ON their equation rows, defect gone;
numeric regression out p124 eq 115-118 + "(for all f...)" tags still attached,
no dup; p133 ELBO/Remark 42 unchanged) + metric (pages 142->141 as the two
stranded tag-lines collapse back, font 6.54pt unchanged, blank 0, cov med 96.4%).

iter (re-verify word-tag fix, no code change): STOP — acceptance met (RE-ASSERTED
after the word-tag reopen). The word-tag fix (f1be6fb) reset the clean counter, so
a fresh from-scratch double-check was run. 14-inspector workflow over TWO
independent page-sets — A {0,14,35,60,90,120,140}, B {7,28,50,75,105,130,138} —
BOTH fully clean (zero defects: equations intact w/ attached numbers, figures
whole, callout boxes at body size, TOC/refs clean, no header/footer dup, correct
order, no stranded pages). p134 (the prior word-tag defect) Read directly: tags
now right-aligned ON their r^recon/r^gen rows — fix holds. Metric: 141 pages,
6.54pt (geometric 6.6pt ceiling), 0 blank, cov med 96.4% / min 52.23%. Two
consecutive clean double-checks + clean metric + font at ceiling => loop complete.

iter (re-verify #4, no code change): STOP — acceptance met. Fresh from-scratch
double-check found ZERO printing defects across TWO independent page-sets
(pass1 {0,12,40,70,100,130}, pass2 {6,25,55,85,115,141}): equations intact with
attached numbers, figures whole, all callout boxes flow at body size, TOC +
references clean, no header/footer duplication, no trailing furniture page,
correct reading order. Metric: 142 pages, font 6.54pt (at the ~6.6pt design-
preserving geometric ceiling), 0 blank, coverage median 96.3% / min 52.23%
(p100 = clean paragraph end, not stranded). Two consecutive clean double-checks
+ clean metric + font at ceiling => loop objective complete.

iter (Lever 1 — minimize device margin, font win): PAGE_MARGIN 6.0pt -> 2.0pt.
Content is width-fit, so each device-margin point directly shrinks the font. On
the 6" landscape long edge the available width goes 335.5pt -> 343.5pt, so the
whole-line fit scale rises ~2.4%. Verified: median body font 6.54pt -> 6.70pt
(p90 6.62 -> 6.78), pages 141 (unchanged), 0 blank, coverage median 96.4% ->
98.5% (min 49.59%, slightly lower because content now sits closer to the page
edge but well within it). Rendered + Read dense body (p40,p90), equation
(p125 eq 119-124, p40 eq 39-42), and figure/DiT (p73) pages: equations intact
with attached numbers, callout boxes at body size, NOTHING clipped at the page
edge (comfortable left/right whitespace remains — tighter margin only enlarged
content, did not push it off). Lever 1 of the retarget done; next: Lever 2
(crop to true text bbox) and Lever 3 (per-region width-fit), or push margin
lower (0-1pt) if a further safe gain is wanted.

iter (Lever 2 — width-fit to TRUE text bbox, font win): in run_split, before
flowing a region's blocks, tighten the region's x-extent to the union of its
actual block rects (min x0 .. max x1) instead of the padded/outlier-trimmed
crop. The MIT body crop is ~508pt but the real text column is ~497-500pt, so
the screen was being width-fit to ~8-11pt of empty side-padding. Fitting to the
true bbox raises the whole-line scale. The union spans every block (incl. the
widest display equation), so the widest real element exactly fills the width and
NOTHING is ever clipped; y is left to the existing vertical flow. Verified:
median body font 6.70pt -> 6.89pt (p90 6.78 -> 6.89), pages 141 -> 146 (the
larger scale spills ~5 regions onto one more device page each — benign), 0 blank,
coverage median 98.5% -> 100.4% (min 49.59% -> 54.48%). Rendered + Read dense
body (p40 Summary-14 box + eq 32-34, p90), equation (p125 Thm-41 + eq 108/109),
figure (p73 DiT + CLIP matrix, both whole), and a page-boundary pair (p128/p129
eq 115-118 + heading C): equations each on their own row with attached numbers
and inline word-tags, figures whole, callout boxes flow at body size, no line/eq
split at the new page breaks, no detached labels, NOTHING clipped at the edge.
Next: Lever 3 (per-region width-fit so a rare wide element doesn't shrink a whole
page) — but note Lever 2 already union-fits per region, so for single-column MIT
(one region/page) Lever 3's remaining gain is limited to pages where a wide eq
forces smaller body; quantify before implementing.

FIXED (2026-05-29 Lever 3 quantified — NOT ACTIONABLE — + re-verify STOP): No
code change. Lever 3 ("don't let a rare wide element force the whole page smaller
than the body needs") quantified by a per-region probe over all 84 src pages
(landscape avail_w=343.5): current per-page body font is already near-uniform
(median 6.91, p10=p90=6.91) because MIT body prose IS a genuine full-column single
column reaching ~496.8pt on ~94% of pages — the body is itself the widest element.
Splitting off the single widest block per page → median 6.91→6.91 (ZERO gain,
< the 0.1pt stop threshold); only 5/84 pages change, and those are false positives
(p75's widest block is real full-width prose; p57's is a Figure-18 band spanning
the column). Implementing it would shrink genuine prose and break cross-page body
uniformity → not done. Regenerated deliverable from HEAD (Levers 1+2): 146 pp,
median 6.89pt, 0 blank, cov med 100.4%/min 54.48%. Two independent double-check
render passes Read in full — A {0,18,45,72,100,128,145}, B {9,33,60,88,118,140} —
BOTH fully clean. FINAL achieved body font = 6.89pt (6.54→6.70→6.89 across the
three levers). 8pt is geometrically impossible on the 6" device without reflow:
body lines ~497pt vs 6" landscape long edge 347.5pt → max whole-line scale
~343.5/497 ≈ 0.69 → ~6.9pt; 8pt would need ~398pt of screen width the device does
not have (reflow / line-cutting BANNED, wider device declined). All three font
levers exhausted at the true geometric ceiling => STOP, loop objective complete.
