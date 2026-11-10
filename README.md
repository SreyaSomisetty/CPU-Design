# SAP-8 — Simple Accumulator Processor (CMPE-220 CPU Design Project)

**Team:** Sreya · Lavya · Manasa

A small 8-bit **accumulator-based CPU** of our own design, with a software simulator that executes
programs and prints the contents of RAM **after every instruction** so memory changes are visible.
Two demo programs are included: one written **directly** in SAP-8 assembly, and one written in
**C** and hand-translated into SAP-8 assembly.

**Final report:** [`SAP8_Report.pdf`](SAP8_Report.pdf) (title page, block diagram, encoding table,
both programs with full memory traces).

---

## Quick start

Requires **Python 3.8+** (no third-party packages needed to run the CPU).

```bash
git clone https://github.com/SreyaSomisetty/CPU-Design.git
cd CPU-Design

python3 test_sap8.py          # self-test: should end with "ALL TESTS PASSED"
python3 prog1_factorial.py    # Program 1: 5! = 120   (direct assembly)
python3 prog2_power.py        # Program 2: 2^4 = 16   (C translated to assembly)
```

| Program | Written in | Expected result | Instructions executed |
| --- | --- | --- | --- |
| `prog1_factorial.py` | SAP-8 assembly | `RES @ 0x41 = 120 (0x78)` | 40 |
| `prog2_power.py` | C → SAP-8 assembly | `result @ 0x42 = 16 (0x10)` | 39 |

---

## CPU at a glance

| Property           | Value                                                 |
| ------------------ | ----------------------------------------------------- |
| Data path          | 8-bit (arithmetic wraps modulo 256)                   |
| RAM                | 256 bytes (`0x00`–`0xFF`)                             |
| Registers          | `A` (accumulator), `B` (temp), `PC` (program counter) |
| Flag               | `Z` (zero)                                            |
| Instruction format | 1 opcode byte, optional +1 operand byte               |
| Code segment       | `0x00`–`0x3F`                                         |
| Data segment       | `0x40`–`0xFF`                                         |

See **Figure 1** (`cpu_diagram.svg`, also exported as `cpu_diagram.png`) for the block diagram.

### Z (zero) flag rule

`Z = 1` when the last value written to `A` was 0. It is **set** by `LDA LDI ADD SUB MUL DCR INR MOV_BA`
and **left unchanged** by `STA MOV_AB JMP JZ JNZ NOP HLT`.

## Instruction set

| Opcode | Mnemonic | Operand | Operation               |
| ------ | -------- | ------- | ----------------------- |
| `00`   | `NOP`    | --      | no operation            |
| `01`   | `LDA`    | addr    | `A <- RAM[addr]`        |
| `02`   | `STA`    | addr    | `RAM[addr] <- A`        |
| `03`   | `LDI`    | imm     | `A <- immediate`        |
| `04`   | `ADD`    | addr    | `A <- A + RAM[addr]`    |
| `05`   | `SUB`    | addr    | `A <- A - RAM[addr]`    |
| `06`   | `MUL`    | addr    | `A <- A * RAM[addr]`    |
| `07`   | `JMP`    | addr    | `PC <- addr`            |
| `08`   | `JZ`     | addr    | if `Z==1`: `PC <- addr` |
| `09`   | `JNZ`    | addr    | if `Z==0`: `PC <- addr` |
| `0A`   | `DCR`    | --      | `A <- A - 1`            |
| `0B`   | `INR`    | --      | `A <- A + 1`            |
| `0C`   | `MOV_AB` | --      | `B <- A`                |
| `0D`   | `MOV_BA` | --      | `A <- B`                |
| `FF`   | `HLT`    | --      | halt                    |

`python3 sap8.py` prints this table (with byte counts).

## Assembler syntax

```
label:  MNEMONIC operand   ; comment
        .org 0x40          ; set the location counter
name:   .byte 5            ; one data byte
```

Operands can be labels, decimal (`5`) or hex (`0x40`).

---

## Files

| File                 | Owner           | Description                                              |
| -------------------- | --------------- | -------------------------------------------------------- |
| `sap8.py`            | Sreya (Part A)  | CPU simulator, ISA, assembler, memory-dump/trace printer |
| `cpu_diagram.svg`    | Sreya (Part A)  | CPU block diagram (Figure 1)                             |
| `cpu_diagram.png`    | Sreya (Part A)  | PNG export of the diagram (used in the PDF)              |
| `make_report.py`     | Sreya (Part A)  | Builds `SAP8_Report.pdf` from the live code              |
| `SAP8_Report.pdf`    | team            | Final report                                             |
| `prog1_factorial.py` | Lavya (Part B)  | `5! = 120` written directly in SAP-8 assembly            |
| `prog2_power.c`      | Manasa (Part C) | `2^4 = 16` in C (source)                                 |
| `prog2_power.py`     | Manasa (Part C) | C → SAP-8 translation + run                              |
| `test_sap8.py`       | team            | self-test (checks both results and basic instructions)   |
| `TASKS.md`           | team            | task division                                            |
| `README.md`          | team            | this file                                                |

---

## Reading a memory dump

RAM is shown as a 16-wide hex grid. The row label is the high nibble of the address; the column
header is the low nibble. For example the cell at row `40`, column `01` is address `0x41`.
Only the 16-byte rows that hold code or data are printed.

Real output from `prog1_factorial.py` (step 6):

```
--- step   6 | 0x0A: MUL 0x40
       00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F
      -----------------------------------------------
 00 | 03 05 02 40 03 01 02 41 01 41 06 40 02 41 01 40  <- code
 10 | 0A 02 40 09 08 FF 00 00 00 00 00 00 00 00 00 00  <- code
 40 | 05 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00  <- data
 A=05   B=00   PC=0C   Z=0   [run]
```

The register line shows `A`, `B`, the **next** `PC`, the `Z` flag and whether the CPU is running.
A `written:` line lists any RAM byte the instruction changed.

---

## Check the C program on the host

```bash
gcc -Wall prog2_power.c -o power && ./power      # prints 16
```

## Rebuild the PDF report

```bash
pip install reportlab
python3 make_report.py          # writes SAP8_Report.pdf
```

The report is generated by running the simulator, so its listings, memory dumps and results
always match the code. (`cpu_diagram.png` must sit next to `make_report.py`.)

## Contributions

| Member | Part | Work |
| --- | --- | --- |
| Sreya  | A | ISA, assembler, simulator (`sap8.py`), block diagram, report generator |
| Lavya  | B | Program 1: factorial written directly in assembly |
| Manasa | C | Program 2: exponent in C and its translation to assembly |
