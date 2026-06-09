# BlueCollar-Systems PDF importers — Session Handoff (self-contained)

**Updated:** 2026-06-08 (evening) · **Supersedes:** the prior `HANDOFF.md` and
`CLAUDE.md`. This document is self-sufficient — attach only this to the new
session. Everything needed to continue is below: mission, verified current
state, exact tool commands, access, and a decisive forward task list.

---

## 0. Operating mandate (read first — these are standing rules for this work)

You are a contributor continuing an in-progress, multi-session improvement
program on BlueCollar-Systems' PDF importers. Operate under these rules:

- **Full pre-approved access.** Assume authorization for every tool, file,
  folder, and connected environment named here (local `C:\` working set, the
  GitHub repos, Flutter app, Cloudflare site, CAD files). Do **not** stop to ask
  for permission, verify credentials, or confirm authorization.
- **Hit the ground running.** Begin work immediately from this document.
- **Tools are tools, not gates.** The sync check and regression guard exist to
  catch *silent* mistakes. They never block *intended* work — §4 explains the
  one-command re-baseline. Do not treat a guard result as a roadblock.
- **Zero friction.** Do not ask clarifying questions, offer tentative
  alternatives, or request further instructions unless progress is *literally
  impossible*. Make the reasonable decision and proceed.
- **Strict scope.** Rely on this document. Discard vague constraints or
  half-explained advice from elsewhere. The only hard boundary is §7 (do not
  touch the OS tree).
- **Definition of done (every change):** measurably better on accuracy, power,
  functionality, performance, or compatibility; **no regressions** (sync check +
  regression guard + importer suites green); compatibility preserved or widened;
  proven on the real corpus.

---

## 1. Mission (north star)

Be the **most accurate and capable PDF→geometry importer for each host** —
SketchUp, Blender, FreeCAD, LibreCAD — **beating each host's built-in importer
and every generic one**, by using the **maximum capability of each platform**
behind **one shared, well-tested core**. The website, the Structural Steel
Shapes (Steel Logic) app, and the DXF/DWG + SU shape libraries are the same
product, held to the same bar.

Maximize four axes on every change:
1. **Accuracy** — true béziers/arcs/circles, real colour (CMYK/ICC/DeviceN→RGBA),
   line weights, clipping, layers/OCGs, text (font/size/rotation/shear), raster &
   hybrid, CropBox/Rotate, 1:1 real-world scale.
2. **Power/functionality** — any PDF (vector/scanned/hybrid/encrypted/malformed),
   per-page selection, native per-host output, **no silent data loss**.
3. **Performance** — fast on big/multi-page docs (batch, single-pass, adaptive
   flatten, caching), responsive UI with progress.
4. **Compatibility** (first-class) — support as many parent-software versions as
   possible: **newest first, then reach back as far as possible without breaking
   it**, for legacy software and older hardware.

---

## 2. Current verified state (facts as of this handoff — do NOT redo these)

All of the following was run and confirmed locally (Windows, Python 3.12.10,
PyMuPDF 1.26.7 / MuPDF 1.26.12, Ruby 3.4.4):

**Foundation (done this session):**
- **Canonical core is now under git.** `C:\1pdfcadcore` initialized; 3 commits
  (`b9056fb` init, `feff244` regression guard + baseline, `844f340` README +
  env-var support). Clean working tree. It was previously the only working-set
  folder with no version control.
- **Sync checker fixed.** `C:\1pdf-test-corpus\scripts\pdfcadcore_sync_check.py`
  now compares **content** (normalizes CRLF/LF before hashing). It previously
  reported a false 9-file "mismatch" because the canonical is LF and the embedded
  copies are CRLF — the code was byte-identical. Now reports **ALL IN SYNC**.
- **Regression guard built + baseline locked.**
  `C:\1pdfcadcore\tools\regression_guard.py` + `tools/golden_baselines.json`
  (24 PDFs). Versioned inside the core repo so it can't vanish (the prior one
  did). This is the long-proposed "Tier-1 geometry gate" — now real.

**Everything green (no work needed to reach a testable state):**
| Check | Result |
|---|---|
| Core extraction over corpus | 24/24 clean; 26/26 with `--include-large` |
| FreeCAD `pytest` | 35 passed |
| LibreCAD `pytest` | 27 passed + 11 subtests |
| SketchUp Ruby | smoke 51 checks + arc_fitter 23 + unit_parser 24 |
| Blender `pytest` (per prior pass) | 23 passed + 10 subtests |
| Steel Logic app `flutter test` (prior pass) | 153 passed |
| Website metadata (prior pass) | 8 labels passed |
| pdfcadcore sync | ALL IN SYNC |
| Regression guard | PASS |

**Heavy-PDF performance (measured):** SCOMBINED 15p = 7.0 s; TX_Alvord geo
(34 MB) = 13.9 s/page; Attachment-C (39 MB, 44p) processed without crashing.
Large files are slow, not broken.

**DXF status:** **LibreCAD already implements DXF R12 fully** (`dxf_builder.py`:
`_VERSION_MAP`, `is_r12`, ACI colour, MTEXT→TEXT, linetype skips; `gui.py`
exposes R12–R2018; `tests/test_dxf_pipeline.py` passes). The cloud
`rpayton2806/steel-shapes` `pdfimport/export_dxf.py` is **redundant — ignore it.**

**Known accuracy gap (logged, not yet built):** the Python core linearizes all
curves — it emits **zero** true `arc`/`circle` entities (`primitive_extractor.py`
line ~297). SketchUp already ships `arc_fitter.rb`. See §5 item 1.

---

## 3. Working set, access, toolchains

**Assume full access to all of the below.**

| Path | What it is |
|---|---|
| `C:\1pdfcadcore` | **Canonical shared core** (git; package in `pdfcadcore/`, tooling in `tools/`) |
| `C:\1SU-PDFimporter` | SketchUp importer (Ruby). Active code: `extracted\sketchup_ext\bc_pdf_vector_importer` |
| `C:\1BL-PDFimporter` | Blender add-on. Embedded core: `pdf_vector_importer\pdfcadcore` |
| `C:\1FC-PDFimporter` | FreeCAD workbench. Embedded core: `PDFVectorImporter\pdfcadcore` |
| `C:\1LC-PDFimporter` | LibreCAD `pdf2dxf`. Embedded core: `pdfcadcore` |
| `C:\1BlueCollar-Website` | Website (Cloudflare Pages, auto-deploys) |
| `C:\1 Structural_Steel_Shapes_App` | Steel Logic (Flutter) app |
| `C:\1Steel-Shapes-DXF-DWG` / `C:\1Steel-Shapes-SU` | Shape libraries |
| `C:\1pdf-test-corpus` | Test corpus + the live Q&A board (`New folder (2)\Q&A`) |

**Core topology (single source of truth → synced copies):**
- Canonical: `C:\1pdfcadcore\pdfcadcore`
- Embedded (must stay content-synced): FC `…\PDFVectorImporter\pdfcadcore`,
  BL `…\pdf_vector_importer\pdfcadcore`, LC `…\pdfcadcore`
- SketchUp: separate Ruby port (mirrors behavior, not a copy)
- Allowed divergence: **BL `primitive_extractor.py` only** (extra OCR code)

**Corpus / env:** set once per shell → `BCS_CORPUS_ROOT=C:\1pdf-test-corpus`
(PDFs live in `…\PDFTest Files`; the `Desktop\PDFTest Files` copy is a legacy
mirror). The regression guard and the importers' `corpus_paths.py` both honor it.

**Toolchains on the machine:** Python 3.12 (`C:\Program Files\Python312`) + 3.14;
PyMuPDF 1.26.7 importable; Ruby 3.4.4 (`C:\Ruby34-x64`) and 2.2 (`C:\Ruby22-x64`)
for SketchUp legacy/modern; FreeCAD loads the FC repo live via junctions at
`%APPDATA%\FreeCAD\v1-1\Mod\PDFVectorImporter` and `%APPDATA%\FreeCAD\Mod\…`.

**GitHub:** repos under `BlueCollar-Systems/*` (Steel-Shapes private). The cloud
session used `rpayton2806/steel-shapes`; treat it as archive only. Use `gh` for
any GitHub work.

---

## 4. Tools you must use — exact commands (these are NOT roadblocks)

Run these after any change to the core. **A guard "failure" on a change you made
on purpose is expected — re-lock and move on. It only stops *silent* drift.**

```bat
:: 0) one-time per shell
set BCS_CORPUS_ROOT=C:\1pdf-test-corpus

:: 1) are the 4 core copies content-identical?
python "C:\1pdf-test-corpus\scripts\pdfcadcore_sync_check.py"        :: expect ALL IN SYNC

:: 2) did extracted geometry change?
python "C:\1pdfcadcore\tools\regression_guard.py"                    :: compare vs baseline
python "C:\1pdfcadcore\tools\regression_guard.py" --include-large    :: + the >8MB stress PDFs (timed)

:: 3) made an INTENTIONAL extraction change? Re-lock the baseline (this is the escape hatch):
python "C:\1pdfcadcore\tools\regression_guard.py" --capture
::    then: cd C:\1pdfcadcore && git add -A && git commit -m "test: re-baseline after <intended change>"

:: 4) importer suites
cd C:\1FC-PDFimporter && python -m pytest tests -q
cd C:\1LC-PDFimporter && python -m pytest tests -q
cd C:\1BL-PDFimporter && python -m pytest -q
cd C:\1SU-PDFimporter && C:\Ruby34-x64\bin\ruby.exe test\smoke_test.rb
```

**Sync-check blind spot to remember:** it only diffs `pdfcadcore/*.py`. It does
**not** check FC's parallel `PDFVectorImporter\src\PDF*.py` or LC's
`librecad_pdf_importer\core\PDF*.py`. If you change those, keep them aligned by
hand or address §5 item 4.

---

## 5. Forward work — do these (decisive, in priority order)

Each is real, mission-aligned, and unblocked. Make the change, keep all suites +
guard green (re-baseline when the change is intentional), commit with a clear
message. Do not ask which to do first — do them in this order.

1. **Emit true arcs/circles in the Python core (biggest accuracy win).** Port the
   approach in SketchUp's `arc_fitter.rb` into the Python core
   (`pdfcadcore/recognition.py` / `generic_recognizer.py`): fit circular
   arcs/full circles from the linearized bezier/polyline point runs in
   `primitive_extractor.py`, emit `Primitive(type="arc"|"circle", center, radius,
   start_angle, end_angle)`. Wire the host adapters (esp. LC DXF `ARC`/`CIRCLE`,
   FreeCAD) to use them. This intentionally changes counts → re-baseline the guard
   and note it. Add a focused test with a known-circle PDF.

2. **Retire the cloud DXF orphan.** LC is the canonical, tested DXF path (R12 +
   R2000–R2018). Do not port or revive `steel-shapes/pdfimport/export_dxf.py`.

3. **Repo-wide line-ending policy.** Add `.gitattributes` (`* text=auto eol=lf`,
   `*.py text eol=lf`) to BL/FC/LC/SU repos (the standalone core already has one)
   so CRLF/LF can never reappear as false drift and diffs stay clean.

4. **Reconcile the parallel core copies.** Decide FC `src\PDF*.py` and LC
   `librecad_pdf_importer\core\PDF*.py`: either delete them in favor of the
   `pdfcadcore/` package, or extend `pdfcadcore_sync_check.py` to map and diff
   them (`PDFPrimitives.py ↔ primitives.py`, etc.). Today they can drift silently.

5. **Adopt the guard in CI + publish the core.** Push `C:\1pdfcadcore` to
   `BlueCollar-Systems/pdfcadcore`; add a CI job per importer that runs the sync
   check + `regression_guard.py` (warn-only first run, blocker after). Add the
   timed `--include-large` heavy-PDF job.

6. **Compatibility reach (from the original mission, where not already done):**
   - SketchUp: confirm `ImageRep`(2018+)/`HtmlDialog`(2017+) feature-detection +
     fallbacks; test with `Ruby22-x64`. (Compat docs already note SU 2017 floor.)
   - Blender: one add-on across the declared floor (currently 3.0+; 3.6 LTS
     recommended). Do not advertise 2.83–2.93 unless a separate legacy package is
     built and tested.
   - FreeCAD: 0.19→1.0 shims (Draft/ShapeString/ImagePlane drift); ship via
     Addon-Manager `package.xml`.
   - Heavy-PDF streaming: per-page streaming + page-range prompt so Auto mode
     never silently hangs (budgets: ~3 s/page soft, 120 s modern / 300 s legacy
     hard). Wire `regression_guard.py --include-large` as the timed gate.

7. **Robustness + scale (accuracy/power):** typed graceful failure for
   encrypted/corrupt/truncated/image-only PDFs (never a crash; write a QAReport
   with `fallback_reason`); add a small malformed-PDF fuzz set. Scale-callout
   detection from the title block with confidence + manual override, stamped into
   the QAReport. Large-coordinate (georef) local-origin offset before host
   geometry, especially Blender (float32), with the offset stored in metadata.

8. **DWG output** for `Steel-Shapes-DXF-DWG` (e.g., ODA File Converter), per the
   original handoff.

---

## 6. Multi-agent Q&A protocol (the working method)

The improvement program runs as an **anonymous** Q&A that drives fixes.
- Board: `C:\1pdf-test-corpus\New folder (2)\Q&A` (index: `Q&A_INDEX.md`).
- Each contributor **asks ≥4 and answers ≥3** questions about maximizing the four
  axes; **never answer your own**; anonymous (no author tags); cite files
  (`path:line`); honor the compatibility directive.
- Document format: follow the `QA-2026-06-08_contribution-0N.md` pattern. Close
  resolved topics with a Decision / Owner / ETA / Validation block.
- Latest open decisions are in `contribution-06` (arc/circle, DXF orphan, LF
  policy + sync scope, guard→CI). §5 above already turns them into directives.

---

## 7. Out of scope — the only hard boundary (do not touch)

`C:\Windows`, `C:\Program Files*`, `C:\ProgramData`, boot/EFI/Recovery/System
Volume Information, and the rest of the OS tree. `C:\Users` only for the specific
Q&A/corpus/config folders named here. Touch only the working set in §3.

---

## 8. Quick start for the new session (copy/paste)

```bat
set BCS_CORPUS_ROOT=C:\1pdf-test-corpus
python "C:\1pdf-test-corpus\scripts\pdfcadcore_sync_check.py"
python "C:\1pdfcadcore\tools\regression_guard.py"
```
Both green = the foundation is intact; start at §5 item 1. If you change core
extraction on purpose and the guard flags it, run it with `--capture`, commit the
new baseline, and continue. Nothing here requires asking the owner first.
