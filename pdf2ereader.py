#!/usr/bin/env python3
"""pdf2ereader — make textbook PDFs readable on small (6") e-ink readers.

The problem: a textbook PDF is a fixed A4/Letter canvas. A 6" Kindle/Kobo is
only ~43% of A4's width, so "fit whole page" shrinks 12pt body text to ~5pt,
and ~half the page is wasted white margin. This tool fixes that *while
preserving layout* (equations, figures stay intact) — no reflow, no EPUB.

Pipeline (all vector, text stays selectable):
  1. Detect the real content bounding box per page (text + drawings + images),
     with outlier rejection (drops page numbers / headers) and separate
     even/odd handling (books have mirrored inner/outer margins).
  2. Crop to that box AND rewrite the MediaBox — not just the CropBox —
     because Kindle's native PDF renderer ignores CropBox.
  3. Optionally split each page so content fills the screen width:
       --mode crop   : crop margins only (one page in -> one page out)
       --mode fitw   : fit-to-width, slice tall content into screen-height pages
       --mode 2col   : split two columns, then fit-to-width each column
  4. Output a PDF sized exactly to your device.

Usage:
  python pdf2ereader.py book.pdf                       # default: crop, kindle6
  python pdf2ereader.py book.pdf --mode fitw           # single-column, slice
  python pdf2ereader.py book.pdf --mode 2col           # two-column papers
  python pdf2ereader.py book.pdf --device kobo_clara -o out.pdf
  python pdf2ereader.py book.pdf --list-devices

Transfer the result as a PDF over USB (Kindle: documents/ ; Kobo: drive root).
Do NOT convert to EPUB — that breaks math.
"""

from __future__ import annotations

import argparse
import re
import statistics
import sys
from dataclasses import dataclass

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("PyMuPDF is required:  pip install pymupdf")


# ---------------------------------------------------------------------------
# Device presets: usable screen in PDF points (1 pt = 1/72 inch).
# pt = pixels / ppi * 72. These are the *active display* areas.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Device:
    name: str
    width_pt: float
    height_pt: float
    desc: str


DEVICES: dict[str, Device] = {
    # 6" 1072x1448 @ 300ppi -> 257.3 x 347.5 pt
    "kindle6": Device("kindle6", 257.3, 347.5, "6\" Kindle Paperwhite/Basic, Kobo Clara/Clara HD"),
    "kobo_clara": Device("kobo_clara", 257.3, 347.5, "6\" Kobo Clara HD/2E (same panel as kindle6)"),
    # 6.8" 1236x1648 @ 300ppi -> 296.6 x 395.5 pt
    "kindle_pw": Device("kindle_pw", 296.6, 395.5, "6.8\" Kindle Paperwhite 11th gen / Signature"),
    # 7" 1264x1680 @ 300ppi -> 303.4 x 403.2 pt
    "kobo_libra": Device("kobo_libra", 303.4, 403.2, "7\" Kobo Libra 2"),
    # 10.2" 1860x2480 @ 300ppi -> 446.4 x 595.2 pt
    "kindle_scribe": Device("kindle_scribe", 446.4, 595.2, "10.2\" Kindle Scribe"),
}


# ---------------------------------------------------------------------------
# Content bounding-box detection
# ---------------------------------------------------------------------------
def page_content_bbox(page: "fitz.Page") -> "fitz.Rect | None":
    """Union bbox of all text blocks, vector drawings, and images on a page."""
    bbox = fitz.Rect()  # empty

    for block in page.get_text("blocks"):
        bbox |= fitz.Rect(block[:4])

    for path in page.get_drawings():
        if path.get("rect"):
            bbox |= fitz.Rect(path["rect"])

    try:  # get_image_rects signature varies across PyMuPDF versions
        for item in page.get_image_rects(full=True):
            r = item[0] if isinstance(item, (tuple, list)) else item
            bbox |= fitz.Rect(r)
    except Exception:
        pass

    # Clamp to the page; ignore degenerate results.
    bbox &= page.rect
    return bbox if (not bbox.is_empty and bbox.width > 1 and bbox.height > 1) else None


def _trimmed(values: list[float], pct: float, take_high: bool) -> float:
    """Outlier-robust bound. take_high -> upper percentile, else lower.

    Used so a stray header/footer or page number doesn't blow the crop open.
    """
    values = sorted(values)
    if len(values) < 5 or pct <= 0:
        return values[-1] if take_high else values[0]
    qs = statistics.quantiles(values, n=100)  # 99 cut points, qs[i] ~ (i+1)th pct
    idx = int(min(98, max(0, (100 - pct - 1) if take_high else (pct - 1))))
    return qs[idx]


