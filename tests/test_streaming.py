from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

try:
    import pymupdf as fitz
except ImportError:
    import fitz

from pdfcadcore import iter_pages, reset_ids


class TestStreaming(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="pdfcadcore_stream_test_")
        self.pdf_path = Path(self._tmp.name) / "three_pages.pdf"
        self._build_pdf(self.pdf_path)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _build_pdf(self, out_path: Path) -> None:
        doc = fitz.open()
        # Page 1: one line. Page 2: two lines. Page 3: three lines.
        for page_idx in range(3):
            page = doc.new_page(width=200, height=200)
            for i in range(page_idx + 1):
                y = 20 + 30 * i
                page.draw_line((10, y), (190, y), color=(0, 0, 0), width=1)
        doc.save(str(out_path))
        doc.close()

    def test_streams_all_pages_in_order(self) -> None:
        reset_ids()
        results = list(iter_pages(str(self.pdf_path)))

        self.assertEqual([n for n, _ in results], [1, 2, 3])
        for expected_lines, (_, page_data) in enumerate(results, start=1):
            self.assertEqual(len(page_data.primitives), expected_lines)

    def test_page_selection_skips_out_of_range(self) -> None:
        reset_ids()
        results = list(iter_pages(str(self.pdf_path), pages=[2, 99]))

        self.assertEqual(len(results), 1)
        page_number, page_data = results[0]
        self.assertEqual(page_number, 2)
        self.assertEqual(len(page_data.primitives), 2)

    def test_progress_callback_reports_and_cancels(self) -> None:
        reset_ids()
        snapshots = []

        def on_progress(p):
            snapshots.append(p)
            return p.page_index < 2  # cancel after the second page

        results = list(iter_pages(str(self.pdf_path), progress=on_progress))

        self.assertEqual(len(results), 2)  # third page never extracted
        self.assertEqual(len(snapshots), 2)
        first = snapshots[0]
        self.assertEqual(first.page_number, 1)
        self.assertEqual(first.page_index, 1)
        self.assertEqual(first.total_pages, 3)
        self.assertEqual(first.primitive_count, 1)
        self.assertGreaterEqual(first.elapsed_s, 0.0)
        self.assertFalse(first.over_budget)

    def test_accepts_open_document_and_leaves_it_open(self) -> None:
        reset_ids()
        doc = fitz.open(str(self.pdf_path))
        try:
            results = list(iter_pages(doc, pages=[3]))
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0][0], 3)
            # Document must still be usable afterwards.
            self.assertEqual(doc.page_count, 3)
        finally:
            doc.close()

    def test_matches_batch_extraction_output(self) -> None:
        from pdfcadcore import extract_page

        reset_ids()
        streamed = [pd for _, pd in iter_pages(str(self.pdf_path))]

        reset_ids()
        doc = fitz.open(str(self.pdf_path))
        try:
            batch = [
                extract_page(doc.load_page(i), page_num=i + 1)
                for i in range(doc.page_count)
            ]
        finally:
            doc.close()

        for s_page, b_page in zip(streamed, batch, strict=True):
            s_types = sorted(p.type for p in s_page.primitives)
            b_types = sorted(p.type for p in b_page.primitives)
            self.assertEqual(s_types, b_types)
            self.assertEqual(len(s_page.text_items), len(b_page.text_items))


if __name__ == "__main__":
    unittest.main(verbosity=2)
