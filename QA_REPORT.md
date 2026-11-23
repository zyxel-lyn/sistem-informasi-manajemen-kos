# QA REPORT

Increment: UI Tkinter (WBS 9.0) + validasi lapisan layanan — 23 Nov 2026

## Scope

- Change / feature: antarmuka Tkinter untuk 8 layar, menu per role, dialog form, dan status bar.
- Environment: Windows 11, Python 3.14.9, Tk 9.0, SQLite 3.53.1, git-bash.
- Build / commit: `REPOSITORY: NONE` (belum ada git), tidak ada build step.
- Audit mode: TARGETED VERIFICATION.
- Reason: perubahan UI pertama, tanpa backend jarak jauh; verifikasi difokuskan pada aksi yang terlihat pengguna.

## Test Summary

| Test | Status | Evidence / Notes |
|---|---|---|
| Skema database | PASS | `python cek_skema.py` → 30 PASS, 0 FAIL, exit 0 |
| Layanan (login, role, aturan bisnis) | PASS | `python cek_services.py` → 69 PASS, 0 FAIL, exit 0 |
| E2E / UI Tk asli (login → 8 layar → dialog → logout) | PASS | `python cek_ui.py` → 28 PASS, 0 FAIL, exit 0 |
| Visual | PASS | 15 tangkapan layar di `bukti/` (PrintWindow, bukan BitBlt) |
| Responsive | NOT APPLICABLE | aplikasi desktop; jendela minimum 1000x600 diuji, tabel punya scrollbar |
| Accessibility | PARTIAL | fokus keyboard + Escape diuji; belum ada pembaca layar |
| Security | PASS | hak akses ditolak di layanan (7 kasus), password PBKDF2, tidak ada plain text |
| Performance | NOT MEASURED | tidak ada target performa formal; query SQLite lokal |
| Build / typecheck / lint | PASS | `python -c "import ast; ast.parse(...)"` bersih untuk semua modul |

## Click-through (bukti R-35)

| Elemen | Hasil yang diamati |
|---|---|
| Login dengan password salah | pesan "Username atau password salah." muncul, sesi tetap kosong, halaman tidak berpindah |
| Login pemilik | sidebar 7 menu tampil, dashboard terbuka |
| Menu Kamar / Penghuni / Pembayaran / Penunggak / Laporan / Pengguna | setiap layar terbuka dan tabel terisi (8 / 5 / 0 / 4 / 5 / 2 baris) |
| Tambah kamar (dialog) | dialog terbuka, isi 4 field, simpan → kamar "09" muncul di tabel |
| Simpan nomor kamar dobel | pesan "Nomor kamar 09 sudah dipakai. Gunakan nomor lain." |
| Hapus kamar (pemilik) | tombol ada, konfirmasi disetujui → kamar 09 hilang dari tabel |
| Pencarian nomor kamar | tabel menyaring menjadi 1 baris |
| Salin teks pengingat | clipboard berisi teks lebih dari 10 karakter |
| Laporan (periode bulan lalu) | total "Rp3.150.000" dari data pembayaran seed |
| Logout lalu login penjaga | menu laporan dan pengguna tidak dibuat, tombol Hapus kamar tidak ada |
| Penjaga mencatat pembayaran | dialog terbuka, simpan berhasil, tabel pembayaran bertambah |
| Escape pada dialog | dialog tertutup |

## Defects

- DEF-001 (FIXED, retested) — Severity Medium — dialog pesan membuat uji UI berhenti menunggu karena `wait_window` tanpa mode uji. Diperbaiki dengan sakelar `SIKOS_UJI_UI`; uji lulus ulang.
- DEF-002 (FIXED, retested) — Severity Low — kolom terakhir tabel tertutup karena `stretch=True` dan total lebar melebihi area tabel. Diperbaiki dengan `stretch=False`, `minwidth`, dan scrollbar horizontal; diverifikasi lewat tangkapan layar PrintWindow dan `identify_column` Tk.
- DEF-003 (FIXED, retested) — Severity Medium — tangkapan layar `ImageGrab` (BitBlt) mengembalikan gambar basi pada jendela berlapis sehingga kolom kanan dan status bar tampak hilang. Diperbaiki dengan `PrintWindow` Win32; tangkapan baru memperlihatkan 6 kolom dan status bar.
- DEF-004 (OPEN, low) — teks fasilitas panjang dipotong elipsis di kolom, bukan bug tetapi keterbacaan; kandidat: tooltip.
- DEF-005 (OPEN, low) — tombol "Ubah" pada tabel belum diuji kliknya di layar kamar (baru diuji keberadaannya).

## Verified

- Semua 7 menu per role tampil sesuai tabel hak akses yang disetujui.
- Aksi terlarang tidak hanya disembunyikan: fungsi layanan menolak (dibuktikan di `cek_services.py`).
- Angka laporan berasal dari data database, bukan angka tetap.
- Status penunggak selalu punya kata ("Belum bayar" / "Kurang bayar"), tidak bergantung warna saja.

## Not Verified / Blocked

- Penghuni: dialog tambah/ubah belum diisi sampai simpan di uji UI (layanan sudah diuji).
- Laporan: ekspor CSV lewat tombol belum diklik di uji UI (fungsi ekspor sudah diuji).
- Pengguna: tambah/ubah akun lewat UI belum diklik (layanan sudah diuji).
- Aksesibilitas: belum diuji dengan pembaca layar atau pemeriksaan kontras otomatis pada render.

## Residual Risks

- Tabel dengan fasilitas sangat panjang akan memotong teks.
- Jendela di bawah 1000x600 belum diuji.
- Pemilik yang lupa password tidak punya jalur pemulihan selain mengubah database langsung.

## Acceptance

- Technical status: VERIFIED untuk cakupan yang tercantum di atas; sisanya IMPLEMENTED — NOT VERIFIED.
- Client acceptance: WAITING.
- Release status: NOT RELEASED (aplikasi lokal).

## Next Action

- Lengkapi uji UI untuk dialog Penghuni, ekspor CSV, dan dialog Pengguna; lalu tulis README dan akhiri increment.