def stable_crop_boxes(
    doc: "fitz.Document", padding: float, outlier_pct: float
) -> dict[int, "fitz.Rect"]:
    """One crop rectangle per page, computed per parity (even/odd) so mirrored
    book margins are respected. Outlier percentile trims headers/footers."""
    per_page: list[tuple[int, fitz.Rect, fitz.Rect]] = []  # (idx, content, mediabox)
    for i, page in enumerate(doc):
        cb = page_content_bbox(page)
        if cb is not None:
            per_page.append((i, cb, fitz.Rect(page.rect)))

    result: dict[int, fitz.Rect] = {}
    for parity in (0, 1):
        subset = [(i, cb, mb) for (i, cb, mb) in per_page if i % 2 == parity]
        if not subset:
            continue
        x0 = _trimmed([cb.x0 for _, cb, _ in subset], outlier_pct, take_high=False)
        y0 = _trimmed([cb.y0 for _, cb, _ in subset], outlier_pct, take_high=False)
        x1 = _trimmed([cb.x1 for _, cb, _ in subset], outlier_pct, take_high=True)
        y1 = _trimmed([cb.y1 for _, cb, _ in subset], outlier_pct, take_high=True)
        crop = fitz.Rect(x0 - padding, y0 - padding, x1 + padding, y1 + padding)
        for i, _, mb in subset:
            result[i] = crop & mb  # never exceed that page's MediaBox
    return result


def detect_column_split(page: "fitz.Page", crop: "fitz.Rect") -> float | None:
    """Return x of a two-column gutter inside `crop`, or None if single column.

    Heuristic: if no text block straddles the centre but blocks sit on both
    sides, the mid-gutter is the largest right-edge -> next-left-edge gap."""
    blocks = [b for b in page.get_text("blocks") if b[6] == 0 and fitz.Rect(b[:4]) in crop or
              (b[6] == 0 and fitz.Rect(b[:4]).intersects(crop))]
    blocks = [b for b in blocks if b[6] == 0]
    if len(blocks) < 4:
        return None
    cx = (crop.x0 + crop.x1) / 2
    margin = crop.width * 0.04
    if any(b[0] < cx - margin and b[2] > cx + margin for b in blocks):
        return None  # a full-width block crosses the centre

    rights = sorted(b[2] for b in blocks)
    lefts = sorted(b[0] for b in blocks)
    best_gap, best_x = 0.0, None
    for r in rights:
        nxt = [l for l in lefts if l > r]
        if not nxt:
            continue
        gap = min(nxt) - r
        # gutter must be reasonably central and reasonably wide
        midpoint = r + gap / 2
        if gap > best_gap and gap > crop.width * 0.03 and abs(midpoint - cx) < crop.width * 0.18:
            best_gap, best_x = gap, midpoint
    return best_x


# ---------------------------------------------------------------------------
# Region -> device-sized output page (aspect-preserving, vector)
# ---------------------------------------------------------------------------
PAGE_MARGIN = 6.0  # uniform output margin (pt), keeps content off the bezel


def emit_region(out: "fitz.Document", src: "fitz.Document", pno: int,
                clip: "fitz.Rect", dev: Device) -> None:
    """Place `clip` from src page `pno` onto a new device-sized output page:
    scaled to fit within a uniform margin, centred horizontally and **top-aligned**
    so successive pages line up. Aspect preserved (no distortion)."""
    if clip.width <= 1 or clip.height <= 1:
        return
    avail_w = dev.width_pt - 2 * PAGE_MARGIN
    avail_h = dev.height_pt - 2 * PAGE_MARGIN
    scale = min(avail_w / clip.width, avail_h / clip.height)
    w, h = clip.width * scale, clip.height * scale
    x = (dev.width_pt - w) / 2  # horizontal centre
    y = PAGE_MARGIN             # top-align
    target = fitz.Rect(x, y, x + w, y + h)
    page = out.new_page(width=dev.width_pt, height=dev.height_pt)
    page.show_pdf_page(target, src, pno, clip=clip)


def region_atoms(page: "fitz.Page", region: "fitz.Rect") -> list["fitz.Rect"]:
    """Indivisible content units inside `region`: text *lines*, images, and
    vector drawings. A page break must never cut through one of these."""
    atoms: list[fitz.Rect] = []

    info = page.get_text("dict")
    for block in info.get("blocks", []):
        if block.get("type", 0) == 0:  # text -> line granularity
            for line in block.get("lines", []):
                r = fitz.Rect(line["bbox"]) & region
                if r.width > 1 and r.height > 1:
                    atoms.append(r)
        else:  # image block
            r = fitz.Rect(block["bbox"]) & region
            if r.width > 1 and r.height > 1:
                atoms.append(r)

    for path in page.get_drawings():
        if path.get("rect"):
            r = fitz.Rect(path["rect"]) & region
            if r.width > 1 and r.height > 1:
                atoms.append(r)

    try:
        for item in page.get_image_rects(full=True):
            rr = item[0] if isinstance(item, (tuple, list)) else item
            r = fitz.Rect(rr) & region
            if r.width > 1 and r.height > 1:
                atoms.append(r)
    except Exception:
        pass

    atoms.sort(key=lambda r: (round(r.y0, 1), round(r.x0, 1)))
    return atoms


