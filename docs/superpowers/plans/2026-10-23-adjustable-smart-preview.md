# Adjustable Smart Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Smart recommendation editable while showing the exact final split summary before generation.

**Architecture:** Add pure presenter helpers for an adjusted Smart plan and its dynamic summary, then bind one editable file-count control in the Smart card to those helpers. The existing split service remains unchanged and receives the currently previewed plan.

**Tech Stack:** Python 3, Tkinter/ttk, pytest, PyInstaller

**Spec:** `docs/superpowers/specs/2026-10-23-adjustable-smart-preview-design.md`

## Global Constraints

- Smart must initialize from the existing deterministic recommendation.
- Adjustment must never permit fewer than 1 or more files than total pages.
- Preview and Generate must use the same `SplitPart` list.
- PDF page content must not be rendered or recompressed.

## Review Focus

- Invalid or temporarily empty typed input disables Generate without crashing.
- A value greater than the page count is rejected clearly.
- Reset restores the original recommendation after adjustment.
- One-page PDFs remain valid with exactly one output.
- Final summary reports the true minimum/maximum pages and estimated size of the actual plan.

---

### Task 1: Adjustable Smart presentation model

**Files:**
- Modify: `pdf_splitter/presenter.py`
- Modify: `tests/test_presenter.py`

**Interfaces:**
- Consumes: `recommend_smart_split(total_pages, total_bytes)` and `plan_by_file_count(total_pages, file_count)`
- Produces: `build_plan("smart", total_pages, adjusted_count, total_bytes)` and `final_split_summary(parts, total_bytes, total_pages)`

- [x] Write failing tests proving Smart uses a positive adjusted count, falls back to recommendation for zero, rejects counts beyond pages, and formats exact final split ranges.
- [x] Run the focused tests and verify they fail for the missing behavior.
- [x] Implement the minimal presenter behavior and summary helper.
- [x] Run focused and full tests.

### Task 2: Editable Smart card

**Files:**
- Modify: `pdf_splitter/app.py`
- Modify: `tests/test_app_contract.py`

**Interfaces:**
- Consumes: Task 1 presenter helpers.
- Produces: editable `smart_file_count_var`, reset action, dynamic Smart copy, and `final_summary_var`.

- [x] Write failing UI contract tests for the Smart count control, reset action, final summary binding, and adjusted Smart plan value.
- [x] Run focused tests and verify the expected failures.
- [x] Add the editable control, minus/plus actions, reset button, and dynamic final summary.
- [x] Ensure inspection initializes the control exactly once from the recommendation and user edits refresh the same preview used by Generate.
- [x] Run focused and full tests.

### Task 3: Portable build and verification

**Files:**
- Modify: `README.md`
- Build: `dist/PDFSplitter.exe`

- [x] Document adjustable Smart behavior.
- [x] Run the full test suite.
- [x] Build the portable executable.
- [x] Smoke-test application startup and inspect the Smart widgets at runtime.
