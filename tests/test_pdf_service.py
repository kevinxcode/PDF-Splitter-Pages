from pathlib import Path

import pytest
from pypdf import PdfReader, PdfWriter

from pdf_splitter.core import SplitPart
from pdf_splitter.pdf_service import (
    PdfPasswordIncorrect,
    PdfPasswordRequired,
    PdfServiceError,
    inspect_pdf,
    split_pdf,
)


def make_pdf(
    path: Path,
    page_sizes: list[tuple[float, float]],
    password: str | None = None,
    encryption_algorithm: str | None = None,
) -> None:
    writer = PdfWriter()
    for width, height in page_sizes:
        writer.add_blank_page(width=width, height=height)
    writer.add_metadata({"/Title": "Dokumen Uji", "/Author": "PDF Splitter"})
    if password is not None:
        writer.encrypt(password, algorithm=encryption_algorithm)
    with path.open("wb") as stream:
        writer.write(stream)


def test_inspect_pdf_reports_file_information(tmp_path: Path) -> None:
    source = tmp_path / "contoh.pdf"
    make_pdf(source, [(595, 842), (612, 792), (420, 595)])

    info = inspect_pdf(source)

    assert info.path == source.resolve()
    assert info.name == "contoh.pdf"
    assert info.page_count == 3
    assert info.file_size == source.stat().st_size
    assert info.encrypted is False


def test_split_pdf_preserves_page_sizes_order_and_metadata(tmp_path: Path) -> None:
    source = tmp_path / "laporan.pdf"
    sizes = [(500, 700), (510, 710), (520, 720)]
    make_pdf(source, sizes)

    result = split_pdf(
        source,
        tmp_path / "hasil",
        [SplitPart(0, 2), SplitPart(2, 3)],
    )

    assert result.output_dir.name == "laporan_split"
    assert [path.name for path in result.files] == [
        "laporan_part_001_pages_1-2.pdf",
        "laporan_part_002_pages_3-3.pdf",
    ]
    readers = [PdfReader(path) for path in result.files]
    assert [len(reader.pages) for reader in readers] == [2, 1]
    actual_sizes = [
        (float(page.mediabox.width), float(page.mediabox.height))
        for reader in readers
        for page in reader.pages
    ]
    assert actual_sizes == sizes
    assert [reader.metadata.title for reader in readers] == ["Dokumen Uji", "Dokumen Uji"]


def test_split_pdf_reports_progress_for_every_completed_part(tmp_path: Path) -> None:
    source = tmp_path / "progress.pdf"
    make_pdf(source, [(100, 100)] * 3)
    updates: list[tuple[int, int]] = []

    split_pdf(
        source,
        tmp_path / "hasil",
        [SplitPart(0, 1), SplitPart(1, 3)],
        progress=lambda completed, total: updates.append((completed, total)),
    )

    assert updates == [(1, 2), (2, 2)]


def test_repeated_split_uses_a_new_output_directory(tmp_path: Path) -> None:
    source = tmp_path / "duplikat.pdf"
    make_pdf(source, [(100, 100)])
    parts = [SplitPart(0, 1)]

    first = split_pdf(source, tmp_path / "hasil", parts)
    second = split_pdf(source, tmp_path / "hasil", parts)

    assert first.output_dir.name == "duplikat_split"
    assert second.output_dir.name == "duplikat_split_2"
    assert first.files[0].exists()
    assert second.files[0].exists()


def test_encrypted_pdf_requires_the_correct_password(tmp_path: Path) -> None:
    source = tmp_path / "rahasia.pdf"
    make_pdf(source, [(100, 100), (100, 100)], password="benar")

    with pytest.raises(PdfPasswordRequired):
        inspect_pdf(source)
    with pytest.raises(PdfPasswordIncorrect):
        inspect_pdf(source, "salah")

    info = inspect_pdf(source, "benar")
    result = split_pdf(source, tmp_path / "hasil", [SplitPart(0, 2)], password="benar")

    assert info.page_count == 2
    assert info.encrypted is True
    assert len(PdfReader(result.files[0]).pages) == 2


def test_owner_encrypted_pdf_with_empty_open_password_needs_no_prompt(tmp_path: Path) -> None:
    source = tmp_path / "akses-otomatis.pdf"
    make_pdf(source, [(100, 100), (100, 100)], password="")

    info = inspect_pdf(source)
    result = split_pdf(source, tmp_path / "hasil", [SplitPart(0, 2)])

    assert info.page_count == 2
    assert info.encrypted is True
    assert len(PdfReader(result.files[0]).pages) == 2


def test_aes_256_encrypted_pdf_can_be_inspected_and_split(tmp_path: Path) -> None:
    source = tmp_path / "aes-modern.pdf"
    make_pdf(source, [(100, 100)], password="aman", encryption_algorithm="AES-256")

    info = inspect_pdf(source, "aman")
    result = split_pdf(source, tmp_path / "hasil", [SplitPart(0, 1)], password="aman")

    assert info.encrypted is True
    assert len(PdfReader(result.files[0]).pages) == 1


def test_out_of_bounds_plan_leaves_no_partial_output(tmp_path: Path) -> None:
    source = tmp_path / "pendek.pdf"
    destination = tmp_path / "hasil"
    make_pdf(source, [(100, 100), (100, 100)])

    with pytest.raises(PdfServiceError, match="rentang"):
        split_pdf(source, destination, [SplitPart(0, 3)])

    assert not destination.exists() or list(destination.iterdir()) == []


def test_non_pdf_input_has_a_friendly_error(tmp_path: Path) -> None:
    source = tmp_path / "bukan.pdf"
    source.write_text("ini bukan pdf", encoding="utf-8")

    with pytest.raises(PdfServiceError, match="tidak dapat dibaca"):
        inspect_pdf(source)

