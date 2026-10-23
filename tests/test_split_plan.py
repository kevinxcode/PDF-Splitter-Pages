import pytest

from pdf_splitter.core import (
    SplitPart,
    plan_by_file_count,
    plan_by_pages_per_file,
    plan_by_percentage,
    recommend_smart_split,
)


def ranges(parts: list[SplitPart]) -> list[tuple[int, int]]:
    return [(part.start, part.end) for part in parts]


def test_file_count_divides_exactly_without_missing_pages() -> None:
    assert ranges(plan_by_file_count(100, 5)) == [
        (0, 20),
        (20, 40),
        (40, 60),
        (60, 80),
        (80, 100),
    ]


def test_file_count_distributes_remainder_to_earliest_files() -> None:
    assert ranges(plan_by_file_count(10, 3)) == [(0, 4), (4, 7), (7, 10)]


def test_pages_per_file_keeps_a_smaller_final_part() -> None:
    assert ranges(plan_by_pages_per_file(10, 4)) == [(0, 4), (4, 8), (8, 10)]


def test_percentage_rounds_chunk_size_up() -> None:
    assert ranges(plan_by_percentage(10, 33)) == [(0, 4), (4, 8), (8, 10)]


def test_all_modes_support_a_single_page() -> None:
    expected = [(0, 1)]
    assert ranges(plan_by_file_count(1, 1)) == expected
    assert ranges(plan_by_pages_per_file(1, 50)) == expected
    assert ranges(plan_by_percentage(1, 1)) == expected


@pytest.mark.parametrize(
    ("function", "args"),
    [
        (plan_by_file_count, (0, 1)),
        (plan_by_file_count, (2, 0)),
        (plan_by_file_count, (2, 3)),
        (plan_by_pages_per_file, (2, 0)),
        (plan_by_percentage, (2, 0)),
        (plan_by_percentage, (2, 101)),
    ],
)
def test_invalid_split_values_are_rejected(function, args) -> None:
    with pytest.raises(ValueError):
        function(*args)


def test_smart_recommendation_matches_the_real_large_sample() -> None:
    recommendation = recommend_smart_split(75_587, 807_905_228)

    assert recommendation.file_count == 76
    assert recommendation.pages_per_file == 995
    assert recommendation.percentage_per_file == pytest.approx(100 / 76)
    assert recommendation.estimated_bytes_per_file == 10_630_332
    assert recommendation.limiting_factor == "pages"
    parts = plan_by_file_count(75_587, recommendation.file_count)
    assert parts[0] == SplitPart(0, 995)
    assert parts[-1] == SplitPart(74_593, 75_587)


@pytest.mark.parametrize(
    ("total_pages", "expected_files", "expected_pages"),
    [(1, 1, 1), (10, 2, 5), (100, 4, 25), (500, 10, 50), (2_000, 20, 100)],
)
def test_smart_recommendation_scales_with_document_page_count(
    total_pages: int, expected_files: int, expected_pages: int
) -> None:
    recommendation = recommend_smart_split(total_pages, 0)

    assert recommendation.file_count == expected_files
    assert recommendation.pages_per_file == expected_pages
    assert recommendation.limiting_factor == "pages"


def test_smart_recommendation_uses_size_limit_for_image_heavy_pdf() -> None:
    recommendation = recommend_smart_split(1_000, 1024 * 1024 * 1024)

    assert recommendation.file_count == 21
    assert recommendation.pages_per_file == 48
    assert recommendation.estimated_bytes_per_file <= 50 * 1024 * 1024
    assert recommendation.limiting_factor == "size"


def test_smart_recommendation_rejects_invalid_page_count() -> None:
    with pytest.raises(ValueError):
        recommend_smart_split(0, 100)

