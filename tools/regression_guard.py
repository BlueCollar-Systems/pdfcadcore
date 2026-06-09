#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regression guard for the BlueCollar pdfcadcore PDF import core.

Runs the canonical core's extract_page() over a fixed PDF corpus and records,
per PDF, a stable fingerprint of what was extracted: page count, primitive
counts by type, text-item count, layer count, and overall import bounds. These
are compared against a locked golden baseline so any code change that silently
alters extracted geometry is caught immediately.

The previous regression_guard.py was lost because it lived only in an
unversioned corpus folder. This copy lives inside the versioned core repo
(<core>/tools/) so it cannot disappear again, and the golden baseline is
committed alongside it so every re-lock is visible in git history.

Usage:
    python tools/regression_guard.py --capture         # lock current output as golden
    python tools/regression_guard.py                   # compare vs golden; exit 1 on drift
    python tools/regression_guard.py --include-large   # also test the big stress PDFs
    python tools/regression_guard.py --corpus <dir>    # override corpus location
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

# This file lives in <core>/tools/, so the core package is one level up.
CORE_ROOT = Path(__file__).resolve().parent.parent
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

BASELINE_PATH = Path(__file__).with_name("golden_baselines.json")
DEFAULT_MAX_MB = 8.0


def _default_corpus() -> Path:
    """Resolve the corpus dir, honoring the project's BCS_CORPUS_ROOT convention.

    Matches corpus_paths.py in the importers: prefer $BCS_CORPUS_ROOT (then the
    $PDF_TEST_CORPUS fallback), expecting a 'PDFTest Files' subfolder of PDFs.
    """
    import os

    root = os.environ.get("BCS_CORPUS_ROOT") or os.environ.get("PDF_TEST_CORPUS")
    if root:
        base = Path(root)
        sub = base / "PDFTest Files"
        return sub if sub.is_dir() else base
    return Path(r"C:\1pdf-test-corpus\PDFTest Files")


def _import_core():
    try:
        import fitz  # PyMuPDF
    except Exception as exc:  # pragma: no cover
        print(f"FAIL: PyMuPDF (fitz) not importable: {exc}")
        raise SystemExit(2)
    import pdfcadcore
    from pdfcadcore import extract_page, compute_import_bounds, reset_ids
    return fitz, pdfcadcore, extract_page, compute_import_bounds, reset_ids


def fingerprint_pdf(pdf_path, fitz, extract_page, compute_import_bounds, reset_ids):
    """Extract every page and return a stable, JSON-comparable fingerprint."""
    reset_ids()
    doc = fitz.open(pdf_path)
    try:
        prim_types: dict[str, int] = {}
        text_total = 0
        layers: set[str] = set()
        pages = []
        for i, page in enumerate(doc):
            pd = extract_page(page, i)
            for prim in pd.primitives:
                prim_types[prim.type] = prim_types.get(prim.type, 0) + 1
            text_total += len(pd.text_items)
            layers.update(pd.layers or [])
            pages.append(pd)
        bbox = None
        bounds = compute_import_bounds(pages) if pages else None
        if bounds is not None:
            bbox = [round(v, 1) for v in bounds.as_tuple()]
        return {
            "pages": int(doc.page_count),
            "primitives_total": int(sum(prim_types.values())),
            "primitives_by_type": dict(sorted(prim_types.items())),
            "text_items": int(text_total),
            "layer_count": len(layers),
            "bounds_mm": bbox,
        }
    finally:
        doc.close()


def collect_corpus(corpus: Path, max_mb: float, include_large: bool):
    seen: dict[str, Path] = {}
    for p in corpus.iterdir():
        if p.is_file() and p.suffix.lower() == ".pdf":
            seen.setdefault(p.name.lower(), p)
    out, skipped = [], []
    for p in sorted(seen.values(), key=lambda x: x.name.lower()):
        size_mb = p.stat().st_size / 1e6
        if not include_large and size_mb > max_mb:
            skipped.append((p.name, size_mb))
        else:
            out.append(p)
    return out, skipped


def main() -> int:
    ap = argparse.ArgumentParser(description="pdfcadcore regression guard")
    ap.add_argument("--capture", action="store_true", help="lock current output as golden baseline")
    ap.add_argument("--corpus", default=None,
                    help="directory of test PDFs (default: $BCS_CORPUS_ROOT/PDFTest Files)")
    ap.add_argument("--include-large", action="store_true", help="also test PDFs above --max-mb")
    ap.add_argument("--max-mb", type=float, default=DEFAULT_MAX_MB, help="size cap for the default run")
    ap.add_argument("--traceback", action="store_true", help="print full tracebacks on error")
    args = ap.parse_args()

    fitz, pdfcadcore, extract_page, compute_import_bounds, reset_ids = _import_core()

    corpus = Path(args.corpus) if args.corpus else _default_corpus()
    if not corpus.is_dir():
        print(f"FAIL: corpus dir not found: {corpus}")
        return 2
    pdfs, skipped = collect_corpus(corpus, args.max_mb, args.include_large)
    for name, mb in skipped:
        print(f"  skip ({mb:.0f}MB > {args.max_mb:.0f}MB, use --include-large): {name}")
    if not pdfs:
        print(f"FAIL: no PDFs to test in {corpus}")
        return 2

    print(f"core v{pdfcadcore.__version__} | {len(pdfs)} PDFs | corpus {corpus}")
    results: dict[str, dict] = {}
    errors: list[str] = []
    for p in pdfs:
        t0 = time.time()
        try:
            fp = fingerprint_pdf(p, fitz, extract_page, compute_import_bounds, reset_ids)
            secs = round(time.time() - t0, 2)
            results[p.name] = fp
            print(f"  ok  {p.name}: {fp['primitives_total']} prims "
                  f"{fp['primitives_by_type']}, {fp['text_items']} text, {fp['pages']}p ({secs}s)")
        except Exception as exc:
            errors.append(f"{p.name}: {exc.__class__.__name__}: {exc}")
            print(f"  ERR {p.name}: {exc.__class__.__name__}: {exc}")
            if args.traceback:
                traceback.print_exc()

    if args.capture:
        if errors:
            print(f"\nRefusing to capture: {len(errors)} file(s) errored (fix first).")
            return 1
        payload = {"core_version": pdfcadcore.__version__, "results": results}
        BASELINE_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"\nCaptured golden baseline ({len(results)} PDFs) -> {BASELINE_PATH}")
        return 0

    if not BASELINE_PATH.exists():
        print(f"\nFAIL: no baseline at {BASELINE_PATH}; run with --capture first.")
        return 1
    golden = json.loads(BASELINE_PATH.read_text(encoding="utf-8")).get("results", {})
    drift = []
    for name, fp in results.items():
        g = golden.get(name)
        if g is None:
            print(f"  new  {name} (not in baseline)")
            continue
        if fp != g:
            drift.append(name)
            print(f"  DRIFT {name}:")
            for key in sorted(set(g) | set(fp)):
                if g.get(key) != fp.get(key):
                    print(f"        {key}: golden={g.get(key)} now={fp.get(key)}")
    for n in sorted(set(golden) - set(results)):
        print(f"  gone {n} (in baseline, not tested this run)")

    if errors:
        print(f"\nFAIL: {len(errors)} file(s) errored.")
        return 1
    if drift:
        print(f"\nFAIL: {len(drift)} file(s) drifted from golden baseline.")
        return 1
    print(f"\nPASS: {len(results)} PDFs match golden baseline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
