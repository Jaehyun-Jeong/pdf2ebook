# pdf2ereader

Make academic / textbook PDFs readable on small (6–7") e-ink readers
**without reflowing** — equations, figures and tables stay exactly where they
are. It crops the wasted margins and rescales the content so it fills the
screen, then writes a PDF sized to your device.

## Why text looks tiny on a Kindle/Kobo

A textbook PDF is a fixed A4/Letter canvas. A 6" screen is ~43% of A4's width,
so the device's "fit whole page" shrinks 12pt body text to ~5pt, and ~half the
page is empty margin. Cropping the margins alone roughly doubles the effective
text size. See the inline docstring in `pdf2ereader.py` for the full reasoning.

## Install

```bash
pip install -r requirements.txt
```

## Use

```bash
# Just point it at a file — it picks the mode automatically (default).
python pdf2ereader.py book.pdf

# Pick your device (default kindle6):
python pdf2ereader.py book.pdf --device kobo_libra
python pdf2ereader.py --list-devices
```

### Automatic mode (default)

`--mode auto` samples the document and chooses:

- **two-column** (most sampled pages have a column gutter) → `2col`
- **single-column**, and cropping alone leaves text ≥ the target size on your
  device → `crop`
- **single-column**, but cropping would still be too small → `fitw`

It estimates the on-device font size as
`median_body_font × min(screen_w/crop_w, screen_h/crop_h)` and compares it to
`--min-font` (default 8.5pt). It prints its decision and the reasoning, e.g.:

```
[auto] chose 'fitw': single-column, ~10.0pt text -> only ~6.1pt if merely
cropped (< 8.5pt); fitting to width instead
```

Force a specific mode any time with `--mode crop|fitw|2col`.

### The three modes

- **crop** — remove margins only. One page in, one page out, text stays
  selectable. Best when the cropped page already fits comfortably.
- **fitw** — fit-to-width: scale content to fill the screen width and slice
  tall pages vertically. For single-column books that are still too small after
  cropping.
- **2col** — split the two columns, then fit each to the screen width.

Key flags:

| Flag | Meaning |
|---|---|
| `--mode auto\|crop\|fitw\|2col` | default `auto` (picks per document) |
| `--min-font 8.5` | auto: target on-device body font in pt |
| `--device <name>` | target screen (`--list-devices`) |
| `--padding 4` | whitespace points kept around content |
| `--outlier-pct 5` | percentile trimmed per edge so headers/page-numbers don't defeat the crop |
| `-o out.pdf` | output path |

## Important: how to get it onto the device

Transfer the output **as a PDF over USB** and keep it a PDF:

- **Kindle:** USB → copy to the `documents/` folder. (Send-to-Kindle also works
  and does *not* convert PDFs.)
- **Kobo:** USB → copy to the root of the `KOBOeReader` drive. Kobo firmware
  4.33+ keeps your zoom level across pages, which pairs well with a cropped PDF.

Do **not** convert to EPUB — Calibre's own docs say PDF→EPUB breaks math
typesetting. The whole point of this tool is to keep the PDF and just make it
fit.

## Notes / limitations

- The crop rewrites the **MediaBox**, not only the CropBox, because Kindle's
  native PDF renderer ignores CropBox.
- Column detection (`--mode 2col`) is a whitespace-gutter heuristic; it bails to
  single-column when unsure. Pages with a full-width figure spanning both
  columns are kept whole.
- Output text stays vector/selectable in all modes (nothing is rasterized).
- For scanned (image-only) textbooks, margin detection still works, but consider
  the `k2pdfopt` CLI tool as an alternative — it's the reference tool for that
  case.
