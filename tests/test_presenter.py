import pytest

from pdf_splitter.presenter import (
    build_plan,
    final_split_summary,
    format_file_size,
    preview_rows,
    smart_recommendation_copy,
)


def test_build_plan_maps_each_ui_mode_to_its_algorithm() -> None:
    assert [(part.start, part.end) for part in build_plan("files", 10, 3)] == [
        (0, 4),
        (4, 7),
        (7, 10),
    ]
    assert [(part.start, part.end) for part in build_plan("pages", 10, 4)] == [
        (0, 4),
        (4, 8),
        (8, 10),
    ]
    assert [(part.start, part.end) for part in build_plan("percentage", 10, 50)] == [
        (0, 5),
        (5, 10),
    ]


def test_build_plan_rejects_an_unknown_ui_mode() -> None:
    with pytest.raises(ValueError, match="Mode"):
        build_plan("unknown", 10, 2)


def test_build_plan_maps_smart_mode_to_balanced_recommendation() -> None:
    parts = build_plan("smart", 75_587, 0, total_bytes=807_905_228)

    assert len(parts) == 76
    assert parts[0].page_count == 995
    assert parts[-1].end == 75_587


def test_build_plan_uses_adjusted_smart_file_count() -> None:
    parts = build_plan("smart", 75_587, 80, total_bytes=807_905_228)

    assert len(parts) == 80
    assert {part.page_count for part in parts} == {944, 945}
    assert parts[-1].end == 75_587


def test_build_plan_rejects_adjusted_smart_count_above_total_pages() -> None:
    with pytest.raises(ValueError, match="melebihi"):
        build_plan("smart", 10, 11, total_bytes=1_000)


def test_preview_rows_use_human_page_numbers_and_stable_names() -> None:
    parts = build_plan("pages", 6, 4)

    rows = preview_rows("Laporan Tahunan", parts)

    assert rows[0].number == 1
    assert rows[0].page_range == "1-4"
    assert rows[0].page_count == 4
    assert rows[0].filename == "Laporan Tahunan_part_001_pages_1-4.pdf"
    assert rows[1].page_range == "5-6"
    assert rows[1].page_count == 2


def test_preview_rows_estimate_each_output_size() -> None:
    parts = build_plan("pages", 10, 4)

    rows = preview_rows("Dokumen", parts, total_bytes=1_000, total_pages=10)

    assert [row.estimated_size for row in rows] == ["400 B", "400 B", "200 B"]


def test_final_split_summary_describes_actual_output_plan() -> None:
    parts = build_plan("smart", 75_587, 80, total_bytes=807_905_228)

    summary = final_split_summary(parts, total_bytes=807_905_228, total_pages=75_587)

    assert summary == "Hasil akhir: 80 file PDF • 944–945 halaman/file • estimasi ±9.6 MB/file"


def test_final_split_summary_shows_size_range_when_visible_after_formatting() -> None:
    parts = build_plan("files", 10, 3)

    summary = final_split_summary(parts, total_bytes=1_000, total_pages=10)

    assert summary == "Hasil akhir: 3 file PDF • 3–4 halaman/file • estimasi 300–400 B/file"


def test_smart_recommendation_copy_explains_the_real_sample() -> None:
    copy = smart_recommendation_copy(75_587, 807_905_228)

    assert copy.title == "76 file direkomendasikan"
    assert "995 halaman/file" in copy.metrics
    assert "1.32%" in copy.metrics
    assert "10.1 MB/file" in copy.metrics
    assert "1.000 halaman" in copy.reason


def test_smart_recommendation_copy_explains_small_document_threshold() -> None:
    copy = smart_recommendation_copy(100, 1_000_000)

    assert copy.title == "4 file direkomendasikan"
    assert "25 halaman" in copy.reason


@pytest.mark.parametrize(
    ("size", "expected"),
    [(0, "0 B"), (999, "999 B"), (1024, "1.0 KB"), (1_572_864, "1.5 MB")],
)
def test_format_file_size_is_easy_to_read(size: int, expected: str) -> None:
    assert format_file_size(size) == expected

