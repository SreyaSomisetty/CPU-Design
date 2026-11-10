#!/usr/bin/env python3
"""
make_report.py  --  builds SAP8_Report.pdf (the project submission) by RUNNING the code.

Every listing, memory dump and result in the PDF comes from sap8.py, prog1_factorial.py
and prog2_power.py, so the report can never disagree with the repository.

USAGE
    pip install reportlab
    python3 make_report.py            # writes SAP8_Report.pdf next to this file

Needs in the same folder: sap8.py, prog1_factorial.py, prog2_power.py, prog2_power.c,
cpu_diagram.png (Figure 1, exported from cpu_diagram.svg).
"""
import math
import os
import shutil
import subprocess
import tempfile

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import (BaseDocTemplate, Flowable, Frame, HRFlowable, Image,
                                KeepTogether, PageBreak, PageTemplate, Paragraph,
                                Preformatted, Spacer, Table, TableStyle)

import prog1_factorial as prog1
import prog2_power as prog2
import sap8 as S

# =============================================================================
# TEAM DETAILS  (edit here if the split of work changes)
# =============================================================================
COURSE = "CMPE-220  |  CPU Design Project"
DATE = "November 2026"
TEAM = [  # (name, part, contribution)
    ("Sreya", "Part A", "SAP-8 design: ISA, assembler, simulator (sap8.py), block diagram, this report"),
    ("Lavya", "Part B", "Program 1: 5! written directly in SAP-8 assembly (prog1_factorial.py)"),
    ("Manasa", "Part C", "Program 2: 2^4 in C (prog2_power.c) and its translation (prog2_power.py)"),
]
# =============================================================================

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PDF = os.path.join(HERE, "SAP8_Report.pdf")

NAVY = colors.HexColor("#1B3A6B")
GREY = colors.HexColor("#E6E6E6")
MIDGREY = colors.HexColor("#8A8A8A")
C_CODE = colors.HexColor("#DCE9F7")
C_DATA = colors.HexColor("#FFF3B8")
C_EXEC = colors.HexColor("#FFC98A")
C_WRITE = colors.HexColor("#8FE08F")
C_NEXT = colors.HexColor("#1F4FBF")

PAGE_W, PAGE_H = letter
MARGIN = 0.6 * inch
CONTENT_W = PAGE_W - 2 * MARGIN

S_BODY = ParagraphStyle("body", fontName="Helvetica", fontSize=9, leading=11.5)
S_H1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=16, leading=19, textColor=NAVY, spaceAfter=2)
S_CAP_BELOW = ParagraphStyle("capb", fontName="Helvetica-Oblique", fontSize=8, leading=10,
                             alignment=TA_CENTER, spaceBefore=3, spaceAfter=9,
                             textColor=colors.HexColor("#222222"))
S_CAP_ABOVE = ParagraphStyle("capa", parent=S_CAP_BELOW, spaceBefore=6, spaceAfter=3)
S_CELL = ParagraphStyle("cell", fontName="Helvetica", fontSize=8, leading=9.5)
S_CELLH = ParagraphStyle("cellh", parent=S_CELL, fontName="Helvetica-Bold", textColor=colors.white)
S_MONO = ParagraphStyle("mono", fontName="Courier", fontSize=7.5, leading=9)
S_STEP = ParagraphStyle("step", fontName="Courier", fontSize=7, leading=8.6)
S_TITLE = ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=38, leading=42,
                         alignment=TA_CENTER, textColor=NAVY)
S_SUB = ParagraphStyle("sub", fontName="Helvetica", fontSize=14, leading=18, alignment=TA_CENTER,
                       textColor=colors.HexColor("#333333"))
S_SMALLC = ParagraphStyle("smallc", fontName="Helvetica", fontSize=10, leading=13, alignment=TA_CENTER)

_count = {"Figure": 0, "Table": 0}


def caption(kind, text, above=False):
    _count[kind] += 1
    return Paragraph(f"<b>{kind} {_count[kind]}.</b> {text}", S_CAP_ABOVE if above else S_CAP_BELOW)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def section(title):
    return [Paragraph(title, S_H1), HRFlowable(width="100%", thickness=1.4, color=NAVY, spaceAfter=6)]


