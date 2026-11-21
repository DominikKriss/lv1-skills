import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))


def _sends():
    d = {str(n): {"on": False, "lvl": -144, "pon": False, "mode": "PRE" if n <= 8 else ("GRP" if n <= 10 else "POST"),
                  "plink": False, "pan": 0} for n in range(1, 17)}
    d.update({f"MX{n}": {"on": False, "lvl": -144, "pon": False, "mode": "PRE", "plink": False, "pan": 0}
              for n in range(1, 9)})
    return d


def _dyn():
    return {"on": False, "mdl": "COMP", "mix": 100, "gain": 0, "thr": -10, "ratio": 3, "knee": 3, "det": "RMS",
            "att": 50, "hld": 20, "rel": 152.5651855, "env": "LOG", "auto": True}


def _sc():
    return {"type": "OFF", "f": 1002.37439, "q": 1.995881796, "src": "SELF", "tap": "IN"}


def _eq():
    d = {"on": False, "mdl": "STD", "mix": 100, "lg": 0, "lf": 80.19641876, "lq": 0.997970223, "leq": "SHV"}
    for b in range(1, 5):
        d.update({f"{b}g": 0, f"{b}f": 200 * b, f"{b}q": 0.997970223})
    d.update({"hg": 0, "hf": 11999.27539, "hq": 0.997970223, "heq": "SHV"})
    return d


def _input(channel):
    d = {"in": {"set": {"inv": False, "trim": 0}, "conn": {"grp": "LCL", "in": 1, "altgrp": "OFF", "altin": 1}},
         "clink": True, "col": 1, "name": "", "fdr": -144, "eq": _eq(), "dyn": _dyn(),
         "main": {str(n): {"on": n == 1, "lvl": 0, "pre": False} for n in range(1, 5)}, "send": _sends(), "tags": ""}
    if channel:
        d.update({"flt": {"lc": False, "lcf": 100.2374573, "lcs": "24", "hc": False, "hcf": 10018.26074, "hcs": "12"},
                  "proc": "GEDI", "gate": {"on": False, "mdl": "GATE", "thr": -40, "range": 40, "att": 10, "hld": 10,
                                           "rel": 199.4042816, "acc": 0, "ratio": "1:3"},
                  "gatesc": _sc(), "dynsc": _sc()})
    return d


def _bus():
    return {"col": 10, "name": "", "busmono": False, "fdr": -144, "dyn": _dyn(),
            "preins": {"on": False, "ins": "NONE"}, "postins": {"on": False, "ins": "NONE"},
            "main": {str(n): {"on": False, "lvl": 0, "pre": False} for n in range(1, 5)},
            "send": {f"MX{n}": {"on": False, "lvl": -144, "pre": False} for n in range(1, 9)}}


def _socket():
    return {"mode": "M", "g": 0, "vph": False, "mute": False, "pol": False, "col": 1, "name": "", "icon": 0,
            "tags": ""}


def snapshot():
    groups_in = {"LCL": 24, "A": 48, "B": 48, "C": 48}
    groups_out = {"LCL": 8, "A": 48, "B": 48, "C": 48}
    ae = {
        "io": {"in": {g: {str(n): _socket() for n in range(1, c + 1)} for g, c in groups_in.items()},
               "out": {g: {str(n): {"grp": "OFF", "in": 1} for n in range(1, c + 1)} for g, c in groups_out.items()}},
        "ch": {str(n): _input(True) for n in range(1, 41)},
        "aux": {str(n): _input(False) for n in range(1, 9)},
        "bus": {str(n): _bus() for n in range(1, 17)},
        "main": {str(n): {"col": 1, "name": "", "busmono": False, "fdr": -144,
                          "send": {f"MX{k}": {"on": False, "lvl": -144, "pre": False} for k in range(1, 9)}}
                 for n in range(1, 5)},
        "mtx": {str(n): {"col": 1, "name": "", "busmono": False, "fdr": -144} for n in range(1, 9)},
        "dca": {str(n): {"name": "", "col": 1, "fdr": -144} for n in range(1, 17)},
        "fx": {str(n): {"mdl": "NONE", "fxmix": 100} for n in range(1, 17)},
    }
    return json.dumps({"type": "snapshot.10", "creator_model": "WING-EDIT", "ae_data": ae}, separators=(",", ":"))


SCENE = """/ch/01/config "kick" 3 WH 1
/ch/01/preamp +3.0 ON ON 24  40
/ch/01/gate ON GATE -25.0 60.0 1 31.7  63 0
/ch/01/gate/filter ON 3.0 108.7
/ch/01/dyn ON COMP PEAK LOG -27.0 4.0 0 4.50 5 0.02  52 PRE 0 100 OFF
/ch/01/dyn/filter OFF 3.0 990.9
/ch/01/eq ON
/ch/01/eq/1 LShv 116.4 -5.00 2.1
/ch/01/eq/2 PEQ 463.5 -12.7 0.4
/ch/01/eq/3 HCut 8k00 +0.00 0.6
/ch/01/eq/4 HShv 4k85 +11.2 0.8
"""
