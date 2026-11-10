#!/usr/bin/env python3
"""
prog2_power.py  --  PROGRAM 2  (Part C, Manasa)
2^4 = 16.  Written in C (prog2_power.c), then TRANSLATED BY HAND to SAP-8 assembly.

C statement                      SAP-8 assembly
-------------------------------  ----------------------------
int base=2, expo=4, result=1;    .byte 2 / .byte 4 / .byte 1   (data segment)
while (expo != 0)                loop: LDA expo ; JZ end
  result = result * base;        LDA result ; MUL base ; STA result
  expo   = expo - 1;             LDA expo ; DCR ; STA expo
(end of loop body)               JMP loop
return 0;                        end: HLT

Run:   python3 prog2_power.py
"""
from sap8 import run_program

SOURCE = """
; ---------------- code segment ----------------
loop:   LDA expo        ; while (expo != 0)  -- load expo, sets Z
        JZ  end         ;   leave the loop when expo == 0
        LDA result      ; result = result * base
        MUL base        ;
        STA result      ;
        LDA expo        ; expo = expo - 1
        DCR             ;
        STA expo        ;
        JMP loop        ; back to the while test
end:    HLT             ; return 0

; ---------------- data segment (the C globals) ----------------
        .org 0x40
base:   .byte 2         ; int base   = 2;
expo:   .byte 4         ; int expo   = 4;
result: .byte 1         ; int result = 1;   (final value 16 = 0x10)
"""

RESULT_ADDR = 0x42
EXPECTED = 16


def main():
    run_program(SOURCE, title="Program 2: 2^4 (C translated to SAP-8 assembly)",
                result_label="result", result_addr=RESULT_ADDR)


if __name__ == "__main__":
    main()
