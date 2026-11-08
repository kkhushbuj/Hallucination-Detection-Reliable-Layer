# -*- coding: utf-8 -*-
"""Build the paper PDF in the layout of the IN939 example (A4, 11 pt serif, 1.5 line spacing)."""
import sys, os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak, Table,
                                TableStyle, Image, KeepTogether, ListFlowable, ListItem)
from PIL import Image as PILImage

sys.path.insert(0, os.path.dirname(__file__))
import content1, content2, content3, content4, refs
import textwrap
from reportlab.platypus import XPreformatted

FD = "C:/Windows/Fonts/"
pdfmetrics.registerFont(TTFont("Geo", FD + "georgia.ttf"))
pdfmetrics.registerFont(TTFont("Geo-B", FD + "georgiab.ttf"))
pdfmetrics.registerFont(TTFont("Geo-I", FD + "georgiai.ttf"))
pdfmetrics.registerFont(TTFont("Geo-BI", FD + "georgiaz.ttf"))
pdfmetrics.registerFontFamily("Geo", normal="Geo", bold="Geo-B", italic="Geo-I", boldItalic="Geo-BI")

W, H = A4
LM = 70.5
TW = 454.3                     # text width (right edge 524.8)
LEAD = float(os.environ.get("LEAD", "16.5"))
BODY = 11

body = ParagraphStyle("body", fontName="Geo", fontSize=BODY, leading=LEAD, alignment=TA_JUSTIFY, firstLineIndent=18,
                      allowWidows=0, allowOrphans=0, spaceAfter=0, spaceBefore=0)
body0 = ParagraphStyle("body0", parent=body, firstLineIndent=0)
h1 = ParagraphStyle("h1", fontName="Geo-B", fontSize=16, leading=20, spaceBefore=26, spaceAfter=9, keepWithNext=1)
h2 = ParagraphStyle("h2", parent=h1, spaceBefore=20, spaceAfter=7)
h3 = ParagraphStyle("h3", fontName="Geo-B", fontSize=13.3, leading=17, spaceBefore=14, spaceAfter=5, keepWithNext=1)
bul = ParagraphStyle("bul", parent=body0, spaceAfter=2.5, leftIndent=24, bulletIndent=8, bulletFontName="Geo", bulletFontSize=11)
eq = ParagraphStyle("eq", fontName="Geo-I", fontSize=11, leading=LEAD, alignment=TA_CENTER, spaceBefore=3, spaceAfter=5)
cap = ParagraphStyle("cap", fontName="Geo-I", fontSize=9.2, leading=11.6, alignment=TA_CENTER, spaceBefore=5, spaceAfter=13)
cell = ParagraphStyle("cell", fontName="Geo", fontSize=9.2, leading=11.4)
cellb = ParagraphStyle("cellb", parent=cell, fontName="Geo-B")
cellc = ParagraphStyle("cellc", parent=cell, alignment=TA_CENTER)
cellcb = ParagraphStyle("cellcb", parent=cellb, alignment=TA_CENTER)
ref = ParagraphStyle("ref", fontName="Geo", fontSize=9.2, leading=12.2, leftIndent=33.5, firstLineIndent=-33.5,
                     spaceAfter=4, alignment=TA_LEFT)
ttl = ParagraphStyle("ttl", fontName="Geo-B", fontSize=17.2, leading=21.9, alignment=TA_CENTER)
auth = ParagraphStyle("auth", fontName="Geo", fontSize=12, leading=15, alignment=TA_CENTER, spaceBefore=22)
aff = ParagraphStyle("aff", fontName="Geo", fontSize=9.2, leading=12, alignment=TA_CENTER, spaceBefore=4)
kw = ParagraphStyle("kw", parent=body0, spaceBefore=8)
code = ParagraphStyle("code", fontName="Courier", fontSize=7.8, leading=10.3, backColor=colors.HexColor("#f4f4f2"),
                      borderPadding=(5, 6, 5, 6), spaceBefore=7, spaceAfter=11, leftIndent=6, rightIndent=6)


def page_deco(canv, doc):
    canv.saveState()
    pn = canv.getPageNumber()
    if pn > 1:
        canv.setFont("Geo-I", 9.6)
        canv.drawRightString(524.8, H - 41, content1.RUNNING)
    canv.setFont("Geo", 10)
    canv.drawCentredString(W / 2, 40, str(pn))
    canv.restoreState()


