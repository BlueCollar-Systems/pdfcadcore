# pdfcadcore — canonical shared PDF→geometry core

**BlueCollar Systems — BUILT. NOT BOUGHT.**

Single source of truth for the host-neutral PDF vector-extraction core used by
the BlueCollar PDF importers. Each Python importer embeds a synced copy of the
`pdfcadcore/` package; the SketchUp importer is a separate Ruby port mirroring
the same behavior.

## Topology — who copies from whom

| Role | Path |
|---|---|
| **Canonical** (edit here) | `C:\1pdfcadcore\pdfcadcore` |
| Embedded — FreeCAD | `C:\1FC-PDFimporter\PDFVectorImporter\pdfcadcore` |
| Embedded — Blender | `C:\1BL-PDFimporter\pdf_vector_importer\pdfcadcore` |
| Embedded — LibreCAD | `C:\1LC-PDFimporter\pdfcadcore` |
| SketchUp (separate Ruby port) | `C:\1SU-PDFimporter\extracted\sketchup_ext\bc_pdf_vector_importer` |

**Allowed divergence:** `BL/primitive_extractor.py` only (extra OCR
normalization). Every other `pdfcadcore/*.py` must be content-identical across
the four copies.

> Note: FC also carries a parallel `PDFVectorImporter/src/PDF*.py` set and LC a
> `librecad_pdf_importer/core/PDF*.py` set. These are **not** covered by the sync
> checker today — keep them aligned manually or treat as a known follow-up.

## Verify before you ship

```bat
:: 1. Are the 4 copies in content-sync? (line-ending agnostic)
python "C:\1pdf-test-corpus\scripts\pdfcadcore_sync_check.py"

:: 2. Did extraction geometry change? (Tier-1 regression gate)
python tools\regression_guard.py                  :: compare vs golden baseline
python tools\regression_guard.py --include-large  :: also the >8MB stress PDFs (timed)
python tools\regression_guard.py --capture        :: re-lock after an INTENDED change
```

The guard honors `BCS_CORPUS_ROOT` (default corpus
`C:\1pdf-test-corpus\PDFTest Files`). Baseline `tools/golden_baselines.json`
captured against core v1.0.0 / PyMuPDF 1.26.7 — 24 PDFs, all green.
**Never accept a count change that was not the stated goal.**

## Line endings

`.gitattributes` normalizes the tree to **LF**, and the sync checker compares
content (CRLF/LF agnostic) so a Windows CRLF checkout of identical code does not
read as drift (this previously caused a false 9-file "mismatch").

## Definition of done (any change)

Measurably better on accuracy / power / performance / compatibility, **no
regressions** (sync check + regression guard green), compatibility preserved or
widened — proven on the real corpus.
