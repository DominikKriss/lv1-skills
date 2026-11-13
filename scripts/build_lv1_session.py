#!/usr/bin/env python3
"""Apply a monitor layout (JSON config) and optional X32 eMo settings to a copy of an LV1 .emo session.

Usage: build_lv1_session.py <source.emo> <output.emo> <layout.json> [x32_scene.scn]

Writes, for the Active state (-1) and every stored snapshot: input / FX / Mon / Matrix names, faders,
channel -> FX and channel -> Mon sends (level, on, pick-off), FX -> Mon returns, Mon / Matrix mono-stereo,
Matrix n <- Mon n. With an X32 scene: eMo F2 / D5 / Q4, trim, polarity and rack order per `x32_to_lv1`.
Does not touch patching or add plugins.
"""
import json
import shutil
import sqlite3
import sys

import emo_presets

PICK = {"INP": 0, "PRE": 1, "PST": 2, "PSP": 3}
OFF_DB = -144.0
T_INPUT, T_AUX, T_MATRIX, T_MON = 0, 2, 6, 25


def send_suffix(kind, index):
    """FX n -> slot n-1; Mon 1-8 -> 8-15, Mon 9-16 -> 2_0-7, Mon 17-24 -> 3_0-7."""
    if kind == "fx":
        return str(index)
    if index < 8:
        return str(8 + index)
    return f"{2 + (index - 8) // 8}_{(index - 8) % 8}"


def main(src, dst, layout_path, x32=None):
    cfg = json.load(open(layout_path))
    inputs = cfg["inputs"]
    mons = cfg["mons"]
    fxs = cfg.get("fx", [])
    lv = cfg.get("levels", {})
    other_db, own_db = lv.get("other_db", -10.0), lv.get("own_db", 0.0)
    ret = cfg.get("fx_returns", {})
    always_pre = set(cfg.get("always_pre_0db", []))
    unknown = ({n for m in mons for n in m.get("own", [])} | always_pre
               | {n for f in fxs for n in f.get("feeds", {})}) - set(inputs)
    if unknown:
        sys.exit(f"layout names not in inputs: {sorted(unknown)}")

    shutil.copyfile(src, dst)
    db = sqlite3.connect(dst)
    cur = db.cursor()
    pid = dict(cur.execute("select name, id from chainer_params"))
    obj = {(t, i): oid for oid, t, i in cur.execute("select id, obj_type, obj_index from object")}
    snaps = [r[0] for r in cur.execute("select id from snapshot")]

    def set_param(t, i, name, value):
        for s in snaps:
            cur.execute("insert or replace into snapshot_chainer_params values (?,?,?,?)",
                        (obj[(t, i)], s, pid[name], float(value)))

    def set_name(t, i, name):
        cur.execute("update snapshot_chainer set name=? where chainer_id=?", (name, obj[(t, i)]))

    def send(t, i, kind, idx, db_val, pick):
        sfx = send_suffix(kind, idx)
        set_param(t, i, f"PARAM_AUX_SEND_GAIN_{sfx}", db_val)
        set_param(t, i, f"PARAM_AUX_SEND_ONOFF_{sfx}", 1 if db_val > OFF_DB else 0)
        set_param(t, i, f"PARAM_AUX_SEND_SOURCE_{sfx}", PICK[pick])

    for i, name in enumerate(inputs):
        set_name(T_INPUT, i, name)
        set_param(T_INPUT, i, "PARAM_OUTPUT_GAIN", 0.0)
        for f, fx in enumerate(fxs):
            level, pick = fx.get("feeds", {}).get(name, [OFF_DB, "PSP"])
            send(T_INPUT, i, "fx", f, level, pick)
        for m, mon in enumerate(mons):
            if not mon.get("sends", True):
                continue
            if name in always_pre or name in mon.get("own", []):
                send(T_INPUT, i, "mon", m, own_db, "PRE")
            else:
                send(T_INPUT, i, "mon", m, other_db, "PSP")

    for f, fx in enumerate(fxs):
        set_name(T_AUX, f, fx["name"])
        set_param(T_AUX, f, "PARAM_OUTPUT_GAIN", 0.0)
        if not fx.get("feeds"):
            continue
        for m, mon in enumerate(mons):
            if not mon.get("sends", True):
                continue
            owner = fx.get("dedicated_to")
            if owner:
                level = ret.get("own_db", -6.0) if owner == mon["name"] else ret.get("other_db", -15.0)
            else:
                level = ret.get("general_db", -10.0)
            send(T_AUX, f, "mon", m, level, "PSP")

    for m, mon in enumerate(mons):
        set_name(T_MON, m, mon["name"])
        set_param(T_MON, m, "PARAM_OUTPUT_GAIN", 0.0)
        width = 2 if mon.get("stereo") else 1
        cur.execute("update chainer set num_inputs=? where obj_id=?", (width, obj[(T_MON, m)]))
        if mon.get("matrix"):
            mx = mon["matrix"] - 1
            set_name(T_MATRIX, mx, mon["name"])
            set_param(T_MATRIX, mx, "PARAM_OUTPUT_GAIN", 0.0)
            cur.execute("update chainer set num_inputs=? where obj_id=?", (width, obj[(T_MATRIX, mx)]))
            for s in snaps:
                cur.execute(
                    "insert or ignore into snapshot_assignment (snapshot_id, src_id, src_section_type,"
                    " src_section_index, src_channel_index, src_control_id, src_asgn_type, dst_id,"
                    " dst_section_type, dst_section_index, dst_channel_index, dst_control_id,"
                    " dst_asgn_type, status) values (?,?,7,-1,-1,0,0,?,0,0,-1,-1,0,0)",
                    (s, obj[(T_MON, m)], obj[(T_MATRIX, mx)]))

    if x32:
        ch_map = {int(k): v - 1 for k, v in cfg["x32_to_lv1"].items()}
        in_ids = {i: obj[(T_INPUT, i)] for i in range(len(inputs))}
        for line in emo_presets.apply(cur, in_ids, x32, ch_map, snaps):
            print(line)

    db.commit()
    ok = cur.execute("pragma integrity_check").fetchone()[0]
    refs = cur.execute("select sum(ref_count), (select count(*) from snapshot_plugin) from plugin_preset").fetchone()
    db.close()
    print(f"wrote {dst} (snapshots {snaps}), integrity: {ok}, preset refs {refs[0]}/{refs[1]}")


if __name__ == "__main__":
    if len(sys.argv) not in (4, 5):
        sys.exit(__doc__)
    main(*sys.argv[1:5])
