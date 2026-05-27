"""
file_parser.py — extract plain text from common upload formats.

Strategy:
  .pptx  → python-pptx, walk slides, dump title + body text per slide
  .docx  → python-docx, dump paragraphs + tables, preserve heading hints
  .pdf   → pdfplumber, dump page text (and basic table extraction where possible)
  .txt / .md / .csv / .json → return decoded UTF-8 directly

The output is plain text intended for the Claude system prompt. Visual
content (images, charts, layout) is stripped; this is the right trade-off for
a re-skin / re-author flow. For multimodal jobs we'd switch to the Anthropic
Files API.
"""
from io import BytesIO
from pathlib import Path


def extract_text(filename: str, blob: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if ext in (".txt", ".md", ".csv", ".json"):
        return blob.decode("utf-8", errors="replace")
    if ext == ".pptx":
        return _parse_pptx(blob)
    if ext == ".docx":
        return _parse_docx(blob)
    if ext == ".pdf":
        return _parse_pdf(blob)
    raise ValueError(f"Unsupported file type: {ext}")


def _parse_pptx(blob: bytes) -> str:
    from pptx import Presentation

    prs = Presentation(BytesIO(blob))
    out = []
    for i, slide in enumerate(prs.slides, 1):
        out.append(f"\n=== SLIDE {i} ===")
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for para in shape.text_frame.paragraphs:
                text = "".join(run.text for run in para.runs).strip()
                if text:
                    out.append(text)
            # Tables embedded in shapes
        # Tables at slide level
        for shape in slide.shapes:
            if shape.has_table:
                out.append("[TABLE]")
                for row in shape.table.rows:
                    cells = [c.text.strip() for c in row.cells]
                    out.append(" | ".join(cells))
        # Notes
        if slide.has_notes_slide:
            notes = slide.notes_slide.notes_text_frame.text.strip()
            if notes:
                out.append(f"[NOTES] {notes}")
    return "\n".join(out)


def _parse_docx(blob: bytes) -> str:
    from docx import Document

    doc = Document(BytesIO(blob))
    out = []
    for para in doc.paragraphs:
        txt = para.text.strip()
        if not txt:
            continue
        # Preserve heading hierarchy as markdown-ish prefix
        style = (para.style.name or "").lower()
        if style.startswith("heading 1"):
            out.append(f"\n# {txt}")
        elif style.startswith("heading 2"):
            out.append(f"\n## {txt}")
        elif style.startswith("heading 3"):
            out.append(f"\n### {txt}")
        else:
            out.append(txt)
    for table in doc.tables:
        out.append("\n[TABLE]")
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells]
            out.append(" | ".join(cells))
    return "\n".join(out)


def _parse_pdf(blob: bytes) -> str:
    import pdfplumber

    out = []
    with pdfplumber.open(BytesIO(blob)) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            out.append(f"\n=== PAGE {i} ===")
            text = page.extract_text() or ""
            out.append(text.strip())
            # Attempt table extraction
            try:
                tables = page.extract_tables()
                for t in tables:
                    out.append("[TABLE]")
                    for row in t:
                        cells = [str(c).strip() if c else "" for c in row]
                        out.append(" | ".join(cells))
            except Exception:
                pass
    return "\n".join(out)
