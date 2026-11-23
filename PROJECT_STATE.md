# PROJECT_STATE

## Project Identity
- Name: Sistem Informasi Manajemen Kos (SI-Kos)
- Goal: Aplikasi desktop untuk mencatat kamar, penghuni, dan pembayaran sewa bulanan, plus rekap penunggak dan pemasukan.
- Repository/workspace: lokal `Project UAS` + GitHub `https://github.com/zyxel-lyn/sistem-informasi-manajemen-kos` (main)
- Current mode: GREENFIELD

## Current Phase
- Phase: 5 (Quality and Acceptance)
- WBS milestone: 9.0 UI + 10.0 QA + 11.0 Docs
- Current scope: UI lengkap, QA, README, repository
- Last completed increment: uji UI 37 PASS, README, git init + push ke GitHub

## Client Collaboration State
- Latest Approval Package: Baseline v0.1 (desktop Tkinter + SQLite, 2 role, sewa bulanan ikut tanggal masuk)
- Approval status: APPROVED (23 Nov 2026)
- Last client instruction: "Approve 1,2,3 + buatkan repo GitHub"
- Pending client confirmations: HAR-1 (cetak kuitansi), HAR-3 (bahasa Indonesia penuh)

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
- DEC-006 (ACCEPTED): hak `pembayaran_batal` ditambahkan khusus Pemilik, menggantikan pemakaian `laporan_lihat` untuk pembatalan.
- DEC-007 (ACCEPTED): repository publik `sistem-informasi-manajemen-kos` di akun zyxel-lyn, branch main.

## Last Verified Evidence
- Build: tidak ada build step (Python murni)
- Tests: `cek_skema.py` 30 PASS · `cek_services.py` 69 PASS · `cek_ui.py` **37 PASS, 0 FAIL** (23 Nov 2026, exit 0 ketiganya)
- Runtime: `python db.py` → database dibuat, 2 users / 8 kamar / 5 penghuni / 8 pembayaran
- Responsive: belum (belum ada UI)
- Accessibility: belum (belum ada UI)
- Security: hash password terverifikasi; akses per role ditolak di layanan (7 kasus negatif lulus); password Pemilik tidak bisa dinonaktifkan sendiri
- Deployment: NOT APPLICABLE (aplikasi lokal)
- Commit/source checkpoint: 60661c9 (main, sudah dipush ke GitHub)

## Open Risks and Defects
- RISK-001: hitungan penunggak di batas tanggal 29/30/31 belum diuji (menunggu `services.py`)
- BUG-001 (ditemukan & diperbaiki di dalam tahap ini): pemeriksa seed salah menghitung karena memakai database yang sudah berisi baris uji; sekarang seed diperiksa di database terpisah

## Current Work
- IN PROGRESS: —
- BLOCKED: —
- WAITING FOR CLIENT: —

## Next Actions
1. Minta client meninjau aplikasi (acceptance) dan menandai WBS 9.0/10.0/11.0 sebagai ACCEPTED bila setuju.
2. Opsional: tombol ubah pada tabel Kamar diuji kliknya, tooltip untuk teks fasilitas panjang, dan jalur pemulihan password Pemilik.
3. Opsional: tangkapan layar di README supaya repo lebih informatif saat dinilai.

## Freshness
- State updated: 23 Nov 2026 13:05
- Source commit: 60661c9
- Evidence timestamp: 23 Nov 2026 11:13
- Graph status: NOT AVAILABLE (RETRIEVAL=none)
- Known stale areas: —