def screen_height_src(region_width: float, dev: Device) -> float:
    """How tall, in source units, one device screen is when `region_width` is
    scaled to fill the device width."""
    return dev.height_pt * region_width / dev.width_pt


def pack_slices(region: "fitz.Rect", atoms: list["fitz.Rect"],
                screen_h: float) -> list["fitz.Rect"]:
    """Group atoms top-to-bottom into slices no taller than `screen_h`, cutting
    only in the whitespace *between* atoms. An atom taller than a screen (a big
    figure) gets its own slice and is scaled down whole. No overlap, so nothing
    is shown twice."""
    if not atoms:
        return [region]
    slices: list[fitz.Rect] = []
    top = region.y0
    last_bot = atoms[0].y1
    for a in atoms[1:]:
        cand_bot = max(last_bot, a.y1)
        if (cand_bot - top) > screen_h and last_bot > top:
            slices.append(fitz.Rect(region.x0, top, region.x1, last_bot))
            top = (last_bot + a.y0) / 2 if a.y0 > last_bot else a.y0
            last_bot = a.y1
        else:
            last_bot = cand_bot
    slices.append(fitz.Rect(region.x0, top, region.x1, last_bot))
    return slices


_PAGENUM_RE = re.compile(r"(?:\d{1,4}|[ivxlcdm]{1,8})", re.IGNORECASE)
# A lone equation label like "(118)" or "(3.2)" (allow a leading tag such as
# "(2.14)"); matched against a right-margin line to re-attach it to its row.
EQNUM_RE = re.compile(r"^\(\d+(?:\.\d+)?\)$")


def _is_furniture(line_bbox, text: str, page_rect: "fitz.Rect") -> bool:
    """True if a text line is publisher furniture — a running header (section
    name repeated atop every page) or a page-number footer — that must NOT flow
    into the body. Detected by position in the SOURCE page's top/bottom margin
    band. A pure-number test gates the footer/number case so real footnotes and
    body lines are never dropped; the body of this corpus starts ~10.5% down, so
    the 7% top band catches only the running header, never a real first line."""
    t = text.strip()
    if not t:
        return False
    H = page_rect.height
    y0 = line_bbox[1]
    in_top = y0 < page_rect.y0 + 0.07 * H
    in_bot = y0 > page_rect.y0 + 0.87 * H
    # Page number: a line that is ONLY a number (arabic or roman) in either margin.
    if (in_top or in_bot) and _PAGENUM_RE.fullmatch(t):
        return True
    # Running header: any line sitting in the very top margin band.
    if in_top:
        return True
    return False


