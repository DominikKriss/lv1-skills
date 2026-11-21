#!/usr/bin/env python3
"""Build the event WING snapshot from a WING-Edit INIT CONSOLE save.

Usage: build_wing_scene.py BASE.snap layout.json OUT.snap [--dry-run] [--changes]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import x32_to_wing  # noqa: E402


class Refuse(Exception):
    pass


PREMIUM = {"HALL", "ROOM", "CHAMBER", "PLATE", "CONCERT", "AMBI", "BPLATE", "V-PLATE", "V-ROOM", "V-REV", "GATED",
           "REVERSE", "VSS3", "SHIMMER", "SPRING", "ST-DL", "TAP-DL", "TAPE-DL", "OILCAN", "BBD-DL", "DEL/REV",
           "CHORUS", "FLANGER", "DIMCRS", "PITCH", "D-PITCH"}


def load(path):
    with open(path, "rb") as f:
        raw = f.read().decode("utf-8")
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")
    pretty = "\n" in text.strip()
    return json.loads(text), text, crlf, pretty


def dump(doc, crlf, pretty, trailing_nl):
    if pretty:
        out = json.dumps(doc, indent=2, ensure_ascii=False)
    else:
        out = json.dumps(doc, separators=(",", ":"), ensure_ascii=False)
    if trailing_nl:
        out += "\n"
    return out.replace("\n", "\r\n") if crlf else out


class Snap:
    def __init__(self, doc):
        self.doc = doc
        self.changes = []

    def node(self, path):
        cur = self.doc["ae_data"]
        for key in path.split("."):
            if not isinstance(cur, dict) or key not in cur:
                raise Refuse(f"ae_data.{path} is not in the base snapshot; refusing to invent keys.")
            cur = cur[key]
        return cur

    def has(self, path):
        try:
            self.node(path)
            return True
        except Refuse:
            return False

    def set(self, path, value):
        parent, _, key = path.rpartition(".")
        holder = self.node(parent)
        if key not in holder:
            raise Refuse(f"ae_data.{path} is not in the base snapshot; refusing to invent keys.")
        old = holder[key]
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        if type(old) is not type(value) and not (isinstance(old, (int, float)) and isinstance(value, (int, float))):
            raise Refuse(f"ae_data.{path} holds {type(old).__name__}, not {type(value).__name__}.")
        if old != value:
            holder[key] = value
            self.changes.append(f"{path}: {old!r} -> {value!r}")

    def set_if(self, path, value):
        if self.has(path):
            self.set(path, value)

    def strip(self, path, name, col):
        self.set(f"{path}.name", name)
        self.set(f"{path}.col", col)

    def matrix_send(self, strip, n):
        for key in (f"MX{n}", str(n)):
            if self.has(f"{strip}.send.{key}"):
                return f"{strip}.send.{key}"
        raise Refuse(f"ae_data.{strip}.send has no matrix {n} send.")


def sockets(spec):
    return [(grp, n) for grp, count in spec for n in range(1, count + 1)]


def patch_socket(snap, i, grp, n, width, sheet):
    for k in range(width):
        sock = f"io.in.{grp}.{n + k}"
        snap.set(f"{sock}.mode", "ST" if width == 2 else "M")
        snap.set(f"{sock}.name", i["name"])
    snap.set(f"{i['strip']}.in.conn.grp", grp)
    snap.set(f"{i['strip']}.in.conn.in", n)
    legs = f"{grp}{n}" + (f"+{n + 1}" if width == 2 else "")
    sheet.append(f"in  {legs:<8} {i['strip']:<6} {i['name']}")


def patch(snap, lay):
    sheet = []
    if any("src" in i for i in lay["inputs"]):
        for i in lay["inputs"]:
            if "src" not in i:
                raise Refuse(f"{i['strip']} {i['name']} has no src while others do.")
            grp, n = i["src"]
            width = 2 if i.get("stereo") else 1
            if width == 2 and n % 2 == 0:
                raise Refuse(f"{i['name']} on {grp}{n}: a stereo source needs an odd/even socket pair.")
            patch_socket(snap, i, grp, n, width, sheet)
        return sheet + patch_outputs(snap, lay)
    free = sockets(lay["in_sockets"])
    pos = 0
    for i in lay["inputs"]:
        width = 2 if i.get("stereo") else 1
        while width == 2 and pos < len(free) and free[pos][1] % 2 == 0:
            sheet.append(f"in  {free[pos][0]}{free[pos][1]:<3} (spare, keeps the next stereo pair on odd/even)")
            pos += 1
        if pos + width > len(free) or (width == 2 and free[pos][0] != free[pos + 1][0]):
            raise Refuse(f"{i['strip']} {i['name']} does not fit on the stagebox inputs.")
        grp, n = free[pos]
        patch_socket(snap, i, grp, n, width, sheet)
        pos += width
    return sheet + patch_outputs(snap, lay)


def patch_outputs(snap, lay):
    sheet = []
    taken = set()
    for o in lay["outputs"]:
        if "sock" in o:
            width = 2 if o.get("stereo") else 1
            legs = {(o["sock"][0], o["sock"][1] + k) for k in range(width)}
            if legs & taken:
                raise Refuse(f"{o['name']}: output socket {sorted(legs & taken)} is already used by another output.")
            taken.update(legs)
    outs = [s for s in sockets(lay.get("out_sockets", [])) if s not in taken]
    pos = 0
    for o in lay["outputs"]:
        legs = [2 * o["strip"] - 1, 2 * o["strip"]] if o.get("stereo") else [2 * o["strip"] - 1]
        if "sock" in o:
            g0, n0 = o["sock"]
            targets = [(g0, n0 + k) for k in range(len(legs))]
        else:
            if pos + len(legs) > len(outs):
                raise Refuse(f"{o['name']} does not fit on the stagebox outputs.")
            targets = outs[pos:pos + len(legs)]
            pos += len(legs)
        for k, src in enumerate(legs):
            g, s = targets[k]
            snap.set(f"io.out.{g}.{s}.grp", o["src"])
            snap.set(f"io.out.{g}.{s}.in", src)
            side = ("", " L", " R")[k + 1 if o.get("stereo") else 0]
            sheet.append(f"out {g}{s:<7} {o['src']} {src:<3} {o['name']}{side}")
    return sheet


def set_fx(snap, slot, model):
    if model in PREMIUM and not 1 <= slot <= 8:
        raise Refuse(f"{model} is a premium model and runs only in FX slots 1-8.")
    node = snap.node(f"fx.{slot}")
    if node.get("mdl") != model:
        snap.changes.append(f"fx.{slot}: {node.get('mdl')!r} -> {model!r} (model defaults)")
        snap.node("fx")[str(slot)] = {"mdl": model, "fxmix": 100}
    else:
        snap.set(f"fx.{slot}.fxmix", 100)


def insert(snap, strip, where, slot, model):
    set_fx(snap, slot, model)
    snap.set(f"{strip}.{where}.on", True)
    snap.set(f"{strip}.{where}.ins", f"FX{slot}")
    if where == "postins":
        snap.set_if(f"{strip}.postins.mode", "FX")


def build(snap, lay):
    col = lay["colours"]
    fx_buses = [f["bus"] for f in lay["fx"]]
    mon_buses = [m["bus"] for m in lay["mons"]]
    groups = lay.get("groups", [])
    member = {}
    for g in groups:
        for name in g["members"]:
            if name not in {i["name"] for i in lay["inputs"]}:
                raise Refuse(f"group {g['name']}: no input named {name!r}.")
            member.setdefault(name, set()).add(g["bus"])
    tags = {}
    for d in lay.get("dcas", []):
        for name in d["members"]:
            tags.setdefault(name, []).append(f"#D{d['n']}")

    for i in lay["inputs"]:
        s = i["strip"]
        if len(i["name"]) > 16:
            raise Refuse(f"{s} name {i['name']!r} is longer than 16 characters.")
        snap.strip(s, i["name"], col[i["group"]])
        snap.set(f"{s}.clink", False)
        snap.set(f"{s}.main.{lay['main']['n']}.on", i["name"] not in member)
        for g in groups:
            snap.set(f"{s}.send.{g['bus']}.on", g["bus"] in member.get(i["name"], ()))
            snap.set(f"{s}.send.{g['bus']}.mode", "GRP")
        if i["name"] in tags:
            snap.set(f"{s}.tags", ",".join(tags[i["name"]]))
        for b in mon_buses:
            snap.set(f"{s}.send.{b}.on", True)
            snap.set(f"{s}.send.{b}.mode", "PRE")
        for b in fx_buses:
            snap.set(f"{s}.send.{b}.on", True)
            snap.set(f"{s}.send.{b}.mode", "POST")
            snap.set(f"{s}.send.{b}.lvl", -144)

    for m in lay["mons"]:
        b = f"bus.{m['bus']}"
        snap.strip(b, m["name"], col["mon"])
        snap.set(f"{b}.busmono", m.get("mono", True))
        snap.set(f"{b}.main.{lay['main']['n']}.on", False)

    for g in groups:
        b = f"bus.{g['bus']}"
        snap.strip(b, g["name"], col[g.get("col", "group")])
        snap.set(f"{b}.busmono", False)
        snap.set(f"{b}.main.{lay['main']['n']}.on", True)
        snap.set(f"{b}.main.{lay['main']['n']}.lvl", 0)
        for where in ("preins", "postins"):
            if where in g:
                insert(snap, b, where, g[where]["slot"], g[where]["model"])
        if "dyn" in g:
            dyn = snap.node(f"{b}.dyn")
            if dyn.get("mdl") != g["dyn"]:
                snap.changes.append(f"{b}.dyn: {dyn.get('mdl')!r} -> {g['dyn']!r} (model defaults, off)")
                snap.node(b)["dyn"] = {"on": False, "mdl": g["dyn"], "mix": 100, "gain": 0}

    for d in lay.get("dcas", []):
        snap.strip(f"dca.{d['n']}", d["name"], col[d["col"]])

    for m in lay.get("main_extra", []):
        snap.strip(f"main.{m['n']}", m["name"], col["main"])

    for f in lay["fx"]:
        b = f"bus.{f['bus']}"
        snap.strip(b, f["name"], col["fx"])
        snap.set(f"{b}.busmono", False)
        insert(snap, b, "preins", f["slot"], f["model"])
        snap.set(f"{b}.main.{lay['main']['n']}.on", True)
        snap.set(f"{b}.main.{lay['main']['n']}.lvl", 0)

    for n in lay.get("unused_buses", []):
        snap.set(f"bus.{n}.main.{lay['main']['n']}.on", False)

    mn = f"main.{lay['main']['n']}"
    snap.strip(mn, lay["main"]["name"], col["main"])
    snap.set_if(f"{mn}.busmono", lay["main"]["mono"])
    for m in lay["matrices"]:
        x = f"mtx.{m['n']}"
        snap.strip(x, m["name"], col["mtx"])
        snap.set(f"{x}.busmono", m["mono"])
        send = snap.matrix_send(mn, m["n"])
        snap.set(f"{send}.on", True)
        snap.set(f"{send}.lvl", 0)
        snap.set_if(f"{send}.pre", False)

    notes = processing(snap, lay)
    return patch(snap, lay), notes


def processing(snap, lay):
    notes = []
    proc = lay.get("processing")
    if not proc:
        return notes
    chans = x32_to_wing.read_scn(os.path.join(lay["_dir"], proc["x32_scene"]))
    done = set()
    for strip, x32ch in proc["from_x32"].items():
        try:
            x32_to_wing.apply(snap, strip, chans[x32ch], notes)
        except ValueError as e:
            raise Refuse(str(e))
        done.add(strip)
    lc = proc["lowcut_rest"]
    for i in lay["inputs"]:
        s = i["strip"]
        if s in done or i["name"] in lc["skip"]:
            continue
        if snap.has(f"{s}.flt"):
            snap.set(f"{s}.flt.lc", True)
            snap.set(f"{s}.flt.lcf", float(lc["freq"]))
            snap.set(f"{s}.flt.lcs", lc["slope"])
        else:
            snap.set(f"{s}.eq.on", True)
            snap.set(f"{s}.eq.leq", lc["eq_token"])
            snap.set(f"{s}.eq.lf", float(lc["freq"]))
            notes.append(f"{s} has no input filter: low cut as EQ low band {lc['eq_token']}")
    return notes


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    dry = "--dry-run" in argv
    if len(args) != 3:
        print(__doc__.strip())
        return 2
    base, layout, out = args
    for src in (base, layout):
        if os.path.abspath(src) == os.path.abspath(out) or (os.path.exists(out) and os.path.samefile(src, out)):
            print(f"refused: write a new file, not {src}.")
            return 1
    doc, text, crlf, pretty = load(base)
    trailing = text.endswith("\n")
    if dump(doc, False, pretty, trailing) != text:
        print("warning: the base does not round-trip byte for byte; WING-Edit will reformat it on save anyway.")
    if not str(doc.get("type", "")).startswith("snapshot."):
        print(f"refused: {base} is not a WING snapshot (type {doc.get('type')!r}).")
        return 1
    with open(layout, encoding="utf-8") as f:
        lay = json.load(f)
    snap = Snap(doc)
    try:
        lay["_dir"] = os.path.dirname(os.path.abspath(layout))
        sheet, notes = build(snap, lay)
    except Refuse as e:
        print(f"refused: {e}")
        return 1
    print(f"{doc['type']}, {len(snap.changes)} changes")
    if "--changes" in argv:
        for c in snap.changes:
            print("  " + c)
    for n in notes:
        print("note: " + n)
    print("patch:")
    for line in sheet:
        print("  " + line)
    if not dry:
        with open(out, "wb") as f:
            f.write(dump(doc, crlf, pretty, trailing).encode("utf-8"))
        print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
