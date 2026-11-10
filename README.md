# SAP-8 — Simple Accumulator Processor (CMPE-220 CPU Design Project)

**Team:** Sreya · Lavya · Manasa

A small 8-bit **accumulator-based CPU** of our own design, with a software
simulator that executes programs and prints the contents of RAM **after every
instruction** so memory changes are visible. Two demo programs are included:
one written **directly** in SAP-8 assembly, and one written in **C** and
hand-translated into SAP-8 assembly.

---

## CPU at a glance

| Property | Value |
|----------|-------|
| Data path | 8-bit |
| RAM | 256 bytes (`0x00`–`0xFF`) |
| Registers | `A` (accumulator), `B` (temp), `PC` (program counter) |
| Flag | `Z` (zero) |
| Instruction format | 1 opcode byte, optional +1 operand byte |
| Code segment | `0x00`–`0x3F` |
| Data segment | `0x40`–`0xFF` |

See **Figure 1** (`cpu_diagram.svg`) for the block diagram.

## Instruction set

| Opcode | Mnemonic | Operand | Operation |
|:------:|----------|---------|-----------|
| `00` | `NOP`    | --        | no operation |
| `01` | `LDA`    | addr      | `A <- RAM[addr]` |
| `02` | `STA`    | addr      | `RAM[addr] <- A` |
| `03` | `LDI`    | imm       | `A <- immediate` |
| `04` | `ADD`    | addr      | `A <- A + RAM[addr]` |
| `05` | `SUB`    | addr      | `A <- A - RAM[addr]` |
| `06` | `MUL`    | addr      | `A <- A * RAM[addr]` |
| `07` | `JMP`    | addr      | `PC <- addr` |
| `08` | `JZ`     | addr      | if `Z==1`: `PC <- addr` |
| `09` | `JNZ`    | addr      | if `Z==0`: `PC <- addr` |
| `0A` | `DCR`    | --        | `A <- A - 1` |
| `0B` | `INR`    | --        | `A <- A + 1` |
| `0C` | `MOV_AB` | --        | `B <- A` |
| `0D` | `MOV_BA` | --        | `A <- B` |
| `FF` | `HLT`    | --        | halt |

---

## Files

| File | Owner | Description |
|------|-------|-------------|
| `sap8.py`             | Sreya (Part A)  | CPU simulator, ISA, assembler, memory-dump/trace printer |
| `cpu_diagram.svg`     | Sreya (Part A)  | CPU block diagram (Figure 1) |
| `prog1_factorial.py`  | Lavya (Part B)  | `5! = 120` written directly in SAP-8 assembly |
| `prog2_power.c`       | Manasa (Part C) | `2^4 = 16` in C (source) |
| `prog2_power.py`      | Manasa (Part C) | C → SAP-8 translation + run |
| `TASKS.md`            | team            | task division |
| `README.md`           | team            | this file |

---

## How to run

Requires Python 3 (no third-party packages).

```bash
# Print the instruction-encoding table
python3 sap8.py

# Program 1 : factorial, direct assembly (prints full memory trace)
python3 prog1_factorial.py

# Program 2 : exponential, translated from C (prints full memory trace)
python3 prog2_power.py
```

Each program prints the initial RAM, then the register state and a RAM window
after every instruction, ending with the final result and its memory location.

---

## Reading a memory dump

RAM is shown as a 16-wide hex grid. The row label is the high nibble of the
address; the column header is the low nibble. For example the cell at row `40`,
column `01` is address `0x41`.

```
       00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F
      -----------------------------------------------
 00 | 03 02 02 40 04 40 02 41 FF 00 00 00 00 00 00 00   <- code
 40 | 02 04 00 00 00 00 00 00 00 00 00 00 00 00 00 00   <- data
```

The register line below each dump reads:

```
 A=04   B=00   PC=08   Z=0   [run]
```
