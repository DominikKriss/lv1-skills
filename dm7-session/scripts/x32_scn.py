"""Read a Behringer X32 scene (.scn): channel lines by channel number.

Usage: imported by build_dm7.py.
"""
import shlex


def freq(s):
    return float(s.replace("k", ".")) * 1000 if "k" in s else float(s)


def num(s):
    return float(s)


def read_scn(path):
    chans = {}
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.startswith("/ch/"):
                continue
            parts = shlex.split(line.strip())
            addr = parts[0].split("/")
            n = int(addr[2])
            chans.setdefault(n, {})["/".join(addr[3:])] = parts[1:]
    return chans
