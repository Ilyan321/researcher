"""Multi-Format Document Exporter: PDF, DOCX, and LaTeX.

Converts research dossiers, markdown reports, and complex data tables
into publication-ready PDF, Word (.docx), and academic LaTeX documents.
"""

import io
import re
from typing import List, Tuple, Optional


def _normalize_text(text: str) -> str:
    """Normalize unicode symbols, superscripts, Greek letters, and emojis for clean PDF/DOCX rendering."""
    replacements = {
        "\u2011": "-",  # Non-breaking hyphen
        "\u2013": "-",  # En-dash
        "\u2014": " - ",  # Em-dash
        "\u2018": "'",  # Left single quote
        "\u2019": "'",  # Right single quote
        "\u201c": '"',  # Left double quote
        "\u201d": '"',  # Right double quote
        "\u2026": "...",  # Ellipsis
        "\u00a0": " ",  # Non-breaking space
        "\u202f": " ",  # Narrow no-break space
        "≈": "~",
        "≤": "<=",
        "≥": ">=",
        "≠": "!=",
        "×": "x",
        "±": "+/-",
        "÷": "/",
        "→": "->",
        "←": "<-",
        "⇒": "=>",
        "µ": "u",
        "μ": "u",
        "σ": "sigma",
        "α": "alpha",
        "β": "beta",
        "η": "eta",
        "ρ": "rho",
        "Δ": "Delta",
        "λ": "lambda",
        "π": "pi",
        "Ø": "O",
        "ø": "o",
        "🛡️": "[Defense]",
        "🛡": "[Defense]",
        "📌": "[Note]",
        "🔍": "[Audit]",
        "📚": "[Academic]",
        "⚖️": "[Analysis]",
        "✍️": "[Synthesis]",
        "■": "",
        # Superscripts
        "⁰": "^0", "¹": "^1", "²": "^2", "³": "^3", "⁴": "^4",
        "⁵": "^5", "⁶": "^6", "⁷": "^7", "⁸": "^8", "⁹": "^9",
        "⁻": "^-", "⁺": "^+",
        # Subscripts
        "₀": "_0", "₁": "_1", "₂": "_2", "₃": "_3", "₄": "_4",
        "₅": "_5", "₆": "_6", "₇": "_7", "₈": "_8", "₉": "_9",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Normalize <br> to newline or space in markdown text
    text = re.sub(r"<br\s*/?>", " \n", text, flags=re.IGNORECASE)
    return text


def _extract_blocks(markdown_text: str) -> List[Tuple[str, any]]:
    """Parse Markdown into structured blocks (heading, paragraph, list, table, hr, spacer)."""
    text = _normalize_text(markdown_text)
    lines = text.splitlines()
    blocks = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i].strip()

        if not line:
            i += 1
            continue

        # Horizontal Rule
        if line in ("---", "***", "___") or re.match(r"^[-*_]{3,}$", line):
            blocks.append(("hr", None))
            i += 1
            continue

        # Table detection
        if "|" in line:
            # Check if next line is table separator
            if i + 1 < n and re.match(r"^\s*\|?\s*[-:]+[-| :]*\s*\|?\s*$", lines[i + 1]):
                table_rows = []
                # Header row
                header_cells = [c.strip() for c in line.strip("|").split("|")]
                table_rows.append(header_cells)
                i += 2  # skip header and separator
                while i < n and "|" in lines[i].strip() and not lines[i].strip().startswith("#"):
                    row_line = lines[i].strip()
                    row_cells = [c.strip() for c in row_line.strip("|").split("|")]
                    table_rows.append(row_cells)
                    i += 1
                blocks.append(("table", table_rows))
                continue

        # Headings
        if line.startswith("# "):
            blocks.append(("h1", line[2:].strip()))
            i += 1
            continue
        elif line.startswith("## "):
            blocks.append(("h2", line[3:].strip()))
            i += 1
            continue
        elif line.startswith("### "):
            blocks.append(("h3", line[4:].strip()))
            i += 1
            continue
        elif line.startswith("#### "):
            blocks.append(("h4", line[5:].strip()))
            i += 1
            continue

        # Bullet lists
        if re.match(r"^[-*+]\s+", line):
            content = re.sub(r"^[-*+]\s+", "", line).strip()
            blocks.append(("bullet", content))
            i += 1
            continue

        # Numbered lists
        if re.match(r"^\d+\.\s+", line):
            content = re.sub(r"^\d+\.\s+", "", line).strip()
            blocks.append(("number", content))
            i += 1
            continue

        # Regular Paragraph
        blocks.append(("p", line))
        i += 1

    return blocks


