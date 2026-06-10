# -*- coding: utf-8 -*-
"""Re-lock review gate in tools/regression_guard.py (board Q-09-d).

The gate must: allow identical re-captures, demand --confirm for any change,
and abort when a primitive type drops to zero corpus-wide unless
--allow-type-removal is passed.
"""
from __future__ import annotations

import argparse
import importlib.util
import unittest
from pathlib import Path

_TOOLS = Path(__file__).resolve().parents[1] / "tools"
_spec = importlib.util.spec_from_file_location(
    "regression_guard", _TOOLS / "regression_guard.py"
)
rg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rg)


def _args(confirm=False, allow_type_removal=False):
    return argparse.Namespace(confirm=confirm, allow_type_removal=allow_type_removal)


def _fp(by_type):
    return {
        "pages": 1,
        "primitives_total": sum(by_type.values()),
        "primitives_by_type": dict(by_type),
        "text_items": 0,
        "layer_count": 0,
        "bounds_mm": None,
    }


OLD = {
    "a.pdf": _fp({"polyline": 700, "arc": 99, "circle": 18}),
    "b.pdf": _fp({"polyline": 50, "arc": 5}),
}


class TestTypeTotals(unittest.TestCase):
    def test_sums_across_files(self):
        totals = rg._type_totals(OLD)
        self.assertEqual(totals, {"polyline": 750, "arc": 104, "circle": 18})


class TestCaptureGate(unittest.TestCase):
    def test_identical_passes_without_confirm(self):
        self.assertEqual(rg._capture_gate(OLD, dict(OLD), _args()), 0)

    def test_changed_counts_require_confirm(self):
        new = dict(OLD)
        new["a.pdf"] = _fp({"polyline": 690, "arc": 105, "circle": 18})
        self.assertEqual(rg._capture_gate(OLD, new, _args(confirm=False)), 1)
        self.assertEqual(rg._capture_gate(OLD, new, _args(confirm=True)), 0)

    def test_type_going_dark_aborts_even_with_confirm(self):
        new = {
            "a.pdf": _fp({"polyline": 800}),
            "b.pdf": _fp({"polyline": 55}),
        }  # arc + circle now zero corpus-wide
        self.assertEqual(rg._capture_gate(OLD, new, _args(confirm=True)), 1)

    def test_type_removal_flag_unlocks(self):
        new = {
            "a.pdf": _fp({"polyline": 800}),
            "b.pdf": _fp({"polyline": 55}),
        }
        self.assertEqual(
            rg._capture_gate(OLD, new, _args(confirm=True, allow_type_removal=True)), 0
        )
        # ...but --allow-type-removal alone still needs --confirm.
        self.assertEqual(
            rg._capture_gate(OLD, new, _args(confirm=False, allow_type_removal=True)), 1
        )

    def test_file_set_changes_are_gated_too(self):
        new = dict(OLD)
        new["c.pdf"] = _fp({"polyline": 10})
        self.assertEqual(rg._capture_gate(OLD, new, _args(confirm=False)), 1)
        self.assertEqual(rg._capture_gate(OLD, new, _args(confirm=True)), 0)


if __name__ == "__main__":
    unittest.main()
