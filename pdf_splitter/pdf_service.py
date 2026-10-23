"""PDF inspection and page-copy splitting without rasterization."""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError

from .core import SplitPart

ProgressCallback = Callable[[int, int], None]


class PdfServiceError(Exception):
    """Base error suitable for display to an end user."""


class PdfPasswordRequired(PdfServiceError):
    """Raised when a PDF needs a password."""


class PdfPasswordIncorrect(PdfServiceError):
    """Raised when the supplied PDF password is incorrect."""


@dataclass(frozen=True, slots=True)
class PdfInfo:
    path: Path
    name: str
    page_count: int
    file_size: int
    encrypted: bool


@dataclass(frozen=True, slots=True)
class SplitResult:
    output_dir: Path
    files: tuple[Path, ...]


def _load_reader(path: Path, password: str | None) -> tuple[PdfReader, bool]:
    try:
        reader = PdfReader(path, strict=False)
        encrypted = reader.is_encrypted
        if encrypted:
            candidate = password if password is not None else ""
            if not reader.decrypt(candidate):
                if password is None:
                    raise PdfPasswordRequired(
                        "PDF dilindungi password. Masukkan password untuk melanjutkan."
                    )
                raise PdfPasswordIncorrect("Password PDF salah.")
        # Force page-tree parsing here so corrupt files fail during inspection.
        len(reader.pages)
        return reader, encrypted
    except (PdfPasswordRequired, PdfPasswordIncorrect):
        raise
    except (OSError, PdfReadError, ValueError, TypeError) as exc:
        raise PdfServiceError("File PDF tidak dapat dibaca atau rusak.") from exc


def inspect_pdf(path: str | Path, password: str | None = None) -> PdfInfo:
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise PdfServiceError("File PDF tidak ditemukan.")

    reader, encrypted = _load_reader(source, password)
    page_count = len(reader.pages)
    if page_count < 1:
        raise PdfServiceError("PDF tidak memiliki halaman.")
    return PdfInfo(
        path=source,
        name=source.name,
        page_count=page_count,
        file_size=source.stat().st_size,
        encrypted=encrypted,
    )


def _validate_parts(parts: Sequence[SplitPart], total_pages: int) -> None:
    if not parts:
        raise PdfServiceError("Rencana pembagian kosong.")
    cursor = 0
    for part in parts:
        if part.start != cursor or part.end > total_pages:
            raise PdfServiceError("Rencana rentang halaman tidak valid.")
        cursor = part.end
    if cursor != total_pages:
        raise PdfServiceError("Rencana rentang halaman tidak mencakup seluruh PDF.")


def _next_output_dir(destination_root: Path, stem: str) -> Path:
    candidate = destination_root / f"{stem}_split"
    suffix = 2
    while candidate.exists():
        candidate = destination_root / f"{stem}_split_{suffix}"
        suffix += 1
    return candidate


def _copy_metadata(reader: PdfReader, writer: PdfWriter) -> None:
    if not reader.metadata:
        return
    metadata = {
        str(key): str(value)
        for key, value in reader.metadata.items()
        if key and value is not None
    }
    if metadata:
        writer.add_metadata(metadata)


def split_pdf(
    source: str | Path,
    destination_root: str | Path,
    parts: Sequence[SplitPart],
    password: str | None = None,
    progress: ProgressCallback | None = None,
) -> SplitResult:
    """Copy page objects into new PDFs and atomically publish the result folder."""

    source_path = Path(source).expanduser().resolve()
    if not source_path.is_file():
        raise PdfServiceError("File PDF tidak ditemukan.")
    reader, _ = _load_reader(source_path, password)
    _validate_parts(parts, len(reader.pages))

    root = Path(destination_root).expanduser().resolve()
    try:
        root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise PdfServiceError("Folder keluaran tidak dapat dibuat.") from exc

    final_dir = _next_output_dir(root, source_path.stem)
    temp_dir = Path(tempfile.mkdtemp(prefix=f".{source_path.stem}_split_", dir=root))
    filenames: list[str] = []
    try:
        total = len(parts)
        for index, part in enumerate(parts, start=1):
            filename = (
                f"{source_path.stem}_part_{index:03d}_"
                f"pages_{part.start + 1}-{part.end}.pdf"
            )
            writer = PdfWriter()
            for page_index in range(part.start, part.end):
                writer.add_page(reader.pages[page_index])
            _copy_metadata(reader, writer)
            with (temp_dir / filename).open("wb") as stream:
                writer.write(stream)
            filenames.append(filename)
            if progress:
                progress(index, total)

        temp_dir.replace(final_dir)
    except PdfServiceError:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    except Exception as exc:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise PdfServiceError("Proses pemisahan PDF gagal. Tidak ada hasil parsial yang disimpan.") from exc

    return SplitResult(
        output_dir=final_dir,
        files=tuple(final_dir / filename for filename in filenames),
    )

