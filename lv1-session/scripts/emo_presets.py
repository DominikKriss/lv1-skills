"""Write X32 channel processing into LV1 eMo F2 / D5 / Q4 plugin presets inside an .emo session.

Parameter order: ParamXML of the installed EMO-F2 / EMO-D5 / EMO-Q4 bundles (or $LV1_EMO_PARAMXML_DIR).
Preset chunks are positional RealWorld values; '*' = display-only slot. Hash = SHA3-256 of the chunk text.
"""
import hashlib
import math
import re
import os
import xml.etree.ElementTree as ET
from pathlib import Path

from x32_to_emo import hz, parse, place_eq

PLUGIN_DIRS = sorted(Path("/Applications/Waves").glob("Plug-Ins V*"), reverse=True)

LOW_TYPE = {"Bell": 0, "LowShelf": 1, "HighPass": 2}
HIGH_TYPE = {"Bell": 0, "HighShelf": 1, "LowPass": 2}
KNEE = {"Soft": 0, "Normal": 1, "Hard": 2}
REL_MANUAL = 0
TRIM_MAX = 10.0


def paramxml_path(plugin):
    override = os.environ.get("LV1_EMO_PARAMXML_DIR")
    if override:
        return Path(override) / f"{plugin}-ParamXML.xml"
    for d in PLUGIN_DIRS:
        p = d / f"{plugin}.bundle" / "Contents" / "Resources" / "ParamXML" / "1000.xml"
        if p.exists():
            return p
    raise FileNotFoundError(f"{plugin} not installed (install eMo F2/D5/Q4 via Waves Central)")


def param_names(plugin):
    root = ET.parse(paramxml_path(plugin)).getroot()
    return [p.get("Name") for p in root.iter("Parameter")]


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def bp_edges(f, q):
    a = math.sqrt(1 + 1 / (4 * q * q))
    return f * (a - 1 / (2 * q)), f * (a + 1 / (2 * q))


def key_filter(flt):
    """X32 dyn/gate filter -> (hpf_hz or None, lpf_hz or None)."""
    on, typ, f = flt[0], flt[1], hz(flt[2])
    if on != "ON":
        return None, None
    if typ.startswith("LC"):
        return f, None
    if typ.startswith("HC"):
        return None, f
    return bp_edges(f, float(typ))


def x32_settings(c):
    """X32 /ch/NN/* lines -> plain settings dict for the eMo writer."""
    trim, inv, hpon, _slope, hpf = c["preamp"][:5]
    s = {"trim": float(trim), "invert": inv == "ON",
         "hp": hz(hpf.strip()) if hpon == "ON" else None, "eq": {}, "eq_dropped": [],
         "gate": None, "comp": None, "comp_post_eq": False, "not_converted": []}
    if c["eq"][0] == "ON":
        bands = [(b[0], hz(b[1]), float(b[2]), float(b[3])) for b in (c[f"eq/{i}"] for i in range(1, 5))]
        s["eq"], s["eq_dropped"] = place_eq(bands)
    g = c["gate"]
    if g[0] == "ON" and g[1] != "GATE":
        s["not_converted"].append(f"X32 gate mode {g[1]} not converted, D5 gate off")
    elif g[0] == "ON":
        hp, lp = key_filter(c.get("gate/filter", ["OFF", "3.0", "1k00"]))
        s["gate"] = {"thr": float(g[2]), "floor": -float(g[3]), "att": float(g[4]), "hold": float(g[5]),
                     "rel": float(g[6]), "key_hp": hp, "key_lp": lp}
    d = c["dyn"]
    if d[0] == "ON" and d[1] != "COMP":
        s["not_converted"].append(f"X32 dynamics mode {d[1]} not converted, D5 comp off")
    elif d[0] == "ON":
        _on, _mode, _det, _env, thr, ratio, kn, mg, att, _hold, rel, pos, _ks, mix = d[:14]
        k = int(kn)
        hp, lp = key_filter(c["dyn/filter"])
        s["comp"] = {"thr": float(thr), "ratio": float(ratio), "knee": "Hard" if k == 0 else "Normal" if k <= 2 else "Soft",
                     "att": float(att), "rel": float(rel), "makeup": float(mg), "mix": float(mix),
                     "key_hp": hp, "key_lp": lp}
        s["comp_post_eq"] = pos == "POST"
    return s


def f2_values(s):
    v = {}
    for side in ("L", "R"):
        v[f"PARAM_{side}_HPF_ON"] = 1 if s["hp"] else 0
        if s["hp"]:
            v[f"PARAM_{side}_HPF_FREQ"] = clamp(s["hp"], 15.625, 21357.44)
        v[f"PARAM_{side}_LPF_ON"] = 0
    return v


