#!/usr/bin/env python3
"""Compatibility entry point for the 20x20 spatial balance simulator.
The old D:/FreedomTower_1 DPS estimate is retired. No spreadsheet is mutated.
Use: python .workbuddy/tools/balance_sim.py --profile D04 --strategy mixed
"""
import sys
from balance_pipeline import main
if __name__ == '__main__':
    main(['simulate'] + sys.argv[1:])