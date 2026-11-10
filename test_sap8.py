#!/usr/bin/env python3
"""test_sap8.py -- quick self-test.   Run:  python3 test_sap8.py"""
import prog1_factorial as p1
import prog2_power as p2
from sap8 import SAP8, assemble


def result_of(mod):
    image, _, _ = assemble(mod.SOURCE)
    cpu = SAP8(image)
    cpu.run()
    assert cpu.halted, "program did not halt"
    return cpu.ram[mod.RESULT_ADDR], cpu.steps


def test_factorial():
    value, steps = result_of(p1)
    assert value == p1.EXPECTED, value
    print(f"PASS  5! = {value}   ({steps} instructions)")


def test_power():
    value, steps = result_of(p2)
    assert value == p2.EXPECTED, value
    print(f"PASS  2^4 = {value}   ({steps} instructions)")


def test_isa_basics():
    image, _, _ = assemble("LDI 3\nINR\nMOV_AB\nLDI 0\nMOV_BA\nHLT")
    cpu = SAP8(image); cpu.run()
    assert (cpu.A, cpu.B, cpu.Z) == (4, 4, 0)
    print("PASS  LDI / INR / MOV_AB / MOV_BA")


def test_wraparound():
    image, _, _ = assemble("LDI 255\nINR\nHLT")
    cpu = SAP8(image); cpu.run()
    assert (cpu.A, cpu.Z) == (0, 1)
    print("PASS  8-bit wrap-around sets Z")


if __name__ == "__main__":
    test_factorial(); test_power(); test_isa_basics(); test_wraparound()
    print("ALL TESTS PASSED")
