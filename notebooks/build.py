#!/usr/bin/env python3
"""실습 노트북 생성기.  python3 notebooks/build.py

각 Day 스펙 하나에서 두 벌을 뽑는다.
  notebooks/dayN.ipynb           빈칸 문제
  notebooks/dayN_solution.ipynb  정답
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nbkit import emit
import day1_spec, day2_spec, day3_spec, day4_spec, day5_spec, day6_spec, day8_spec, day9_spec, day10_spec, day11_spec, day12_spec

if __name__ == "__main__":
    print("생성:")
    emit(1, *day1_spec.SPEC, renumber=True, no_blank=True, lab=True)
    emit(2, *day2_spec.SPEC, renumber=True, no_blank=True, lab=True)
    emit(3, *day3_spec.SPEC, renumber=True, no_blank=True, lab=True)
    emit(4, *day4_spec.SPEC, renumber=True, no_blank=True, lab=True)
    emit(5, *day5_spec.SPEC, renumber=True, no_blank=True, lab=True)
    emit(6, *day6_spec.SPEC, renumber=True, no_blank=True, lab=True)
    emit(8, *day8_spec.SPEC, renumber=True, no_blank=True, lab=True)
    emit(9, *day9_spec.SPEC, renumber=True, no_blank=True, lab=True)
    emit(10, *day10_spec.SPEC, renumber=True, no_blank=True, lab=True)
    emit(11, *day11_spec.SPEC, renumber=True, no_blank=True, lab=True)
    emit(12, *day12_spec.SPEC, renumber=True, no_blank=True, lab=True)
