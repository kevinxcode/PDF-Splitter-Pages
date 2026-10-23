"""Presentation helpers shared by the Tkinter UI and tests."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Sequence

from .core import (
    SplitPart,
    plan_by_file_count,
    plan_by_pages_per_file,
    plan_by_percentage,
    recommend_smart_split,
)


@dataclass(frozen=True, slots=True)
class PreviewRow:
    number: int
    page_range: str
    page_count: int
    estimated_size: str
    filename: str


@dataclass(frozen=True, slots=True)
class SmartRecommendationCopy:
    title: str
    metrics: str
    reason: str


def build_plan(
    mode: str,
    total_pages: int,
    value: int,
    total_bytes: int = 0,
) -> list[SplitPart]:
    if mode == "smart":
        file_count = value
        if file_count <= 0:
            file_count = recommend_smart_split(total_pages, total_bytes).file_count
        return plan_by_file_count(total_pages, file_count)
    if mode == "files":
        return plan_by_file_count(total_pages, value)
    if mode == "pages":
        return plan_by_pages_per_file(total_pages, value)
    if mode == "percentage":
        return plan_by_percentage(total_pages, value)
    raise ValueError("Mode pembagian tidak dikenal.")


def preview_rows(
    stem: str,
    parts: Sequence[SplitPart],
    total_bytes: int = 0,
    total_pages: int = 0,
) -> list[PreviewRow]:
    return [
        PreviewRow(
            number=index,
            page_range=f"{part.start + 1}-{part.end}",
            page_count=part.page_count,
            estimated_size=(
                format_file_size(ceil(total_bytes * part.page_count / total_pages))
                if total_bytes > 0 and total_pages > 0
                else "-"
            ),
            filename=f"{stem}_part_{index:03d}_pages_{part.start + 1}-{part.end}.pdf",
        )
        for index, part in enumerate(parts, start=1)
    ]


def final_split_summary(
    parts: Sequence[SplitPart],
    total_bytes: int = 0,
    total_pages: int = 0,
) -> str:
    if not parts:
        return "Hasil akhir belum tersedia"

    page_counts = [part.page_count for part in parts]
    page_range = _format_number_range(min(page_counts), max(page_counts))
    size_text = "-"
    if total_bytes > 0 and total_pages > 0:
        size_estimates = [ceil(total_bytes * count / total_pages) for count in page_counts]
        smallest = format_file_size(min(size_estimates))
        largest = format_file_size(max(size_estimates))
        size_text = f"±{smallest}" if smallest == largest else _format_size_range(smallest, largest)

    return (
        f"Hasil akhir: {len(parts)} file PDF • {page_range} halaman/file • "
        f"estimasi {size_text}/file"
    )


def _format_number_range(smallest: int, largest: int) -> str:
    if smallest == largest:
        return f"{smallest:,}"
    return f"{smallest:,}–{largest:,}"


def _format_size_range(smallest: str, largest: str) -> str:
    smallest_value, smallest_unit = smallest.rsplit(" ", 1)
    largest_value, largest_unit = largest.rsplit(" ", 1)
    if smallest_unit == largest_unit:
        return f"{smallest_value}–{largest_value} {smallest_unit}"
    return f"{smallest}–{largest}"


def smart_recommendation_copy(total_pages: int, total_bytes: int) -> SmartRecommendationCopy:
    recommendation = recommend_smart_split(total_pages, total_bytes)
    metrics = (
        f"±{recommendation.pages_per_file:,} halaman/file • "
        f"{recommendation.percentage_per_file:.2f}% • "
        f"estimasi ±{format_file_size(recommendation.estimated_bytes_per_file)}/file"
    )
    if recommendation.limiting_factor == "size":
        reason = "Disesuaikan agar estimasi setiap hasil tetap sekitar 50 MB atau lebih kecil."
    else:
        page_target = f"{recommendation.page_target:,}".replace(",", ".")
        reason = f"Disesuaikan agar setiap hasil tidak melebihi target nyaman {page_target} halaman."
    return SmartRecommendationCopy(
        title=f"{recommendation.file_count} file direkomendasikan",
        metrics=metrics,
        reason=reason,
    )


def format_file_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    if size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    return f"{size / (1024 * 1024 * 1024):.1f} GB"

