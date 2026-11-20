"""X32 scene (.scn) channel processing to WING strip keys.

Usage: imported by build_wing_scene.py.
"""
import shlex

KEY_TYPES = {"LC6": "HP6", "LC12": "HP12", "HC6": "LP6", "HC12": "LP12"}


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


def key_filter(snap, path, f, notes):
    on, typ, fr = f
    if on != "ON":
        snap.set(f"{path}.type", "OFF")
        return
    if typ in KEY_TYPES:
        snap.set(f"{path}.type", KEY_TYPES[typ])
        notes.append(f"{path} {KEY_TYPES[typ]}: only OFF and BP are seen in WING files")
    else:
        snap.set(f"{path}.type", "BP")
        snap.set(f"{path}.q", num(typ))
    snap.set(f"{path}.f", freq(fr))


def apply(snap, strip, ch, notes):
    trim, inv, lc_on, lc_slope, lc_f = ch["preamp"]
    snap.set(f"{strip}.in.set.inv", inv == "ON")
    snap.set(f"{strip}.flt.lc", lc_on == "ON")
    snap.set(f"{strip}.flt.lcs", lc_slope)
    snap.set(f"{strip}.flt.lcf", freq(lc_f))

    on, mode, thr, rng, att, hld, rel, _ = ch["gate"]
    if mode != "GATE":
        raise ValueError(f"{strip}: X32 gate mode {mode} is not mapped.")
    g = f"{strip}.gate"
    snap.set(f"{g}.on", on == "ON")
    snap.set(f"{g}.mdl", "GATE")
    snap.set(f"{g}.ratio", "GATE")
    for k, v in (("thr", thr), ("range", rng), ("att", att), ("hld", hld), ("rel", rel)):
        snap.set(f"{g}.{k}", num(v))
    key_filter(snap, f"{strip}.gatesc", ch["gate/filter"], notes)

    on, mode, det, env, thr, ratio, knee, gain, att, hld, rel, pos, _, mix, auto = ch["dyn"]
    if mode != "COMP":
        raise ValueError(f"{strip}: X32 dyn mode {mode} is not mapped.")
    d = f"{strip}.dyn"
    snap.set(f"{d}.on", on == "ON")
    snap.set(f"{d}.mdl", "COMP")
    snap.set(f"{d}.det", det)
    snap.set(f"{d}.env", env)
    snap.set(f"{d}.auto", auto == "ON")
    for k, v in (("thr", thr), ("ratio", ratio), ("knee", knee), ("gain", gain), ("att", att),
                 ("hld", hld), ("rel", rel), ("mix", mix)):
        snap.set(f"{d}.{k}", num(v))
    key_filter(snap, f"{strip}.dynsc", ch["dyn/filter"], notes)
    snap.set(f"{strip}.proc", "GEDI" if pos == "POST" else "GDEI")

    e = f"{strip}.eq"
    snap.set(f"{e}.on", ch["eq"][0] == "ON")
    snap.set(f"{e}.mdl", "STD")
    for b in range(1, 5):
        typ, fr, gn, q = ch[f"eq/{b}"]
        fr, gn, q = freq(fr), num(gn), num(q)
        if typ in ("PEQ", "VEQ"):
            snap.set(f"{e}.{b}f", fr)
            snap.set(f"{e}.{b}g", gn)
            snap.set(f"{e}.{b}q", q)
        elif typ in ("LShv", "HShv"):
            side = "l" if typ == "LShv" else "h"
            snap.set(f"{e}.{side}eq", "SHV")
            snap.set(f"{e}.{side}f", fr)
            snap.set(f"{e}.{side}g", gn)
            snap.set(f"{e}.{side}q", q)
        elif typ in ("LCut", "HCut"):
            if ch["eq"][0] != "ON":
                continue
            side = "lc" if typ == "LCut" else "hc"
            snap.set(f"{strip}.flt.{side}", True)
            snap.set(f"{strip}.flt.{side}f", fr)
            snap.set(f"{strip}.flt.{side}s", "12")
        else:
            raise ValueError(f"{strip}: X32 EQ type {typ} is not mapped.")