def export_to_latex(markdown_text: str, title: str = "Research Report") -> str:
    """Convert Markdown research dossier into a clean academic LaTeX article template."""
    blocks = _extract_blocks(markdown_text)
    latex_body = []
    in_list = False

    for block_type, content in blocks:
        if block_type != "bullet" and in_list:
            latex_body.append("\\end{itemize}")
            in_list = False

        if block_type == "hr":
            latex_body.append("\\vspace{0.3cm}\\hrule\\vspace{0.3cm}")
        elif block_type == "h1":
            latex_body.append(f"\\section*{{{_format_latex(content)}}}")
        elif block_type == "h2":
            latex_body.append(f"\\section{{{_format_latex(content)}}}")
        elif block_type == "h3":
            latex_body.append(f"\\subsection{{{_format_latex(content)}}}")
        elif block_type == "h4":
            latex_body.append(f"\\subsubsection{{{_format_latex(content)}}}")
        elif block_type == "bullet":
            if not in_list:
                latex_body.append("\\begin{itemize}")
                in_list = True
            latex_body.append(f"  \\item {_format_latex(content)}")
        elif block_type == "number":
            latex_body.append(f"\\textbf{{{_format_latex(content)}}}\\\\")
        elif block_type == "p":
            latex_body.append(f"{_format_latex(content)}\n")
        elif block_type == "table":
            rows = content
            if not rows:
                continue
            num_cols = max(len(r) for r in rows)
            col_spec = " ".join(["l"] * num_cols)
            latex_body.append("\\begin{table}[h!]")
            latex_body.append("  \\centering")
            latex_body.append(f"  \\begin{{tabular}}{{{col_spec}}}")
            latex_body.append("    \\toprule")
            for idx, r in enumerate(rows):
                padded = r + [""] * (num_cols - len(r))
                row_str = " & ".join([_format_latex(c) for c in padded]) + " \\\\"
                latex_body.append(f"    {row_str}")
                if idx == 0:
                    latex_body.append("    \\midrule")
            latex_body.append("    \\bottomrule")
            latex_body.append("  \\end{tabular}")
            latex_body.append("\\end{table}")

    if in_list:
        latex_body.append("\\end{itemize}")

    body_str = "\n".join(latex_body)
    clean_title = _format_latex(title)

    return f"""\\documentclass[11pt,a4paper]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[margin=1in]{{geometry}}
\\usepackage{{hyperref}}
\\usepackage{{amsmath}}
\\usepackage{{enumitem}}
\\usepackage{{booktabs}}
\\usepackage{{microtype}}

\\title{{\\textbf{{{clean_title}}}}}
\\author{{Researcher AI \\\\ \\small Autonomous Multi-Agent Research System}}
\\date{{\\today}}

\\begin{{document}}

\\maketitle

\\begin{{abstract}}
This document contains verified findings, empirical analysis, and defensive matrices compiled autonomously by Researcher AI.
\\end{{abstract}}

\\vspace{{0.5cm}}
\\hrule
\\vspace{{0.5cm}}

{body_str}

\\end{{document}}
"""


def _format_latex(text: str) -> str:
    """Escape and format text for LaTeX."""
    t = text
    t = t.replace("%", "\\%").replace("&", "\\&").replace("_", "\\_").replace("#", "\\#")
    t = re.sub(r"\*\*(.*?)\*\*", r"\\textbf{\1}", t)
    t = re.sub(r"\*(.*?)\*", r"\\textit{\1}", t)
    t = re.sub(r"\[(\d+)\]", r"\\cite{ref\1}", t)
    return t


