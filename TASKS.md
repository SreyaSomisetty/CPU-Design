# CMPE-220 — CPU Design Project — Task Division

**Team:** Sreya · Lavya · Manasa

---

## Project goal (shared)

Design a simple 8-bit **accumulator-based CPU** ("SAP-8"), build a **software
simulator** that executes programs and prints the RAM block **after every
instruction**, write **two demo programs** (one directly in our assembly, one in
C then hand-translated to our assembly), and produce a **neatly formatted,
page-numbered PDF** with a title page, CPU diagram, instruction-encoding table,
and memory traces.

### Locked design decisions (agreed before work starts)

| Item | Decision |
|------|----------|
| Architecture | 8-bit accumulator machine |
| Registers | `A` (accumulator), `B` (temp), `PC` (program counter) |
| Flag | `Z` (zero flag) |
| Memory | 256 bytes RAM (`0x00`–`0xFF`), shown as a 16-wide hex grid |
| Instruction format | Variable length: 1 opcode byte, optional +1 operand byte |
| Memory map | Program at `0x00`; data segment at `0x40`+ |
| Program 1 (direct asm) | Factorial: **5! = 120 (0x78)** |
| Program 2 (C → asm) | Exponential: **2⁴ = 16 (0x10)** — stays inside 8 bits |
| Deliverable | Single PDF: title page (3 names), pages numbered `##/##`, captioned figures & tables |

---

## 👤 Sreya — Part A: CPU Architecture & Simulator Core

The "machine" itself. Everyone else depends on this, so Sreya publishes the
final ISA table first.

- Define the final ISA: opcodes, mnemonics, operand sizes, semantics.
- Build the simulator core (`sap8.py`): registers, fetch–decode–execute, Z flag, RAM.
- Implement the memory-dump printer (16-wide hex grid) and per-instruction trace.
- Create the **CPU block diagram** (A, B, PC, ALU, RAM, bus, control) — clean, annotated.
- Create the **instruction-encoding table** (opcode | mnemonic | operand | meaning).

**Deliverables:** `sap8.py`, CPU diagram, instruction-encoding table.

---

## 👤 Lavya — Part B: Program 1 (Direct Assembly — Factorial)

The hand-written-assembly demonstration.

- Write `5!` in SAP-8 assembly (loop: `result = result * n`, `n--`, until `n==0`).
- Define its memory layout (result, n, answer addresses).
- Run it on Sreya's simulator; capture the full step-by-step memory trace.
- Verify final answer = `0x78` (120); format the trace neatly for the PDF.

**Deliverables:** `prog1_factorial.py` (assembly listing + run), formatted memory-trace pages.

---

## 👤 Manasa — Part C: Program 2 (C → Assembly — Exponential) + Final PDF

The C-translation demonstration and the final document assembly.

- Write the exponential in **C** (`2⁴`), then hand-translate to SAP-8 assembly,
  documenting each C line → assembly lines mapping.
- Run it on the simulator; capture its memory trace.
- Build the **final PDF**: title page (Sreya, Lavya, Manasa), page numbers `##/##`,
  captions on every figure/table, consistent formatting — combining Sreya's
  diagram/table with Lavya's and Manasa's traces.

**Deliverables:** `prog2_power.c`, `prog2_power.py`, the final submission **PDF**.

---

## Order of work & dependencies

1. **Sreya (Part A) first** — freeze the ISA + simulator so programs can be written against it.
2. **Lavya (Part B)** and **Manasa (Part C program)** proceed in parallel once the ISA is frozen.
3. **Manasa** closes the project by compiling the PDF (needs Sreya's diagram/table + Lavya's trace).