def q4_values(s):
    v = {}
    names = {1: ("PARAM_BAND_STATE", "PARAM_BAND_TYPE", "PARAM_BAND_GAIN", "PARAM_BAND_FRQ", "PARAM_BAND_QF")}
    for b in range(2, 5):
        names[b] = tuple(f"PARAM_BAND{b}_{x}_L" for x in ("STATE", "TYPE", "GAIN", "FREQ", "Q"))
    rnames = {b: tuple(f"PARAM_BAND{b}_{x}_R" for x in ("STATE", "TYPE", "GAIN", "FREQ", "Q")) for b in range(1, 5)}
    for b in range(1, 5):
        v[names[b][0]] = v[rnames[b][0]] = 0
    for slot, (kind, f, g, q) in s["eq"].items():
        code = LOW_TYPE.get(kind) if slot in (1, 2) else HIGH_TYPE.get(kind)
        vals = [1, code, 0 if kind in ("HighPass", "LowPass") else clamp(g, -18, 18), clamp(f, 15.625, 21357.44)]
        qv = None if kind in ("HighPass", "LowPass") else clamp(q, 0.05, 6.5)
        for nm in (names[slot], rnames[slot]):
            for n, x in zip(nm[:4], vals):
                v[n] = x
            if qv is not None:
                v[nm[4]] = qv
    extra = s["trim"] - TRIM_MAX if s["trim"] > TRIM_MAX else 0.0
    v["PARAM_OUT_GAIN_L"] = v["PARAM_OUT_GAIN_R"] = clamp(extra, -12, 12)
    return v


def d5_values(s):
    v = {}
    g = s["gate"]
    v["PARAM_GATE_ON"] = 1 if g else 0
    if g:
        v.update({"PARAM_GATE_EXP": 0, "PARAM_GATE_THRESH": clamp(g["thr"], -144, 0),
                  "PARAM_GATE_FLOOR": clamp(g["floor"], -144, 0), "PARAM_GATE_ATT": clamp(g["att"], 0.1, 100),
                  "PARAM_GATE_HOLD": clamp(g["hold"], 0.4, 10000), "PARAM_GATE_REL": clamp(g["rel"], 1, 1000),
                  "PARAM_GATE_HPF_ON": 1 if g["key_hp"] else 0, "PARAM_GATE_LPF_ON": 1 if g["key_lp"] else 0})
        if g["key_hp"]:
            v["PARAM_GATE_HPF_FREQ"] = clamp(g["key_hp"], 15.625, 18000)
        if g["key_lp"]:
            v["PARAM_GATE_LPF_FREQ"] = clamp(g["key_lp"], 15.625, 18000)
    c = s["comp"]
    v["PARAM_COMP_ON"] = 1 if c else 0
    if c:
        v.update({"PARAM_COMP_THRESH": clamp(c["thr"], -48, 0), "PARAM_COMP_RATIO": clamp(c["ratio"], 1, 20),
                  "PARAM_COMP_KNEE": KNEE[c["knee"]], "PARAM_COMP_ATT": clamp(c["att"], 0.5, 300),
                  "PARAM_COMP_REL_MODE": REL_MANUAL, "PARAM_COMP_MAX_REL": clamp(c["rel"], 1, 3000),
                  "PARAM_COMP_MAKEUP": clamp(c["makeup"], -18, 18), "PARAM_COMP_MIX": clamp(c["mix"], 0, 100),
                  "PARAM_COMP_HPF_ON": 1 if c["key_hp"] else 0, "PARAM_COMP_LPF_ON": 1 if c["key_lp"] else 0})
        if c["key_hp"]:
            v["PARAM_COMP_HPF_FREQ"] = clamp(c["key_hp"], 15.625, 18000)
        if c["key_lp"]:
            v["PARAM_COMP_LPF_FREQ"] = clamp(c["key_lp"], 15.625, 18000)
    return v


def fmt(x):
    if isinstance(x, str):
        return x
    return str(int(x)) if float(x).is_integer() else format(float(x), ".17g")


def build_chunk(template, names, values):
    def repl(m):
        toks = m.group(1).split()
        if len(toks) != len(names):
            raise ValueError(f"chunk has {len(toks)} values, ParamXML lists {len(names)}")
        for n, x in values.items():
            i = names.index(n)
            if toks[i] == "*":
                raise ValueError(f"{n} is display-only")
            toks[i] = fmt(x)
        lines = [" ".join(toks[i:i + 10]) for i in range(0, len(toks), 10)]
        return '<Parameters Type="RealWorld">\n' + "\n".join(lines) + "\n</Parameters>"
    return re.sub(r'<Parameters Type="RealWorld">(.*?)</Parameters>', repl, template, flags=re.S)


