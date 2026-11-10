#!/usr/bin/env python3
"""
sap8.py  --  SAP-8 (Simple Accumulator Processor, 8-bit)      CMPE-220 CPU Design
Part A: ISA definition, assembler, CPU simulator, memory-dump / trace printer.

RUN
    python3 sap8.py          # prints the instruction-encoding table

USE FROM A PROGRAM (see prog1_factorial.py / prog2_power.py)
    from sap8 import run_program
    run_program(SOURCE, title="5! = 120", result_label="RES", result_addr=0x41)

MACHINE
    Data path .... 8 bits (arithmetic wraps modulo 256)
    RAM .......... 256 bytes, 0x00-0xFF   (code 0x00-0x3F, data 0x40-0xFF)
    Registers .... A (accumulator), B (temp), PC (program counter)
    Flag ......... Z (zero)
    Instruction .. 1 opcode byte, plus 1 operand byte for LDA/STA/LDI/ADD/SUB/MUL/JMP/JZ/JNZ
    Z flag ....... set by LDA LDI ADD SUB MUL DCR INR MOV_BA  (Z=1 when A becomes 0)
                   left unchanged by STA MOV_AB JMP JZ JNZ NOP HLT
"""
import re
import sys

RAM_SIZE = 256
CODE_END = 0x3F          # code segment 0x00-0x3F
DATA_START = 0x40        # data segment 0x40-0xFF

# mnemonic -> (opcode, has_operand, operand kind, description)
ISA = {
    "NOP":    (0x00, False, "--",   "no operation"),
    "LDA":    (0x01, True,  "addr", "A <- RAM[addr]"),
    "STA":    (0x02, True,  "addr", "RAM[addr] <- A"),
    "LDI":    (0x03, True,  "imm",  "A <- immediate"),
    "ADD":    (0x04, True,  "addr", "A <- A + RAM[addr]"),
    "SUB":    (0x05, True,  "addr", "A <- A - RAM[addr]"),
    "MUL":    (0x06, True,  "addr", "A <- A * RAM[addr]"),
    "JMP":    (0x07, True,  "addr", "PC <- addr"),
    "JZ":     (0x08, True,  "addr", "if Z==1: PC <- addr"),
    "JNZ":    (0x09, True,  "addr", "if Z==0: PC <- addr"),
    "DCR":    (0x0A, False, "--",   "A <- A - 1"),
    "INR":    (0x0B, False, "--",   "A <- A + 1"),
    "MOV_AB": (0x0C, False, "--",   "B <- A"),
    "MOV_BA": (0x0D, False, "--",   "A <- B"),
    "HLT":    (0xFF, False, "--",   "halt"),
}
BY_OPCODE = {v[0]: k for k, v in ISA.items()}


# ============================================================================
# 1. Assembler
# ============================================================================
class AsmError(Exception):
    pass


def _num(tok):
    return int(tok, 0)          # decimal (5) or hex (0x40)


def assemble(source):
    """
    Two-pass assembler.
    Syntax:   [label:] MNEMONIC [operand]   ; comment
              .org ADDR                      set location counter
              [label:] .byte VALUE           one data byte
    Returns (image, listing, symbols)
        image   : dict {address: byte}
        listing : list of dicts {addr, bytes, label, text, comment}
        symbols : dict {label: address}
    """
    lines = []
    for n, raw in enumerate(source.splitlines(), 1):
        code, _, comment = raw.partition(";")
        lines.append((n, code.strip(), comment.strip()))

    def split_label(code):
        m = re.match(r"^(\w+):\s*(.*)$", code)
        return (m.group(1), m.group(2)) if m else ("", code)

    # ---- pass 1: labels ------------------------------------------------------
    symbols, pc = {}, 0
    for n, code, _ in lines:
        label, code = split_label(code)
        if label:
            symbols[label] = pc
        if not code:
            continue
        tok = code.split()
        op = tok[0].upper()
        if op == ".ORG":
            pc = _num(tok[1])
        elif op == ".BYTE":
            pc += 1
        elif op in ISA:
            pc += 1 + (1 if ISA[op][1] else 0)
        else:
            raise AsmError(f"line {n}: unknown mnemonic '{tok[0]}'")

    # ---- pass 2: encode ------------------------------------------------------
    image, listing, pc = {}, [], 0

    def value(tok, n):
        if tok in symbols:
            return symbols[tok]
        try:
            return _num(tok)
        except ValueError:
            raise AsmError(f"line {n}: unknown symbol '{tok}'")

    for n, code, comment in lines:
        label, code = split_label(code)
        if not code:
            continue
        tok = code.split()
        op = tok[0].upper()
        if op == ".ORG":
            pc = _num(tok[1])
            continue
        if op == ".BYTE":
            b = [value(tok[1], n) & 0xFF]
            text = f".byte {tok[1]}"
        else:
            opcode, has_operand, _, _ = ISA[op]
            if has_operand:
                if len(tok) < 2:
                    raise AsmError(f"line {n}: {op} needs an operand")
                b = [opcode, value(tok[1], n) & 0xFF]
                text = f"{op} {tok[1]}"
            else:
                b = [opcode]
                text = op
        if pc + len(b) > RAM_SIZE:
            raise AsmError(f"line {n}: program does not fit in RAM")
        for i, byte in enumerate(b):
            image[pc + i] = byte
        listing.append(dict(addr=pc, bytes=b, label=label, text=text, comment=comment))
        pc += len(b)
    return image, listing, symbols


