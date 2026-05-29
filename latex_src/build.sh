#!/usr/bin/env bash
# Build the 6"-Kindle e-reader PDF by recompiling the arXiv LaTeX source on a
# small page (see notes.sty geometry knob). Downloads the source only if absent
# (so it never clobbers the loop's patched notes.sty / math edits).
set -e
cd "$(dirname "$0")"
if [ ! -f main.tex ]; then
  echo "[build] fetching arXiv:2506.02070 source"
  curl -fsSL "https://arxiv.org/e-print/2506.02070" -o source.tar.gz
  tar xzf source.tar.gz && rm -f source.tar.gz
fi
latexmk -pdf -interaction=nonstopmode main.tex
echo "[build] -> latex_src/main.pdf"
