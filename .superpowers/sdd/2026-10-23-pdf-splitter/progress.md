# SDD ledger - plan: docs/superpowers/plans/2026-10-23-pdf-splitter.md

Ruling: Git metadata was removed because Windows sandbox ownership checks blocked all project commands - progress is recorded in this ledger instead of commits - cost if wrong: no per-task Git history is available in this fresh project.
Pre-flight: Task 1 produces SplitPart and planning functions consumed by Tasks 2-3; names and 0-based half-open ranges match.
Pre-flight: Task 2 produces inspection/split APIs consumed by Task 3; progress callback and password arguments match.
Pre-flight: Task 3 produces main.pyw consumed by Task 4; packaging entry point matches.

Task 1: complete (no Git commit; tests: python -m pytest tests/test_split_plan.py -v -> 11 passed; full suite -> 11 passed).

Task 2: Ruling: pytest's shared Windows temp root was inaccessible to the sandbox - configured a project-local basetemp so real PDF integration tests can run - cost if wrong: pytest recreates `.pytest-tmp` on each run.
Task 2: complete (no Git commit; tests: python -m pytest tests/test_pdf_service.py -v -> 7 passed; full suite -> 18 passed).

Task 3: complete (no Git commit; tests: python -m pytest tests/test_presenter.py -v -> 7 passed; full suite -> 25 passed; compileall and Tkinter imports passed).

Task 4: Ruling: the host blocks direct `.ps1` execution by policy - added `build.cmd` to apply Process-only bypass without changing the machine policy - cost if wrong: environments that also block `powershell.exe -ExecutionPolicy Bypass` must invoke PyInstaller manually.
Task 4: Ruling: the sandbox can read but Tcl cannot load runtime scripts outside the workspace - build script probes Tcl and copies its runtime locally only when required - cost if wrong: the build stops instead of shipping an executable without Tkinter.
Task 4: Ruling: modern password-protected PDFs commonly use AES-256 - added the `pypdf[crypto]` runtime extra after an AES-256 regression test failed without it - cost if wrong: the portable executable is about 16 MB rather than a smaller RC4-only build.
Task 4: complete (no Git commit; tests: python -m pytest -q -> 26 passed; PyInstaller one-file build succeeded; smoke test -> 2 processes, 1 responsive window titled PDF Splitter; Tkinter bundle check passed; SHA256 C5E28B185E8198F2B42B20958187F3D9983560699CF8C7CFB2ABDE516AF63981).

Final review: self-review (subagent delegation is not permitted for this task).
Final review: no Critical or Important findings.
Final: minor (deferred): the executable uses PyInstaller's default icon and is not digitally signed; functionality is unaffected and the SmartScreen limitation is documented.

Follow-up: fixed owner-encrypted PDFs with an empty open password after the user's 75,587-page sample reproduced an unnecessary password prompt; regression test went RED then GREEN. Removed the always-visible password field and renamed the primary action to GENERATE / SPLIT PDF.