def apply(cur, obj_ids, x32_scene, ch_map, snaps, fixed_rack=False):
    """ch_map: {x32_channel: lv1_input_index}. fixed_rack: keep the layout's plugin order. Returns report lines."""
    ch, _head, xname = parse(x32_scene)
    names = {p: param_names(p) for p in ("EMO-F2", "EMO-D5", "EMO-Q4")}
    pid = dict(cur.execute("select name, id from chainer_params"))
    report = []
    for x32n, lv1i in sorted(ch_map.items()):
        s = x32_settings(ch[x32n])
        chainer = obj_ids[lv1i]
        plugs = dict(cur.execute("select plugin_name, id from plug where chainer_id=?", (chainer,)))
        notes = list(s["not_converted"])
        notes += [f"{p} not in the rack, its settings skipped" for p in names if p not in plugs]
        if not fixed_rack and "EMO-D5" in plugs and "EMO-Q4" in plugs:
            slots = dict(cur.execute("select plugin_name, slot from plug where chainer_id=?", (chainer,)))
            if (slots["EMO-Q4"] < slots["EMO-D5"]) != s["comp_post_eq"]:
                d5, q4 = plugs["EMO-D5"], plugs["EMO-Q4"]
                cur.execute("update plug set slot=-1 where id=?", (d5,))
                cur.execute("update plug set slot=? where id=?", (slots["EMO-D5"], q4))
                cur.execute("update plug set slot=? where id=?", (slots["EMO-Q4"], d5))
        slots = dict(cur.execute("select plugin_name, slot from plug where chainer_id=?", (chainer,)))
        extra = s["trim"] - TRIM_MAX if s["trim"] > TRIM_MAX else 0.0
        d5_before_gain = "EMO-Q4" not in plugs or ("EMO-D5" in plugs and slots["EMO-D5"] < slots["EMO-Q4"])
        if extra and d5_before_gain and (s["gate"] or s["comp"]):
            for k in ("gate", "comp"):
                if s[k]:
                    s[k]["thr"] -= extra
            notes.append(f"D5 thresholds {-extra:+.1f} dB: D5 runs before the Q4 gain, so it gets {extra:.1f} dB less")
        vals = {"EMO-F2": f2_values(s), "EMO-D5": d5_values(s), "EMO-Q4": q4_values(s)}
        active = {"EMO-F2": bool(s["hp"]), "EMO-D5": bool(s["gate"] or s["comp"]), "EMO-Q4": bool(s["eq"] or extra)}
        for pname, v in vals.items():
            if pname not in plugs:
                continue
            template = cur.execute(
                "select pp.preset from snapshot_plugin sp join plugin_preset pp on pp.id=sp.preset_id"
                " where sp.plug_id=? and sp.snapshot_id=?", (plugs[pname], snaps[0])).fetchone()[0]
            chunk = build_chunk(template, names[pname], v)
            h = hashlib.sha3_256(chunk.encode()).hexdigest()
            row = cur.execute("select id from plugin_preset where hash=?", (h,)).fetchone()
            if row:
                new_id = row[0]
            else:
                cur.execute("insert into plugin_preset (hash, ref_count, preset) values (?,0,?)", (h, chunk))
                new_id = cur.lastrowid
            for snap in snaps:
                old = cur.execute("select preset_id from snapshot_plugin where plug_id=? and snapshot_id=?",
                                  (plugs[pname], snap)).fetchone()
                if old and old[0] != new_id:
                    cur.execute("update snapshot_plugin set preset_id=? where plug_id=? and snapshot_id=?",
                                (new_id, plugs[pname], snap))
            bypassed = cur.execute("select count(*) from snapshot_plugin where plug_id=? and bypass",
                                   (plugs[pname],)).fetchone()[0]
            if active[pname] and bypassed:
                notes.append(f"{pname} is bypassed in the session; settings written, left bypassed")
        for snap in snaps:
            phase, trim = 1 if s["invert"] else 0, min(s["trim"], TRIM_MAX)
            for n, x in [(f"PARAM_INPUT_PHASE_ONOFF{sfx}", phase) for sfx in ("", "_L", "_R")] + \
                        [(f"PARAM_INPUT_DIGITAL_TRIM{sfx}", trim) for sfx in ("", "_L", "_R")]:
                cur.execute("insert or replace into snapshot_chainer_params values (?,?,?,?)",
                            (chainer, snap, pid[n], float(x)))
        if extra and "EMO-Q4" in plugs:
            notes.append(f"trim {s['trim']:+.1f} dB -> {TRIM_MAX:+.0f} trim + {extra:+.1f} Q4 out")
        elif extra:
            notes.append(f"trim {s['trim']:+.1f} dB -> {TRIM_MAX:+.0f} trim, {extra:+.1f} dB missing"
                         " (no EMO-Q4 to make it up)")
        if s["eq_dropped"]:
            notes.append("EQ band dropped: " + ", ".join(f"{k} {f:.0f} Hz" for k, f, _g, _q in s["eq_dropped"]))
        if s["comp"] and s["comp"]["ratio"] > 20:
            notes.append(f"ratio {s['comp']['ratio']:g} -> 20")
        if s["gate"] and s["gate"]["rel"] > 1000:
            notes.append(f"gate release {s['gate']['rel']:g} -> 1000 ms")
        if fixed_rack:
            order = "rack from layout" + ("" if s["comp_post_eq"] or not s["comp"] else ", X32 comp was PRE EQ")
        else:
            order = "F2 Q4 D5" if s["comp_post_eq"] else "F2 D5 Q4"
        report.append(f"X32 ch {x32n} {xname[x32n]} -> LV1 ch {lv1i + 1}: {order}"
                      + (f" ({'; '.join(notes)})" if notes else ""))
    return report
