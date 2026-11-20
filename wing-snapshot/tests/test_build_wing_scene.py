import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import fixtures
import build_wing_scene as b

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def run(layout, extra=None):
    with tempfile.TemporaryDirectory() as d:
        base, out, lay = Path(d, "base.snap"), Path(d, "out.snap"), Path(d, "layout.json")
        base.write_text(fixtures.snapshot())
        data = json.loads(Path(layout).read_text()) if isinstance(layout, (str, Path)) else layout
        if extra:
            Path(d, "scene.scn").write_text(extra)
        lay.write_text(json.dumps(data))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = b.main([str(base), str(lay), str(out)])
        snap = json.loads(out.read_text()) if out.exists() else None
        return code, buf.getvalue(), snap


class Examples(unittest.TestCase):
    def test_auto_patch(self):
        code, out, snap = run(EXAMPLES / "layout-auto.example.json")
        self.assertEqual(code, 0, out)
        ae = snap["ae_data"]
        self.assertEqual(ae["ch"]["8"]["name"], "KEYS LR")
        self.assertEqual(ae["ch"]["8"]["in"]["conn"], {"grp": "A", "in": 9, "altgrp": "OFF", "altin": 1})
        self.assertEqual(ae["io"]["in"]["A"]["9"]["mode"], "ST")
        self.assertIn("A8   (spare", out)
        self.assertTrue(ae["bus"]["1"]["busmono"])
        self.assertEqual(ae["bus"]["13"]["preins"], {"on": True, "ins": "FX1"})
        self.assertEqual(ae["fx"]["1"]["mdl"], "HALL")
        self.assertTrue(ae["main"]["1"]["send"]["MX2"]["on"])
        self.assertEqual(ae["io"]["out"]["A"]["5"], {"grp": "MTX", "in": 1})

    def test_explicit_patch_groups_dcas(self):
        code, out, snap = run(EXAMPLES / "layout-explicit.example.json")
        self.assertEqual(code, 0, out)
        ae = snap["ae_data"]
        kick = ae["ch"]["1"]
        self.assertFalse(kick["main"]["1"]["on"])
        self.assertEqual((kick["send"]["8"]["on"], kick["send"]["8"]["mode"]), (True, "GRP"))
        self.assertEqual(kick["tags"], "#D1")
        self.assertTrue(ae["ch"]["11"]["main"]["1"]["on"])
        self.assertEqual(ae["ch"]["11"]["in"]["conn"]["grp"], "LCL")
        self.assertEqual(ae["bus"]["8"]["dyn"]["mdl"], "LA")
        self.assertFalse(ae["bus"]["8"]["dyn"]["on"])
        self.assertEqual(ae["bus"]["9"]["postins"], {"on": True, "ins": "FX10"})
        self.assertEqual(ae["dca"]["2"]["name"], "D VOX")
        self.assertEqual(ae["main"]["2"]["name"], "SMAART RET.")


class Guards(unittest.TestCase):
    def test_stereo_on_even_socket_refused(self):
        lay = json.loads((EXAMPLES / "layout-explicit.example.json").read_text())
        lay["inputs"][7]["src"] = ["A", 8]
        code, out, snap = run(lay)
        self.assertEqual(code, 1)
        self.assertIn("odd/even", out)
        self.assertIsNone(snap)

    def test_premium_fx_outside_slots_1_8_refused(self):
        lay = json.loads((EXAMPLES / "layout-auto.example.json").read_text())
        lay["fx"][0]["slot"] = 9
        code, out, _ = run(lay)
        self.assertEqual(code, 1)
        self.assertIn("premium", out)

    def test_unknown_key_refused(self):
        snap = b.Snap(json.loads(fixtures.snapshot()))
        with self.assertRaises(b.Refuse):
            snap.set("ch.1.nokey", 1)

    def test_unknown_group_member_refused(self):
        lay = json.loads((EXAMPLES / "layout-explicit.example.json").read_text())
        lay["groups"][0]["members"].append("NOBODY")
        code, out, _ = run(lay)
        self.assertEqual(code, 1)


