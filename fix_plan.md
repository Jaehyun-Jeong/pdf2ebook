# Fix Plan — LaTeX-recompile pipeline (retargeted 2026-05-29)

One item per line, top = next. **GOAL: 6" Kindle PDF, body 8–10pt, original
design, ALL equations intact — via recompiling arXiv:2506.02070 source on a
small page.** Verify every change by build + metric + render. Commit only
verified wins.

## Breakthrough already proven (do not re-litigate)

Recompiling the LaTeX source onto a 257.3x347.5pt page (notes.sty geometry knob)
gives median body font ~9.96pt with the EXACT original design and real vector
equations. This beats the 8-9pt target and is impossible via PDF reformatting.
Baseline + kindle build both compile clean (exit 0).

## THE defect to fix

Wide display equations overflow the narrow column (right edge). Build: ~258
Overfull \hbox (~200 >30pt, worst ~246pt too wide); ~51/241 pages have content
past the right edge. Examples: p94 (classifier-free guidance align block runs
off), p124, p191, p192, p199, p218.

## To do

- [x] **Lever 1 — shrink DISPLAY math only (not body prose).** DONE: added
      `\AtBeginDocument{\everydisplay\expandafter{\the\everydisplay\small}}` in
      notes.sty. Display math renders ~9pt; body prose stays 9.96pt. Overfull
      \hbox 128->118 (>30pt 100->89), worst 246->210pt, pages-past-edge ~40, 233pp.
      Verified render p94/p124/p40: body unchanged ~10pt, equations smaller but
      correct. PARTIAL — wide single-line eqs + trailing `▶` margin-annotations
      still overflow; that's Lever 2's job.
- [x] **Lever 2a — auto-fit UNNUMBERED `align*`** (116 envs) via environ +
      `\resizebox` to `\linewidth` (only when wider; `\aligned` keeps the `&`
      alignment). DONE (commit ed0a10a): overfull 118->71 (>30pt 89->48),
      pages-past-edge 40->22, body 9.96pt unchanged, p193 derivation now fits.
      NOTE: `equation*` (5 envs) excluded — environ mis-scans it across mdframed
      boxes; `\[...\]` maps to equation* here so the redef must use \centerline.
- [ ] **Lever 2b — auto-fit `alignat*`** (7 envs). These hold the `\blacktriangleright`
      `&&\text{...}` margin annotations (p24, p30) that overflow. Same treatment as
      2a: `\RenewEnviron{alignat*}` (note it takes a `{n}` col-count arg — drop it,
      `\aligned` handles `&`/`&&` itself) -> `\rldisplay{...\begin{aligned}\BODY\end{aligned}...}`.
      Test the `&&` spacing renders sanely; verify p24/p30.
- [ ] **Lever 2c — auto-fit NUMBERED `align`/`equation`** (100 + 35 envs; worst
      overflow, e.g. p138 eq85/86, p94 eq63/64, worst 210pt). Can't use `\aligned`
      (loses the (n) tag). Options: (i) keep `\begin{align}` but scale rows that
      are too wide individually; (ii) capture each numbered row, scale body in a
      box, re-attach the tag with `\tag` + reserved space; (iii) `breqn`. Hardest;
      test on a few. Keep tag visible and correct.
- [ ] **Lever 3 — landscape (`pdflscape`) the handful that still can't fit.**
      Only for genuinely un-shrinkable wide equations/tables; read sideways.
- [ ] **Re-verify + document + deliver.** When overflow ~0 and body 8-10pt:
      two independent double-check render passes (include p94/p124/p191/p218),
      then copy main.pdf -> papers/ereader/MIT_flow_matching_diffusion.latex.ereader.pdf.
      Record final body font + overflow count in FIXES.md.

## Known pitfalls

- Run `.venv/bin/python` from repo ROOT (venv is not inside latex_src).
- biblatex uses biber; let `latexmk` drive the passes. If aux corrupts: `latexmk -C`.
- Custom macros live in math_commands.tex + notes.sty; breqn may choke on them —
  test on a few equations before applying widely.
- Editing math size globally can shrink inline math too; prefer DISPLAY-only.
- notes.sty.orig is the pristine backup of the geometry/style file.
- A parse-OK .tex can still fail mid-build; always confirm exit 0 + a real render.

## Archived: prior PDF-reformat objective (superseded by this pipeline)

The pdf2ereader.py reformat approach reached its hard ceiling (~6.89pt on 6",
design-preserving) — see git history + FIXES.md. The reader9/kobo_libra presets
deliver 8-9pt only on larger screens. This LaTeX pipeline supersedes it for the
"8-9pt on a real 6" Paperwhite" goal. Do not revert to reformatting.
