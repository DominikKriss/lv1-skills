import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))


class FakeSession:
    def __init__(self):
        self.values = {}

    def mix(self, path, prm, idx, value):
        self.values[(path, prm, tuple(idx))] = value


def x32_channel():
    return {
        "preamp": ["+3.0", "ON", "ON", "24", "40"],
        "gate": ["ON", "GATE", "-25.0", "60.0", "1", "31.7", "63", "0"],
        "gate/filter": ["ON", "LC12", "90.0"],
        "dyn": ["ON", "COMP", "PEAK", "LOG", "-27.0", "100", "2", "4.50", "5", "0.02", "52", "PRE", "0", "80", "OFF"],
        "dyn/filter": ["ON", "3.0", "120.5"],
        "eq": ["ON"],
        "eq/1": ["PEQ", "2k00", "+3.00", "1.5"],
        "eq/2": ["HShv", "8k00", "+2.00", "0.8"],
        "eq/3": ["PEQ", "300.0", "-4.00", "2.0"],
        "eq/4": ["HCut", "12k00", "+0.00", "2.0"],
    }
