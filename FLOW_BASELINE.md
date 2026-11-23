# FLOW BASELINE

Baseline v0.1 — 23 Nov 2026. Status kebutuhan mengikuti label Starter Pack.

## Product Goal

Aplikasi desktop untuk mencatat kamar, penghuni, dan pembayaran sewa kos bulanan, serta menampilkan penunggak dan rekap pemasukan bulanan kepada Pemilik.

## Actors / Roles

| Aksi | Pemilik | Penjaga Kos |
|---|---|---|
| Login | ya | ya |
| Lihat data kamar & penghuni | ya | ya |
| Tambah/ubah kamar & penghuni | ya | ya |
| Hapus kamar & penghuni | ya | tidak |
| Catat pembayaran sewa | ya | ya |
| Lihat daftar penunggak | ya | ya |
| Laporan pemasukan bulanan | ya | tidak |
| Kelola akun pengguna | ya | tidak |

Status: CONFIRMED (client, 23 Nov 2026).

## Primary Journey

**Jalur A — Pemilik**

```text
Buka aplikasi → Login (Pemilik) → Dashboard ringkas
→ Kelola Kamar (tambah/ubah/hapus/cari)
→ Kelola Penghuni (daftar ke kamar, tanggal masuk, sewa)
→ Catat Pembayaran → Lihat Penunggak → Laporan Pemasukan Bulanan
→ Logout
```

**Jalur B — Penjaga Kos**

```text
Buka aplikasi → Login (Penjaga) → Dashboard ringkas
→ Kelola Penghuni → Catat Pembayaran → Lihat Penunggak
→ (menu Hapus dan Laporan tidak tampil) → Logout
```

## Secondary / Exception Flows

- Login salah 3 kali berturut-turut → pesan gagal, akun tidak dikunci otomatis (tanpa rate limit, disebut sebagai batasan).
- Username/nonaktif → pesan "Akun tidak aktif atau tidak ditemukan".
- Kamar dihapus padahal masih ada penghuni aktif → **ditolak** dengan pesan; penghuni harus dipindah atau dikeluarkan lebih dulu.
- Kamar sudah terisi → tidak bisa ditempati dua penghuni aktif sekaligus.
- Penghuni keluar → tanggal keluar diisi, kamar kembali "kosong", riwayat pembayaran tetap tersimpan.
- Pembayaran untuk bulan yang sudah lunas → ditolak dengan pesan "Bulan ini sudah dibayar".
- Data kosong (belum ada kamar/penghuni/pembayaran) → tampil empty state yang menjelaskan langkah berikutnya.
- Input tidak valid (angka kosong, tanggal salah format, nominal negatif) → ditolak di form, pesan spesifik di dekat field.
- Database belum ada / rusak → aplikasi menampilkan pesan error yang bisa ditindaklanjuti, bukan menutup diam-diam.

## Screen Map

| # | Screen | Tujuan | Role | Aksi utama |
|---|---|---|---|---|
| S1 | Login | Membuktikan identitas dan role | semua | Masuk, keluar aplikasi |
| S2 | Dashboard | Ringkasan cepat: okupansi, penunggak bulan ini, pemasukan bulan ini | semua (angka laporan hanya Pemilik) | Navigasi ke layar lain |
| S3 | Data Kamar | Melihat & mengelola kamar | semua lihat; Pemilik hapus | Tambah, ubah, hapus, cari |
| S4 | Data Penghuni | Melihat & mengelola penghuni | semua lihat; Pemilik hapus | Tambah, ubah, keluar, hapus, cari |
| S5 | Pembayaran | Mencatat pembayaran sewa per bulan | semua | Catat pembayaran, filter bulan |
| S6 | Penunggak | Daftar penghuni aktif yang belum bayar pada bulan tertentu | semua | Pilih bulan, kirim pengingat manual (salin teks) |
| S7 | Laporan Pemasukan | Rekap pemasukan per bulan | Pemilik saja | Pilih bulan/tahun, ekspor CSV |
| S8 | Pengguna | Mengelola akun pemakai aplikasi | Pemilik saja | Tambah, ubah peran, nonaktifkan |

## Core Data / Objects