def make_table(caption, header, rows, widths):
    numeric = caption.startswith("Table 4")
    data = []
    data.append([Paragraph(h, cellcb if (numeric and i > 0) else cellb) for i, h in enumerate(header)])
    for r in rows:
        bold = r[0] == "Total" or r[0] == "All"
        data.append([Paragraph(c, (cellcb if bold else cellc) if (numeric and i > 0) else (cellb if bold else cell))
                     for i, c in enumerate(r)])
    scale = (TW - 2 * 18) / float(sum(widths))
    t = Table(data, colWidths=[w * scale for w in widths], repeatRows=1)
    st = [("LINEABOVE", (0, 0), (-1, 0), 0.9, colors.black), ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
          ("LINEBELOW", (0, -1), (-1, -1), 0.9, colors.black), ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("TOPPADDING", (0, 0), (-1, -1), 2.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.4),
          ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
    if rows and (rows[-1][0] in ("Total", "All")):
        st.append(("LINEABOVE", (0, len(rows)), (-1, len(rows)), 0.4, colors.black))
    t.setStyle(TableStyle(st))
    if len(rows) > 12:
        return [Spacer(1, 4), t, Paragraph(caption, cap)]
    return KeepTogether([Spacer(1, 4), t, Paragraph(caption, cap)])


def make_fig(path, width_in, caption):
    p = os.path.join(os.path.dirname(__file__), path)
    w, h = PILImage.open(p).size
    wpt = width_in * 72
    img = Image(p, width=wpt, height=wpt * h / w)
    return KeepTogether([Spacer(1, 3), img, Paragraph(caption, cap)])


def build(out):
    doc = BaseDocTemplate(out, pagesize=A4, leftMargin=LM, rightMargin=W - LM - TW, topMargin=66, bottomMargin=64,
                          title="LLM Trust Score: Scoring the Reliability of Language-Model Answers with Cross-Model Judges and Self-Consistency",
                          author=content1.AUTHOR)
    frame = Frame(LM, 64, TW, H - 64 - 66, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id="f")
    doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=page_deco)])
    S = []
    # title page
    S.append(Spacer(1, 38))
    for line in content1.TITLE:
        S.append(Paragraph(line, ttl))
    S.append(Paragraph(content1.AUTHOR, auth))
    S.append(Paragraph(content1.AFFIL, aff))
    S.append(Spacer(1, 34))
    S.append(Paragraph("Abstract", h1))
    S.append(Paragraph(content1.ABSTRACT, body0))
    S.append(Paragraph("<b>Keywords:</b> " + content1.KEYWORDS, kw))
    S.append(PageBreak())
    for blk in content1.B1 + content2.B2 + content3.B3 + content4.B4:
        k = blk[0]
        if k == "h1": S.append(Paragraph(blk[1], h1))
        elif k == "h2": S.append(Paragraph(blk[1], h2))
        elif k == "h3": S.append(Paragraph(blk[1], h3))
        elif k == "p": S.append(Paragraph(blk[1], body))
        elif k == "pf": S.append(Paragraph(blk[1], body0))
        elif k == "eq": S.append(Paragraph(blk[1], eq))
        elif k == "bul":
            for t in blk[1]:
                S.append(Paragraph(t, bul, bulletText="•"))
            S.append(Spacer(1, 4))
        elif k == "prompt":
            paras = blk[1].split(chr(10) * 2)
            out = []
            for pi, para in enumerate(paras):
                ls = para.split(chr(10))
                if pi == 0:
                    out.append(ls[0])
                    ls = ls[1:]
                text = " ".join(x.strip() for x in ls)
                if text:
                    out.extend(textwrap.wrap(text, 92) or [""])
                out.append("")
            esc = chr(10).join(l.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") for l in out[:-1])
            S.append(XPreformatted(esc, code))
        elif k == "code":
            lines = []
            for ln in blk[1].split(chr(10)):
                lines.extend(textwrap.wrap(ln, 90, subsequent_indent="  ") or [""])
            esc = chr(10).join(l.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") for l in lines)
            S.append(XPreformatted(esc, code))
        elif k == "table":
            tb = make_table(blk[1], blk[2], blk[3], blk[4])
            S.extend(tb if isinstance(tb, list) else [tb])
        elif k == "fig": S.append(make_fig(blk[1], blk[2], blk[3]))
    S.append(Paragraph("References", h1))
    for r in refs.REFS:
        S.append(Paragraph(r, ref))
    doc.build(S)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "paper.pdf"
    build(out)
    import pypdf
    print("pages:", len(pypdf.PdfReader(out).pages))
