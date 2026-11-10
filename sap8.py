#!/usr/bin/env python3
"""
SAP-8 : Simple Accumulator Processor (8-bit)
============================================
Part A deliverable (owner: Sreya).

A tiny accumulator-based CPU simulator.

Architecture
------------
  * 8-bit data path, 256 bytes of RAM (0x00..0xFF)
  * Registers : A  (accumulator)
                B  (temporary register)
                PC (program counter)
  * Flag      : Z  (zero flag) - set from the accumulator after ALU ops
  * Variable length instructions:
        1 opcode byte, optionally followed by 1 operand byte
        (operand = a RAM address or an 8-bit immediate)

Memory map (convention used by all demo programs)
  0x00 .. 0x3F : program (code)
  0x40 .. 0xFF : data

The simulator loads a program (list of bytes) into RAM starting at 0x00,
then executes ONE instruction per step, printing the register state and a
window of RAM after EVERY instruction so memory changes are visible.
"""

# ----------------------------------------------------------------------
# Instruction set   opcode -> (mnemonic, operand_bytes)
# ----------------------------------------------------------------------
#   operand_bytes = 0 : opcode only
#   operand_bytes = 1 : opcode followed by one byte (address or immediate)
ISA = {
    0x00: ("NOP",    0),   # no operation
    0x01: ("LDA",    1),   # A  <- RAM[addr]
    0x02: ("STA",    1),   # RAM[addr] <- A
    0x03: ("LDI",    1),   # A  <- immediate
    0x04: ("ADD",    1),   # A  <- A + RAM[addr]
    0x05: ("SUB",    1),   # A  <- A - RAM[addr]
    0x06: ("MUL",    1),   # A  <- A * RAM[addr]
    0x07: ("JMP",    1),   # PC <- addr
    0x08: ("JZ",     1),   # if Z==1: PC <- addr
    0x09: ("JNZ",    1),   # if Z==0: PC <- addr
    0x0A: ("DCR",    0),   # A  <- A - 1
    0x0B: ("INR",    0),   # A  <- A + 1
    0x0C: ("MOV_AB", 0),   # B  <- A
    0x0D: ("MOV_BA", 0),   # A  <- B
    0xFF: ("HLT",    0),   # halt
}

# reverse map  mnemonic -> opcode  (used by the assembler)
OPC = {name: code for code, (name, _) in ISA.items()}


class SAP8:
    """The CPU: registers, RAM, and a single-step execution engine."""

    def __init__(self, program, data=None, mem_size=256):
        self.mem = [0] * mem_size
        self.A = 0
        self.B = 0
        self.PC = 0
        self.Z = 0
        self.halted = False
        self.mem_size = mem_size

        # load program at 0x00
        for i, byte in enumerate(program):
            self.mem[i] = byte & 0xFF
        self.prog_len = len(program)

        # load data segment (dict addr -> value) if provided
        if data:
            for addr, val in data.items():
                self.mem[addr] = val & 0xFF

    # -- internal helpers ---------------------------------------------
    def _setA(self, value):
        """Write the accumulator (wrap to 8 bits) and update the Z flag."""
        self.A = value & 0xFF
        self.Z = 1 if self.A == 0 else 0

    def fetch(self):
        """Read the byte at PC and advance PC."""
        byte = self.mem[self.PC]
        self.PC = (self.PC + 1) & 0xFF
        return byte

    # -- the fetch / decode / execute cycle ---------------------------
    def step(self):
        """Execute a single instruction. Return a text decode of it."""
        if self.halted:
            return "HALTED"

        opcode = self.fetch()                       # FETCH opcode
        name, nargs = ISA.get(opcode, ("???", 0))   # DECODE
        operand = self.fetch() if nargs == 1 else None

        # EXECUTE
        if name == "NOP":
            pass
        elif name == "LDA":
            self._setA(self.mem[operand])
        elif name == "STA":
            self.mem[operand] = self.A
        elif name == "LDI":
            self._setA(operand)
        elif name == "ADD":
            self._setA(self.A + self.mem[operand])
        elif name == "SUB":
            self._setA(self.A - self.mem[operand])
        elif name == "MUL":
            self._setA(self.A * self.mem[operand])
        elif name == "JMP":
            self.PC = operand
        elif name == "JZ":
            if self.Z == 1:
                self.PC = operand
        elif name == "JNZ":
            if self.Z == 0:
                self.PC = operand
        elif name == "DCR":
            self._setA(self.A - 1)
        elif name == "INR":
            self._setA(self.A + 1)
        elif name == "MOV_AB":
            self.B = self.A
        elif name == "MOV_BA":
            self._setA(self.B)
        elif name == "HLT":
            self.halted = True
        else:
            raise ValueError(f"Unknown opcode {opcode:#04x}")

        if operand is None:
            return name
        return f"{name} {operand:#04x}"


