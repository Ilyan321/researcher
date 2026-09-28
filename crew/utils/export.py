"""Multi-Format Document Exporter: PDF, DOCX, and LaTeX.

Converts research dossiers and markdown reports into publication-ready documents.
"""

import io
import re
from typing import Optional


def export_to_latex(markdown_text: str, title: str = "Research Report") -> str:
    """Convert Markdown research dossier into a clean academic LaTeX article template."""
    lines = markdown_text.splitlines()
    latex_body = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            latex_body.append("")
            continue

        # Headers
        if stripped.startswith("# "):
            header_text = stripped[2:].strip()
            latex_body.append(f"\\section*{{{header_text}}}")
        elif stripped.startswith("## "):
            header_text = stripped[3:].strip()
            latex_body.append(f"\\section{{{header_text}}}")
        elif stripped.startswith("### "):
            header_text = stripped[4:].strip()
            latex_body.append(f"\\subsection{{{header_text}}}")
        elif stripped.startswith("#### "):
            header_text = stripped[5:].strip()
            latex_body.append(f"\\subsubsection{{{header_text}}}")
        elif stripped.startswith("- ") or stripped.startswith("* "):
            item_text = stripped[2:].strip()
            # Convert bold and italics
            item_text = re.sub(r"\*\*(.*?)\*\*", r"\\textbf{\1}", item_text)
            item_text = re.sub(r"\*(.*?)\*", r"\\textit{\1}", item_text)
            latex_body.append(f"\\item {item_text}")
        else:
            # Paragraph formatting
            p_text = stripped
            p_text = re.sub(r"\*\*(.*?)\*\*", r"\\textbf{\1}", p_text)
            p_text = re.sub(r"\*(.*?)\*", r"\\textit{\1}", p_text)
            p_text = re.sub(r"\[(\d+)\]", r"\\cite{ref\1}", p_text)
            latex_body.append(f"{p_text}\n")

    body_str = "\n".join(latex_body)

    latex_document = f"""\\documentclass[11pt,a4paper]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[margin=1in]{{geometry}}
\\usepackage{{hyperref}}
\\usepackage{{amsmath}}
\\usepackage{{enumitem}}
\\usepackage{{booktabs}}
\\usepackage{{microtype}}

\\title{{\\textbf{{{title}}}}}
\\author{{Researcher AI \\\\ \\small Autonomous Multi-Agent Research System}}
\\date{{\\today}}

\\begin{{document}}

\\maketitle

\\begin{{abstract}}
This document contains the verified findings and synthesis compiled autonomously by Researcher AI multi-agent pipeline.
\\end{{abstract}}

\\vspace{{0.5cm}}
\\hrule
\\vspace{{0.5cm}}

{body_str}

\\end{{document}}
"""
    return latex_document


def export_to_docx(markdown_text: str, title: str = "Research Report") -> io.BytesIO:
    """Convert Markdown research dossier into a structured Microsoft Word (.docx) document."""
    try:
        import docx
        from docx.shared import Pt, Inches, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
    except ImportError:
        # Fallback to plain text buffer if docx not available
        buffer = io.BytesIO()
        buffer.write(markdown_text.encode("utf-8"))
        buffer.seek(0)
        return buffer

    doc = docx.Document()

    # Set Margins
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Document Title
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    title_run = title_p.add_run(title)
    title_run.font.name = "Arial"
    title_run.font.size = Pt(22)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(30, 41, 59)  # Slate 800

    # Subtitle / Metadata
    sub_p = doc.add_paragraph()
    sub_run = sub_p.add_run("Autonomous Multi-Agent Research Dossier • Verified Empirical Synthesis")
    sub_run.font.name = "Arial"
    sub_run.font.size = Pt(10)
    sub_run.font.italic = True
    sub_run.font.color.rgb = RGBColor(100, 116, 139)

    doc.add_paragraph()  # Spacer

    # Parse Markdown lines
    lines = markdown_text.splitlines()
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith("# "):
            h = doc.add_heading(level=1)
            run = h.add_run(stripped[2:].strip())
            run.font.size = Pt(16)
            run.font.bold = True
        elif stripped.startswith("## "):
            h = doc.add_heading(level=2)
            run = h.add_run(stripped[3:].strip())
            run.font.size = Pt(13)
            run.font.bold = True
        elif stripped.startswith("### "):
            h = doc.add_heading(level=3)
            run = h.add_run(stripped[4:].strip())
            run.font.size = Pt(11.5)
            run.font.bold = True
        elif stripped.startswith("- ") or stripped.startswith("* "):
            p = doc.add_paragraph(style="List Bullet")
            _add_formatted_text(p, stripped[2:].strip())
        elif re.match(r"^\d+\.\s", stripped):
            p = doc.add_paragraph(style="List Number")
            num_match = re.match(r"^\d+\.\s(.*)", stripped)
            _add_formatted_text(p, num_match.group(1) if num_match else stripped)
        else:
            p = doc.add_paragraph()
            _add_formatted_text(p, stripped)

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


def export_to_pdf(markdown_text: str, title: str = "Research Report") -> io.BytesIO:
    """Convert Markdown research dossier into a styled PDF document using ReportLab."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
    except ImportError:
        # Fallback buffer
        buffer = io.BytesIO()
        buffer.write(markdown_text.encode("utf-8"))
        buffer.seek(0)
        return buffer

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette & Styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=6,
    )
    meta_style = ParagraphStyle(
        "DocMeta",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=12,
    )
    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=14,
        spaceAfter=6,
    )
    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Heading3"],
        fontSize=11.5,
        leading=15,
        textColor=colors.HexColor("#334155"),
        spaceBefore=10,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6,
    )
    bullet_style = ParagraphStyle(
        "DocBullet",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#1e293b"),
        leftIndent=15,
        spaceAfter=4,
    )

    story = []

    # Title & Subtitle
    story.append(Paragraph(title, title_style))
    story.append(Paragraph("Researcher AI • Autonomous Empirical Dossier", meta_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=14))

    lines = markdown_text.splitlines()
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Escape XML entities for ReportLab Paragraph
        safe_line = stripped.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        # Formatting
        safe_line = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", safe_line)
        safe_line = re.sub(r"\*(.*?)\*", r"<i>\1</i>", safe_line)

        if stripped.startswith("# "):
            story.append(Paragraph(safe_line[2:], h1_style))
        elif stripped.startswith("## "):
            story.append(Paragraph(safe_line[3:], h1_style))
        elif stripped.startswith("### "):
            story.append(Paragraph(safe_line[4:], h2_style))
        elif stripped.startswith("- ") or stripped.startswith("* "):
            story.append(Paragraph(f"• {safe_line[2:]}", bullet_style))
        elif re.match(r"^\d+\.\s", stripped):
            story.append(Paragraph(safe_line, bullet_style))
        else:
            story.append(Paragraph(safe_line, body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer


def _add_formatted_text(paragraph, text: str):
    """Helper to parse markdown bold and italic formatting into docx runs."""
    import re
    tokens = re.split(r"(\*\*.*?\*\*|\*.*?\*)", text)
    for token in tokens:
        if not token:
            continue
        if token.startswith("**") and token.endswith("**") and len(token) > 4:
            run = paragraph.add_run(token[2:-2])
            run.font.bold = True
        elif token.startswith("*") and token.endswith("*") and len(token) > 2:
            run = paragraph.add_run(token[1:-1])
            run.font.italic = True
        else:
            paragraph.add_run(token)
