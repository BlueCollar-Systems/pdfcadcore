# pdfcadcore — Shared Extraction Library

Canonical development tree for the Python extraction core vendored into BL, FC, and LC importers.

## Python runtime

| Context | Python | Notes |
|---------|--------|-------|
| Maintained floor | **3.10+** | PEP 604 unions with `from __future__ import annotations` |
| CI compile matrix | 3.8–3.12 (FC), 3.10–3.12 (BL/LC) | Catches accidental syntax regressions |
| PyMuPDF pin | `>=1.24,<2.0` | Use `fitz_loader.import_fitz()` — skips namespace-only stubs |

## Sync enforcement

Embedded copies in importer repos must match `pdfcadcore_sync_manifest.json` (maintained in FC, copied to BL/LC):

```bash
python scripts/pdfcadcore_sync_check.py --repo-root C:\1FC-PDFimporter
python scripts/pdfcadcore_sync_check.py --write-manifest   # after intentional core edits (FC only)
```

SketchUp uses a Ruby port — it cannot share this Python tree but must track the same BCS-ARCH-001 contract.

## Host mapping

| Host | Embed path |
|------|------------|
| FreeCAD | `PDFVectorImporter/pdfcadcore/` |
| Blender | `pdf_vector_importer/pdfcadcore/` |
| LibreCAD | `pdfcadcore/` |

## Status labels

- **Verified**: host-run QA captured in release notes
- **Expected**: syntax/runtime compatible; not yet host-verified
- **Not supported**: outside maintained scope