# ----------------------------------------------------------------------
# Pretty printing   (memory dump + register line + full trace)
# ----------------------------------------------------------------------
def fmt_mem_window(cpu, start, end):
    """Return a 16-wide hex grid of RAM[start..end] as a string."""
    start &= 0xF0            # align window to a 16-byte row
    lines = []
    lines.append("       " + " ".join(f"{c:02X}" for c in range(16)))
    lines.append("      " + "-" * 47)
    row = start
    while row <= end:
        cells = " ".join(f"{cpu.mem[row + c]:02X}" for c in range(16))
        lines.append(f" {row:02X} | {cells}")
        row += 16
    return "\n".join(lines)


def regs_line(cpu):
    """One-line register / flag snapshot."""
    flag = "HALT" if cpu.halted else "run"
    return (f" A={cpu.A:02X}   B={cpu.B:02X}   PC={cpu.PC:02X}   "
            f"Z={cpu.Z}   [{flag}]")


def run_and_trace(cpu, title, win_start, win_end, max_steps=500):
    """Run the CPU to HLT, printing full state after every instruction."""
    bar = "=" * 60
    print(bar)
    print(title)
    print(bar)
    print("Initial memory:")
    print(fmt_mem_window(cpu, win_start, win_end))
    print(regs_line(cpu))
    print()

    step_no = 0
    while not cpu.halted and step_no < max_steps:
        step_no += 1
        pc_before = cpu.PC
        decode = cpu.step()
        print(f"Step {step_no:>2} :  (PC {pc_before:02X})  {decode}")
        print(regs_line(cpu))
        print(fmt_mem_window(cpu, win_start, win_end))
        print()

    print(f"Finished in {step_no} steps.")
    print(bar + "\n")


# ----------------------------------------------------------------------
# A tiny assembler so programs read as (mnemonic, operand) lines
# ----------------------------------------------------------------------
def inst_size(mnemonic):
    """Return the encoded byte length of an instruction (1 or 2)."""
    return 1 + ISA[OPC[mnemonic]][1]


def assemble(lines):
    """Flatten a list of (mnemonic, operand) tuples into a byte list.
       operand is an int, or None for operand-less instructions."""
    prog = []
    for mnem, operand in lines:
        prog.append(OPC[mnem])
        if ISA[OPC[mnem]][1] == 1:
            prog.append((operand or 0) & 0xFF)
    return prog


# ----------------------------------------------------------------------
# Printable instruction-encoding table (also rendered into the PDF)
# ----------------------------------------------------------------------
def print_isa_table():
    print("Opcode | Mnemonic | Operand   | Operation")
    print("-------+----------+-----------+------------------------------")
    meaning = {
        "NOP":    "no operation",
        "LDA":    "A <- RAM[addr]",
        "STA":    "RAM[addr] <- A",
        "LDI":    "A <- immediate",
        "ADD":    "A <- A + RAM[addr]",
        "SUB":    "A <- A - RAM[addr]",
        "MUL":    "A <- A * RAM[addr]",
        "JMP":    "PC <- addr",
        "JZ":     "if Z==1: PC <- addr",
        "JNZ":    "if Z==0: PC <- addr",
        "DCR":    "A <- A - 1",
        "INR":    "A <- A + 1",
        "MOV_AB": "B <- A",
        "MOV_BA": "A <- B",
        "HLT":    "halt execution",
    }
    for code in sorted(ISA):
        name, nargs = ISA[code]
        operand = "addr/imm" if nargs == 1 else "--"
        print(f"  {code:02X}   | {name:<8} | {operand:<9} | {meaning[name]}")


if __name__ == "__main__":
    print("SAP-8 instruction set\n")
    print_isa_table()