def region_blocks(page: "fitz.Page", region: "fitz.Rect"
                  ) -> list[tuple["fitz.Rect", str]]:
    """Tagged, figure-clustered content blocks inside `region`, sorted top->bottom.
    Text lines stay SEPARATE (so they flow across pages); figure atoms (images +
    vector drawings) that are near each other MERGE into one composite block (so
    a figure is never split). Returns list of (rect, kind) where kind is
    'text' or 'fig'."""
    texts: list[fitz.Rect] = []
    figs: list[fitz.Rect] = []
    eqnums: list[fitz.Rect] = []  # right-margin equation labels, e.g. "(118)"

    info = page.get_text("dict")
    for block in info.get("blocks", []):
        if block.get("type", 0) == 0:
            for line in block.get("lines", []):
                ltxt = "".join(s.get("text", "") for s in line.get("spans", []))
                if _is_furniture(line["bbox"], ltxt, page.rect):
                    continue  # drop running header / page-number footer
                r = fitz.Rect(line["bbox"]) & region
                if r.width > 1 and r.height > 1:
                    # A lone "(n)" parked in the right margin is an equation
                    # number. A ~25pt alignment gap separates it from its
                    # equation row (wider than the merge reach below), so it
                    # would otherwise flow detached into the dead space under
                    # the equation. Set it aside to re-attach to its band.
                    if (EQNUM_RE.match(ltxt.strip())
                            and r.x0 > region.x0 + 0.75 * region.width):
                        eqnums.append(r)
                    else:
                        texts.append(r)
        else:
            r = fitz.Rect(block["bbox"]) & region
            if r.width > 1 and r.height > 1:
                figs.append(r)

    for path in page.get_drawings():
        if path.get("rect"):
            r = fitz.Rect(path["rect"]) & region
            if r.width <= 1 or r.height <= 1:
                continue
            # Drop page-scale background fills behind text (shaded Remark /
            # Definition callout boxes): a near-full-column rect enclosing many
            # text lines is a background tint, not a figure. Kept, it absorbs the
            # enclosed prose into one giant block that overflows a page (scaled
            # down to tiny text) and strands the previous page near-empty. Drop
            # the tint so the text flows at body size — line positions are
            # unchanged (no reflow); only the background shade is lost.
            if (r.width >= 0.9 * region.width and r.height >= 0.45 * region.height
                    and sum(1 for t in texts if r.intersects(t)) >= 6):
                continue
            figs.append(r)
    try:
        for item in page.get_image_rects(full=True):
            rr = item[0] if isinstance(item, (tuple, list)) else item
            r = fitz.Rect(rr) & region
            if r.width > 1 and r.height > 1:
                figs.append(r)
    except Exception:
        pass

    # Merge nearby figure atoms into composite figure blocks (generous gap).
    figs = _merge_rects(figs, 10.0)
    # Merge text atoms ANISOTROPICALLY: wide horizontal reach, tiny vertical.
    # PyMuPDF splits a display equation row into many separate "line" atoms
    # (TimeEmb(t)=, cos(...), ···, sin(...), tall brackets) with ~10pt gaps on
    # ONE horizontal band; a 1pt isotropic inflate never fused them, so _Flow
    # stacked each fragment vertically and scattered the equation down the page.
    # Generous infl_x (16pt) fuses everything on a line into ONE block (the
    # whole equation row travels intact, internal 2D layout preserved by the
    # clip), while small infl_y (1pt) keeps stacked PROSE lines separate so they
    # still flow across pages (no chaining → no page blowup). Prose lines are
    # already single full-width atoms, so wide infl_x cannot wrongly fuse them.
    texts = _merge_rects(texts, 16.0, 1.0)
    # Absorb a text block into a figure it overlaps (equation numbers, captions
    # sitting against a figure) so they travel together.
    free_text: list[fitz.Rect] = []
    for t in texts:
        for k, f in enumerate(figs):
            if fitz.Rect(f.x0 - 2, f.y0 - 2, f.x1 + 2, f.y1 + 2).intersects(t):
                figs[k] = f | t
                break
        else:
            free_text.append(t)

    blocks = [(r, "text") for r in free_text] + [(r, "fig") for r in figs]
    # Re-attach each right-margin equation number to the block on its
    # horizontal band (the equation it labels), preferring the nearest block
    # to its left. Merging extends that block's clip to include the number at
    # its true position (no reflow) instead of letting it flow as a stranded
    # line below the equation.
    # Pick each number's target against the UNMUTATED blocks: several numbers
    # may belong to one tall equation block, and absorbing the first would grow
    # that block past the next number, wrongly failing the left-of guard.
    targets: list[int | None] = []
    for num in eqnums:
        cy = (num.y0 + num.y1) / 2.0
        best = None
        for idx, (br, _kind) in enumerate(blocks):
            # The equation on the number's band: a block straddling the
            # number's vertical centre that starts at or left of it. (Don't
            # require the block to end left of the number — a tall equation's
            # merged bbox can already reach the margin; merging is then a
            # no-op, but skipping it would leave the number to flow detached.)
            if br.y0 - 2 <= cy <= br.y1 + 2 and num.x0 >= br.x0 - 2:
                if best is None or br.x1 > blocks[best][0].x1:
                    best = idx
        targets.append(best)
    for num, best in zip(eqnums, targets):
        if best is not None:
            br, kind = blocks[best]
            blocks[best] = (br | num, kind)
        else:
            blocks.append((num, "text"))
    blocks.sort(key=lambda it: (round(it[0].y0, 1), round(it[0].x0, 1)))
    return blocks


