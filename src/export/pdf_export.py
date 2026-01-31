# src/export/pdf_export.py
from __future__ import annotations

import io
from typing import List

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Preformatted,
    PageBreak,
)
from reportlab.pdfbase.pdfmetrics import stringWidth


def _header_footer(canvas, doc, title: str, client_name: str):
    """
    Draw a simple header + footer on every page.
    """
    canvas.saveState()

    width, height = doc.pagesize
    left = doc.leftMargin
    right = width - doc.rightMargin

    # Header
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(left, height - 0.65 * inch, title)

    if client_name:
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(right, height - 0.65 * inch, f"Prepared for: {client_name}")

    # Divider line under header
    canvas.setStrokeColor(colors.lightgrey)
    canvas.setLineWidth(0.7)
    canvas.line(left, height - 0.72 * inch, right, height - 0.72 * inch)

    # Footer
    canvas.setStrokeColor(colors.lightgrey)
    canvas.setLineWidth(0.7)
    canvas.line(left, 0.75 * inch, right, 0.75 * inch)

    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.grey)
    canvas.drawString(left, 0.55 * inch, "Travel Planner Report")
    canvas.drawRightString(right, 0.55 * inch, f"Page {doc.page}")

    canvas.restoreState()


def build_itinerary_pdf(title: str, client_name: str, content: str) -> bytes:
    """
    Create a clean, client-ready PDF from your plain-text report.

    - Uses Platypus flowables for proper wrapping and multi-page layout.
    - Preserves indentation for lines like " Address: ...".
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.95 * inch,
        bottomMargin=0.9 * inch,
        title=title,
        author="Travel Planner",
    )

    styles = getSampleStyleSheet()

    # Main body style (for wrapped paragraphs)
    body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=13,
        spaceAfter=6,
    )

    # Preformatted style keeps indentation aligned (monospace look)
    # Use this for lines where you care about exact spacing.
    pre = ParagraphStyle(
        "Pre",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=9.5,
        leading=12,
        spaceAfter=2,
    )

    story: List = []

    # We’ll render each line. If it has leading spaces, keep it as Preformatted.
    # Otherwise, treat it as a normal Paragraph (wraps naturally).
    lines = (content or "").splitlines()

    for ln in lines:
        if ln.strip() == "":
            story.append(Spacer(1, 8))
            continue

        # Page-break safety: if user ever inserts a hard marker
        if ln.strip().upper() == "__PAGEBREAK__":
            story.append(PageBreak())
            continue

        # Preserve exact formatting for indented lines (addresses)
        if ln.startswith(" ") or ln.startswith("\t"):
            story.append(Preformatted(ln.rstrip(), pre))
            continue

        # Preserve separators nicely
        if set(ln.strip()) == {"="} or set(ln.strip()) == {"-"}:
            story.append(Paragraph(f"<font color='#666666'>{ln}</font>", body))
            continue

        # Normal wrapped paragraph
        safe_text = (
            ln.replace("&", "&amp;")
              .replace("<", "&lt;")
              .replace(">", "&gt;")
        )
        story.append(Paragraph(safe_text, body))

    doc.build(
        story,
        onFirstPage=lambda c, d: _header_footer(c, d, title=title, client_name=client_name),
        onLaterPages=lambda c, d: _header_footer(c, d, title=title, client_name=client_name),
    )

    buffer.seek(0)
    return buffer.read()
