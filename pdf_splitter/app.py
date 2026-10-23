"""Tkinter desktop interface for PDF Splitter."""

from __future__ import annotations

import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from .core import SplitPart, recommend_smart_split
from .pdf_service import (
    PdfInfo,
    PdfPasswordIncorrect,
    PdfPasswordRequired,
    PdfServiceError,
    SplitResult,
    inspect_pdf,
    split_pdf,
)
from .presenter import (
    build_plan,
    final_split_summary,
    format_file_size,
    preview_rows,
    smart_recommendation_copy,
)


class PdfSplitterApp:
    """Main application window."""

    BG = "#f4f6f8"
    SURFACE = "#ffffff"
    TEXT = "#17202a"
    MUTED = "#5f6b76"
    PRIMARY = "#1666d3"
    PRIMARY_DARK = "#0f52ad"
    SUCCESS = "#16845b"
    BORDER = "#d8dee6"

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.info: PdfInfo | None = None
        self.parts: list[SplitPart] = []
        self._inspection_token = 0
        self._busy = False

        self.source_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.mode_var = tk.StringVar(value="smart")
        self.smart_file_count_var = tk.StringVar()
        self.file_count_var = tk.StringVar(value="5")
        self.pages_per_file_var = tk.StringVar(value="25")
        self.percentage_var = tk.IntVar(value=25)
        self.percentage_text_var = tk.StringVar(value="25%")
        self.summary_var = tk.StringVar(value="Belum ada PDF dipilih")
        self.preview_summary_var = tk.StringVar(value="Pilih PDF untuk melihat pratinjau")
        self.status_var = tk.StringVar(value="Siap")
        self.recommendation_title_var = tk.StringVar(value="Pilih PDF untuk mendapatkan rekomendasi")
        self.recommendation_metrics_var = tk.StringVar(value="Jumlah file, halaman, persentase, dan ukuran akan dihitung otomatis.")
        self.recommendation_reason_var = tk.StringVar(value="Smart mempertimbangkan skala dokumen dan estimasi ukuran hasil.")
        self.final_summary_var = tk.StringVar(value="Hasil akhir belum tersedia")
        self._recommended_file_count = 0

        self._configure_window()
        self._configure_styles()
        self._build_ui()
        self._bind_events()

    def _configure_window(self) -> None:
        self.root.title("PDF Splitter")
        self.root.geometry("1000x760")
        self.root.minsize(860, 650)
        self.root.configure(background=self.BG)

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("App.TFrame", background=self.BG)
        style.configure("Surface.TFrame", background=self.SURFACE)
        style.configure("Header.TLabel", background=self.BG, foreground=self.TEXT, font=("Segoe UI Semibold", 22))
        style.configure("Subtitle.TLabel", background=self.BG, foreground=self.MUTED, font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background=self.SURFACE, foreground=self.TEXT, font=("Segoe UI Semibold", 11))
        style.configure("Body.TLabel", background=self.SURFACE, foreground=self.TEXT)
        style.configure("Muted.TLabel", background=self.SURFACE, foreground=self.MUTED)
        style.configure("Quality.TLabel", background="#e8f6f0", foreground=self.SUCCESS, font=("Segoe UI Semibold", 9), padding=(10, 6))
        style.configure("Recommend.TFrame", background="#eaf2fd")
        style.configure("RecommendTag.TLabel", background="#eaf2fd", foreground=self.PRIMARY, font=("Segoe UI Semibold", 9))
        style.configure("RecommendTitle.TLabel", background="#eaf2fd", foreground=self.TEXT, font=("Segoe UI Semibold", 16))
        style.configure("RecommendBody.TLabel", background="#eaf2fd", foreground=self.TEXT, font=("Segoe UI Semibold", 10))
        style.configure("RecommendMuted.TLabel", background="#eaf2fd", foreground=self.MUTED, font=("Segoe UI", 9))
        style.configure("FinalSummary.TLabel", background=self.SURFACE, foreground=self.PRIMARY, font=("Segoe UI Semibold", 10))
        style.configure("Primary.TButton", font=("Segoe UI Semibold", 10), padding=(18, 9))
        style.configure("Secondary.TButton", padding=(12, 7))
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI Semibold", 9))

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, style="App.TFrame", padding=(24, 18, 24, 18))
        outer.grid(row=0, column=0, sticky="nsew")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(3, weight=1)

        header = ttk.Frame(outer, style="App.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="PDF Splitter", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Bagi dokumen PDF dengan cepat, aman, dan tanpa menurunkan kualitas halaman.",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))
        header_actions = ttk.Frame(header, style="App.TFrame")
        header_actions.grid(row=0, column=1, rowspan=2, sticky="e")
        ttk.Label(header_actions, text="KUALITAS ASLI DIPERTAHANKAN", style="Quality.TLabel").grid(row=0, column=0, sticky="e", pady=(0, 7))
        self.split_button = ttk.Button(
            header_actions,
            text="GENERATE PDF",
            command=self.start_split,
            style="Primary.TButton",
            state="disabled",
        )
        self.split_button.grid(row=1, column=0, sticky="ew")

        source_card = self._card(outer, 1)
        source_card.columnconfigure(1, weight=1)
        ttk.Label(source_card, text="1. Pilih dokumen", style="CardTitle.TLabel").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))
        ttk.Label(source_card, text="File PDF", style="Body.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 10))
        ttk.Entry(source_card, textvariable=self.source_var, state="readonly").grid(row=1, column=1, sticky="ew")
        ttk.Button(source_card, text="Pilih PDF...", command=self.choose_pdf, style="Secondary.TButton").grid(row=1, column=2, padx=(10, 0))
        ttk.Label(source_card, textvariable=self.summary_var, style="Muted.TLabel").grid(row=2, column=0, columnspan=3, sticky="w", pady=(10, 0))

        settings_card = self._card(outer, 2)
        settings_card.columnconfigure(0, weight=1)
        ttk.Label(settings_card, text="2. Pilih cara pembagian", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.mode_notebook = ttk.Notebook(settings_card)
        self.mode_notebook.grid(row=1, column=0, sticky="ew")
        self.mode_tabs = ("smart", "files", "pages", "percentage")

        smart_tab = ttk.Frame(self.mode_notebook, padding=(12, 12))
        files_tab = ttk.Frame(self.mode_notebook, padding=(12, 12))
        pages_tab = ttk.Frame(self.mode_notebook, padding=(12, 12))
        percentage_tab = ttk.Frame(self.mode_notebook, padding=(12, 12))
        self.mode_notebook.add(smart_tab, text="  Smart  ")
        self.mode_notebook.add(files_tab, text="  Jumlah File  ")
        self.mode_notebook.add(pages_tab, text="  Halaman / File  ")
        self.mode_notebook.add(percentage_tab, text="  Persentase  ")

        recommendation = ttk.Frame(smart_tab, style="Recommend.TFrame", padding=(16, 12))
        recommendation.grid(row=0, column=0, sticky="ew")
        smart_tab.columnconfigure(0, weight=1)
        recommendation.columnconfigure(0, weight=1)
        ttk.Label(recommendation, text="REKOMENDASI SMART", style="RecommendTag.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(recommendation, textvariable=self.recommendation_title_var, style="RecommendTitle.TLabel").grid(row=1, column=0, sticky="w", pady=(3, 2))
        smart_controls = ttk.Frame(recommendation, style="Recommend.TFrame")
        smart_controls.grid(row=2, column=0, sticky="w", pady=(6, 5))
        ttk.Label(smart_controls, text="Jumlah file hasil", style="RecommendBody.TLabel").grid(row=0, column=0, padx=(0, 8))
        ttk.Button(smart_controls, text="−", width=3, command=lambda: self.adjust_smart_file_count(-1)).grid(row=0, column=1)
        self.smart_file_count_spin = ttk.Spinbox(
            smart_controls,
            from_=1,
            to=999999,
            textvariable=self.smart_file_count_var,
            width=9,
            justify="center",
            command=self.refresh_preview,
        )
        self.smart_file_count_spin.grid(row=0, column=2, padx=5)
        ttk.Button(smart_controls, text="+", width=3, command=lambda: self.adjust_smart_file_count(1)).grid(row=0, column=3)
        ttk.Button(smart_controls, text="Reset rekomendasi", command=self.reset_smart_recommendation).grid(row=0, column=4, padx=(10, 0))
        ttk.Label(recommendation, textvariable=self.recommendation_metrics_var, style="RecommendBody.TLabel").grid(row=3, column=0, sticky="w")
        ttk.Label(recommendation, textvariable=self.recommendation_reason_var, style="RecommendMuted.TLabel").grid(row=4, column=0, sticky="w", pady=(4, 0))

        files_tab.columnconfigure(1, weight=1)
        ttk.Label(files_tab, text="Jumlah file hasil", style="Body.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 12))
        self.file_count_spin = ttk.Spinbox(files_tab, from_=1, to=9999, textvariable=self.file_count_var, width=12, command=self.refresh_preview)
        self.file_count_spin.grid(row=0, column=1, sticky="w")
        ttk.Label(files_tab, text="Halaman akan dibagi serata ke jumlah file yang Anda tentukan.", style="Muted.TLabel").grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))

        pages_tab.columnconfigure(1, weight=1)
        ttk.Label(pages_tab, text="Maksimal halaman per file", style="Body.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 12))
        self.pages_spin = ttk.Spinbox(pages_tab, from_=1, to=999999, textvariable=self.pages_per_file_var, width=12, command=self.refresh_preview)
        self.pages_spin.grid(row=0, column=1, sticky="w")
        ttk.Label(pages_tab, text="File terakhir dapat berisi lebih sedikit halaman.", style="Muted.TLabel").grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))

        percentage_tab.columnconfigure(1, weight=1)
        ttk.Label(percentage_tab, text="Persentase halaman per file", style="Body.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 12))
        self.percentage_scale = ttk.Scale(percentage_tab, from_=1, to=100, variable=self.percentage_var, command=self._on_percentage_change)
        self.percentage_scale.grid(row=0, column=1, sticky="ew")
        ttk.Label(percentage_tab, textvariable=self.percentage_text_var, width=6).grid(row=0, column=2, sticky="e", padx=(10, 0))
        ttk.Label(percentage_tab, text="Contoh: 10% menghasilkan sekitar 10 file.", style="Muted.TLabel").grid(row=1, column=0, columnspan=3, sticky="w", pady=(8, 0))
        ttk.Label(settings_card, textvariable=self.final_summary_var, style="FinalSummary.TLabel").grid(row=2, column=0, sticky="w", pady=(10, 0))

        preview_card = self._card(outer, 3, sticky="nsew")
        preview_card.rowconfigure(1, weight=1)
        preview_card.columnconfigure(0, weight=1)
        preview_header = ttk.Frame(preview_card, style="Surface.TFrame")
        preview_header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        preview_header.columnconfigure(1, weight=1)
        ttk.Label(preview_header, text="3. Pratinjau hasil", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(preview_header, textvariable=self.preview_summary_var, style="Muted.TLabel").grid(row=0, column=1, sticky="e")

        table_frame = ttk.Frame(preview_card, style="Surface.TFrame")
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        self.preview_tree = ttk.Treeview(table_frame, columns=("number", "range", "count", "size", "name"), show="headings", height=7)
        self.preview_tree.heading("number", text="#")
        self.preview_tree.heading("range", text="Halaman")
        self.preview_tree.heading("count", text="Jumlah")
        self.preview_tree.heading("size", text="Estimasi ukuran")
        self.preview_tree.heading("name", text="Nama file")
        self.preview_tree.column("number", width=48, anchor="center", stretch=False)
        self.preview_tree.column("range", width=110, anchor="center", stretch=False)
        self.preview_tree.column("count", width=90, anchor="center", stretch=False)
        self.preview_tree.column("size", width=125, anchor="center", stretch=False)
        self.preview_tree.column("name", width=470, anchor="w")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.preview_tree.yview)
        self.preview_tree.configure(yscrollcommand=scrollbar.set)
        self.preview_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        footer = ttk.Frame(outer, style="App.TFrame")
        footer.grid(row=4, column=0, sticky="ew", pady=(14, 0))
        footer.columnconfigure(1, weight=1)
        ttk.Label(footer, text="Folder hasil", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Entry(footer, textvariable=self.output_var, state="readonly").grid(row=0, column=1, sticky="ew")
        ttk.Button(footer, text="Pilih Folder...", command=self.choose_output, style="Secondary.TButton").grid(row=0, column=2, padx=(8, 0))
        self.progress = ttk.Progressbar(footer, mode="determinate")
        self.progress.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(12, 0))
        ttk.Label(footer, textvariable=self.status_var, style="Subtitle.TLabel").grid(row=2, column=0, columnspan=3, sticky="w", pady=(7, 0))

    def _card(self, parent: ttk.Frame, row: int, sticky: str = "ew") -> ttk.Frame:
        frame = ttk.Frame(parent, style="Surface.TFrame", padding=(16, 14))
        frame.grid(row=row, column=0, sticky=sticky, pady=(0, 12))
        return frame

    def _bind_events(self) -> None:
        self.root.bind("<Control-o>", lambda _event: self.choose_pdf())
        self.root.bind("<Control-Return>", lambda _event: self.start_split())
        self.mode_notebook.bind("<<NotebookTabChanged>>", self._on_mode_tab_changed)
        self.smart_file_count_var.trace_add("write", lambda *_args: self.refresh_preview())
        self.file_count_var.trace_add("write", lambda *_args: self.refresh_preview())
        self.pages_per_file_var.trace_add("write", lambda *_args: self.refresh_preview())

    def _on_mode_tab_changed(self, _event: tk.Event | None = None) -> None:
        selected = self.mode_notebook.index(self.mode_notebook.select())
        self.mode_var.set(self.mode_tabs[selected])
        self.refresh_preview()

    def choose_pdf(self) -> None:
        path = filedialog.askopenfilename(
            title="Pilih file PDF",
            filetypes=(("PDF files", "*.pdf"), ("Semua file", "*.*")),
        )
        if not path:
            return
        self.source_var.set(path)
        self.password_var.set("")
        self.output_var.set(str(Path(path).parent / "PDF Splitter Output"))
        self.inspect_selected()

    def choose_output(self) -> None:
        initial = self.output_var.get() or str(Path.home())
        path = filedialog.askdirectory(title="Pilih folder keluaran", initialdir=initial)
        if path:
            self.output_var.set(path)

    def inspect_selected(self) -> None:
        source = self.source_var.get()
        if not source:
            messagebox.showinfo("Pilih PDF", "Pilih file PDF terlebih dahulu.", parent=self.root)
            return
        self._inspection_token += 1
        token = self._inspection_token
        password = self.password_var.get() or None
        self.info = None
        self.parts = []
        self.split_button.configure(state="disabled")
        self.status_var.set("Membaca informasi PDF...")
        self.summary_var.set("Memeriksa dokumen...")
        threading.Thread(target=self._inspect_worker, args=(token, Path(source), password), daemon=True).start()

    def _inspect_worker(self, token: int, source: Path, password: str | None) -> None:
        try:
            info = inspect_pdf(source, password)
        except Exception as exc:
            self.root.after(0, self._finish_inspection_error, token, exc)
        else:
            self.root.after(0, self._finish_inspection, token, info)

    def _finish_inspection(self, token: int, info: PdfInfo) -> None:
        if token != self._inspection_token:
            return
        self.info = info
        encrypted_text = " • Dibuka dengan password" if info.encrypted and self.password_var.get() else ""
        self.summary_var.set(
            f"{info.page_count:,} halaman • {format_file_size(info.file_size)}{encrypted_text}"
        )
        smart_copy = smart_recommendation_copy(info.page_count, info.file_size)
        recommendation = recommend_smart_split(info.page_count, info.file_size)
        self._recommended_file_count = recommendation.file_count
        self.recommendation_title_var.set(smart_copy.title)
        self.recommendation_metrics_var.set(smart_copy.metrics)
        self.recommendation_reason_var.set(smart_copy.reason)
        self.smart_file_count_var.set(str(recommendation.file_count))
        self.status_var.set("PDF siap dibagi")
        self.refresh_preview()

    def _finish_inspection_error(self, token: int, error: Exception) -> None:
        if token != self._inspection_token:
            return
        self.summary_var.set("Dokumen belum dapat dibaca")
        self.status_var.set("Periksa file atau password")
        if isinstance(error, (PdfPasswordRequired, PdfPasswordIncorrect)):
            prompt = "Masukkan password PDF:" if isinstance(error, PdfPasswordRequired) else "Password salah. Coba lagi:"
            password = simpledialog.askstring("PDF Terenkripsi", prompt, show="*", parent=self.root)
            if password is not None:
                self.password_var.set(password)
                self.inspect_selected()
            return
        messagebox.showerror("Gagal membaca PDF", str(error), parent=self.root)

    def _on_percentage_change(self, _value: str | None = None) -> None:
        value = max(1, min(100, round(self.percentage_var.get())))
        self.percentage_text_var.set(f"{value}%")
        self.refresh_preview()

    def adjust_smart_file_count(self, delta: int) -> None:
        if not self.info:
            return
        try:
            current = int(self.smart_file_count_var.get())
        except (TypeError, ValueError, tk.TclError):
            current = self._recommended_file_count or 1
        adjusted = max(1, min(self.info.page_count, current + delta))
        self.smart_file_count_var.set(str(adjusted))

    def reset_smart_recommendation(self) -> None:
        if self._recommended_file_count:
            self.smart_file_count_var.set(str(self._recommended_file_count))

    def _selected_value(self) -> int:
        mode = self.mode_var.get()
        raw_value: str | int
        if mode == "smart":
            raw_value = self.smart_file_count_var.get()
        elif mode == "files":
            raw_value = self.file_count_var.get()
        elif mode == "pages":
            raw_value = self.pages_per_file_var.get()
        else:
            raw_value = round(self.percentage_var.get())
        try:
            value = int(raw_value)
        except (TypeError, ValueError, tk.TclError) as exc:
            raise ValueError("Masukkan angka pembagian yang valid.") from exc
        if mode == "smart" and value < 1:
            raise ValueError("Jumlah file minimal 1.")
        return value

    def refresh_preview(self) -> None:
        mode = self.mode_var.get()
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)

        if not self.info:
            self.preview_summary_var.set("Pilih PDF untuk melihat pratinjau")
            self.final_summary_var.set("Hasil akhir belum tersedia")
            self.split_button.configure(state="disabled")
            return
        try:
            self.parts = build_plan(
                mode,
                self.info.page_count,
                self._selected_value(),
                total_bytes=self.info.file_size,
            )
        except ValueError as exc:
            self.parts = []
            self.preview_summary_var.set(str(exc))
            self.final_summary_var.set("Hasil akhir belum tersedia")
            self.split_button.configure(state="disabled")
            return

        self.final_summary_var.set(
            final_split_summary(
                self.parts,
                total_bytes=self.info.file_size,
                total_pages=self.info.page_count,
            )
        )
        if mode == "smart":
            selected_count = len(self.parts)
            smart_copy = smart_recommendation_copy(self.info.page_count, self.info.file_size)
            if selected_count == self._recommended_file_count:
                self.recommendation_title_var.set(smart_copy.title)
                self.recommendation_metrics_var.set(smart_copy.metrics)
                self.recommendation_reason_var.set(smart_copy.reason)
            else:
                self.recommendation_title_var.set(
                    f"Disesuaikan dari rekomendasi {self._recommended_file_count} file"
                )
                self.recommendation_metrics_var.set(f"Nilai awal Smart: {smart_copy.metrics}")
                self.recommendation_reason_var.set(
                    "Pratinjau dan Generate menggunakan jumlah file yang Anda tentukan."
                )

        for row in preview_rows(
            self.info.path.stem,
            self.parts,
            total_bytes=self.info.file_size,
            total_pages=self.info.page_count,
        ):
            self.preview_tree.insert(
                "",
                "end",
                values=(row.number, row.page_range, row.page_count, row.estimated_size, row.filename),
            )
        self.preview_summary_var.set(f"{len(self.parts)} file • {self.info.page_count:,} halaman tercakup")
        self.split_button.configure(text=f"GENERATE {len(self.parts)} FILE PDF")
        self.split_button.configure(state="disabled" if self._busy else "normal")

    def start_split(self) -> None:
        if self._busy or not self.info or not self.parts:
            return
        output = self.output_var.get()
        if not output:
            messagebox.showinfo("Pilih Folder", "Pilih folder keluaran terlebih dahulu.", parent=self.root)
            return

        self._busy = True
        self.split_button.configure(state="disabled")
        self.progress.configure(maximum=len(self.parts), value=0)
        self.status_var.set("Memisahkan PDF...")
        source = self.info.path
        parts = tuple(self.parts)
        password = self.password_var.get() or None
        threading.Thread(
            target=self._split_worker,
            args=(source, Path(output), parts, password),
            daemon=True,
        ).start()

    def _split_worker(
        self,
        source: Path,
        output: Path,
        parts: tuple[SplitPart, ...],
        password: str | None,
    ) -> None:
        try:
            result = split_pdf(
                source,
                output,
                parts,
                password=password,
                progress=lambda completed, total: self.root.after(
                    0, self._update_progress, completed, total
                ),
            )
        except Exception as exc:
            self.root.after(0, self._finish_split_error, exc)
        else:
            self.root.after(0, self._finish_split, result)

    def _update_progress(self, completed: int, total: int) -> None:
        self.progress.configure(maximum=total, value=completed)
        self.status_var.set(f"Menyimpan file {completed} dari {total}...")

    def _finish_split(self, result: SplitResult) -> None:
        self._busy = False
        self.split_button.configure(state="normal")
        self.status_var.set(f"Selesai • {len(result.files)} file dibuat")
        open_folder = messagebox.askyesno(
            "Split PDF Selesai",
            f"Berhasil membuat {len(result.files)} file.\n\nFolder hasil:\n{result.output_dir}\n\nBuka folder sekarang?",
            parent=self.root,
        )
        if open_folder:
            try:
                os.startfile(result.output_dir)  # type: ignore[attr-defined]
            except OSError as exc:
                messagebox.showwarning("Folder tidak dapat dibuka", str(exc), parent=self.root)

    def _finish_split_error(self, error: Exception) -> None:
        self._busy = False
        self.progress.configure(value=0)
        self.status_var.set("Proses gagal")
        self.refresh_preview()
        message = str(error) if isinstance(error, PdfServiceError) else "Terjadi kesalahan yang tidak terduga."
        messagebox.showerror("Gagal memisahkan PDF", message, parent=self.root)


def run() -> None:
    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass
    root = tk.Tk()
    PdfSplitterApp(root)
    root.mainloop()

