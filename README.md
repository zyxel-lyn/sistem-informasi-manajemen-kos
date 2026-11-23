# SI-Kos: Sistem Informasi Manajemen Kos

Aplikasi desktop Python untuk mengelola kos skala kecil: data kamar, data penghuni, pembayaran sewa bulanan, daftar penunggak, dan laporan pemasukan. Dibuat untuk UAS mata kuliah Pemrograman 2, Jurusan Informatika FMIPA Universitas Syiah Kuala.

Python + Tkinter + SQLite, tanpa dependency eksternal.

## Menjalankan

```bash
python main.py
```

Saat pertama dijalankan, `db.py` membuat `sikos.db` dan mengisi data demo. Tidak perlu instalasi library apa pun.

## Akun demo

| Username | Password | Peran |
|---|---|---|
| `pemilik` | `pemilik123` | Pemilik kos |
| `penjaga` | `penjaga123` | Penjaga kos |

Password disimpan sebagai hash PBKDF2-SHA256 dengan salt, bukan teks biasa.

## Hak akses

| Aksi | Pemilik | Penjaga |
|---|---|---|
| Lihat kamar dan penghuni | ya | ya |
| Tambah/ubah kamar dan penghuni | ya | ya |
| Hapus kamar dan penghuni | ya | tidak |
| Catat pembayaran | ya | ya |
| Lihat daftar penunggak | ya | ya |
| Laporan pemasukan dan ekspor CSV | ya | tidak |
| Kelola akun pengguna | ya | tidak |

Hak akses ditegakkan di `services.py`, bukan hanya dengan menyembunyikan tombol.

## Aturan bisnis

- Sewa bulanan, jatuh tempo mengikuti tanggal masuk penghuni. Tanggal 29, 30, 31 dipadatkan ke hari terakhir bulan berjalan.
- Satu kamar hanya boleh punya satu penghuni aktif (dijaga partial unique index).
- Satu penghuni hanya boleh punya satu pembayaran per periode (dijaga unique constraint).
- Kamar yang masih dihuni atau punya riwayat penghuni tidak dapat dihapus.
- Penghuni yang punya riwayat pembayaran tidak dihapus, hanya ditandai keluar.

## Struktur berkas

```text
main.py                 titik masuk aplikasi
db.py                   skema database, seed demo, hash password
services.py             login, hak akses, kamar, penghuni, jatuh tempo, penunggak
services_lanjutan.py    pembayaran, laporan + CSV, kelola pengguna
ui/tema.py              token warna, style, dialog, tangkapan layar
ui/komponen.py          tabel, bilah aksi, field form
ui/app.py               login, sidebar per peran, status bar
ui/layar.py             layar Ringkasan, Kamar, Penghuni
ui/layar_lanjutan.py    layar Pembayaran, Penunggak, Laporan, Akun
```

Berkas pendukung: `PRODUCT.md`, `FLOW_BASELINE.md`, `DESIGN.md`, `WBS.md`, `QA_REPORT.md`, `PROJECT_STATE.md`.

## Skema database

| Tabel | Isi |
|---|---|
| `users` | id, username (unik, case-insensitive), password_hash, nama, role, aktif |
| `kamar` | id, nomor_kamar (unik), harga_sewa, status_pakai, fasilitas, keterangan |
| `penghuni` | id, nama, no_hp, kamar_id, tanggal_masuk, tanggal_keluar, tarif_sewa, status |
| `pembayaran` | id, penghuni_id, periode (YYYY-MM), tanggal_bayar, jumlah, metode, catatan, dicatat_oleh |

## Menjalankan pemeriksaan

```bash
python cek_skema.py      # 30 pemeriksaan skema dan seed
python cek_services.py   # 69 pemeriksaan layanan dan hak akses
python cek_ui.py         # 37 pemeriksaan antarmuka, hasil tangkapan di bukti/
```

`cek_ui.py` menjalankan aplikasi Tk sungguhan lalu mengklik kontrolnya. Tangkapan layar tersimpan di folder `bukti/`. Pemeriksaan memakai database sementara, jadi `sikos.db` aplikasi tidak berubah.

## Batasan yang diketahui

- Aplikasi desktop untuk satu komputer. Tidak dapat diakses dari perangkat lain.
- Belum ada fitur cetak kuitansi.
- Pemilik yang lupa password harus mengubahnya lewat database, belum ada pemulihan mandiri.
- Teks fasilitas yang sangat panjang akan terpotong dengan elipsis di kolom tabel.