def _merge_rects(rects: list["fitz.Rect"], infl_x: float,
                 infl_y: float | None = None) -> list["fitz.Rect"]:
    """Iteratively union rects whose bboxes intersect after inflating by
    (infl_x, infl_y). Anisotropic inflation lets text atoms fuse along a line
    (wide infl_x) without chaining stacked lines together (small infl_y). When
    infl_y is None the inflation is isotropic (infl_x both ways)."""
    if infl_y is None:
        infl_y = infl_x
    rects = [fitz.Rect(r) for r in rects]
    changed = True
    while changed and rects:
        changed = False
        out: list[fitz.Rect] = []
        used = [False] * len(rects)
        for a in range(len(rects)):
            if used[a]:
                continue
            cur = fitz.Rect(rects[a])
            used[a] = True
            for b in range(a + 1, len(rects)):
                if used[b]:
                    continue
                box = fitz.Rect(cur.x0 - infl_x, cur.y0 - infl_y,
                                cur.x1 + infl_x, cur.y1 + infl_y)
                if box.intersects(rects[b]):
                    cur |= rects[b]
                    used[b] = True
                    changed = True
            out.append(cur)
        rects = out
    return rects


def emit_stacked(out: "fitz.Document", src: "fitz.Document", pno: int,
                 region: "fitz.Rect", blocks: list[tuple["fitz.Rect", str]],
                 dev: Device) -> None:
    """Flow `blocks` top-to-bottom onto device pages with whitespace COLLAPSED:
    scale to fill the width, place each block at a running y with a small capped
    gap, start a new page when the next block won't fit. No near-empty pages, no
    big blank bands, nothing cut. A block taller than a page gets its own page,
    scaled down whole. Horizontal offset within the region is preserved (centred
    titles stay centred, columns stay aligned)."""
    if not blocks:
        return
    scale = (dev.width_pt - 2 * PAGE_MARGIN) / region.width
    avail_h = dev.height_pt - 2 * PAGE_MARGIN
    max_gap = 6.0  # device pt: caps large source gaps, keeps paragraphs tidy
    page = None
    y = PAGE_MARGIN
    prev_y1 = None
    for rect, _kind in blocks:
        bw, bh = rect.width * scale, rect.height * scale
        if bh > avail_h:  # oversized figure: own page, whole
            fit = min((dev.width_pt - 2 * PAGE_MARGIN) / rect.width, avail_h / rect.height)
            w, h = rect.width * fit, rect.height * fit
            p = out.new_page(width=dev.width_pt, height=dev.height_pt)
            x = (dev.width_pt - w) / 2
            p.show_pdf_page(fitz.Rect(x, PAGE_MARGIN, x + w, PAGE_MARGIN + h),
                            src, pno, clip=rect)
            page, y, prev_y1 = None, PAGE_MARGIN, rect.y1
            continue
        gap = 0.0 if prev_y1 is None else min(max(0.0, rect.y0 - prev_y1) * scale, max_gap)
        if page is None or y + gap + bh > PAGE_MARGIN + avail_h:
            page = out.new_page(width=dev.width_pt, height=dev.height_pt)
            y, gap = PAGE_MARGIN, 0.0
        y += gap
        x = PAGE_MARGIN + (rect.x0 - region.x0) * scale
        page.show_pdf_page(fitz.Rect(x, y, x + bw, y + bh), src, pno, clip=rect)
        y += bh
        prev_y1 = rect.y1


class _Flow:
    """Continuous block flow across the WHOLE document. Blocks are placed onto
    device pages with collapsed whitespace; a new page starts only when the next
    block won't fit — NOT at source-page boundaries. This removes the partial
    last page that each source page used to leave behind (the main source of
    near-empty output pages)."""

    INTRA_GAP = 6.0   # max gap (device pt) between blocks within one region
    REGION_GAP = 5.0  # gap between regions / source pages

    def __init__(self, out: "fitz.Document", dev: Device) -> None:
        self.out = out
        self.dev = dev
        self.avail_h = dev.height_pt - 2 * PAGE_MARGIN
        self.page = None
        self.y = PAGE_MARGIN
        self.prev_y1 = None
        self.prev_region = None

    def _new_page(self) -> None:
        self.page = self.out.new_page(width=self.dev.width_pt, height=self.dev.height_pt)
        self.y = PAGE_MARGIN

    def add(self, src: "fitz.Document", pno: int, rect: "fitz.Rect",
            region: "fitz.Rect") -> None:
        scale = (self.dev.width_pt - 2 * PAGE_MARGIN) / region.width
        bw, bh = rect.width * scale, rect.height * scale

        if bh > self.avail_h:  # oversized figure: its own page, whole
            fit = min((self.dev.width_pt - 2 * PAGE_MARGIN) / rect.width,
                      self.avail_h / rect.height)
            w, h = rect.width * fit, rect.height * fit
            p = self.out.new_page(width=self.dev.width_pt, height=self.dev.height_pt)
            x = (self.dev.width_pt - w) / 2
            p.show_pdf_page(fitz.Rect(x, PAGE_MARGIN, x + w, PAGE_MARGIN + h),
                            src, pno, clip=rect)
            self.page, self.prev_y1, self.prev_region = None, None, None
            return

        if self.prev_y1 is None or region is not self.prev_region:
            gap = 0.0 if self.page is None else self.REGION_GAP
        else:
            gap = min(max(0.0, rect.y0 - self.prev_y1) * scale, self.INTRA_GAP)

        if self.page is None or self.y + gap + bh > PAGE_MARGIN + self.avail_h:
            self._new_page()
            gap = 0.0

        self.y += gap
        x = PAGE_MARGIN + (rect.x0 - region.x0) * scale
        self.page.show_pdf_page(fitz.Rect(x, self.y, x + bw, self.y + bh),
                                src, pno, clip=rect)
        self.y += bh
        self.prev_y1 = rect.y1
        self.prev_region = region