# ---------------------------------------------------------------- page numbers ##/##
class NumberedCanvas(rl_canvas.Canvas):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved)
        for state in self._saved:
            self.__dict__.update(state)
            self.setStrokeColor(MIDGREY)
            self.setLineWidth(0.5)
            self.line(MARGIN, 0.55 * inch, PAGE_W - MARGIN, 0.55 * inch)
            self.setFont("Helvetica", 8.5)
            self.setFillColor(colors.HexColor("#444444"))
            self.drawString(MARGIN, 0.38 * inch, "SAP-8  |  CMPE-220 CPU Design Project")
            self.drawRightString(PAGE_W - MARGIN, 0.38 * inch, f"{self._pageNumber:02d}/{total:02d}")
            super().showPage()
        super().save()


# ---------------------------------------------------------------- Figure: instruction format
class FormatDiagram(Flowable):
    DW, DH = 580, 175

    def __init__(self, width):
        super().__init__()
        self.width, self.scale = width, width / self.DW
        self.height = self.DH * self.scale

    def wrap(self, aw, ah):
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.saveState()
        c.scale(self.scale, self.scale)
        x0, cw, gap = 125, 24, 16
        BLUE, GREEN = colors.HexColor("#BBD3F2"), colors.HexColor("#BFE8B8")
        EMPTY = colors.HexColor("#F2F2F2")

        def cx(byte, bit):
            return x0 + byte * (8 * cw + gap) + (7 - bit) * cw

        def txt(x, y, s, size=8, bold=False, align="c", col=colors.black):
            c.setFillColor(col)
            c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
            {"c": c.drawCentredString, "l": c.drawString, "r": c.drawRightString}[align](x, y, s)

        # headers
        for byte in (0, 1):
            mid = cx(byte, 7) + 4 * cw
            txt(mid, 160, f"byte at address N{'+1' if byte else ''}", 8.5, True)
            for bit in range(8):
                txt(cx(byte, bit) + cw / 2, 146, str(bit), 7, col=colors.HexColor("#555555"))

        def row(y, name, b0, b1, hexs):
            txt(x0 - 10, y + 7, name, 9, True, "r")
            for byte, val, fill in ((0, b0, BLUE), (1, b1, GREEN)):
                for bit in range(8):
                    x = cx(byte, bit)
                    if val is None:
                        c.setFillColor(EMPTY)
                    else:
                        c.setFillColor(fill)
                    c.setStrokeColor(colors.black)
                    c.setLineWidth(0.8)
                    c.rect(x, y, cw, 22, fill=1, stroke=1)
                    c.setFillColor(colors.black)
                    c.setFont("Courier-Bold", 11)
                    c.drawCentredString(x + cw / 2, y + 7, "-" if val is None else f"{val:08b}"[7 - bit])
            txt(cx(1, 0) + cw + 10, y + 7, hexs, 9, True, "l")

        row(112, "DCR (1 byte)", 0x0A, None, "= 0A")
        row(78, "LDA 0x41 (2 bytes)", 0x01, 0x41, "= 01 41")
        row(44, "LDI 5 (2 bytes)", 0x03, 0x05, "= 03 05")

        def bracket(byte, y, text):
            xl, xr = cx(byte, 7), cx(byte, 0) + cw
            c.setStrokeColor(colors.black)
            c.setLineWidth(0.9)
            c.line(xl + 1, y, xr - 1, y)
            c.line(xl + 1, y, xl + 1, y + 5)
            c.line(xr - 1, y, xr - 1, y + 5)
            txt((xl + xr) / 2, y - 10, text, 7.5, True)

        bracket(0, 30, "OPCODE")
        bracket(1, 30, "OPERAND: RAM address (LDA...) or immediate (LDI)")
        c.restoreState()


