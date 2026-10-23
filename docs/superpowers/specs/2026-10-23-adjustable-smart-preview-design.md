# Adjustable Smart Preview Design

## Intent

Smart tetap memberikan jumlah file awal yang aman, tetapi pengguna dapat menyesuaikannya langsung tanpa berpindah tab. Sebelum Generate, pengguna harus dapat melihat hasil akhir pembagian secara ringkas dan detail.

## Goals

- Isi kontrol jumlah file Smart dengan rekomendasi saat PDF selesai dibaca.
- Izinkan input langsung serta tombol kurang/tambah.
- Sediakan Reset Rekomendasi setelah nilai diubah.
- Perbarui rencana, tabel, estimasi ukuran, dan tombol Generate secara langsung.
- Tampilkan ringkasan hasil akhir: jumlah file, rentang halaman per file, dan estimasi ukuran per file.

## Non-goals

- Mengubah algoritma rekomendasi atau proses penulisan PDF.
- Menghapus mode manual yang sudah tersedia.

## Approach

Dipilih: kontrol jumlah file diletakkan langsung di kartu Smart. Alternatif memindahkan pengguna ke tab Jumlah File ditolak karena menambah langkah dan memisahkan rekomendasi dari penyesuaiannya. Kartu tetap ringkas: label rekomendasi, kontrol jumlah, tombol reset, metrik dinamis, dan alasan rekomendasi.

## Behavior

Nilai awal berasal dari algoritma Smart. Selama pengguna tidak mengubah nilai, tampilan menandainya sebagai rekomendasi. Setelah diubah, tampilan menjelaskan bahwa hasil telah disesuaikan dari nilai awal. Nilai harus antara 1 dan jumlah halaman. Ringkasan final dan tabel selalu berasal dari rencana pembagian aktual yang akan digunakan oleh Generate.