# ============================================================================
# 2. CPU simulator
# ============================================================================
class SAP8:
    def __init__(self, image):
        self.ram = [0] * RAM_SIZE
        for a, b in image.items():
            self.ram[a] = b
        self.A = self.B = self.PC = self.Z = 0
        self.halted = False
        self.steps = 0

    def _load_a(self, v):
        """Write A (8-bit wrap) and update Z."""
        self.A = v & 0xFF
        self.Z = 1 if self.A == 0 else 0

    def step(self):
        """Execute one instruction; return a snapshot for the trace printer."""
        before = list(self.ram)
        pc0 = self.PC
        opcode = self.ram[self.PC]                     # FETCH opcode
        name = BY_OPCODE.get(opcode)
        if name is None:
            raise RuntimeError(f"illegal opcode 0x{opcode:02X} at 0x{pc0:02X}")
        has_operand = ISA[name][1]
        operand = self.ram[(self.PC + 1) % RAM_SIZE] if has_operand else None  # FETCH operand
        self.PC = (self.PC + 1 + (1 if has_operand else 0)) % RAM_SIZE

        # EXECUTE
        if   name == "LDA": self._load_a(self.ram[operand])
        elif name == "STA": self.ram[operand] = self.A
        elif name == "LDI": self._load_a(operand)
        elif name == "ADD": self._load_a(self.A + self.ram[operand])
        elif name == "SUB": self._load_a(self.A - self.ram[operand])
        elif name == "MUL": self._load_a(self.A * self.ram[operand])
        elif name == "JMP": self.PC = operand
        elif name == "JZ":
            if self.Z == 1: self.PC = operand
        elif name == "JNZ":
            if self.Z == 0: self.PC = operand
        elif name == "DCR": self._load_a(self.A - 1)
        elif name == "INR": self._load_a(self.A + 1)
        elif name == "MOV_AB": self.B = self.A
        elif name == "MOV_BA": self._load_a(self.B)
        elif name == "HLT": self.halted = True
        self.steps += 1

        return dict(step=self.steps, pc=pc0, name=name, operand=operand,
                    text=name if operand is None else f"{name} 0x{operand:02X}",
                    A=self.A, B=self.B, next_pc=self.PC, Z=self.Z,
                    halted=self.halted, ram=list(self.ram),
                    changed=[i for i in range(RAM_SIZE) if self.ram[i] != before[i]])

    def run(self, max_steps=10000):
        trace = []
        while not self.halted and self.steps < max_steps:
            trace.append(self.step())
        return trace


# ============================================================================
# 3. Printing: encoding table, memory dump, trace
# ============================================================================
def print_encoding_table():
    print("SAP-8 INSTRUCTION ENCODING")
    print(" Opcode  Mnemonic  Operand  Bytes  Operation")
    print(" ------  --------  -------  -----  ----------------------")
    for name, (op, has, kind, desc) in sorted(ISA.items(), key=lambda kv: kv[1][0]):
        print(f"   {op:02X}    {name:<8}  {kind:<7}  {2 if has else 1:^5}  {desc}")


def print_memory(ram, rows=(0x00, 0x40)):
    """16-wide hex grid. Row label = high nibble. Only the rows in `rows` are shown."""
    print("       " + " ".join(f"{c:02X}" for c in range(16)))
    print("      " + "-" * 47)
    for r in rows:
        cells = " ".join(f"{ram[r + c]:02X}" for c in range(16))
        tag = "  <- code" if r <= CODE_END else "  <- data"
        print(f" {r:02X} | {cells}{tag}")


def reg_line(cpu_or_snap):
    s = cpu_or_snap
    state = "halt" if s["halted"] else "run"
    return f" A={s['A']:02X}   B={s['B']:02X}   PC={s['next_pc']:02X}   Z={s['Z']}   [{state}]"


def print_listing(listing):
    print("ASSEMBLY LISTING")
    print(" addr  bytes   label     instruction      ; comment")
    for r in listing:
        by = " ".join(f"{b:02X}" for b in r["bytes"])
        print(f" {r['addr']:02X}    {by:<7} {r['label']:<9} {r['text']:<16} ; {r['comment']}")


def used_rows(image):
    """Rows (high nibble) of the 16-wide grid that contain assembled bytes."""
    return tuple(sorted({a & 0xF0 for a in image}))


def run_program(source, title="", result_label="RESULT", result_addr=None,
                rows=None, max_steps=10000):
    """Assemble `source`, run it, print RAM + registers after every instruction.
    rows=None -> show every 16-byte row that holds code or data."""
    image, listing, symbols = assemble(source)
    cpu = SAP8(image)
    if rows is None:
        rows = used_rows(image)
    if title:
        print("=" * 60 + f"\n {title}\n" + "=" * 60)
    print_listing(listing)
    print("\nINITIAL RAM")
    print_memory(cpu.ram, rows)
    print()
    trace = cpu.run(max_steps)
    for t in trace:
        print(f"--- step {t['step']:>3} | 0x{t['pc']:02X}: {t['text']}")
        print_memory(t["ram"], rows)
        print(reg_line(t))
        if t["changed"]:
            print(" written: " + ", ".join(f"RAM[0x{a:02X}]=0x{t['ram'][a]:02X}" for a in t["changed"]))
        print()
    print(f"HALTED after {cpu.steps} instructions.")
    if result_addr is not None:
        v = cpu.ram[result_addr]
        print(f"RESULT: {result_label} @ 0x{result_addr:02X} = {v} (0x{v:02X})")
    return cpu, trace


if __name__ == "__main__":
    print_encoding_table()
