# PDF Splitter Portable - Design

## Intent

Membuat aplikasi desktop Windows yang mudah dipakai untuk membaca total halaman sebuah PDF dan membaginya menjadi beberapa PDF tanpa menurunkan kualitas halaman.

## Goals

- Berjalan sebagai aplikasi desktop Windows dan dapat dibangun menjadi satu file `.exe` portable.
- Menampilkan nama file, ukuran, total halaman, dan status enkripsi.
- Menyediakan tiga mode pembagian: jumlah file, halaman per file, dan persentase halaman per potongan.
- Menampilkan pratinjau jumlah file dan rentang halaman sebelum proses dimulai.
- Mempertahankan isi halaman dengan menyalin objek PDF secara langsung, tanpa rasterisasi, resize, atau kompresi ulang.
- Menulis hasil ke folder baru, menampilkan progres, dan tidak meninggalkan hasil setengah jadi bila proses gagal.
- Memberikan rekomendasi Smart sebagai pilihan default berdasarkan total halaman dan estimasi ukuran rata-rata halaman.

## Non-goals

- Mengedit isi halaman, mengubah resolusi gambar, melakukan OCR, atau mengompres PDF.
- Membagi berdasarkan bookmark atau ukuran byte.
- Mengubah PDF bertanda tangan agar tanda tangannya tetap valid; pemisahan halaman secara alami menghasilkan dokumen baru.

## Constraints and Decisions

- UI memakai Tkinter/ttk agar ringan dan minim dependensi.
- Pemrosesan PDF memakai `pypdf`; halaman ditambahkan langsung ke writer sehingga kualitas visual tidak dirender ulang.
- Mode **Jumlah file** membagi halaman serata mungkin. Contoh 100 halaman menjadi 5 file menghasilkan 20 halaman per file.
- Mode **Halaman per file** memakai ukuran potongan tetap. Contoh 100 halaman dengan 25 halaman per file menghasilkan 4 file.
- Mode **Persentase** menentukan ukuran tiap potongan sebagai persentase dari total halaman, dibulatkan ke atas. Contoh 25% dari 100 menghasilkan potongan 25 halaman.
- Mode **Smart** memilih jumlah file seimbang dengan dua batas kenyamanan: target halaman berdasarkan skala dokumen (25/50/100/500/1.000 halaman) dan estimasi maksimum 50 MB per file. Batas yang lebih kecil dipakai.
- Untuk dokumen dua halaman atau lebih, Smart selalu merekomendasikan sedikitnya dua file; satu halaman tetap satu file.
- Kartu rekomendasi menampilkan jumlah file, perkiraan halaman per file, persentase, estimasi ukuran, dan alasan rekomendasi.
- Kontrol manual disusun sebagai tab **Smart**, **Jumlah File**, **Halaman/File**, dan **Persentase**; Smart aktif secara default.
- Nilai yang menghasilkan file kosong ditolak; jumlah file tidak boleh melebihi total halaman.
- PDF dengan password pembuka kosong diproses otomatis. Dialog password hanya muncul bila password benar-benar diperlukan, dan password tidak disimpan.
- Metadata dokumen dasar disalin bila valid. Anotasi dan isi halaman ikut bersama objek halaman; form interaktif lintas halaman dan tanda tangan digital tidak dijamin tetap berfungsi.
- Nama hasil stabil: `<nama>_part_001_pages_1-25.pdf`.

## Approaches Considered

- **Tkinter + PyInstaller (dipilih):** ukuran relatif ringan, komponen UI sudah tersedia bersama Python, dan cocok untuk satu file portable.
- **CustomTkinter + PyInstaller:** lebih modern tetapi menambah dependensi dan ukuran distribusi.
- **PySide6:** UI sangat kaya, tetapi ukuran executable jauh lebih besar untuk kebutuhan sederhana ini.

## User Flow

1. Pengguna memilih satu PDF.
2. Aplikasi membaca informasi PDF dan menampilkan total halaman.
3. Aplikasi langsung memilih rekomendasi Smart; pengguna dapat beralih ke tab manual dan mengubah jumlah file, halaman per file, atau persentase.
4. Tabel pratinjau langsung menampilkan nama file dan rentang halaman.
5. Pengguna memilih folder keluaran dan menekan **Split PDF**.
6. Proses berjalan di thread latar, progres ditampilkan, lalu aplikasi menawarkan membuka folder hasil.

## Error Handling

- File bukan PDF, rusak, tidak dapat dibaca, password salah, dan input pembagian tidak valid ditampilkan sebagai pesan yang mudah dipahami.
- Hasil ditulis ke folder sementara di dalam tujuan dan baru dipindahkan ke folder final setelah semua file berhasil dibuat.
- Folder final tidak ditimpa; nama dengan nomor tambahan digunakan bila sudah ada.

