import contextlib
import io
import tempfile
import unittest
from pathlib import Path

import fixtures
import x32_to_emo


def run(scene):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        x32_to_emo.main(scene)
    return out.getvalue()


class Helpers(unittest.TestCase):
    def test_hz(self):
        self.assertEqual(x32_to_emo.hz("1k00"), 1000.0)
        self.assertEqual(x32_to_emo.hz("2k50"), 2500.0)
        self.assertEqual(x32_to_emo.hz("80.0"), 80.0)

    def test_bandpass_key_filter_gives_both_edges(self):
        self.assertIn("Key HPF", x32_to_emo.key_filter(["ON", "2.0", "1k00"]))
        self.assertIn("LPF", x32_to_emo.key_filter(["ON", "2.0", "1k00"]))
        self.assertEqual(x32_to_emo.key_filter(["OFF", "2.0", "1k00"]), "-")


class Report(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_parse_names_and_headamps(self):
        scene = fixtures.write_scene(self.dir / "s.scn", {1: {"name": "KICK"}, 2: {"name": "SN"}},
                                     headamps={0: ("+30.0", "ON")})
        ch, head, name = x32_to_emo.parse(scene)
        self.assertEqual(name, {1: "KICK", 2: "SN"})
        self.assertEqual(head[0], ["+30.0", "ON"])

    def test_flat_channel_is_skipped(self):
        scene = fixtures.write_scene(self.dir / "s.scn", {1: {"name": "FLAT"}})
        self.assertNotIn("FLAT", run(scene))

    def test_channel_with_processing_is_reported(self):
        scene = fixtures.write_scene(self.dir / "s.scn", {1: {"name": "KICK", "hp": ("ON", "80"),
                                                              "dyn": {"on": "ON", "ratio": "30.0"}}})
        out = run(scene)
        self.assertIn("Ch 1 KICK", out)
        self.assertIn("F2: HP ON 80 Hz", out)
        self.assertIn("Ratio 20", out)

    def test_trim_only_channel_is_reported(self):
        scene = fixtures.write_scene(self.dir / "s.scn", {1: {"name": "TRIM", "trim": "+6.0"}})
        self.assertIn("Ch 1 TRIM", run(scene))

    def test_polarity_only_channel_is_reported(self):
        scene = fixtures.write_scene(self.dir / "s.scn", {1: {"name": "INV", "inv": "ON"}})
        self.assertIn("polarity invert ON", run(scene))

    def test_preamp_from_the_routed_local_block(self):
        scene = fixtures.write_scene(self.dir / "s.scn", {1: {"name": "K", "hp": ("ON", "80")},
                                                          10: {"name": "G", "hp": ("ON", "80")}},
                                     headamps={0: ("+30.0", "ON"), 9: ("+12.5", "OFF")})
        out = run(scene)
        self.assertIn("preamp gain +30.0 dB, phantom ON", out)
        self.assertIn("preamp gain +12.5 dB, phantom OFF", out)

    def test_preamp_follows_the_channel_source_not_the_channel_number(self):
        scene = fixtures.write_scene(self.dir / "s.scn", {1: {"name": "HI HAT", "source": 10, "trim": "+3.0"}},
                                     headamps={0: ("+30.0", "ON"), 9: ("+12.5", "OFF")})
        out = run(scene)
        self.assertIn("(X32 source AN9-16)", out)
        self.assertIn("preamp gain +12.5 dB, phantom OFF", out)

if __name__ == "__main__":
    unittest.main()