def _merge_y_bands(rects: list["fitz.Rect"], crop: "fitz.Rect") -> list["fitz.Rect"]:
    """Merge rects with overlapping/adjacent y-intervals into full-width bands."""
    if not rects:
        return []
    rs = sorted(rects, key=lambda r: r.y0)
    bands = [[rs[0].y0, rs[0].y1]]
    for r in rs[1:]:
        if r.y0 <= bands[-1][1] + 2:
            bands[-1][1] = max(bands[-1][1], r.y1)
        else:
            bands.append([r.y0, r.y1])
    return [fitz.Rect(crop.x0, t, crop.x1, b) for t, b in bands]


def estimate_gutter(atoms: list["fitz.Rect"], crop: "fitz.Rect") -> float | None:
    """Estimate the two-column gutter x from atoms that don't cross the centre.
    Returns None if the page doesn't actually look two-column."""
    cx = (crop.x0 + crop.x1) / 2
    m = crop.width * 0.04
    col = [a for a in atoms if not (a.x0 < cx - m and a.x1 > cx + m)]
    lefts = [a for a in col if a.x1 <= cx + m]
    rights = [a for a in col if a.x0 >= cx - m]
    if len(lefts) < 3 or len(rights) < 3:
        return None
    return (max(a.x1 for a in lefts) + min(a.x0 for a in rights)) / 2


def two_col_regions(page: "fitz.Page", crop: "fitz.Rect") -> list["fitz.Rect"]:
    """Reading-ordered regions for a two-column page. Full-width spans (title,
    authors, abstract banner, wide figures/tables) become their own full-width
    region; the two-column bands between them split into left then right. Keeps
    wide elements intact and reading order correct even when a figure interrupts
    the columns, and stops whole pages collapsing to one tiny full-width strip."""
    atoms = region_atoms(page, crop)
    gutter = estimate_gutter(atoms, crop)
    if gutter is None:
        return [crop]  # not really two-column

    cx = (crop.x0 + crop.x1) / 2
    m = crop.width * 0.04
    spans = [a for a in atoms if a.x0 < cx - m and a.x1 > cx + m]
    bands = _merge_y_bands(spans, crop)

    regions: list[fitz.Rect] = []
    y = crop.y0
    for band in bands:
        if band.y0 > y + 2:  # two-column strip above this span
            regions.append(fitz.Rect(crop.x0, y, gutter, band.y0))
            regions.append(fitz.Rect(gutter, y, crop.x1, band.y0))
        regions.append(fitz.Rect(crop.x0, max(y, band.y0), crop.x1, band.y1))
        y = band.y1
    if y < crop.y1 - 2:  # trailing two-column strip
        regions.append(fitz.Rect(crop.x0, y, gutter, crop.y1))
        regions.append(fitz.Rect(gutter, y, crop.x1, crop.y1))
    return regions


