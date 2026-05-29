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
- [x] **Lever 2b — auto-fit `alignat*`** (7 envs). DONE (this iter):
      `\RenewEnviron{alignat*}[1]{...}` absorbs the `{n}` col-count arg (#1) and
      reuses the 2a `\rldisplay{$\small\displaystyle\begin{aligned}\BODY\end{aligned}$}`
      machinery; `\aligned` handles `&`/`&&`. overfull 71->66 (>30pt 48->43),
      worst 210->189pt, pages-past-edge 22->19, body 9.96pt unchanged, 229pp.
      Verified render: out-p23 Heun's-method block — both rows aligned at `=`, the
      two `►` `&&\text{...}` margin annotations ("initial guess…", "update with
      average…") fit the column, vector+correct, sane `&&` spacing.
- [x] **Lever 2c (equation half) — auto-fit NUMBERED `equation`** (35 envs). DONE
      (this iter): `\let`-saved the genuine `equation` env, then `\RenewEnviron`
      re-enters it placing `\rlfitnum{$\small\displaystyle\BODY$}` as the math —
      `\rlfitnum` `\resizebox`es the body to `\linewidth-26pt` ONLY when wider, so
      the env still emits the `(n)` tag at FULL size in the right margin (no boxing
      of the display env; fitting eqs untouched). overfull 66->55 (>30pt 43->34),
      176pt VAE `equation` (p122 eq83) fixed, pages-past-edge 19->16, body 9.96pt
      unchanged, 229pp. Verified render: p122 eq(83) 3-line aligned body fits w/
      full-size (83); p100 wide eq(68) TimeEmb scaled+fits while narrow eq(69)
      untouched; p110 figure/body clean. No regression.
- [x] **Lever 2c (align half) — SINGLE-ROW numbered `align`** (64 of 100). DONE
      (this iter): `\\`-detection (`\rl@detectbreak`) splits align into single- vs
      multi-row. Single-row is numerically an `equation` (same counter, one number)
      so route it through the proven equation re-entry, wrapping `\BODY` in `\aligned`
      to keep inner `&` then `\rlfitnum`-resizing to the column. Multi-row invokes a
      CLONE of genuine align (`rlgenalign`) — preserves per-row (n) tags + `=`
      alignment exactly. CAVEAT FIXED: amsmath `\endalignat`/`\endflalign` are literal
      `\endalign`; redefining align clobbered `\endalign` → repointed them to the saved
      genuine end. overfull/pass 55→33 (>30pt 34→20), worst 189→135pt, pages-past-edge
      16→13, body 9.96pt unchanged, 228pp. Verified render: p64 eq(39) (was 189pt) fits
      w/ full-size (39); p81 eq(54) DSM-loss + margin annotation fits; p186 eqs115-118
      multi-row native intact (still overflow=next); p68 alignat Thm17 (44/45) unbroken.
- [x] **Lever 2d — auto-fit UNNUMBERED `\[ ... \]` displays** (was deliberately
      excluded as equation*). DONE (this iter): discovered 5 of the 20 worst-overflow
      boxes — incl. THE worst (135pt) — were `\[...\]` displays, not align. Fixed by
      direct redef (NOT environ): `\def\[{\setbox\rldispbox\hbox\bgroup$\small\displaystyle}`,
      `\def\]{$\egroup $$\ifdim\wd>\linewidth\resizebox{\linewidth}{!}{..}\else..\fi$$}`.
      Emits via plain `$$...$$` (centers AND keeps the paragraph continuing
      un-indented after `\]`, unlike `\centerline`); `\resizebox`es only when wider.
      `\[...\]` is single-line (no top-level `\\`/`&`); `\\` nested in array/pmatrix/
      cases is fine (verified). overfull 33->28 (>30pt 20->15), worst 135.8->129.1
      (now a multi-row align), pages-past-edge 13->10, body 9.96pt unchanged, 228pp.
      Verified render: p121 KL-proof logq/logp display fits + eq(81) full-size tag;
      p107 DiT — wide `z=x..`(98pt) & `MultiHead=Concat`(120pt) scaled to fit while
      narrow `Attn`/`head_h` untouched. No regression.
- [x] **Lever 2c (align half, part 2) — MULTI-ROW numbered `align`.** DONE (this
      iter): the split-and-tag option was UNSAFE (a `\nonumber`-first-row appendix
      align would be miscounted; \notag/\label per-row parsing is fragile). Instead:
      measure block natural width via `\sbox{aligned}`; if `>\linewidth`, render the
      GENUINE align inside `\begin{minipage}{natw+30pt}` then `\resizebox{\linewidth}`
      the whole minipage. Content+numbers scale uniformly => cross-row `=` alignment,
      per-row (n), `\notag`, `\label`, count ALL preserved (standalone-verified: a
      `\nonumber`-first-row block keeps exactly 1 number). Fitting blocks stay native.
      pages-past-PAPER-edge 13->1 (the authoritative metric: text/draw maxx>W+2), overfull
      >30pt 15->1, body 9.96pt, 224pp. Rendered: VAE eq(136/137), Prop1 eq(41/42) in-box,
      L_FM proof (i)-(iv) all fit w/ full-size numbers + alignment; Taylor align* unchanged.
- [x] **Lever 2c (align half, part 3) — the LONE numbered `alignat{2}`** (part_04
      Thm17 SDE-extension, eq 44/45, p68). DONE (this iter): saved genuine `\alignat`
      as clone `rlgenalignat` BEFORE renewing alignat, then `\RenewEnviron{alignat}[1]`
      mirroring the align machinery — multi-row measures via `alignedat{#1}` then
      minipage+resizebox the genuine clone; single-row routes through equation. REMOVED
      the old `\endalignat\endrlgenalign` repoint (environ now owns `\endalignat`); kept
      the `\endflalign` repoint. pages-past-PAPER-edge 1->0 (ZERO — all pages now fit),
      overfull>30pt 1->0 (worst 73.1->24pt, all ≤24pt margin-spill still ON the page),
      body 9.96pt unchanged, 224pp. Verified render: p68 eq(44/45) fits the theorem box
      w/ &&-alignment, full-size (44)/(45), \notag middle row unnumbered, colors intact;
      p55 multi-row L_FM proof (i)-(iv) unchanged (no regression).
- [~] **Lever 3 — landscape (`pdflscape`).** NOT NEEDED: zero pages past the paper edge
      after part-3. The 14 residual overfull \hbox are all ≤24pt (margin-spill into the
      7.2pt geometry margin, linewidth ~243pt < pagewidth 257.3pt — still on the paper).
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