- **User**: id, username (unik), password_hash, nama, role (`pemilik` | `penjaga`), aktif, dibuat_pada.
- **Kamar**: id, nomor_kamar (unik), harga_sewa (per bulan), status_pakai (`kosong` | `terisi`), fasilitas (teks bebas), keterangan.
- **Penghuni**: id, nama, no_hp, kamar_id, tanggal_masuk, tanggal_keluar (boleh kosong), tarif_sewa, status (`aktif` | `keluar`).
- **Pembayaran**: id, penghuni_id, periode (`YYYY-MM`), tanggal_bayar, jumlah, metode (`tunai` | `transfer`), catatan, dicatat_oleh (user id).

## Business Rules

1. Periode sewa **bulanan**; jatuh tempo mengikuti **tanggal masuk** penghuni (masuk tgl 20 → jatuh tempo tiap tgl 20). Status: CONFIRMED.
2. Penghuni dengan tanggal keluar terisi berstatus `keluar` dan tidak dihitung sebagai penunggak.
3. Satu kamar maksimum satu penghuni aktif.
4. Kunci pembayaran: kombinasi (penghuni, periode) unik — tidak boleh dobel untuk bulan yang sama.
5. Nominal pembayaran diisi manual oleh pencatat (tidak dikunci ke tarif) karena sewa bisa berubah di tengah huni; tarif pada data penghuni menjadi nilai default di form.
6. Menunggak = penghuni `aktif` yang tidak memiliki baris pembayaran untuk periode terpilih, atau ada tetapi jumlahnya kurang dari tarif yang berlaku di periode itu ditandai "kurang bayar" (pada implementasi awal: hanya status belum ada pembayaran / sudah ada).
7. Hapus kamar ditolak bila masih ada penghuni aktif.
8. Data penghuni dan pembayaran lama tidak dihapus otomatis ketika kamar dihapus; sebaliknya, penghuni hanya dapat dihapus Pemilik dan hanya bila belum punya riwayat pembayaran (kalau punya, gunakan "keluar").
9. Password disimpan sebagai hash (PBKDF2-HMAC dari `hashlib` standar, dengan salt), tidak pernah plain text.
10. Semua validasi form berlaku di lapisan aplikasi, bukan hanya di tombol; penegakan role dicek di fungsi layanan sebelum aksi dijalankan (bukan hanya menyembunyikan tombol).

## Integrations

Tidak ada integrasi eksternal. Ekspor CSV ke berkas lokal memakai `csv` standard library. Status: CONFIRMED (no dependencies).

## Confirmed Requirements

- REQ-001 Login dengan username, password, dan role; sesi berlaku selama aplikasi terbuka.
- REQ-002 CRUD kamar + pencarian berdasarkan nomor kamar.
- REQ-003 CRUD penghuni + pencarian berdasarkan nama atau nomor kamar.
- REQ-004 Catat pembayaran per bulan dengan tanggal bayar dan nominal.
- REQ-005 Daftar penunggak per bulan.
- REQ-006 Laporan pemasukan bulanan (khusus Pemilik).
- REQ-007 Hak akses sesuai tabel pada bagian Actors / Roles.
- REQ-008 Data tersimpan permanen di SQLite.
- REQ-009 Validasi input: tidak boleh kosong pada field wajib, tidak boleh angka negatif, tidak boleh dobel pada data yang wajib unik.

## Proposed by AI

- Ekspor laporan ke CSV (tambahan kecil, berguna untuk laporan tugas).
- Seed data contoh: 2 pengguna (pemilik/penjaga), 8 kamar, 5 penghuni, pembayaran beberapa bulan — agar demo tidak kosong.
- Pengingat manual berupa tombol "Salin teks pengingat" pada layar Penunggak.
- Menandai "kurang bayar" bila nominal di bawah tarif.

## Needs Client Confirmation

- HAR-1 Apakah butuh tampilan kuitansi/bukti bayar yang bisa dicetak? (usulan: tidak, di luar scope)
- HAR-2 Data kamar/penghuni contoh untuk demo: boleh memakai nama fiktif? (jika ya, tidak boleh diklaim sebagai data nyata)
- HAR-3 Bahasa aplikasi: Indonesia penuh? (usulan: ya)

## Non-Functional Baseline

- Berjalan di Windows tanpa instalasi tambahan (Python sudah tersedia).
- Tampilan ramah resolusi kecil (minimum 1024x600) dan bisa di-resize tanpa elemen terpotong.
- Aksi tidak boleh membuat aplikasi crash; error ditampilkan sebagai pesan.
- Waktu respons aksi < 500 ms untuk data ratusan baris (SQLite lokal).
- Aksesibilitas minimum: navigasi keyboard penuh, fokus terlihat, kontras teks memadai.
