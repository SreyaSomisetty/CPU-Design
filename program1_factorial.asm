; Program 1: 5! = 120
; Directly written in SAP-8 assembly

        LDI 5          ; A = 5
        STA N          ; N = 5

        LDI 1          ; A = 1
        STA RES        ; RES = 1

loop:
        LDA RES        ; A = RES
        MUL N          ; A = RES * N
        STA RES        ; RES = A

        LDA N          ; A = N
        DCR            ; A = N - 1
        STA N          ; N = N - 1
        JNZ loop       ; repeat while N != 0

        HLT            ; stop; RES contains 120

        .org 0x40

N:      .byte 0
RES:    .byte 0
