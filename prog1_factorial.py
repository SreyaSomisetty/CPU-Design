#!/usr/bin/env python3
"""
prog1_factorial.py  --  PROGRAM 1  (Part B, Lavya)
5! = 120, written DIRECTLY in SAP-8 assembly (no C involved).

Equivalent pseudo-code (for reading only):
    n = 5;  res = 1;
    do { res = res * n;  n = n - 1; } while (n != 0);

Run:   python3 prog1_factorial.py
Shows: the assembly listing, RAM + registers after EVERY instruction,
       and the final result (RES @ 0x41 = 120).
"""
from sap8 import run_program

# Memory map:  code 0x00-0x15   |   data: N = 0x40, RES = 0x41
SOURCE = """
; ---------------- code segment ----------------
        LDI 5           ; A = 5
        STA N           ; N = 5          (loop counter)
        LDI 1           ; A = 1
        STA RES         ; RES = 1        (running product)
loop:   LDA RES         ; A = RES
        MUL N           ; A = RES * N
        STA RES         ; RES = A
        LDA N           ; A = N
        DCR             ; A = N - 1      (sets the Z flag)
        STA N           ; N = N - 1      (STA does not change Z)
        JNZ loop        ; repeat while N != 0
        HLT             ; done, answer is in RES

; ---------------- data segment ----------------
        .org 0x40
N:      .byte 0         ; loop counter
RES:    .byte 0         ; result (5! = 120 = 0x78)
"""

RESULT_ADDR = 0x41
EXPECTED = 120


def main():
    run_program(SOURCE, title="Program 1: 5! (written directly in SAP-8 assembly)",
                result_label="RES", result_addr=RESULT_ADDR)


if __name__ == "__main__":
    main()
