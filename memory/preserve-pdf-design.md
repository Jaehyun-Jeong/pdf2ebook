---
name: preserve-pdf-design
description: "For pdf2ebooks, preserve the PDF's original design/layout when improving e-reader readability"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c10b2eea-c48d-4dc4-bc58-60d7d7a630b2
---

When converting PDFs for e-readers in the pdf2ebooks project, the user wants the
paper's **main/original design preserved** — equations, figures, columns, and
visual layout must stay as the author designed them. Improve readability without
destroying layout.

**Why:** The user reacted negatively to `--mode reflow`, which rewraps prose to
the screen and discards the original layout. They said "maintain pdf's main
design while improving its readability."

**How to apply:**
- Do NOT use reflow for these papers. Prefer layout-preserving modes: `crop`
  (margin trim), `fitw`, `2col`, and especially `landscape` rotation for wide
  single-column papers (keeps everything intact, just rotated so font is larger).
- Reserve reflow only if the user explicitly asks for it.
- The tool is `pdf2ereader.py`; outputs go to `papers/ereader/`.
