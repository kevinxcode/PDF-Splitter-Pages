"""Deterministic page-range planning for PDF splitting."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil


@dataclass(frozen=True, slots=True)
class SplitPart:
    """A zero-based, half-open page range."""

    start: int
    end: int

    def __post_init__(self) -> None:
        if self.start < 0 or self.end <= self.start:
            raise ValueError("Rentang halaman tidak valid.")

    @property
    def page_count(self) -> int:
        return self.end - self.start


@dataclass(frozen=True, slots=True)
class SmartRecommendation:
    """A human-readable recommendation derived from page count and file size."""

    file_count: int
    pages_per_file: int
    percentage_per_file: float
    estimated_bytes_per_file: int
    page_target: int
    limiting_factor: str


def _validate_total_pages(total_pages: int) -> None:
    if total_pages < 1:
        raise ValueError("PDF harus memiliki minimal 1 halaman.")


def plan_by_file_count(total_pages: int, file_count: int) -> list[SplitPart]:
    """Split pages as evenly as possible across exactly ``file_count`` files."""

    _validate_total_pages(total_pages)
    if file_count < 1:
        raise ValueError("Jumlah file minimal 1.")
    if file_count > total_pages:
        raise ValueError("Jumlah file tidak boleh melebihi jumlah halaman.")

    base_size, remainder = divmod(total_pages, file_count)
    parts: list[SplitPart] = []
    start = 0
    for index in range(file_count):
        size = base_size + (1 if index < remainder else 0)
        parts.append(SplitPart(start, start + size))
        start += size
    return parts


def plan_by_pages_per_file(total_pages: int, pages_per_file: int) -> list[SplitPart]:
    """Split pages into fixed-size chunks with a possibly smaller final chunk."""

    _validate_total_pages(total_pages)
    if pages_per_file < 1:
        raise ValueError("Halaman per file minimal 1.")

    return [
        SplitPart(start, min(start + pages_per_file, total_pages))
        for start in range(0, total_pages, pages_per_file)
    ]


def plan_by_percentage(total_pages: int, percentage: int) -> list[SplitPart]:
    """Use a percentage of total pages, rounded up, as each chunk size."""

    _validate_total_pages(total_pages)
    if not 1 <= percentage <= 100:
        raise ValueError("Persentase harus antara 1 dan 100.")
    pages_per_file = ceil(total_pages * percentage / 100)
    return plan_by_pages_per_file(total_pages, pages_per_file)


def _page_target(total_pages: int) -> int:
    if total_pages <= 100:
        return 25
    if total_pages <= 500:
        return 50
    if total_pages <= 2_000:
        return 100
    if total_pages <= 10_000:
        return 500
    return 1_000


def recommend_smart_split(total_pages: int, total_bytes: int) -> SmartRecommendation:
    """Recommend balanced parts capped by page scale and about 50 MiB each."""

    _validate_total_pages(total_pages)
    scale_page_target = _page_target(total_pages)
    page_target = scale_page_target
    limiting_factor = "pages"

    if total_bytes > 0:
        average_page_bytes = total_bytes / total_pages
        pages_for_50_mib = max(1, int((50 * 1024 * 1024) // average_page_bytes))
        if pages_for_50_mib < page_target:
            page_target = pages_for_50_mib
            limiting_factor = "size"

    file_count = ceil(total_pages / page_target)
    if total_pages > 1:
        file_count = max(2, file_count)
    pages_per_file = ceil(total_pages / file_count)
    estimated_bytes = ceil(max(0, total_bytes) / file_count)
    return SmartRecommendation(
        file_count=file_count,
        pages_per_file=pages_per_file,
        percentage_per_file=100 / file_count,
        estimated_bytes_per_file=estimated_bytes,
        page_target=scale_page_target,
        limiting_factor=limiting_factor,
    )

