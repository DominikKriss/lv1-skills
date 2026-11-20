import unittest

import fixtures
import build_dm7 as b

IC = "InputChannel"


class Allocate(unittest.TestCase):
    def test_stereo_pairs_start_odd(self):
        chans, nxt = b.allocate([{"name": "A", "group": "x"}, {"name": "B LR", "group": "x", "stereo": True},
                                 {"name": "C", "group": "x"}])
        self.assertEqual([c.get("name", "spare") for c in chans], ["A", "spare", "B LR", "B LR", "C"])
        self.assertEqual([c["ch"] for c in chans], [1, 2, 3, 4, 5])
        self.assertEqual(nxt, 6)

    def test_labels(self):
        self.assertEqual(b.label({"name": "KEYS LR", "half": "L"}, {}), "KEYS L")
        self.assertEqual(b.label({"name": "JULIA VOX"}, {"JULIA VOX": "JULIAVOX"}), "JULIAVOX")
        with self.assertRaises(b.Refuse):
            b.label({"name": "TOO LONG NAME"}, {})

    def test_comp_ratio(self):
        self.assertEqual(b.comp_ratio("2.5"), 25)
        self.assertEqual(b.comp_ratio("100"), 255)


class X32(unittest.TestCase):
    def setUp(self):
        self.s = fixtures.FakeSession()
        self.notes = []
        b.x32_processing(self.s, 0, fixtures.x32_channel(), self.notes, "CH 1")
        self.v = self.s.values

    def test_filters_polarity_order(self):
        self.assertEqual(self.v[(IC + "/Input", "Phase", (0, 0))], 1)
        self.assertEqual(self.v[(IC + "/HPF", "Frequency", (0, 0))], 400)
        self.assertEqual(self.v[(IC + "/HPF", "Slope", (0, 0))], 24)
        self.assertEqual(self.v[(IC + "/Proc", "EQDynOrder", (0, 0))], 1)
        self.assertEqual(self.v[(IC + "/LPF", "Frequency", (0, 0))], 120000)

    def test_gate_and_comp_words(self):
        gate = [self.v[(IC + "/Dynamics/Bank/Parameter", "Value", (0, 0, 0, j))] for j in range(5)]
        self.assertEqual(gate, [-2500, 1, -6000, 31700, 63000])
        comp = [self.v[(IC + "/Dynamics/Bank/Parameter", "Value", (0, 1, 0, j))] for j in range(6)]
        self.assertEqual(comp, [-2700, 5, 52000, 255, 2, 450])
        self.assertEqual(self.v[(IC + "/Dynamics/Bank", "Type", (0, 1, 0))], "PM Comp")
        self.assertEqual(self.v[(IC + "/Dynamics/Bank", "MixBalance", (0, 1, 0))], 80)
        self.assertEqual(self.v[(IC + "/Dynamics/KeyIn", "FilterType", (0, 0, 0))], "HPF")
        self.assertEqual(self.v[(IC + "/Dynamics/KeyIn", "FilterType", (0, 1, 0))], "NONE")
        self.assertEqual(len(self.notes), 1)

    def test_eq_shelf_last_bells_in_frequency_order(self):
        f = {k: self.v.get((IC + "/PEQ/Bank/Band", "Frequency", (0, 0, 0, k))) for k in range(4)}
        self.assertEqual(f, {0: 3000, 1: 20000, 2: None, 3: 80000})
        self.assertEqual(self.v[(IC + "/PEQ/Bank/Band", "Gain", (0, 0, 0, 2))], 0)
        self.assertEqual(self.v[(IC + "/PEQ/Bank/HighShelving", "On", (0, 0, 0, 0))], 1)
        self.assertEqual(self.v[(IC + "/PEQ/Bank/LowShelving", "On", (0, 0, 0, 0))], 0)

    def test_too_many_shelves_refused(self):
        ch = fixtures.x32_channel()
        ch["eq/1"] = ["HShv", "5k00", "+1.00", "1.0"]
        with self.assertRaises(b.Refuse):
            b.x32_processing(fixtures.FakeSession(), 0, ch, [], "CH 1")


class EqOff(unittest.TestCase):
    def test_lpf_off_when_x32_eq_off(self):
        ch = fixtures.x32_channel()
        ch["eq"] = ["OFF"]
        s = fixtures.FakeSession()
        b.x32_processing(s, 0, ch, [], "CH 1")
        self.assertEqual(s.values[(IC + "/LPF", "On", (0, 0))], 0)


if __name__ == "__main__":
    unittest.main()
