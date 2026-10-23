# PDF Splitter Portable

Aplikasi desktop Windows untuk membagi satu PDF menjadi beberapa file berdasarkan jumlah file, jumlah halaman per file, atau persentase halaman.

## Fitur

- Membaca dan menampilkan total halaman serta ukuran PDF.
- Empat mode pembagian:
  - **Smart (direkomendasikan)**: menghitung jumlah file awal dari total halaman dan rata-rata ukuran halaman. Jumlah tersebut tetap dapat diubah langsung sebelum Generate.
  - **Jumlah file**: halaman dibagi serata mungkin. PDF 100 halaman menjadi 5 file menghasilkan 20 halaman per file.
  - **Halaman per file**: menentukan ukuran setiap potongan. PDF 100 halaman dengan nilai 25 menghasilkan 4 file.
  - **Persentase per file**: slider menentukan persentase total halaman di setiap potongan. Nilai dibulatkan ke atas.
- Ringkasan hasil akhir memperlihatkan jumlah file, rentang halaman per file, dan estimasi ukuran per file.
- Pratinjau nama file, rentang halaman, jumlah halaman, dan estimasi ukuran setiap hasil sebelum proses.
- PDF dengan password pembuka kosong diproses otomatis; dialog password hanya muncul jika benar-benar diperlukan.
- Proses latar belakang dan indikator progres agar jendela tidak macet.
- Folder hasil baru dibuat otomatis dan hasil lama tidak ditimpa.
- Penulisan aman: folder hasil baru ditampilkan hanya setelah seluruh potongan berhasil dibuat.

## Cara kerja rekomendasi Smart

Smart memilih batas halaman sesuai skala dokumen:

- Hingga 100 halaman: target 25 halaman per file.
- Hingga 500 halaman: target 50 halaman per file.
- Hingga 2.000 halaman: target 100 halaman per file.
- Hingga 10.000 halaman: target 500 halaman per file.
- Lebih dari 10.000 halaman: target 1.000 halaman per file.

Jika estimasi ukuran hasil akan melebihi sekitar 50 MB, jumlah halaman per file diturunkan otomatis. Halaman kemudian diseimbangkan agar semua file hasil memiliki jumlah halaman yang hampir sama.

Untuk contoh 75.587 halaman berukuran sekitar 770,5 MB, Smart merekomendasikan 76 file dengan sekitar 994-995 halaman dan estimasi sekitar 10,1 MB per file. Angka 76 menjadi nilai awal yang dapat diketik ulang atau disesuaikan memakai tombol kurang/tambah. Tombol **Reset rekomendasi** mengembalikannya ke 76.

## Kualitas PDF

Aplikasi memakai `pypdf` untuk menyalin objek halaman langsung ke dokumen baru. Halaman **tidak** diubah menjadi gambar, tidak di-resize, dan tidak dikompres ulang. Resolusi gambar, ukuran halaman, teks vektor, serta anotasi yang melekat pada halaman tetap dibawa oleh objek halaman aslinya.

Pemisahan tetap membuat dokumen PDF baru. Karena itu, tanda tangan digital pada dokumen asal tidak akan berlaku pada hasil split, dan form interaktif yang saling bergantung antarhalaman mungkin tidak berfungsi sama persis.

## Cara memakai versi portable

1. Buka `PDFSplitter.exe`.
2. Klik **Pilih PDF...** dan pilih dokumen.
3. Jika PDF benar-benar terkunci, masukkan password saat diminta.
4. Gunakan rekomendasi Smart, sesuaikan jumlah file bila perlu, atau pilih tab manual.
5. Periksa ringkasan hasil akhir dan tabel pratinjau.
6. Pilih folder keluaran.
7. Klik **GENERATE ... FILE PDF**.

Hasil akan tersimpan dalam folder seperti `NamaDokumen_split`. Jika folder tersebut sudah ada, aplikasi memakai akhiran `_2`, `_3`, dan seterusnya.

## Menjalankan dari source

Persyaratan: Windows dan Python 3.11 atau lebih baru.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\pythonw.exe main.pyw
```

## Membuat file EXE portable

Jalankan dari Command Prompt atau PowerShell di folder proyek:

```powershell
.\build.cmd
```

Script akan memasang dependensi build, menjalankan seluruh tes, lalu menghasilkan:

```text
dist\PDFSplitter.exe
```

File tersebut dapat disalin dan dijalankan di komputer Windows lain tanpa memasang Python. Windows SmartScreen mungkin menampilkan peringatan untuk executable yang belum ditandatangani secara digital; pilih opsi lanjutan hanya bila file berasal dari build yang Anda percaya.

`build.cmd` memakai execution-policy bypass hanya untuk proses build saat itu dan tidak mengubah pengaturan PowerShell komputer.

## Pengujian

```powershell
.venv\Scripts\python.exe -m pytest -q
```