# ---------------------------------------------------------------------------
# Automatic mode selection
# ---------------------------------------------------------------------------
def _sample_indices(n: int, k: int = 12) -> list[int]:
    """Up to k page indices spread across [0, n), skipping the very first page
    (often a chapter/title page with atypical layout)."""
    if n <= 1:
        return [0] if n else []
    start = 1 if n > 3 else 0
    span = n - start
    k = min(k, span)
    return sorted({start + (i * span) // k for i in range(k)})


def median_font_size(doc: "fitz.Document", pages: list[int]) -> float | None:
    """Character-count-weighted median body font size (pt) over sampled pages."""
    weighted: list[tuple[float, int]] = []
    for i in pages:
        for block in doc[i].get_text("dict").get("blocks", []):
            if block.get("type", 0) != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    txt = span.get("text", "").strip()
                    if txt:
                        weighted.append((round(span["size"], 1), len(txt)))
    if not weighted:
        return None
    weighted.sort()
    total = sum(w for _, w in weighted)
    acc = 0
    for size, w in weighted:
        acc += w
        if acc * 2 >= total:
            return size
    return weighted[-1][0]


def two_column_fraction(doc: "fitz.Document", crops: dict[int, "fitz.Rect"],
                        pages: list[int]) -> float:
    """Fraction of sampled pages that look two-column."""
    hits = considered = 0
    for i in pages:
        crop = crops.get(i)
        if crop is None:
            continue
        considered += 1
        if detect_column_split(doc[i], crop) is not None:
            hits += 1
    return hits / considered if considered else 0.0


def choose_mode(doc: "fitz.Document", crops: dict[int, "fitz.Rect"],
                dev: Device, min_font: float) -> tuple[str, str]:
    """Return (mode, human-readable reason). Decision:
      - mostly two-column            -> 2col
      - single-column, crop is big enough on device -> crop
      - single-column, crop too small              -> fitw
    """
    pages = _sample_indices(doc.page_count)
    if not pages:
        return "crop", "empty/degenerate document"

    col_frac = two_column_fraction(doc, crops, pages)
    if col_frac >= 0.5:
        return "2col", f"{col_frac:.0%} of sampled pages are two-column"

    sampled_crops = [crops[i] for i in pages if i in crops]
    if not sampled_crops:
        return "crop", "no detectable content to measure"
    crop_w = statistics.median(c.width for c in sampled_crops)
    crop_h = statistics.median(c.height for c in sampled_crops)

    font = median_font_size(doc, pages)
    if font is None:
        # No extractable text (likely scanned): cropping is the safe default.
        return "crop", "no embedded text (scanned?); cropping margins only"

    # crop mode: device fits the WHOLE cropped page -> min of the two scales.
    crop_scale = min(dev.width_pt / crop_w, dev.height_pt / crop_h)
    eff = font * crop_scale
    if eff >= min_font:
        return "crop", (f"single-column, ~{font:.1f}pt text -> ~{eff:.1f}pt on "
                        f"device after crop (>= {min_font:.1f}pt target)")
    return "fitw", (f"single-column, ~{font:.1f}pt text -> only ~{eff:.1f}pt if "
                    f"merely cropped (< {min_font:.1f}pt); fitting to width instead")


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------
def run_crop(src: "fitz.Document", crops: dict[int, "fitz.Rect"]) -> "fitz.Document":
    """Crop margins in place by rewriting BOTH CropBox and MediaBox (Kindle
    honours only MediaBox). One input page -> one output page; text untouched."""
    for i, page in enumerate(src):
        crop = crops.get(i)
        if crop is None:
            continue
        crop = crop & page.rect
        page.set_cropbox(crop)
        src.xref_set_key(
            page.xref, "MediaBox",
            f"[{crop.x0:.2f} {crop.y0:.2f} {crop.x1:.2f} {crop.y1:.2f}]",
        )
    return src


def run_split(src: "fitz.Document", crops: dict[int, "fitz.Rect"],
              dev: Device, two_col: bool) -> "fitz.Document":
    """Rebuild as a new device-sized PDF: crop, optionally split columns,
    fit-to-width and vertically slice each region."""
    out = fitz.open()
    flow = _Flow(out, dev)
    for i, page in enumerate(src):
        crop = crops.get(i) or page_content_bbox(page) or fitz.Rect(page.rect)
        crop = crop & page.rect

        regions = two_col_regions(page, crop) if two_col else [crop]

        for region in regions:
            for rect, _kind in region_blocks(page, region):
                flow.add(src, i, rect, region)
    return out


def run_reflow(src: "fitz.Document", dev: Device, font_pt: float) -> "fitz.Document":
    """Reflow (rewrap) the document to the device width via fitz.Story so body
    text is a large, readable size regardless of the source column width — best
    for prose papers. Source font sizes are scaled proportionally so headings stay
    bigger than body. Figures embedded in the page flow inline. Equations and
    complex layout may not survive — this is the trade-off for big upright text."""
    import io
    import re

    parts: list[str] = []
    for page in src:
        xhtml = page.get_text("xhtml")
        m = re.search(r"<body[^>]*>(.*)</body>", xhtml, re.S)
        body = m.group(1) if m else xhtml
        # Drop the source's inline font sizes so our CSS size actually wins;
        # otherwise Story keeps per-span sizes (or its ~12pt default).
        body = re.sub(r"font-size\s*:\s*[0-9.]+\s*pt\s*;?", "", body)
        parts.append(body)

    # Force a uniform target body size; bold text still stands out for headings.
    html = (
        '<html><head><meta charset="utf-8"><style>'
        f'*{{font-size:{font_pt}pt;}}'
        'body{margin:0;line-height:1.35;}'
        'p{margin:0 0 0.4em 0;}'
        'img{max-width:100%;height:auto;}'
        '</style></head><body>' + "\n".join(parts) + '</body></html>'
    )

    story = fitz.Story(html=html)
    buf = io.BytesIO()
    writer = fitz.DocumentWriter(buf)
    mediabox = fitz.Rect(0, 0, dev.width_pt, dev.height_pt)
    where = fitz.Rect(PAGE_MARGIN, PAGE_MARGIN,
                      dev.width_pt - PAGE_MARGIN, dev.height_pt - PAGE_MARGIN)
    more = 1
    while more:
        dev_page = writer.begin_page(mediabox)
        more, _ = story.place(where)
        story.draw(dev_page)
        writer.end_page()
    writer.close()
    return fitz.open("pdf", buf.getvalue())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Optimize textbook PDFs for small e-ink readers (layout-preserving).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("input", nargs="?", help="input PDF")
    p.add_argument("-o", "--output", help="output PDF (default: <input>.ereader.pdf)")
    p.add_argument("--device", default="kindle6", choices=sorted(DEVICES),
                   help="target device preset (default: kindle6)")
    p.add_argument("--mode", default="auto", choices=("auto", "crop", "fitw", "2col", "reflow"),
                   help="auto=pick per document (default); crop=margins only; "
                        "fitw=fit-to-width slice; 2col=split columns; "
                        "reflow=rewrap text to screen (big upright font, prose only)")
    p.add_argument("--reflow-font", type=float, default=11.0,
                   help="reflow mode: target body font size in pt (default: 11)")
    p.add_argument("--min-font", type=float, default=8.5,
                   help="auto mode: target on-device body font in pt; below this "
                        "it slices to width instead of just cropping (default: 8.5)")
    p.add_argument("--landscape", choices=("auto", "on", "off"), default="auto",
                   help="landscape output (read device sideways) for wide single-"
                        "column docs whose text would otherwise be tiny: "
                        "auto=on when fitw text < --min-font (default), on, off")
    p.add_argument("--padding", type=float, default=4.0,
                   help="points of whitespace to keep around content (default: 4)")
    p.add_argument("--outlier-pct", type=float, default=5.0,
                   help="percentile trimmed per edge to ignore headers/footers (default: 5)")
    p.add_argument("--list-devices", action="store_true", help="list device presets and exit")
    args = p.parse_args(argv)

    if args.list_devices:
        for d in DEVICES.values():
            print(f"  {d.name:<14} {d.width_pt:6.1f} x {d.height_pt:6.1f} pt   {d.desc}")
        return 0

    if not args.input:
        p.error("input PDF is required (or use --list-devices)")

    dev = DEVICES[args.device]
    out_path = args.output or args.input.rsplit(".", 1)[0] + ".ereader.pdf"

    src = fitz.open(args.input)
    if src.page_count == 0:
        sys.exit("input PDF has no pages")

    crops = stable_crop_boxes(src, args.padding, args.outlier_pct)

    mode = args.mode
    if mode == "auto":
        mode, reason = choose_mode(src, crops, dev, args.min_font)
        print(f"[auto] chose '{mode}': {reason}")

    if mode == "reflow":
        result = run_reflow(src, dev, args.reflow_font)
        result.save(out_path, garbage=4, deflate=True)
        pages_out = result.page_count
        result.close()
        print(f"[reflow] body ~{args.reflow_font:.0f}pt")
    elif mode == "crop":
        result = run_crop(src, crops)
        result.save(out_path, garbage=4, deflate=True)
        pages_out = result.page_count
    else:
        use_dev = dev
        want_land = args.landscape == "on"
        if args.landscape == "auto" and mode == "fitw":
            cw = statistics.median([crops[i].width for i in crops]) if crops else dev.width_pt
            f = median_font_size(src, _sample_indices(src.page_count)) or 10.0
            eff = f * (dev.width_pt - 2 * PAGE_MARGIN) / cw
            want_land = eff < args.min_font
        if want_land:
            use_dev = Device(dev.name + "+landscape", dev.height_pt, dev.width_pt, dev.desc)
            print(f"[landscape] rotated for readability "
                  f"({use_dev.width_pt:.0f}x{use_dev.height_pt:.0f} pt) — read device sideways")
        result = run_split(src, crops, use_dev, two_col=(mode == "2col"))
        result.save(out_path, garbage=4, deflate=True)
        pages_out = result.page_count
        result.close()

    print(f"[{mode}] {args.input} -> {out_path}")
    print(f"  device {dev.name} ({dev.width_pt:.0f}x{dev.height_pt:.0f} pt), "
          f"{src.page_count} src pages -> {pages_out} output pages")
    src.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
