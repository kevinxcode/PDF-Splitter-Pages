# PDF Splitter Portable Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a polished Windows desktop app that previews and splits PDFs by file count, pages per file, or percentage without rasterizing pages.

**Architecture:** Keep deterministic split calculations and PDF I/O in a small testable core module. A Tkinter UI owns selection, validation messages, live preview, background execution, and progress. PyInstaller packaging is isolated in a build script and spec file.

**Tech Stack:** Python 3.11+, Tkinter/ttk, pypdf, pytest, PyInstaller

**Spec:** `docs/superpowers/specs/2026-10-23-pdf-splitter-design.md`

## Global Constraints

- Windows desktop app distributable as one portable `.exe`.
- Copy page objects without rendering, resizing, or recompressing them.
- Keep output atomic and never overwrite an existing result folder.
- Use Indonesian UI copy and accessible keyboard-friendly controls.

## Review Focus

- A requested file count larger than the page count must be rejected.
- Uneven splits must cover every page exactly once.
- Percentage rounding must never create empty or missing ranges.
- Wrong passwords and corrupt/non-PDF files must produce friendly errors.
- A write failure must not leave a partial final output folder.

---

### Task 1: Split planning core

**Files:**
- Create: `tests/test_split_plan.py`
- Create: `pdf_splitter/core.py`
- Create: `pdf_splitter/__init__.py`

**Interfaces:**
- Produces: `SplitPart`, `plan_by_file_count(total_pages, file_count)`, `plan_by_pages_per_file(total_pages, pages_per_file)`, and `plan_by_percentage(total_pages, percentage)`.

- [ ] Write failing tests for exact, uneven, single-page, invalid, and percentage-rounded partitions.
- [ ] Run `pytest tests/test_split_plan.py -v` and confirm failure because the core does not exist.
- [ ] Implement the planning types and functions with 0-based half-open page ranges.
- [ ] Run the focused tests and then the full suite.

### Task 2: PDF inspection and lossless split service

**Files:**
- Create: `tests/test_pdf_service.py`
- Create: `pdf_splitter/pdf_service.py`

**Interfaces:**
- Consumes: `SplitPart` from Task 1.
- Produces: `PdfInfo`, `inspect_pdf(path, password=None)`, and `split_pdf(source, destination_root, parts, password=None, progress=None)`.

- [ ] Write failing integration tests using real generated PDFs for inspection, page preservation, metadata, unique output directories, encrypted input, and atomic cleanup.
- [ ] Run the focused tests and confirm the service is missing.
- [ ] Implement direct page-object copying with `pypdf.PdfReader`/`PdfWriter`, metadata copying, password validation, temporary output, and atomic finalization.
- [ ] Run the focused tests and then the full suite.

### Task 3: Windows desktop interface

**Files:**
- Create: `tests/test_presenter.py`
- Create: `pdf_splitter/presenter.py`
- Create: `pdf_splitter/app.py`
- Create: `main.pyw`

**Interfaces:**
- Consumes: planning and service APIs from Tasks 1-2.
- Produces: preview row formatting and `PdfSplitterApp` desktop entry point.

- [ ] Write failing tests for mode-to-plan mapping and Indonesian preview rows.
- [ ] Run focused tests and confirm presenter functions are missing.
- [ ] Implement the presenter functions.
- [ ] Build the Tkinter UI with file/output pickers, PDF summary, three modes, percentage slider, live preview, password field, progress bar, and background worker.
- [ ] Run focused tests and then the full suite.

### Task 4: Packaging and user documentation

**Files:**
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `PDFSplitter.spec`
- Create: `build.ps1`
- Create: `README.md`

**Interfaces:**
- Consumes: `main.pyw` application entry point.
- Produces: reproducible `dist/PDFSplitter.exe` build and Indonesian usage instructions.

- [ ] Pin runtime/dev dependencies and create a one-command PyInstaller build.
- [ ] Document source execution, portable build, splitting semantics, quality guarantees, and limitations.
- [ ] Run tests, build the executable, and smoke-launch it.
- [ ] Verify a sample split by reopening every result and checking page counts and media boxes.