# ---------------------------------------------------------------- memory table (16 wide)
def mem_table(ram, rows, exec_addrs=(), changed=(), next_pc=None, kinds=None,
              first=0.30 * inch, col=0.195 * inch):
    rows = list(rows)
    data = [[""] + [f"{i:X}" for i in range(16)]]
    for r in rows:
        data.append([f"{r:02X}:"] + [f"{ram[r + k]:02X}" for k in range(16)])
    st = [("FONT", (0, 0), (-1, -1), "Courier", 6.6), ("FONT", (0, 0), (-1, 0), "Courier-Bold", 6.6),
          ("FONT", (0, 1), (0, -1), "Courier-Bold", 6.6), ("ALIGN", (0, 0), (-1, -1), "CENTER"),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("BACKGROUND", (0, 0), (-1, 0), GREY),
          ("BACKGROUND", (0, 1), (0, -1), GREY), ("GRID", (0, 0), (-1, -1), 0.4, MIDGREY),
          ("TOPPADDING", (0, 0), (-1, -1), 1.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6),
          ("LEFTPADDING", (0, 0), (-1, -1), 0.5), ("RIGHTPADDING", (0, 0), (-1, -1), 0.5)]

    def pos(a):
        r = a & 0xF0
        return (a % 16 + 1, rows.index(r) + 1) if r in rows else None

    if kinds:
        for a, k in kinds.items():
            p = pos(a)
            if p:
                st.append(("BACKGROUND", p, p, C_CODE if k == "code" else C_DATA))
    for a in exec_addrs:
        p = pos(a)
        if p:
            st.append(("BACKGROUND", p, p, C_EXEC))
    for a in changed:
        p = pos(a)
        if p:
            st.append(("BACKGROUND", p, p, C_WRITE))
            st.append(("FONT", p, p, "Courier-Bold", 6.6))
    if next_pc is not None and pos(next_pc):
        p = pos(next_pc)
        st.append(("BOX", p, p, 1.4, C_NEXT))
    t = Table(data, colWidths=[first] + [col] * 16)
    t.setStyle(TableStyle(st))
    return t


def legend_table(trace=True):
    sw = 0.22 * inch
    if trace:
        cells = [["", "instruction just executed (opcode + operand)", "", "byte written", "", "next instruction (PC)"]]
        widths = [sw, 2.6 * inch, sw, 0.9 * inch, sw, 1.4 * inch]
        st = [("BACKGROUND", (0, 0), (0, 0), C_EXEC), ("BACKGROUND", (2, 0), (2, 0), C_WRITE),
              ("BOX", (4, 0), (4, 0), 1.5, C_NEXT), ("GRID", (0, 0), (0, 0), 0.4, MIDGREY),
              ("GRID", (2, 0), (2, 0), 0.4, MIDGREY)]
    else:
        cells = [["", "code", "", "data"]]
        widths = [sw, 0.6 * inch, sw, 0.6 * inch]
        st = [("BACKGROUND", (0, 0), (0, 0), C_CODE), ("BACKGROUND", (2, 0), (2, 0), C_DATA),
              ("GRID", (0, 0), (0, 0), 0.4, MIDGREY), ("GRID", (2, 0), (2, 0), 0.4, MIDGREY)]
    t = Table(cells, colWidths=widths)
    t.setStyle(TableStyle([("FONT", (0, 0), (-1, -1), "Helvetica", 7.5), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)] + st))
    t.hAlign = "CENTER"
    return t


# ---------------------------------------------------------------- program runner
class Run:
    def __init__(self, source):
        self.source = source
        self.image, self.listing, self.symbols = S.assemble(source)
        self.cpu = S.SAP8(self.image)
        self.mem0 = list(self.cpu.ram)
        self.trace = self.cpu.run()
        self.rev = {v: k for k, v in self.symbols.items()}
        self.rows = S.used_rows(self.image)
        self.kinds = {}
        for r in self.listing:
            for i in range(len(r["bytes"])):
                self.kinds[r["addr"] + i] = "data" if r["text"].startswith(".byte") else "code"
        written = {a for t in self.trace for a in t["changed"]}
        self.var_addrs = sorted(a for a in written if a >= S.DATA_START)

    def sym(self, t):
        if t["operand"] is None:
            return t["name"]
        if t["name"] == "LDI":
            return f"LDI {t['operand']}"
        return f"{t['name']} {self.rev.get(t['operand'], f'0x{t['operand']:02X}')}"


def simple_table(rows, widths, mono_cols=(), header=True):
    data = []
    for ri, r in enumerate(rows):
        data.append([Paragraph(esc(c), S_CELLH if (header and ri == 0) else
                               (S_MONO if ci in mono_cols else S_CELL)) for ci, c in enumerate(r)])
    t = Table(data, colWidths=widths, repeatRows=1)
    st = [("GRID", (0, 0), (-1, -1), 0.4, MIDGREY), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
          ("BACKGROUND", (0, 0), (-1, 0), NAVY)]
    for i in range(2, len(rows), 2):
        st.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#F3F6FB")))
    t.setStyle(TableStyle(st))
    return t


