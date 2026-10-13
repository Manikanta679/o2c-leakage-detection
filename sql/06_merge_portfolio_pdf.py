"""Build application PDFs: brief + Power BI pages framed on A4 landscape.

Power BI "Export to PDF" uses a huge page size; some viewers also mis-scale vector
embeds. This script rasterizes each report page (or uses PNG screenshots you drop in
docs/dashboard_pages/) so each dashboard fills the page like a full-screen capture.

Outputs:
  docs/O2C_Leakage_Dashboard.pdf   — 4 dashboard pages (A4 landscape)
  docs/O2C_Leakage_Portfolio.pdf   — narrative brief only (4 pages; dashboard separate)

Optional PNGs (best quality): docs/dashboard_pages/
  01_executive.png, 02_process.png, 03_leakage.png, 04_segment_region.png
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT / "docs" / "O2C_Leakage_Brief.pdf"
DASHBOARD = ROOT / "docs" / "O2C_Leakage_Dashboard.pdf"
OUT = ROOT / "docs" / "O2C_Leakage_Portfolio.pdf"
PNG_DIR = ROOT / "docs" / "dashboard_pages"
PNG_FILES = (
    "01_executive.png",
    "02_process.png",
    "03_leakage.png",
    "04_segment_region.png",
)

A4P = pymupdf.paper_rect("a4")
A4L = pymupdf.paper_rect("a4-l")
MARGIN = 14  # tight frame like a screenshot
NAVY = (0.043, 0.122, 0.227)
TEAL = (0.122, 0.435, 0.545)
GRAY = (0.29, 0.333, 0.408)


def _target_rect() -> pymupdf.Rect:
    return pymupdf.Rect(MARGIN, MARGIN, A4L.width - MARGIN, A4L.height - MARGIN)


def _placement_rect(src_w: float, src_h: float, target: pymupdf.Rect) -> pymupdf.Rect:
    if src_w <= 0 or src_h <= 0:
        raise ValueError("empty image")
    scale = min(target.width / src_w, target.height / src_h)
    w = src_w * scale
    h = src_h * scale
    x0 = target.x0 + (target.width - w) / 2
    y0 = target.y0 + (target.height - h) / 2
    return pymupdf.Rect(x0, y0, x0 + w, y0 + h)


def _new_dashboard_page(out: pymupdf.Document) -> pymupdf.Page:
    page = out.new_page(width=A4L.width, height=A4L.height)
    page.draw_rect(A4L, color=None, fill=(1, 1, 1))
    return page


def _add_png_page(out: pymupdf.Document, png_path: Path) -> None:
    page = _new_dashboard_page(out)
    target = _target_rect()
    img = pymupdf.open(str(png_path))
    try:
        base = img[0]
        # High-quality raster of the image at fit-to-page resolution
        sx = target.width / base.rect.width
        sy = target.height / base.rect.height
        z = min(sx, sy) * 2.0  # 2x for print sharpness
        pix = base.get_pixmap(matrix=pymupdf.Matrix(z, z), alpha=False)
        place = _placement_rect(pix.width, pix.height, target)
        page.insert_image(place, pixmap=pix)
    finally:
        img.close()


def _add_pdf_page_raster(out: pymupdf.Document, src: pymupdf.Document, page_index: int) -> None:
    page = _new_dashboard_page(out)
    target = _target_rect()
    src_page = src[page_index]
    sx = target.width / src_page.rect.width
    sy = target.height / src_page.rect.height
    z = min(sx, sy) * 2.0
    pix = src_page.get_pixmap(matrix=pymupdf.Matrix(z, z), alpha=False)
    place = _placement_rect(pix.width, pix.height, target)
    page.insert_image(place, pixmap=pix)


def build_dashboard_pdf(raw_export: Path, dest: Path) -> pymupdf.Document:
    src = pymupdf.open(str(raw_export))
    out = pymupdf.open()
    try:
        for i, png_name in enumerate(PNG_FILES):
            png_path = PNG_DIR / png_name
            if png_path.is_file():
                _add_png_page(out, png_path)
            else:
                if i >= src.page_count:
                    raise SystemExit(f"Missing PNG {png_path} and PDF has only {src.page_count} pages")
                _add_pdf_page_raster(out, src, i)
    finally:
        src.close()
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.save(str(dest))
    return out


def assemble_portfolio_pdf() -> None:
    """Portfolio = standard A4 brief (vector PDF, full page — not re-framed)."""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(BRIEF, OUT)


def divider_page() -> pymupdf.Document:
    doc = pymupdf.open()
    page = doc.new_page(width=A4P.width, height=A4P.height)
    page.draw_rect(A4P, color=None, fill=(1, 1, 1))
    bar_h = 52
    page.draw_rect(pymupdf.Rect(0, A4P.height - bar_h, A4P.width, A4P.height), fill=NAVY)
    page.insert_text(
        (36, A4P.height - 22),
        "O2C Leakage Detection  |  Power BI dashboard",
        fontsize=11,
        fontname="tibo",
        color=(1, 1, 1),
    )
    page.insert_textbox(
        pymupdf.Rect(A4P.width - 220, A4P.height - 30, A4P.width - 36, A4P.height - 14),
        "Manikanta Engalligi",
        fontsize=10,
        fontname="tiro",
        color=(1, 1, 1),
        align=pymupdf.TEXT_ALIGN_RIGHT,
    )
    y = A4P.height - 120
    page.insert_text((36, y), "Dashboard pages", fontsize=22, fontname="tibo", color=NAVY)
    y += 28
    page.insert_text(
        (36, y),
        "Executive  ·  Process  ·  Leakage  ·  Segment & region",
        fontsize=12,
        fontname="tiit",
        color=TEAL,
    )
    y += 36
    for line in (
        "Screenshots in docs/dashboard_pages/ are used when present (best framing).",
        "Otherwise pages are rasterized from the Power BI PDF export.",
    ):
        page.insert_text((36, y), line, fontsize=10, fontname="tiro", color=GRAY)
        y += 16
    return doc


def build_portfolio(dashboard_src: Path) -> None:
    if not BRIEF.is_file():
        raise SystemExit(f"Missing brief: {BRIEF}. Run: python sql/05_build_brief_pdf.py")
    if not dashboard_src.is_file():
        raise SystemExit(f"Missing dashboard PDF: {dashboard_src}")

    raw_copy = ROOT / "docs" / "_dashboard_export_raw.pdf"
    if dashboard_src.resolve() != raw_copy.resolve():
        shutil.copy2(dashboard_src, raw_copy)
    normalize_from = raw_copy

    build_dashboard_pdf(normalize_from, DASHBOARD)
    assemble_portfolio_pdf()

    used = [n for n in PNG_FILES if (PNG_DIR / n).is_file()]
    print("Wrote", DASHBOARD)
    print("Wrote", OUT, "bytes", OUT.stat().st_size, "(standard A4 brief, 4 pages)")
    if used:
        print("  PNG pages used:", ", ".join(used))
    missing = [n for n in PNG_FILES if not (PNG_DIR / n).is_file()]
    if missing:
        print("  Raster from PDF for:", ", ".join(missing))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        src = Path(sys.argv[1])
    elif Path(r"D:\Downloads\O2C_Leakage.pdf").is_file():
        src = Path(r"D:\Downloads\O2C_Leakage.pdf")
    else:
        raw = ROOT / "docs" / "_dashboard_export_raw.pdf"
        src = raw if raw.is_file() else DASHBOARD
    if not src.is_file():
        raise SystemExit(
            "No dashboard PDF found. Export from Power BI, then run:\n"
            "  python sql/06_merge_portfolio_pdf.py D:\\Downloads\\O2C_Leakage.pdf"
        )
    build_portfolio(src)
