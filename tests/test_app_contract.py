from pathlib import Path
import tkinter as tk

import pytest

from pdf_splitter.app import PdfSplitterApp
from pdf_splitter.pdf_service import PdfInfo


@pytest.fixture(scope="module")
def app() -> PdfSplitterApp:
    root = tk.Tk()
    root.withdraw()
    instance = PdfSplitterApp(root)
    yield instance
    root.destroy()


def sample_info(page_count: int = 75_587) -> PdfInfo:
    return PdfInfo(
        path=Path("contoh.pdf"),
        name="contoh.pdf",
        page_count=page_count,
        file_size=807_905_228,
        encrypted=False,
    )


def test_smart_control_starts_from_recommendation_and_drives_final_preview(
    app: PdfSplitterApp,
) -> None:
    app._finish_inspection(0, sample_info())

    assert app.smart_file_count_var.get() == "76"
    assert len(app.parts) == 76
    assert "Hasil akhir: 76 file PDF" in app.final_summary_var.get()

    app.smart_file_count_var.set("80")

    assert len(app.parts) == 80
    assert "Hasil akhir: 80 file PDF" in app.final_summary_var.get()
    assert "944–945 halaman/file" in app.final_summary_var.get()
    assert app.split_button.cget("text") == "GENERATE 80 FILE PDF"
    assert "Disesuaikan dari rekomendasi 76 file" in app.recommendation_title_var.get()


def test_reset_smart_recommendation_restores_original_count(app: PdfSplitterApp) -> None:
    app._finish_inspection(0, sample_info())
    app.smart_file_count_var.set("80")

    app.reset_smart_recommendation()

    assert app.smart_file_count_var.get() == "76"
    assert len(app.parts) == 76
    assert app.recommendation_title_var.get() == "76 file direkomendasikan"


def test_temporarily_empty_smart_input_disables_generate_without_crashing(
    app: PdfSplitterApp,
) -> None:
    app._finish_inspection(0, sample_info())

    app.smart_file_count_var.set("")

    assert app.parts == []
    assert app.split_button.instate(["disabled"])
    assert app.final_summary_var.get() == "Hasil akhir belum tersedia"


def test_zero_smart_input_is_rejected_instead_of_silently_using_recommendation(
    app: PdfSplitterApp,
) -> None:
    app._finish_inspection(0, sample_info())

    app.smart_file_count_var.set("0")

    assert app.parts == []
    assert app.split_button.instate(["disabled"])
    assert "minimal 1" in app.preview_summary_var.get()


def test_smart_adjust_buttons_stay_within_page_count(app: PdfSplitterApp) -> None:
    app._finish_inspection(0, sample_info(page_count=2))

    app.adjust_smart_file_count(10)
    assert app.smart_file_count_var.get() == "2"

    app.adjust_smart_file_count(-10)
    assert app.smart_file_count_var.get() == "1"
