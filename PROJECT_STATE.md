# PROJECT_STATE

## Project Identity
- Name: Sistem Informasi Manajemen Kos (SI-Kos)
- Goal: Aplikasi desktop untuk mencatat kamar, penghuni, dan pembayaran sewa bulanan, plus rekap penunggak dan pemasukan.
- Repository/workspace: `D:\Wildanun Mukhallid\Tugas\Semester 5\Pemrograman 2\Project UAS`
- Current mode: GREENFIELD

## Current Phase
- Phase: 3 (Core Implementation) — lapisan data dan layanan selesai
- WBS milestone: 3.0 / 4.0 / 5.0 / 6.0 / 7.0 / 8.0 (layanan)
- Current scope: logika layanan tanpa UI
- Last completed increment: `services.py` + `services_lanjutan.py` + `cek_services.py`

## Client Collaboration State
- Latest Approval Package: Baseline v0.1 (desktop Tkinter + SQLite, 2 role, sewa bulanan ikut tanggal masuk)
- Approval status: APPROVED (23 Nov 2026)
- Last client instruction: "Lanjutkan" (melanjutkan ke layanan)
- Pending client confirmations: HAR-1 (cetak kuitansi), HAR-3 (bahasa Indonesia penuh) — tidak menghalangi

## Requirement State
- CONFIRMED: REQ-001 … REQ-009 (lihat `FLOW_BASELINE.md`)
- PROPOSED: ekspor CSV, seed demo, tombol salin teks pengingat, penanda "kurang bayar"
- NEEDS CONFIRMATION: HAR-1, HAR-2, HAR-3
- LOCKED: baseline v0.1, tabel hak akses Pemilik/Penjaga
- CHANGED: —

## Stack and Environment
- Frontend/UI: Tkinter (Tk 9.0, terverifikasi di mesin ini)
- Backend: Python 3.14.9
- Database: SQLite 3.53.1, berkas `sikos.db`
- Runtime: Windows 11, git-bash
- Deployment: aplikasi lokal; belum ada target deploy
- Relevant versions: tanpa dependency eksternal

## Product and UI Baseline
- FLOW_BASELINE path/version: `FLOW_BASELINE.md` v0.1 (LOCKED)
- DESIGN path/version: `DESIGN.md` v0.1 (PROPOSED BY AI, disetujui bersama baseline)
- UI_SYSTEM path/version/status: belum dibuat — direncanakan sebagai bagian `DESIGN.md` karena proyek kecil
- Representative reference surface: layar Data Penghuni (dipilih nanti di tahap UI)
- Known component gaps: sidebar, tabel data, dialog form, dialog konfirmasi, badge status

## Architecture Snapshot
- Entry point: `main.py` (belum dibuat)
- Skema: `db.py` — tabel users, kamar, penghuni, pembayaran; index unik satu penghuni aktif; CHECK role/status/periode/jumlah
- Aturan bisnis: `services.py` (belum dibuat) — semua cek role di sini
- UI: paket `ui/` (belum dibuat)
- Auth/roles: `pemilik` dan `penjaga`
- External integrations: tidak ada

## Active Skills and Tools
- Name: Anti Slop (core + `antislop-ui` saat tahap UI)
- Why needed: menyaring pola UI/teks generik
- Availability verified: skill `antislop` termuat di sesi ini; sub-skill dimuat saat dibutuhkan
- Version/commit: tidak dicatat, mengikuti instalasi lokal

## Decisions
- DEC-001 (ACCEPTED): aplikasi desktop Tkinter + SQLite, bukan web. Alasan: sesuai deck kelompok, tanpa dependency, cepat dinilai.
- DEC-002 (ACCEPTED): dua role dengan tabel hak akses yang disetujui client.
- DEC-003 (ACCEPTED): sewa bulanan, jatuh tempo mengikuti tanggal masuk penghuni.
- DEC-004 (ACCEPTED): password disimpan sebagai PBKDF2-SHA256 + salt (`hashlib` standar), tanpa library luar.
- DEC-005 (ACCEPTED): status kamar `terisi/kosong` disimpan sebagai kolom dan dijaga konsisten dengan data penghuni aktif.
- RETRIEVAL: none — proyek kecil, tanpa Graphify/Codebase Memory.

## Last Verified Evidence
- Build: tidak ada build step (Python murni)
- Tests: `python cek_skema.py` → **30 PASS, 0 FAIL**; `python cek_services.py` → **69 PASS, 0 FAIL** (23 Nov 2026, exit code 0 keduanya)
- Runtime: `python db.py` → database dibuat, 2 users / 8 kamar / 5 penghuni / 8 pembayaran
- Responsive: belum (belum ada UI)
- Accessibility: belum (belum ada UI)
- Security: hash password terverifikasi; akses per role ditolak di layanan (7 kasus negatif lulus)
- Deployment: NOT APPLICABLE (aplikasi lokal)
- Commit/source checkpoint: NONE — belum ada repository

## Open Risks and Defects
- RISK-001: hitungan penunggak di batas tanggal 29/30/31 belum diuji (menunggu `services.py`)
- BUG-001 (ditemukan & diperbaiki di dalam tahap ini): pemeriksa seed salah menghitung karena memakai database yang sudah berisi baris uji; sekarang seed diperiksa di database terpisah

## Current Work
- IN PROGRESS: —
- BLOCKED: —
- WAITING FOR CLIENT: —

## Next Actions
1. Buat UI Tkinter: `main.py` (login + app shell), `ui/` berisi layar Kamar, Penghuni, Pembayaran, Penunggak, Laporan, Pengguna, Dashboard.
2. Jalankan aplikasi dan lakukan click-through setiap tombol; catat bukti per elemen.
3. Tulis `QA_REPORT.md` dan `README.md` (akun demo + cara menjalankan).

## Freshness
- State updated: 23 Nov 2026 11:25
- Source commit: NONE
- Evidence timestamp: 23 Nov 2026 11:13
- Graph status: NOT AVAILABLE (RETRIEVAL=none)
- Known stale areas: —
