# Smart Split UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Smart splitting the default and present an understandable, polished recommendation for any PDF size.

**Architecture:** Add a deterministic recommendation model to the tested core/presenter boundary, then consume it from a redesigned Tkinter settings card. Keep PDF writing unchanged and derive all preview/output behavior from the selected plan.

**Tech Stack:** Python 3.11+, Tkinter/ttk, pypdf, pytest, PyInstaller

**Spec:** `docs/superpowers/specs/2026-10-23-pdf-splitter-design.md`

## Global Constraints

- Preserve PDF page objects without rasterization or recompression.
- Smart is the default, but every existing manual mode remains available.
- Recommendation output must be deterministic and understandable.
- The 75,587-page, 807,905,228-byte sample must recommend 76 balanced files.

## Review Focus

- Very small PDFs must not create empty files.
- Image-heavy PDFs must respect the 50 MB estimate before the page-count target.
- Zero/invalid file sizes must still produce a page-based recommendation.
- Manual modes must retain their existing calculations.
- A large recommendation preview must remain navigable and clearly summarized.

---

### Task 1: Smart recommendation model

**Files:**
- Modify: `pdf_splitter/core.py`
- Modify: `tests/test_split_plan.py`

**Interfaces:**
- Produces: `SmartRecommendation` and `recommend_smart_split(total_pages, total_bytes)`.

- [ ] Write failing tests for the real sample, small documents, image-heavy documents, invalid sizes, and exact coverage.
- [ ] Run focused tests and confirm failure because the API is missing.
- [ ] Implement the tiered page target, 50 MB estimated-size cap, balanced file count, percentage, and estimated size.
- [ ] Run focused tests and the full suite.

### Task 2: Presentation model and UI redesign

**Files:**
- Modify: `pdf_splitter/presenter.py`
- Modify: `tests/test_presenter.py`
- Modify: `pdf_splitter/app.py`

**Interfaces:**
- Consumes: `SmartRecommendation` from Task 1.
- Produces: Smart plan mapping, recommendation copy, estimated-size preview rows, and tabbed mode selection.

- [ ] Write failing presenter tests for Smart mode, recommendation copy, and row size estimates.
- [ ] Run focused tests and confirm the new behavior is absent.
- [ ] Implement presenter behavior and make Smart the default.
- [ ] Replace radio layout with clear Smart/manual tabs, recommendation card, improved preview columns, and dynamic generate button text.
- [ ] Run focused tests, compile checks, and the full suite.

### Task 3: Documentation, build, and executable verification

**Files:**
- Modify: `README.md`
- Modify: `.superpowers/sdd/2026-10-23-pdf-splitter/progress.md`
- Rebuild: `dist/PDFSplitter.exe`

**Interfaces:**
- Consumes: the completed Smart UI.
- Produces: updated portable executable and user documentation.

- [ ] Document Smart thresholds and the sample recommendation.
- [ ] Run all tests and rebuild the one-file executable.
- [ ] Smoke-launch the final executable and verify one titled window remains responsive.
- [ ] Reinspect the real sample and confirm the recommendation is 76 files with complete page coverage.

