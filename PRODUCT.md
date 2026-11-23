# PRODUCT

## Product Truth

- Name: Sistem Informasi Manajemen Kos (sebutan kerja: **SI-Kos**)
- Jenis: aplikasi **desktop** Python (Tkinter + SQLite). Bukan aplikasi web.
- Lingkup: pengelolaan kos skala kecil oleh pengelola sendiri, bukan marketplace atau multi-properti.

## Masalah yang Diselesaikan

Pengelolaan kos kecil masih dicatat di buku atau chat: rawan salah catat, data hilang, pemilik tidak tahu kamar kosong, dan sulit mengetahui penghuni yang menunggak serta total pemasukan per bulan.

## Pengguna

| Role | Deskripsi | Kebutuhan utama |
|---|---|---|
| Pemilik | Pemilik kos, pemegang keputusan dan uang | Melihat pemasukan, siapa menunggak, mengendalikan data kamar/penghuni, mengelola akun operator |
| Penjaga Kos | Orang yang menjalankan operasional harian | Mencatat data kamar/penghuni dan mencatat pembayaran tanpa harus melapor ke pemilik |

Admin tidak lagi berupa peran tunggal tanpa nama: kata "admin" pada dokumen kelompok dipetakan menjadi **Pemilik** dan **Penjaga Kos**.

## Nilai / Hasil yang Diharapkan

1. Pencatatan kamar, penghuni, dan pembayaran tersimpan rapi di satu database.
2. Data bertahan setelah aplikasi ditutup (SQLite di disk, bukan variabel memori).
3. Pemilik bisa melihat kamar kosong, penghuni menunggak, dan total pemasukan bulanan tanpa menghitung manual.
4. Setiap data hanya bisa diakses setelah login, dan hak lihat/ubah dibatasi per role.

## Batas Scope Awal

In scope:
- Login dengan role.
- CRUD kamar, CRUD penghuni, pencarian.
- Catat pembayaran sewa bulanan.
- Daftar penunggak.
- Laporan pemasukan bulanan.

Out of scope (belum diminta, tidak dikerjakan tanpa change request):
- Aplikasi web / multi-perangkat / akses jarak jauh.
- Pembayaran online, integrasi bank atau e-wallet.
- Notifikasi WhatsApp/SMS/email otomatis.
- Multi-properti atau multi-cabang.
- Foto/scan bukti transfer, cetak kuitansi berdesain.
- Aplikasi mobile.

## Konteks Akademik

Dibuat untuk UAS mata kuliah Pemrograman 2, Semester 5, Jurusan Informatika FMIPA USK. Referensi ide dan kebutuhan berasal dari deck kelompok `PEMRO 2.pdf`. Penilaian menekankan fungsi yang berjalan, bukan sekadar tampilan.

## Stack

- Python 3 (verifikasi lokal: 3.14.9 tersedia).
- Tkinter (terverifikasi: Tk 9.0).
- SQLite (terverifikasi: 3.53.1).
- Tanpa dependency eksternal; seluruhnya modul standard library.
