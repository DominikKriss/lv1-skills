#!/usr/bin/env python3
"""Build the event DM7 session from a DM Editor 2.0.1 (V2.01) session.

Usage: build_dm7.py BASE.dmxf layout.json OUT.dmxf [--dry-run] [--changes]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "vendor"))
sys.path.insert(0, HERE)
import yamaha_tool as yt  # noqa: E402
import x32_scn  # noqa: E402

IC = "InputChannel"
DANTE_IN, OMNI_IN, FX_RET = 0x01A00000, 0x01401000, 0x06C00000
MIX_OUT, MTX_OUT = 0x03E00000, 0x04000000
INF = -32768


class Refuse(Exception):
    pass


class Session:
    def __init__(self, data):
        self.show = yt.Gen2Show(data)
        if self.show.model_key != "dm7" or self.show.version != "V2.01":
            raise Refuse("Only a DM7 (not Compact) session from firmware V2.01 is written.")
        m = self.show.m
        left = [yt.MAX_TOTAL_INFLATED]
        self.copies = {"Current": [], "Setup": []}
        for i, r in enumerate(m.records):
            if r["type"] != "file":
                continue
            if r["name"] in ("CurrentBackupFile.bup", "CurrentBackupFile.bup.old"):
                self.copies["Current"].append((i, yt.mbdf_parse(yt.inflate(m, r, left), 1, m.budget)))
            elif r["name"] in ("SetupBackupFile.bup", "SetupBackupFile.bup.old"):
                self.copies["Setup"].append((i, yt.mbdf_parse(yt.inflate(m, r, left), 1, m.budget)))
        if len(self.copies["Current"]) != 2 or len(self.copies["Setup"]) != 2:
            raise Refuse("The session needs both Current and Setup backups and their .old copies.")
        self.bufs = {i: bytearray(inner.data) for k in self.copies for i, inner in self.copies[k]}
        self.changes = []

    def sec(self, entry, name, n=0):
        return self.copies[entry][n][1].section(name)

    def get(self, entry, sname, path, prm, idx):
        return self.sec(entry, sname).get(path, prm, idx)

    def set(self, entry, sname, path, prm, idx, value):
        for n, (i, inner) in enumerate(self.copies[entry]):
            s = inner.section(sname)
            if s is None or not s.has(path, prm):
                raise Refuse(f"{sname}/{path}.{prm} is not in this session.")
            old = s.get(path, prm, idx, d=self.bufs[i])
            if old == value:
                continue
            try:
                s.put(self.bufs[i], path, prm, value, idx)
            except ValueError as e:
                raise Refuse(f"{sname}/{path}.{prm}{list(idx)} = {value!r}: {e}.")
            if n == 0:
                self.changes.append(f"{path}{list(idx)}.{prm}: {old!r} -> {value!r}")

    def mix(self, path, prm, idx, value):
        self.set("Current", "Mixing", path, prm, idx, value)

    def build(self):
        replace = {}
        for k in self.copies:
            for i, inner in self.copies[k]:
                if bytes(self.bufs[i]) != inner.data:
                    replace[i] = bytes(self.bufs[i])
        return yt.mbdf_build(self.show.m, replace)


def cdb(x):
    return int(round(float(x) * 100))


def hz(x):
    return int(round(float(x) * 10))


def allocate(inputs):
    chans, ch = [], 1
    for i in inputs:
        if i.get("stereo") and ch % 2 == 0:
            chans.append({"spare": True, "ch": ch})
            ch += 1
        if i.get("stereo"):
            chans.append(dict(i, ch=ch, half="L"))
            chans.append(dict(i, ch=ch + 1, half="R"))
            ch += 2
        else:
            chans.append(dict(i, ch=ch))
            ch += 1
    return chans, ch


def label(i, short):
    name = short.get(i["name"], i["name"])
    if "half" in i:
        base = name[:-3] if name.endswith(" LR") else name
        name = f"{base} {i['half']}"
    if len(name) > 8:
        raise Refuse(f"{name!r} is longer than the DM7's 8 characters.")
    return name


def pair(s, ch_l):
    for k, rel in ((ch_l, 128), (ch_l + 1, 1)):
        s.mix(IC, "GainGang", (k - 1,), 1)
        s.mix(IC, "DelayGang", (k - 1,), 1)
        s.mix(IC + "/Signal", "Relation", (k - 1, 0), rel)
        s.mix(IC + "/Signal", "StereoInputType", (k - 1, 0), "STEREO")
        s.mix(IC + "/ToStereo", "PanType", (k - 1, 0), "BALANCE")
        s.mix(IC + "/ToStereo", "Pan", (k - 1, 0), 0)


def hpf(s, c, on, freq, slope):
    s.mix(IC + "/HPF", "On", (c, 0), 1 if on else 0)
    s.mix(IC + "/HPF", "Frequency", (c, 0), hz(freq))
    s.mix(IC + "/HPF", "Slope", (c, 0), int(slope))


def key_filter(s, c, slot, f, notes, who):
    on, typ, fr = f
    s.mix(IC + "/Dynamics/KeyIn", "SourceSelect", (c, slot, 0), "SELF POST EQ")
    if on == "ON" and typ in ("LC6", "LC12"):
        s.mix(IC + "/Dynamics/KeyIn", "FilterType", (c, slot, 0), "HPF")
        s.mix(IC + "/Dynamics/KeyIn", "FilterFrequency", (c, slot, 0), hz(x32_scn.freq(fr)))
    else:
        s.mix(IC + "/Dynamics/KeyIn", "FilterType", (c, slot, 0), "NONE")
        if on == "ON":
            notes.append(f"{who}: X32 key filter {typ} {fr} has no DM7 match (HPF only); left off")


def dyn_params(s, c, slot, typ, on, mix, words):
    s.mix(IC + "/Dynamics", "Select", (c, slot), 0)
    s.mix(IC + "/Dynamics/Bank", "Type", (c, slot, 0), typ)
    s.mix(IC + "/Dynamics/Bank", "On", (c, slot, 0), 1 if on else 0)
    s.mix(IC + "/Dynamics/Bank", "MixBalance", (c, slot, 0), int(mix))
    for j in range(10):
        s.mix(IC + "/Dynamics/Bank/Parameter", "Value", (c, slot, 0, j), words[j] if j < len(words) else 0)


def comp_ratio(r):
    r = float(r)
    return 255 if r >= 100 else int(round(r * 10))


def x32_processing(s, c, x, notes, who):
    trim, inv, lc_on, lc_slope, lc_f = x["preamp"]
    s.mix(IC + "/Input", "Phase", (c, 0), 1 if inv == "ON" else 0)
    hpf(s, c, lc_on == "ON", x32_scn.freq(lc_f), lc_slope)

    on, mode, thr, rng, att, hld, rel, _ = x["gate"]
    if mode != "GATE":
        raise Refuse(f"{who}: X32 gate mode {mode} is not mapped.")
    dyn_params(s, c, 0, "GATE", on == "ON", 100,
               [cdb(thr), int(round(float(att))), -cdb(rng), int(round(float(hld) * 1000)), int(round(float(rel) * 1000))])
    key_filter(s, c, 0, x["gate/filter"], notes, who + " gate")

    on, mode, det, env, thr, ratio, knee, gain, att, hld, rel, pos, _, mix, auto = x["dyn"]
    if mode != "COMP":
        raise Refuse(f"{who}: X32 dyn mode {mode} is not mapped.")
    dyn_params(s, c, 1, "PM Comp", on == "ON", float(mix),
               [cdb(thr), int(round(float(att))), int(round(float(rel) * 1000)), comp_ratio(ratio), int(knee), cdb(gain)])
    key_filter(s, c, 1, x["dyn/filter"], notes, who + " comp")
    s.mix(IC + "/Proc", "EQDynOrder", (c, 0), 0 if pos == "POST" else 1)

    bells, low, high, lpf = [], None, None, None
    for b in range(1, 5):
        typ, fr, gn, q = x[f"eq/{b}"]
        band = (x32_scn.freq(fr), float(gn), float(q))
        if typ in ("PEQ", "VEQ"):
            bells.append(band)
        elif typ == "LShv" and low is None:
            low = band
        elif typ == "HShv" and high is None:
            high = band
        elif typ == "HCut" and lpf is None:
            lpf = band
        else:
            raise Refuse(f"{who}: X32 EQ band {b} {typ} does not fit the DM7 4-band EQ.")
    slots = [None] * 4
    if low:
        slots[0] = low
    if high:
        slots[3] = high
    free = [k for k in range(4) if slots[k] is None]
    if len(bells) > len(free):
        raise Refuse(f"{who}: more bells than free DM7 EQ bands.")
    for k, band in zip(free, sorted(bells)):
        slots[k] = band
    e = IC + "/PEQ/Bank"
    s.mix(IC + "/PEQ", "Select", (c, 0), 0)
    s.mix(e, "On", (c, 0, 0), 1 if x["eq"][0] == "ON" else 0)
    s.mix(e + "/LowShelving", "On", (c, 0, 0, 0), 1 if low else 0)
    s.mix(e + "/HighShelving", "On", (c, 0, 0, 0), 1 if high else 0)
    if low:
        s.mix(e + "/LowShelving", "Q", (c, 0, 0, 0), int(round(low[2] * 1000)))
    if high:
        s.mix(e + "/HighShelving", "Q", (c, 0, 0, 0), int(round(high[2] * 1000)))
    for k, band in enumerate(slots):
        if band is None:
            s.mix(e + "/Band", "Gain", (c, 0, 0, k), 0)
            continue
        f, g, q = band
        s.mix(e + "/Band", "Bypass", (c, 0, 0, k), 0)
        s.mix(e + "/Band", "Frequency", (c, 0, 0, k), hz(f))
        s.mix(e + "/Band", "Gain", (c, 0, 0, k), cdb(g))
        if not ((k == 0 and low) or (k == 3 and high)):
            s.mix(e + "/Band", "Q", (c, 0, 0, k), int(round(q * 1000)))
    s.mix(IC + "/LPF", "On", (c, 0), 1 if lpf else 0)
    if lpf:
        s.mix(IC + "/LPF", "Frequency", (c, 0), hz(lpf[0]))
        s.mix(IC + "/LPF", "Slope", (c, 0), 12)


def tio_units(s):
    units = []
    for u in range(24):
        if s.get("Setup", "Setup", "DanteRemoteControl/IOUnit", "DeviceMount", (0, u)) and \
                s.get("Setup", "Setup", "DanteRemoteControl/IOUnit", "ModelName", (0, u)).startswith("Tio1608"):
            units.append(u + 1)
    return units


def fx_slots(s):
    found = {}
    for f in range(16):
        name = s.get("Current", "FX", "FX/Param", "PluginName", (f, 0))
        if not name:
            continue
        low = name.lower()
        kind = "reverb" if ("rev" in low or "hall" in low or "plate" in low or "room" in low) else \
            "delay" if ("delay" in low or "echo" in low or "dly" in low) else None
        if kind and kind not in found:
            found[kind] = (f, name)
    return found


def build(s, lay, base_dir):
    src, src_dir = lay, base_dir
    if "inputs_from" in lay:
        src_path = os.path.join(base_dir, lay["inputs_from"])
        with open(src_path, encoding="utf-8") as fh:
            src = json.load(fh)
        src_dir = os.path.dirname(src_path)
    x32 = src.get("processing", {})
    from_x32 = x32.get("from_x32", {})
    scn = x32_scn.read_scn(os.path.join(src_dir, x32["x32_scene"])) if from_x32 else {}
    lowcut = x32.get("lowcut_rest", {"freq": 80, "slope": "12", "skip": [], "off": True})
    short, col = lay["short_names"], lay["colours"]
    notes, sheet = [], []

    chans, next_ch = allocate(src["inputs"])
    tio_ports = [i for i in chans if not i.get("spare") and i["group"] not in lay["dante_playback_groups"]]
    play = [i for i in chans if not i.get("spare") and i["group"] in lay["dante_playback_groups"]]
    tio_total = lay["tio_units"] * lay["tio_inputs"]
    if len(tio_ports) > tio_total:
        raise Refuse(f"{len(tio_ports)} stagebox inputs do not fit {tio_total} Tio inputs.")
    for n, i in enumerate(tio_ports):
        i["dante"] = n + 1
        i["tio"] = (n // lay["tio_inputs"] + 1, n % lay["tio_inputs"] + 1)
    for n, i in enumerate(play):
        i["dante"] = lay["playback_dante_start"] + n

    for i in chans:
        c = i["ch"] - 1
        if i.get("spare"):
            s.mix(IC + "/Label", "Name", (c, 0), "spare")
            s.mix(IC + "/Label", "Color", (c, 0), col["spare"])
            s.mix(IC + "/InPatch/Bank", "Source", (c, 0, 0), 0)
            sheet.append(f"CH {i['ch']:<3} spare (keeps the next stereo pair on odd/even)")
            continue
        name = label(i, short)
        s.mix(IC + "/Label", "Name", (c, 0), name)
        s.mix(IC + "/Label", "Color", (c, 0), col[i["group"]])
        s.mix(IC + "/InPatch", "Select", (c, 0), 0)
        s.mix(IC + "/InPatch/Bank", "Source", (c, 0, 0), DANTE_IN + i["dante"] - 1)
        for mx in range(len(lay["mons"])):
            s.mix(IC + "/ToMix", "Pre", (c, mx), 1)
            s.mix(IC + "/ToMix", "PrePoint", (c, mx), 100)
        strip = i["strip"]
        if strip in from_x32:
            x32_processing(s, c, scn[from_x32[strip]], notes, f"CH {i['ch']} {name}")
        elif lowcut.get("off") or i["name"] in lowcut["skip"]:
            hpf(s, c, False, 80, 12)
        else:
            hpf(s, c, True, lowcut["freq"], int(lowcut["slope"]))
        where = f"Tio {i['tio'][0]} in {i['tio'][1]}" if "tio" in i else "playback laptop"
        if i.get("half") != "R":
            sheet.append(f"CH {i['ch']:<3}{'-' + str(i['ch'] + 1) if 'half' in i else '':<4} {i['name']:<10} "
                         f"DANTE {i['dante']}{'-' + str(i['dante'] + 1) if 'half' in i else '':<4} {where}"
                         f"{' + next' if 'half' in i else ''}")
        if i.get("half") == "L":
            pair(s, i["ch"])

    fx = fx_slots(s)
    ret_ch = next_ch + (next_ch + 1) % 2
    for k, m in enumerate(lay["mons"]):
        s.mix("Mix/Label", "Name", (k, 0), m)
        s.mix("Mix", "BusType", (k,), "VARI")
        s.mix("Mix/ToStereo", "ToStereoA", (k, 0), 0)
    for f in lay["fx_sends"]:
        k = f["mix"] - 1
        s.mix("Mix/Label", "Name", (k, 0), f["name"])
        s.mix("Mix/Label", "Color", (k, 0), col["fx"])
        s.mix("Mix/ToStereo", "ToStereoA", (k, 0), 0)
        if f["kind"] not in fx:
            notes.append(f"no {f['kind']} in the FX rack of the base: mix {f['mix']} {f['name']} is named, "
                         f"but nothing is patched to it")
            continue
        slot, plug = fx[f["kind"]]
        s.mix("EffectRack/Slot/InputPort/Patch", "Source", (0, slot, 0, 0), MIX_OUT + k)
        s.mix("EffectRack/Slot/InputPort/Patch", "Source", (0, slot, 1, 0), MIX_OUT + k)
        for side, half in ((0, "L"), (1, "R")):
            c = ret_ch - 1 + side
            s.mix(IC + "/Label", "Name", (c, 0), f"{f['name']} {half}")
            s.mix(IC + "/Label", "Color", (c, 0), col["fx"])
            s.mix(IC + "/InPatch", "Select", (c, 0), 0)
            s.mix(IC + "/InPatch/Bank", "Source", (c, 0, 0), FX_RET + slot * 16 + side)
            s.mix(IC + "/Fader", "Level", (c, 0), 0)
            for fs in lay["fx_sends"]:
                s.mix(IC + "/ToMix", "On", (c, fs["mix"] - 1), 0)
        pair(s, ret_ch)
        sheet.append(f"CH {ret_ch}-{ret_ch + 1} {f['name']} return from FX slot {slot + 1} {plug}, fed by mix {f['mix']}")
        ret_ch += 2

    for k in range(2):
        s.mix("Stereo/Label", "Name", (k, 0), lay["main_name"])
    for t in lay["matrices"]:
        legs = [t["first"], t["first"] + 1] if t.get("stereo") else [t["first"]]
        for n, leg in enumerate(legs):
            s.mix("Matrix/Label", "Name", (leg - 1, 0), t["name"])
            if t.get("stereo"):
                s.mix("Matrix/Signal", "Relation", (leg - 1, 0), 128 if n == 0 else 1)
                s.mix("Matrix", "DelayGang", (leg - 1,), 1)
            for st in range(2):
                feed = (not t.get("stereo")) or st == n
                s.mix("Stereo/ToMatrix", "On", (st, leg - 1), 1)
                s.mix("Stereo/ToMatrix", "Level", (st, leg - 1), 0 if feed else INF)

    for k, (kind, n) in enumerate(lay["dante_outputs"]):
        code = (MIX_OUT if kind == "mix" else MTX_OUT) + n - 1
        s.set("Current", "Processing", "Dante/OutputPort/Patch", "Source", (0, k, 0), code)
        sheet.append(f"DANTE OUT {k + 1:<3} {kind} {n}")

    units = tio_units(s)
    if len(units) == lay["tio_units"]:
        for i in tio_ports:
            u, p = i["tio"]
            s.set("Setup", "Setup", "DanteNetwork/InputPort/Patch", "Source", (0, i["dante"] - 1, 0),
                  0x44000000 | (units[u - 1] << 12) | (p - 1))
        sheet.append(f"Dante IN 1-{len(tio_ports)} subscribed to Tio units {units}")
    else:
        notes.append(f"{len(units)} Tio1608-D mounted in the base, not {lay['tio_units']}: Dante input "
                     f"subscriptions left as they are")
    return sheet, notes


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 3:
        print(__doc__.strip())
        return 2
    base, layout, out = args
    if os.path.abspath(base) == os.path.abspath(out):
        print("refused: write a new file, not the base.")
        return 1
    with open(base, "rb") as fh:
        data = fh.read()
    with open(layout, encoding="utf-8") as fh:
        lay = json.load(fh)
    try:
        s = Session(data)
        if s.build() != data:
            raise Refuse("the base does not rebuild byte for byte before any change.")
        sheet, notes = build(s, lay, os.path.dirname(os.path.abspath(layout)))
    except (Refuse, yt.Refused) as e:
        print(f"refused: {e}")
        return 1
    print(f"DM7 {s.show.version}, {len(s.changes)} changes")
    if "--changes" in argv:
        for c in s.changes:
            print("  " + c)
    for n in notes:
        print("note: " + n)
    for line in sheet:
        print("  " + line)
    if "--dry-run" not in argv:
        new = s.build()
        problems = [msg for ok, msg in yt.check(new) if not ok]
        if problems:
            print("refused: the written file fails the check: " + "; ".join(problems))
            return 1
        with open(out, "wb") as fh:
            fh.write(new)
        print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
