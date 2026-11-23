# WBS

## Project
- Name: Sistem Informasi Manajemen Kos (SI-Kos)
- Mode: GREENFIELD
- Baseline version: v0.1
- Last updated: 23 Nov 2026
- Repository: NONE — belum ada repository (folder lokal, tanpa git)

Status memakai daftar kanonis `05_PROJECT_MANAGEMENT.md` §6.5. `DONE` tidak dipakai.

| ID | Phase | Deliverable | Priority | Owner | Dependency | Status | Acceptance Criteria | Evidence | Risk |
|---|---|---|---|---|---|---|---|---|---|
| 1.0 | Discovery | Product + Flow Baseline + DESIGN + WBS | CRITICAL | AI + Client | — | WAITING FOR CLIENT | Baseline disetujui client | Approval Package di chat | Ambiguitas |
| 2.0 | UX/Build | Lapisan database: skema 4 tabel, foreign key, unique, seed | CRITICAL | AI | 1.0 | NOT STARTED | `db.py` membuat/membuka database; skema cocok dengan FLOW_BASELINE; seed terisi sekali | Skrip cek skema + output | Skema berubah |
| 3.0 | Build | Autentikasi + penegakan role di lapisan layanan | CRITICAL | AI | 2.0 | NOT STARTED | Login benar/salah berfungsi; aksi terlarang ditolak di layanan, bukan hanya tombol disembunyikan | Uji login 3 kasus + uji akses per role | Hash password |
| 4.0 | Build | CRUD Kamar + pencarian | CRITICAL | AI | 2.0, 3.0 | NOT STARTED | Tambah/ubah/hapus/cari berfungsi; hapus ditolak bila ada penghuni aktif; nomor unik | Uji 6 kasus | Relasi |
| 5.0 | Build | CRUD Penghuni + pencarian + keluar | CRITICAL | AI | 4.0 | NOT STARTED | Satu kamar satu penghuni aktif; tanggal masuk mengisi jatuh tempo; "keluar" mengosongkan kamar | Uji 7 kasus | Aturan tanggal |
| 6.0 | Build | Pembayaran + penunggak | CRITICAL | AI | 5.0 | NOT STARTED | Pembayaran tersimpan dan tidak bisa dobel per (penghuni, periode); daftar penunggak benar menurut tanggal masuk | Uji periode lintas bulan | Hitungan tanggal |
| 7.0 | Build | Laporan pemasukan bulanan + ekspor CSV (Pemilik) | IMPORTANT | AI | 6.0 | NOT STARTED | Total per bulan benar; hanya Pemilik bisa membuka | Uji total vs hitungan manual | — |
| 8.0 | Build | Manajemen pengguna (Pemilik) | IMPORTANT | AI | 3.0 | NOT STARTED | Tambah user, ubah role, nonaktifkan; akun nonaktif tidak bisa login | Uji login akun nonaktif | Privilege escalation |
| 9.0 | UI | Shell aplikasi, sidebar per role, dashboard, empty/error state | IMPORTANT | AI | 3.0 | NOT STARTED | Sesuai DESIGN.md; minimum 1024x600 tanpa elemen terpotong | Screenshot + checklist | UI drift |
| 10.0 | QA | QA fungsional + role + input valid + keyboard | CRITICAL | AI | 4.0–9.0 | NOT STARTED | Setiap REQ punya bukti VERIFIED — <bukti> | `QA_REPORT.md` | — |
| 11.0 | Docs | README cara menjalankan, akun demo, skema DB | IMPORTANT | AI | 10.0 | NOT STARTED | Orang lain bisa menjalankan tanpa bertanya | File README | — |

## Urutan Pengerjaan yang Disetujui untuk Dikunci

1. 1.0 (baseline) → 2.0 (database) → 3.0 (auth/role) → 4.0 (kamar) → 5.0 (penghuni) → 6.0 (pembayaran/penunggak) → 7.0, 8.0 → 9.0 (UI shell & dashboard) → 10.0 (QA) → 11.0 (docs).

Alasan urutan: data dulu, aturan akses kedua, lalu fitur yang saling bergantung. UI shell baru setelah layanan stabil agar tidak menyesuaikan tampilan berulang.

## Risiko Utama

- Hitungan penunggak salah di batas bulan (penghuni masuk tanggal 31). Mitigasi: uji kasus tanggal 29/30/31.
- Role hanya disembunyikan di UI, bukan ditegakkan. Mitigasi: uji fungsi layanan secara langsung.
- Password plain text. Mitigasi: hash + salt sejak versi pertama.
