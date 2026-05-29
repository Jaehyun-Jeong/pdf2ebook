# Ralph Loop — Objective (retargeted 2026-05-29: LaTeX-recompile pipeline)

**Produce a 6"-Kindle PDF of the MIT diffusion textbook with body font 8–10pt,
the ORIGINAL design preserved, and ALL equations intact — by recompiling the
arXiv LaTeX source onto a small page.** The breakthrough is already proven; the
remaining job is to make wide display equations FIT the narrow page without
shrinking body text below 8pt or breaking any equation.

## Why this approach (architecture change — authorized by the user)

Reformatting the rendered PDF caps at ~6.9pt on a 6" screen (a 497pt text line
can't be enlarged without reflow). We stopped doing that. Instead we recompile
arXiv:2506.02070's LaTeX source with a tiny page (`geometry` paperwidth/height =
the 6" Kindle panel). A LaTeX point is absolute, so keeping the source's 10pt
font on a 257x347pt page makes the body render at ~10pt PHYSICAL on the 6"
screen — with real vector equations and the identical design. Verified working.

## Current state (commit at retarget)

- Build: `cd latex_src && latexmk -pdf -interaction=nonstopmode main.tex` ->
  `latex_src/main.pdf`. Builds clean (exit 0).
- Page = 257.3 x 347.5 pt (exact 6" Kindle). Median body font ~9.96pt. 241 pages.
- Design identical (theorem/callout boxes, fonts, colors, hyperlinks, figures).
- **THE DEFECT TO FIX:** wide display equations (multi-line `align`, long single
  lines) overflow the right page edge. Build emits ~258 Overfull \hbox, ~200 of
  them >30pt over, worst ~246pt too wide. ~51 of 241 pages have content past the
  right edge. Example pages: 94, 124, 191, 192, 199, 218 (and others).
- The geometry knob lives in `latex_src/notes.sty` (the `\usepackage[...]{geometry}`
  line we edited; `notes.sty.orig` is the untouched backup).

## The one rule

Each iteration: read state, pick the SINGLE top item in `fix_plan.md`, make ONE
focused change (to `notes.sty`, `math_commands.tex`, a wrapper, or a small patch
applied by `build.sh`), rebuild, verify visually + by metric, commit, update the
plan. Then stop.

## Levers to fit wide equations (keep body >= 8pt, keep equations correct)

Prefer global, low-risk levers first; per-equation edits last.
1. **Shrink DISPLAY math only** (not body): e.g. wrap display math in a smaller
   size, set a smaller `\everydisplay`/`\Dorder`, or use `\thinmuskip` tweaks.
   Body prose stays ~10pt; only equations get a bit smaller. Cheapest win.
2. **Auto-wrap long equations** with `breqn` (`dmath`/`dgroup`) — but it needs
   per-environment edits and can choke on custom macros; test on a few first.
3. **Scale individual oversized equations** with `adjustbox`/`\resizebox{\linewidth}{!}`
   — surgical, keeps them vector + correct, only the widest ones.
4. **Landscape pages** (`pdflscape`) for a handful of genuinely un-shrinkable wide
   equations/figures — read sideways, still correct.
5. **Tune page width** slightly (notes.sty geometry) — small increases reduce
   overflow but shrink on-screen font; only if levers 1–4 are insufficient and
   font stays >= 8pt.
BANNED: dropping body font below 8pt; rasterizing or otherwise mangling math
(it must stay correct, selectable vector); reverting to the pdf2ereader.py
reformat approach.

## Environment

- LaTeX: system `pdflatex`, `biber`, `latexmk` (TeX Live 2019, apt-installed).
- Rendering/metric: `.venv/bin/python` (PyMuPDF) — run from repo ROOT, the venv
  is NOT inside latex_src.
- Build:        `cd latex_src && latexmk -pdf -interaction=nonstopmode main.tex`
- Clean build:  `cd latex_src && latexmk -C` (then rebuild) if aux state corrupts.

## How to verify EVERY iteration (do not skip)

1. Rebuild; confirm `exit 0` and `latex_src/main.pdf` exists.
2. METRIC (from repo root, .venv/bin/python + fitz):
   - median body font (sample prose pages) — must stay 8–10pt.
   - count pages with content past the right edge (block x1 > pagewidth+2) AND
     count Overfull \hbox >30pt in the build log — both must go DOWN, target ~0.
   - page_count > 0, text selectable (get_text non-empty).
3. RENDER + Read (`.venv/bin/python` get_pixmap dpi=200 -> PNG, then Read):
   a dense body page, a PREVIOUSLY-OVERFLOWING equation page (e.g. 94 or 124),
   and a figure page. Confirm the equation now fits, is still correct, and body
   text is unchanged ~10pt. Never claim a fix you did not render this iteration.
4. Better -> commit referencing the fix_plan item + append a line to FIXES.md.
   Worse/broken -> revert the edit (`git checkout --` the file, or restore from
   notes.sty.orig), note why in AGENT.md.

## Acceptance / stopping

Stop when: zero (or a tiny, documented, landscape-handled) set of pages have
equation overflow; body font is 8–10pt everywhere; every equation is correct and
sharp; design preserved; AND two consecutive double-check passes (independent
page-sets, including the formerly-broken pages) find no overflow or new defect.
Then regenerate the deliverable to `papers/ereader/MIT_flow_matching_diffusion.latex.ereader.pdf`.

## Guardrails

- One change per iteration. Verify before commit. Never claim a result you did
  not build + render + measure this iteration.
- Keep equations correct vector LaTeX. Body font >= 8pt always.
- Never edit `loop.sh` or `PROMPT.md` from inside the loop.
- If a build hangs or aux state corrupts, `latexmk -C` and rebuild before judging.