def listing_table(run):
    rows = [["Addr", "Bytes", "Label", "Instruction", "Comment"]]
    for r in run.listing:
        rows.append([f"0x{r['addr']:02X}", " ".join(f"{b:02X}" for b in r["bytes"]), r["label"], r["text"],
                     Paragraph(esc(r["comment"]), S_CELL)])
    data = [[Paragraph(esc(c), S_CELLH) for c in rows[0]]] + rows[1:]
    t = Table(data, colWidths=[0.55 * inch, 0.7 * inch, 0.8 * inch, 1.2 * inch, 4.05 * inch], repeatRows=1)
    st = [("FONT", (0, 1), (3, -1), "Courier", 7.5), ("BACKGROUND", (0, 0), (-1, 0), NAVY),
          ("GRID", (0, 0), (-1, -1), 0.4, MIDGREY), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("TOPPADDING", (0, 0), (-1, -1), 1.8), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.8)]
    for i, r in enumerate(run.listing, 1):
        st.append(("BACKGROUND", (0, i), (-1, i), C_DATA if r["text"].startswith(".byte") else C_CODE))
    t.setStyle(TableStyle(st))
    return t


def trace_table(run):
    cells, prev_a = [], 0
    for t in run.trace:
        head = Paragraph(f"<b>#{t['step']:02d}</b>  0x{t['pc']:02X}: <b>{esc(run.sym(t))}</b>", S_STEP)
        regs = Paragraph(f"A {prev_a:02X}-&gt;{t['A']:02X}  B={t['B']:02X}  Z={t['Z']}  "
                         f"PC-&gt;0x{t['next_pc']:02X}", S_STEP)
        vars_ = "  ".join(f"{run.rev.get(a, hex(a))}={t['ram'][a]}" for a in run.var_addrs)
        ex = [t["pc"]] + ([t["pc"] + 1] if t["operand"] is not None else [])
        cells.append([head, regs, Paragraph(f"vars: {esc(vars_)}", S_STEP),
                      mem_table(t["ram"], run.rows, exec_addrs=ex, changed=t["changed"],
                                next_pc=None if t["halted"] else t["next_pc"])])
        prev_a = t["A"]
    rows = []
    for i in range(0, len(cells), 2):
        pair = cells[i:i + 2]
        if len(pair) == 1:
            pair.append("")
        rows.append(pair)
    tb = Table(rows, colWidths=[CONTENT_W / 2] * 2)
    tb.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.5, MIDGREY), ("INNERGRID", (0, 0), (-1, -1), 0.5, MIDGREY),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 5),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 3), ("TOPPADDING", (0, 0), (-1, -1), 3),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    return tb


def result_table(headers, values):
    n = len(headers)
    t = Table([[Paragraph(h, S_CELLH) for h in headers], [Paragraph(v, S_CELL) for v in values]],
              colWidths=[CONTENT_W / n] * n)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, MIDGREY), ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                           ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return t


def program_block(story, run, tag, title_listing):
    """Listing + initial RAM + trace, shared by both programs."""
    story += [caption("Table", f"{tag} source, assembled (blue = code, yellow = data)", above=True),
              listing_table(run), Spacer(1, 8)]
    story += [KeepTogether([caption("Table", f"{tag} initial RAM (before step 1); only 16-byte rows that hold code or data are shown",
                                    above=True),
                            mem_table(run.mem0, run.rows, next_pc=0, kinds=run.kinds), Spacer(1, 3),
                            legend_table(trace=False)])]
    story += [Spacer(1, 6), caption("Table", f"{tag} execution trace: RAM after each instruction "
                                             "(RAM = hex, vars = decimal)", above=True),
              legend_table(), Spacer(1, 5), trace_table(run), Spacer(1, 8)]


