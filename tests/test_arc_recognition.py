from __future__ import annotations

import math
import tempfile
import unittest
from pathlib import Path

try:
    import pymupdf as fitz
except ImportError:
    import fitz

from pdfcadcore import extract_page, reset_ids


class TestArcRecognition(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="pdfcadcore_arc_test_")
        self.pdf_path = Path(self._tmp.name) / "arc_circle.pdf"
        self._build_pdf(self.pdf_path)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _build_pdf(self, out_path: Path) -> None:
        doc = fitz.open()
        page = doc.new_page(width=300, height=300)

        page.draw_circle((120, 120), 40, color=(1, 0, 0), width=1)

        center = (190, 180)
        radius = 45
        arc_pts = []
        for i in range(13):
            angle = math.radians(20 + (120 * i / 12))
            arc_pts.append((
                center[0] + radius * math.cos(angle),
                center[1] + radius * math.sin(angle),
            ))
        page.draw_polyline(arc_pts, color=(0, 0, 1), width=1)

        page.draw_rect(fitz.Rect(20, 20, 80, 60), color=(0, 0, 0), width=1)
        doc.save(str(out_path))
        doc.close()

    def test_extract_page_promotes_true_circle_and_arc(self) -> None:
        doc = fitz.open(self.pdf_path)
        try:
            reset_ids()
            page_data = extract_page(doc[0], page_num=1)
        finally:
            doc.close()

        by_type = {}
        for primitive in page_data.primitives:
            by_type.setdefault(primitive.type, []).append(primitive)

        self.assertEqual(len(by_type.get("circle", [])), 1)
        self.assertEqual(len(by_type.get("arc", [])), 1)
        self.assertEqual(len(by_type.get("closed_loop", [])), 1)

        circle = by_type["circle"][0]
        self.assertIsNotNone(circle.center)
        self.assertIsNotNone(circle.radius)
        self.assertEqual(circle.start_angle, 0.0)
        self.assertEqual(circle.end_angle, 360.0)
        self.assertTrue(circle.closed)
        self.assertGreater(len(circle.points), 8)

        arc = by_type["arc"][0]
        self.assertIsNotNone(arc.center)
        self.assertIsNotNone(arc.radius)
        self.assertIsNotNone(arc.start_angle)
        self.assertIsNotNone(arc.end_angle)
        self.assertFalse(arc.closed)
        self.assertGreater(len(arc.points), 4)

    def test_extract_page_can_leave_linearized_primitives_unpromoted(self) -> None:
        doc = fitz.open(self.pdf_path)
        try:
            reset_ids()
            page_data = extract_page(doc[0], page_num=1, detect_arcs=False)
        finally:
            doc.close()

        prim_types = {primitive.type for primitive in page_data.primitives}
        self.assertNotIn("circle", prim_types)
        self.assertNotIn("arc", prim_types)
        self.assertIn("polyline", prim_types)
        self.assertIn("closed_loop", prim_types)


if __name__ == "__main__":
    unittest.main(verbosity=2)