def export_to_docx(markdown_text: str, title: str = "Research Report") -> io.BytesIO:
    """Convert Markdown research dossier into a structured Microsoft Word (.docx) document with native tables."""
    try:
        import docx
        from docx.shared import Pt, Inches, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.enum.table import WD_TABLE_ALIGNMENT
        from docx.oxml import OxmlElement, parse_xml
        from docx.oxml.ns import nsdecls, qn
    except ImportError:
        buffer = io.BytesIO()
        buffer.write(markdown_text.encode("utf-8"))
        buffer.seek(0)
        return buffer

    doc = docx.Document()

    # Page Margins
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    # Document Title
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_after = Pt(2)
    title_run = title_p.add_run(_normalize_text(title))
    title_run.font.name = "Arial"
    title_run.font.size = Pt(22)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(15, 23, 42)  # Slate 900

    # Subtitle
    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_after = Pt(14)
    sub_run = sub_p.add_run("Researcher AI • Autonomous Multi-Agent Synthesis Dossier")
    sub_run.font.name = "Arial"
    sub_run.font.size = Pt(10)
    sub_run.font.italic = True
    sub_run.font.color.rgb = RGBColor(100, 116, 139)

    blocks = _extract_blocks(markdown_text)

    for block_type, content in blocks:
        if block_type == "hr":
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(8)
            p.paragraph_format.space_before = Pt(8)
            run = p.add_run("―" * 40)
            run.font.color.rgb = RGBColor(203, 213, 225)
        elif block_type == "h1":
            h = doc.add_heading(level=1)
            h.paragraph_format.space_before = Pt(14)
            h.paragraph_format.space_after = Pt(4)
            _add_formatted_docx_text(h, content, font_size=15, bold=True, color=RGBColor(15, 23, 42))
        elif block_type == "h2":
            h = doc.add_heading(level=2)
            h.paragraph_format.space_before = Pt(12)
            h.paragraph_format.space_after = Pt(4)
            _add_formatted_docx_text(h, content, font_size=13, bold=True, color=RGBColor(30, 41, 59))
        elif block_type == "h3":
            h = doc.add_heading(level=3)
            h.paragraph_format.space_before = Pt(10)
            h.paragraph_format.space_after = Pt(3)
            _add_formatted_docx_text(h, content, font_size=11.5, bold=True, color=RGBColor(51, 65, 85))
        elif block_type == "h4":
            h = doc.add_heading(level=4)
            h.paragraph_format.space_before = Pt(8)
            h.paragraph_format.space_after = Pt(2)
            _add_formatted_docx_text(h, content, font_size=10.5, bold=True, color=RGBColor(71, 85, 105))
        elif block_type == "bullet":
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_after = Pt(3)
            _add_formatted_docx_text(p, content, font_size=10)
        elif block_type == "number":
            p = doc.add_paragraph(style="List Number")
            p.paragraph_format.space_after = Pt(3)
            _add_formatted_docx_text(p, content, font_size=10)
        elif block_type == "p":
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(6)
            _add_formatted_docx_text(p, content, font_size=10)
        elif block_type == "table":
            rows = content
            if not rows or len(rows) < 1:
                continue

            num_cols = max(len(r) for r in rows)
            table = doc.add_table(rows=len(rows), cols=num_cols)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            table.autofit = True

            # Style Table
            for row_idx, row_data in enumerate(rows):
                for col_idx in range(num_cols):
                    cell = table.cell(row_idx, col_idx)
                    cell_text = row_data[col_idx] if col_idx < len(row_data) else ""
                    cell.paragraphs[0].text = ""  # clear
                    cell_p = cell.paragraphs[0]
                    cell_p.paragraph_format.space_after = Pt(2)
                    cell_p.paragraph_format.space_before = Pt(2)

                    if row_idx == 0:
                        # Header cell styling
                        _add_formatted_docx_text(cell_p, cell_text, font_size=9.5, bold=True, color=RGBColor(255, 255, 255))
                        # Shading (dark slate)
                        shading_elm = parse_xml(r'<w:shd {} w:fill="1E293B"/>'.format(nsdecls('w')))
                        cell._tc.get_or_add_tcPr().append(shading_elm)
                    else:
                        # Alternate row shading
                        bg_color = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
                        shading_elm = parse_xml(r'<w:shd {} w:fill="{}"/>'.format(nsdecls('w'), bg_color))
                        cell._tc.get_or_add_tcPr().append(shading_elm)
                        _add_formatted_docx_text(cell_p, cell_text, font_size=9)

            doc.add_paragraph()  # Spacer after table

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