# =============================================================================
def build():
    story = []
    r1, r2 = Run(prog1.SOURCE), Run(prog2.SOURCE)
    v1, v2 = r1.cpu.ram[prog1.RESULT_ADDR], r2.cpu.ram[prog2.RESULT_ADDR]

    # ------------------------------------------------------------ title page
    story += [Spacer(1, 1.1 * inch), Paragraph("SAP-8", S_TITLE), Spacer(1, 6),
              Paragraph("Simple Accumulator Processor<br/>An 8-bit CPU: Design, Simulation and Programs<br/>"
                        "in Assembly and C", S_SUB),
              Spacer(1, 0.3 * inch),
              HRFlowable(width="60%", thickness=1.5, color=NAVY, spaceAfter=0.3 * inch, hAlign="CENTER"),
              Paragraph("<b>Team Members</b>", ParagraphStyle("tm", parent=S_SMALLC, fontSize=13, leading=16,
                                                              textColor=NAVY)),
              Spacer(1, 8)]
    team = Table([[Paragraph(h, S_CELLH) for h in ("Name", "Part", "Contribution")]] +
                 [[Paragraph(f"<b>{esc(n)}</b>", S_CELL), Paragraph(p, S_CELL), Paragraph(esc(c), S_CELL)]
                  for n, p, c in TEAM], colWidths=[1.2 * inch, 0.8 * inch, 4.8 * inch])
    team.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("GRID", (0, 0), (-1, -1), 0.5, MIDGREY),
                              ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                              ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story += [team, Spacer(1, 0.35 * inch), Paragraph(esc(COURSE), S_SMALLC), Paragraph(DATE, S_SMALLC),
              Spacer(1, 0.45 * inch)]
    summary = Table([[Paragraph(h, S_CELLH) for h in ("Program", "Written in", "Result")],
                     [Paragraph("Factorial 5!", S_CELL), Paragraph("SAP-8 assembly (directly)", S_CELL),
                      Paragraph(f"{v1}", S_CELL)],
                     [Paragraph("Exponent 2^4", S_CELL), Paragraph("C, translated by hand to assembly", S_CELL),
                      Paragraph(f"{v2}", S_CELL)]], colWidths=[1.6 * inch, 3.0 * inch, 1.2 * inch])
    summary.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("GRID", (0, 0), (-1, -1), 0.5, MIDGREY),
                                 ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    summary.hAlign = "CENTER"
    story += [summary, PageBreak()]

    # ------------------------------------------------------------ 1. design
    story += section("1.  CPU Design")
    spec = [["Property", "SAP-8"],
            ["Architecture", "Accumulator machine; code and data share one RAM"],
            ["Data path", "8 bits; arithmetic wraps modulo 256"],
            ["RAM", "256 bytes (0x00 - 0xFF); code segment 0x00 - 0x3F, data segment 0x40 - 0xFF"],
            ["Registers", "A (accumulator), B (temp), PC (program counter); internal IR and OPR"],
            ["Flag", "Z (zero)"],
            ["Instruction format", "1 opcode byte, plus 1 operand byte for 2-byte instructions"],
            ["Instruction set", "15 instructions (see Table 3)"],
            ["Cycle", "Fetch -> Decode -> Execute (simulator prints RAM after every cycle)"]]
    story += [caption("Table", "SAP-8 specification", above=True),
              simple_table(spec, [1.5 * inch, 5.8 * inch]), Spacer(1, 8)]
    from reportlab.lib.utils import ImageReader
    iw, ih = ImageReader(os.path.join(HERE, "cpu_diagram.png")).getSize()
    img_h = CONTENT_W * ih / iw
    story += [KeepTogether([Image(os.path.join(HERE, "cpu_diagram.png"), width=CONTENT_W, height=img_h),
                            caption("Figure", "SAP-8 block diagram (registers, ALU, control unit, buses, RAM)")])]
    steps = [["#", "Phase", "What happens"],
             ["1", "Fetch", "IR <- RAM[PC]   (opcode byte)"],
             ["2", "Fetch", "If the instruction has an operand: OPR <- RAM[PC+1]"],
             ["3", "Advance", "PC <- PC + 1  (1-byte)  or  PC + 2  (2-byte)"],
             ["4", "Decode", "Control unit reads the opcode in IR"],
             ["5", "Execute", "Memory op, ALU op (updates Z), register move, or jump (tests Z, may load PC)"]]
    story += [caption("Table", "Fetch-decode-execute steps", above=True),
              simple_table(steps, [0.3 * inch, 1.0 * inch, 6.0 * inch])]
    story.append(PageBreak())

    # ------------------------------------------------------------ 2. encoding
    story += section("2.  Instruction Encoding")
    story += [KeepTogether([FormatDiagram(CONTENT_W),
                            caption("Figure", "Instruction formats: 1-byte and 2-byte, with worked examples")])]
    z_set = {"LDA", "LDI", "ADD", "SUB", "MUL", "DCR", "INR", "MOV_BA"}
    ex = {"NOP": "00", "LDA": "LDA 0x41 = 01 41", "STA": "STA 0x41 = 02 41", "LDI": "LDI 5 = 03 05",
          "ADD": "ADD 0x40 = 04 40", "SUB": "SUB 0x40 = 05 40", "MUL": "MUL 0x40 = 06 40",
          "JMP": "JMP 0x08 = 07 08", "JZ": "JZ 0x11 = 08 11", "JNZ": "JNZ 0x08 = 09 08",
          "DCR": "0A", "INR": "0B", "MOV_AB": "0C", "MOV_BA": "0D", "HLT": "FF"}
    ex["NOP"], ex["DCR"], ex["INR"] = "NOP = 00", "DCR = 0A", "INR = 0B"
    ex["MOV_AB"], ex["MOV_BA"], ex["HLT"] = "MOV_AB = 0C", "MOV_BA = 0D", "HLT = FF"
    rows = [["Opcode", "Binary", "Mnemonic", "Operand", "Bytes", "Operation", "Z flag", "Example = bytes"]]
    for name, (op, has, kind, desc) in sorted(S.ISA.items(), key=lambda kv: kv[1][0]):
        rows.append([f"{op:02X}", f"{op:08b}", name, kind if has else "--", "2" if has else "1", desc,
                     "set" if name in z_set else "unchanged", ex[name]])
    story += [caption("Table", "SAP-8 instruction set and encoding", above=True),
              simple_table(rows, [0.62 * inch, 0.82 * inch, 0.78 * inch, 0.68 * inch, 0.52 * inch, 1.5 * inch,
                                  0.7 * inch, 1.68 * inch], mono_cols=(0, 1, 2, 7)), Spacer(1, 8)]
    story += [caption("Table", "Z flag rule: Z = 1 when the last result written to A was 0", above=True),
              simple_table([["Event", "A after", "Z"],
                            ["LDI 0", "00", "1"], ["DCR on A = 01", "00", "1"],
                            ["INR on A = FF (8-bit wrap)", "00", "1"], ["DCR on A = 05", "04", "0"],
                            ["STA / MOV_AB / jumps", "unchanged", "unchanged"]],
                           [3.0 * inch, 2.0 * inch, 2.3 * inch])]
    story.append(PageBreak())

    # ------------------------------------------------------------ 3. program 1
    story += section("3.  Program 1: Factorial 5!  (written directly in assembly)")
    program_block(story, r1, "Program 1", "")
    story += [KeepTogether([
        caption("Table", "Program 1 result", above=True),
        result_table(["Result variable", "CPU result", "Expected (Python)", "Instructions executed", "Verdict"],
                     [f"RES @ 0x{prog1.RESULT_ADDR:02X}", f"<b>{v1}</b> (0x{v1:02X})",
                      f"math.factorial(5) = {math.factorial(5)}", str(r1.cpu.steps),
                      "<b>PASS</b>" if v1 == math.factorial(5) else "<b>FAIL</b>"])])]
    story.append(PageBreak())

    # ------------------------------------------------------------ 4. program 2
    story += section("4.  Program 2: Exponent 2^4  (written in C, translated to assembly)")
    csrc = open(os.path.join(HERE, "prog2_power.c")).read().splitlines()
    numbered = "\n".join(f"{i:2d}  {l}" for i, l in enumerate(csrc, 1))
    ct = Table([[Preformatted(numbered, ParagraphStyle("c", fontName="Courier", fontSize=7, leading=8.5))]],
               colWidths=[CONTENT_W])
    ct.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F5F5")),
                            ("BOX", (0, 0), (-1, -1), 0.5, MIDGREY)]))
    story += [caption("Table", "Program 2 C source (prog2_power.c)", above=True), ct, Spacer(1, 8)]

    L = {r["addr"]: r for r in r2.listing}

    def tr(c_txt, addrs):
        asm = "\n".join(L[a]["text"] for a in addrs)
        byt = "\n".join(" ".join(f"{b:02X}" for b in L[a]["bytes"]) for a in addrs)
        return [Preformatted(c_txt, S_MONO), Preformatted(asm, S_MONO), Preformatted(byt, S_MONO)]

    code_addrs = sorted(a for a, r in L.items() if not r["text"].startswith(".byte"))
    # statement -> instruction addresses, derived from the listing so it always matches
    idx = {a: i for i, a in enumerate(code_addrs)}
    ca = lambda *i: [code_addrs[k] for k in i]
    trows = [[Paragraph(h, S_CELLH) for h in ("C statement", "SAP-8 assembly", "Bytes")],
             tr("int base=2, expo=4, result=1;", sorted(a for a in L if a >= S.DATA_START)),
             tr("while (expo != 0)", ca(0, 1)),
             tr("  result = result * base;", ca(2, 3, 4)),
             tr("  expo = expo - 1;", ca(5, 6, 7)),
             tr("}   /* end of loop body */", ca(8)),
             tr("return 0;", ca(9))]
    tt = Table(trows, colWidths=[2.6 * inch, 2.6 * inch, 2.1 * inch])
    tt.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, MIDGREY), ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    story += [caption("Table", "C-to-assembly translation (line by line)", above=True), tt, Spacer(1, 8)]
    program_block(story, r2, "Program 2", "")
    host = "n/a (gcc not found)"
    if shutil.which("gcc"):
        try:
            with tempfile.TemporaryDirectory() as d:
                exe = os.path.join(d, "power")
                subprocess.run(["gcc", os.path.join(HERE, "prog2_power.c"), "-o", exe], check=True,
                               capture_output=True)
                host = subprocess.run([exe], capture_output=True, text=True).stdout.strip()
        except Exception:
            host = "n/a (compile failed)"
    story += [KeepTogether([
        caption("Table", "Program 2 result", above=True),
        result_table(["Result variable", "CPU result", "Expected (Python)", "Same C file via gcc",
                      "Instructions executed", "Verdict"],
                     [f"result @ 0x{prog2.RESULT_ADDR:02X}", f"<b>{v2}</b> (0x{v2:02X})", f"2**4 = {2 ** 4}",
                      host, str(r2.cpu.steps), "<b>PASS</b>" if v2 == 2 ** 4 else "<b>FAIL</b>"])])]
    story.append(PageBreak())

    # ------------------------------------------------------------ 5. run + contributions
    story += section("5.  How to Run, Files and Team Contributions")
    cmds = [["Command", "Effect"],
            ["python3 sap8.py", "Print the instruction-encoding table"],
            ["python3 prog1_factorial.py", "Program 1: listing + RAM after every instruction"],
            ["python3 prog2_power.py", "Program 2: listing + RAM after every instruction"],
            ["python3 test_sap8.py", "Self-test (expects: ALL TESTS PASSED)"],
            ["gcc prog2_power.c -o power && ./power", "Run the original C program on the host (prints 16)"],
            ["pip install reportlab && python3 make_report.py", "Rebuild this PDF from the live code"]]
    story += [caption("Table", "Commands (Python 3.8+; only the last one needs a package)", above=True),
              simple_table(cmds, [3.6 * inch, 3.7 * inch], mono_cols=(0,)), Spacer(1, 8)]
    files = [["File", "Owner", "Purpose"],
             ["sap8.py", "Sreya (A)", "ISA, assembler, CPU simulator, memory-dump printer"],
             ["cpu_diagram.svg / .png", "Sreya (A)", "Block diagram (Figure 1)"],
             ["make_report.py", "Sreya (A)", "Generates this PDF"],
             ["prog1_factorial.py", "Lavya (B)", "5! in assembly"],
             ["prog2_power.c", "Manasa (C)", "2^4 in C"],
             ["prog2_power.py", "Manasa (C)", "C translated to SAP-8 assembly"],
             ["test_sap8.py", "team", "Self-test"],
             ["README.md / TASKS.md", "team", "Instructions and task division"]]
    story += [caption("Table", "Project files and owners", above=True),
              simple_table(files, [2.0 * inch, 1.2 * inch, 4.1 * inch], mono_cols=(0,))]

    doc = BaseDocTemplate(OUT_PDF, pagesize=letter, leftMargin=MARGIN, rightMargin=MARGIN,
                          topMargin=0.6 * inch, bottomMargin=0.75 * inch,
                          title="SAP-8: CPU Design Project", author=", ".join(n for n, _, _ in TEAM))
    frame = Frame(MARGIN, 0.75 * inch, CONTENT_W, PAGE_H - 1.35 * inch, id="f", leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="p", frames=[frame])])
    doc.build(story, canvasmaker=NumberedCanvas)
    print("wrote", OUT_PDF)


if __name__ == "__main__":
    build()
