/* prog2_power.c -- PROGRAM 2 source (Part C, Manasa)
 * Computes 2^4 = 16 by repeated multiplication.
 * Hand-translated to SAP-8 assembly in prog2_power.py.
 *
 * Host check:  gcc -Wall prog2_power.c -o power && ./power     (prints 16)
 */
#include <stdio.h>

int base   = 2;                  /* initialised globals -> data segment 0x40.. */
int expo   = 4;
int result = 1;

int main(void) {
    while (expo != 0) {          /* loop: LDA expo / JZ end                    */
        result = result * base;  /* LDA result / MUL base / STA result         */
        expo   = expo - 1;       /* LDA expo / DCR / STA expo                  */
    }                            /* JMP loop                                   */
    printf("%d\n", result);      /* host check only (not translated)           */
    return 0;                    /* end: HLT                                   */
}