class Outputs(unittest.TestCase):
    def test_auto_outputs_skip_explicit_sockets(self):
        lay = json.loads((EXAMPLES / "layout-auto.example.json").read_text())
        lay["outputs"][0]["sock"] = ["A", 1]
        code, out, snap = run(lay)
        self.assertEqual(code, 0, out)
        self.assertEqual(snap["ae_data"]["io"]["out"]["A"]["1"], {"grp": "BUS", "in": 1})
        self.assertEqual(snap["ae_data"]["io"]["out"]["A"]["2"], {"grp": "BUS", "in": 3})

    def test_output_over_base_refused(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d, "base.snap")
            base.write_text(fixtures.snapshot())
            link = Path(d, "link.snap")
            link.symlink_to(base)
            with contextlib.redirect_stdout(io.StringIO()):
                code = b.main([str(base), str(EXAMPLES / "layout-auto.example.json"), str(link)])
            self.assertEqual(code, 1)
            self.assertEqual(base.read_text(), fixtures.snapshot())


class X32(unittest.TestCase):
    def test_processing_from_scene(self):
        lay = json.loads((EXAMPLES / "layout-auto.example.json").read_text())
        lay["processing"] = {"x32_scene": "scene.scn", "from_x32": {"ch.1": 1},
                             "lowcut_rest": {"freq": 120, "slope": "24", "eq_token": "CUT", "skip": ["BASS"]}}
        code, out, snap = run(lay, fixtures.SCENE)
        self.assertEqual(code, 0, out)
        ch = snap["ae_data"]["ch"]
        self.assertTrue(ch["1"]["in"]["set"]["inv"])
        self.assertEqual(ch["1"]["flt"]["lcf"], 40)
        self.assertEqual(ch["1"]["gate"]["ratio"], "GATE")
        self.assertEqual(ch["1"]["gatesc"]["type"], "BP")
        self.assertEqual(ch["1"]["proc"], "GDEI")
        self.assertEqual((ch["1"]["eq"]["lf"], ch["1"]["eq"]["hf"]), (116.4, 4850))
        self.assertEqual(ch["1"]["flt"]["hcf"], 8000)
        self.assertEqual(ch["2"]["flt"]["lcf"], 120)
        self.assertFalse(ch["6"]["flt"]["lc"])


class X32EqOff(unittest.TestCase):
    def test_cut_stays_off_when_x32_eq_off(self):
        lay = json.loads((EXAMPLES / "layout-auto.example.json").read_text())
        lay["processing"] = {"x32_scene": "scene.scn", "from_x32": {"ch.1": 1},
                             "lowcut_rest": {"freq": 120, "slope": "24", "eq_token": "CUT", "skip": []}}
        code, out, snap = run(lay, fixtures.SCENE.replace("/ch/01/eq ON", "/ch/01/eq OFF"))
        self.assertEqual(code, 0, out)
        self.assertFalse(snap["ae_data"]["ch"]["1"]["flt"]["hc"])

    def test_preamp_low_cut_kept_when_eq_off_has_lcut(self):
        lay = json.loads((EXAMPLES / "layout-auto.example.json").read_text())
        lay["processing"] = {"x32_scene": "scene.scn", "from_x32": {"ch.1": 1},
                             "lowcut_rest": {"freq": 120, "slope": "24", "eq_token": "CUT", "skip": []}}
        scene = fixtures.SCENE.replace("/ch/01/eq ON", "/ch/01/eq OFF").replace("HCut 8k00", "LCut 300.0")
        code, out, snap = run(lay, scene)
        self.assertEqual(code, 0, out)
        flt = snap["ae_data"]["ch"]["1"]["flt"]
        self.assertEqual((flt["lc"], flt["lcf"], flt["lcs"]), (True, 40, "24"))


if __name__ == "__main__":
    unittest.main()