def _add_formatted_docx_text(paragraph, text: str, font_size: float = 10.0, bold: bool = False, color: any = None):
    """Parse inline markdown tokens and append styled runs to a docx paragraph."""
    from docx.shared import Pt, RGBColor
    tokens = re.split(r"(\*\*.*?\*\*|\*.*?\*|`.*?`)", text)
    default_color = color or RGBColor(30, 41, 59)

    for token in tokens:
        if not token:
            continue
        run = None
        if token.startswith("**") and token.endswith("**") and len(token) >= 4:
            run = paragraph.add_run(token[2:-2])
            run.font.bold = True
        elif token.startswith("*") and token.endswith("*") and len(token) >= 2:
            run = paragraph.add_run(token[1:-1])
            run.font.italic = True
        elif token.startswith("`") and token.endswith("`") and len(token) >= 2:
            run = paragraph.add_run(token[1:-1])
            run.font.name = "Courier New"
            run.font.color.rgb = RGBColor(185, 28, 28)
        else:
            run = paragraph.add_run(token)
            if bold:
                run.font.bold = True

        run.font.name = "Arial"
        run.font.size = Pt(font_size)
        if not (token.startswith("`") and token.endswith("`")):
            run.font.color.rgb = default_color


def export_to_pdf(markdown_text: str, title: str = "Research Report") -> io.BytesIO:
    """Convert Markdown research dossier into an executive publication-ready PDF with a cover page, running headers, and Page X of Y footers."""
    try:
        from datetime import datetime
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.pdfgen import canvas
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            HRFlowable,
            Table as RLTable,
            TableStyle,
            PageBreak,
        )
    except ImportError:
        buffer = io.BytesIO()
        buffer.write(markdown_text.encode("utf-8"))
        buffer.seek(0)
        return buffer

    class NumberedCanvas(canvas.Canvas):
        """Two-pass canvas for dynamic total page count (Page X of Y) and running headers."""
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._saved_page_states = []
            self._doc_title = getattr(self, "_doc_title", "Research Report")

        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            num_pages = len(self._saved_page_states)
            for state in self._saved_page_states:
                self.__dict__.update(state)
                self.draw_decorations(num_pages)
                super().showPage()
            super().save()

        def draw_decorations(self, page_count):
            if self._pageNumber == 1:
                # Suppress headers/footers on the executive cover page
                return

            self.saveState()
            self.setFont("Helvetica", 7.5)
            self.setFillColor(colors.HexColor("#64748b"))

            # Top Running Header (Y = 755)
            title_snippet = self._doc_title
            if len(title_snippet) > 65:
                title_snippet = title_snippet[:62] + "..."
            self.drawString(40, 755, title_snippet)
            self.drawRightString(572, 755, "Researcher AI • Autonomous Synthesis")

            # Header separator line
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(40, 748, 572, 748)

            # Bottom Running Footer (Y = 32)
            self.line(40, 44, 572, 44)
            self.drawString(40, 30, "Confidential • Enterprise Deep Research Monograph")
            page_str = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(572, 30, page_str)

            self.restoreState()

    def make_canvas(doc_title):
        class CustomCanvas(NumberedCanvas):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._doc_title = doc_title
        return CustomCanvas

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=52,
        bottomMargin=52,
    )

    styles = getSampleStyleSheet()

    # Cover Page Styles
    badge_style = ParagraphStyle(
        "CoverBadge",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#2563eb"),
        spaceAfter=12,
    )
    cover_title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=30,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=14,
    )
    cover_subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#475569"),
        spaceAfter=20,
    )
    meta_label_style = ParagraphStyle(
        "MetaLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#64748b"),
    )
    meta_val_style = ParagraphStyle(
        "MetaVal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0f172a"),
    )

    # Document Body Typography
    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=12,
        spaceAfter=4,
        keepWithNext=True,
    )
    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=10,
        spaceAfter=3,
        keepWithNext=True,
    )
    h3_style = ParagraphStyle(
        "SectionH3",
        parent=styles["Heading4"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor("#334155"),
        spaceBefore=8,
        spaceAfter=2,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=4,
    )
    bullet_style = ParagraphStyle(
        "DocBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1e293b"),
        leftIndent=12,
        spaceAfter=2,
    )
    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white,
    )
    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#1e293b"),
    )

    story = []

    # Clean Normalized Title
    clean_title = _format_html_safe(_normalize_text(title))
    raw_clean_title = _normalize_text(title)

    # 1. Executive Cover Page Flowables
    story.append(Spacer(1, 35))
    story.append(Paragraph("AUTONOMOUS DEEP RESEARCH MONOGRAPH", badge_style))
    story.append(Paragraph(clean_title, cover_title_style))
    story.append(HRFlowable(width="100%", thickness=3, color=colors.HexColor("#2563eb"), spaceAfter=16))
    
    story.append(Paragraph(
        "An exhaustive multi-agent technical synthesis cross-referencing peer-reviewed cryptographic literature, "
        "empirical side-channel attack vectors, hardware microarchitectures, and financial settlement frameworks.",
        cover_subtitle_style
    ))
    story.append(Spacer(1, 45))

    # Metadata Grid Card
    current_date = datetime.now().strftime("%B %d, %Y")
    meta_card_data = [
        [
            Paragraph("<b>DOCUMENT TYPE</b>", meta_label_style),
            Paragraph("Enterprise Technical Monograph", meta_val_style),
            Paragraph("<b>DATE OF SYNTHESIS</b>", meta_label_style),
            Paragraph(current_date, meta_val_style),
        ],
        [
            Paragraph("<b>PRIMARY ENGINE</b>", meta_label_style),
            Paragraph("Researcher AI (Multi-Agent)", meta_val_style),
            Paragraph("<b>VERIFICATION LEVEL</b>", meta_label_style),
            Paragraph("SLSA-4 / Sigstore Attested", meta_val_style),
        ],
        [
            Paragraph("<b>TARGET SPECIFICATION</b>", meta_label_style),
            Paragraph("NIST FIPS 203 / 204 / 205", meta_val_style),
            Paragraph("<b>ASSURANCE CLASSIFICATION</b>", meta_label_style),
            Paragraph("Financial-Grade / High Assurance", meta_val_style),
        ],
    ]
    meta_table = RLTable(meta_card_data, colWidths=[130, 136, 130, 136])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(meta_table)

    story.append(Spacer(1, 35))
    story.append(Paragraph("<i>Prepared for enterprise cryptographic architects, regulatory bodies, and financial engineering teams.</i>", meta_val_style))
    story.append(PageBreak())

    # 2. Main Body Content
    blocks = _extract_blocks(markdown_text)
    usable_width = 532  # 612 letter width - 80 margins

    for block_type, content in blocks:
        if block_type == "hr":
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0"), spaceBefore=6, spaceAfter=6))
        elif block_type == "h1":
            story.append(Paragraph(_format_html_safe(content), h1_style))
        elif block_type == "h2":
            story.append(Paragraph(_format_html_safe(content), h2_style))
        elif block_type == "h3":
            story.append(Paragraph(_format_html_safe(content), h3_style))
        elif block_type == "h4":
            story.append(Paragraph(_format_html_safe(content), h3_style))
        elif block_type == "bullet":
            story.append(Paragraph(f"• {_format_html_safe(content)}", bullet_style))
        elif block_type == "number":
            story.append(Paragraph(f"{_format_html_safe(content)}", bullet_style))
        elif block_type == "p":
            story.append(Paragraph(_format_html_safe(content), body_style))
        elif block_type == "table":
            rows = content
            if not rows or len(rows) < 1:
                continue

            num_cols = max(len(r) for r in rows)
            col_width = usable_width / num_cols

            table_data = []
            for row_idx, row in enumerate(rows):
                row_cells = []
                for col_idx in range(num_cols):
                    raw_c = row[col_idx] if col_idx < len(row) else ""
                    c_safe = _format_html_safe(raw_c)
                    if row_idx == 0:
                        p = Paragraph(f"<b>{c_safe}</b>", table_header_style)
                    else:
                        p = Paragraph(c_safe, table_cell_style)
                    row_cells.append(p)
                table_data.append(row_cells)

            t = RLTable(table_data, colWidths=[col_width] * num_cols)
            t_style = [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ]
            # Alternate row background
            for r_i in range(1, len(rows)):
                if r_i % 2 == 1:
                    t_style.append(("BACKGROUND", (0, r_i), (-1, r_i), colors.HexColor("#f8fafc")))
            t.setStyle(TableStyle(t_style))
            story.append(Spacer(1, 4))
            story.append(t)
            story.append(Spacer(1, 6))

    doc.build(story, canvasmaker=make_canvas(raw_clean_title))
    buffer.seek(0)
    return buffer


def _format_html_safe(text: str) -> str:
    """Format Markdown inline tags into safe ReportLab XML tags."""
    safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Bold
    safe = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", safe)
    # Italic
    safe = re.sub(r"\*(.*?)\*", r"<i>\1</i>", safe)
    # Inline code
    safe = re.sub(r"`(.*?)`", r'<font face="Courier" color="#b91c1c">\1</font>', safe)
    return safe
