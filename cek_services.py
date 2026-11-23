"""Cek lapisan layanan SI-Kos: login, hak akses per role, aturan bisnis kamar,
penghuni, pembayaran, penunggak, dan laporan.

Dijalankan: python cek_services.py
Memakai database sementara; tidak menyentuh sikos.db aplikasi.
"""

from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import db  # noqa: E402
import services as sv  # noqa: E402
import services_lanjutan as sl  # noqa: E402

lulus = 0
gagal = 0


def cek(nama: str, kondisi: bool, detail: str = "") -> None:
    global lulus, gagal
    if kondisi:
        lulus += 1
        print(f"  PASS  {nama}" + (f"  ({detail})" if detail else ""))
    else:
        gagal += 1
        print(f"  FAIL  {nama}" + (f"  ({detail})" if detail else ""))


def ditolak(fn, jenis=sv.KesalahanAplikasi):
    """Jalankan fn, kembalikan pesan error bila ditolak, None bila lolos."""
    try:
        fn()
    except jenis as e:
        return str(e)
    except sqlite3.IntegrityError as e:
        return f"IntegrityError: {e}"
    return None


def baru() -> tuple[sqlite3.Connection, sv.Sesi, sv.Sesi]:
    folder = tempfile.mkdtemp(prefix="sikos_svc_")
    conn = db.siapkan_database(os.path.join(folder, "uji.db"))
    pemilik = sv.login(conn, "pemilik", "pemilik123")
    penjaga = sv.login(conn, "penjaga", "penjaga123")
    return conn, pemilik, penjaga


def main() -> int:
    conn, pemilik, penjaga = baru()
    print("Sesi: pemilik =", pemilik.nama, "| penjaga =", penjaga.nama, "\n")

    print("[1] Login")
    cek("login benar mengembalikan role", pemilik.role == "pemilik" and penjaga.role == "penjaga")
    cek("password salah ditolak",
        ditolak(lambda: sv.login(conn, "pemilik", "salah")) is not None)
    cek("username tidak ada ditolak",
        ditolak(lambda: sv.login(conn, "tidakada", "x")) is not None)
    cek("username beda kapital tetap bisa login",
        sv.login(conn, "PEMILIK", "pemilik123").role == "pemilik")
    cek("field kosong ditolak", ditolak(lambda: sv.login(conn, "", "")) is not None)
    conn.execute("UPDATE users SET aktif = 0 WHERE username = 'penjaga'")
    conn.commit()
    cek("akun nonaktif ditolak",
        "tidak aktif" in (ditolak(lambda: sv.login(conn, "penjaga", "penjaga123")) or ""))
    conn.execute("UPDATE users SET aktif = 1 WHERE username = 'penjaga'")
    conn.commit()

    print("\n[2] Hak akses per role (ditegakkan di layanan, bukan hanya di UI)")
    cek("penjaga punya hak ubah kamar", penjaga.boleh("kamar_ubah"))
    cek("penjaga TIDAK punya hak hapus kamar", not penjaga.boleh("kamar_hapus"))
    cek("penjaga TIDAK punya hak hapus penghuni", not penjaga.boleh("penghuni_hapus"))
    cek("penjaga TIDAK punya hak laporan", not penjaga.boleh("laporan_lihat"))
    cek("penjaga TIDAK punya hak kelola pengguna", not penjaga.boleh("pengguna_kelola"))
    cek("pemilik punya semua hak", pemilik.boleh("kamar_hapus") and pemilik.boleh("laporan_lihat"))
    cek("sesi None ditolak (belum login)",
        isinstance(ditolak(lambda: sv.daftar_kamar(conn, None)), str))

    kamar_tanpa_penghuni = sv.tambah_kamar(conn, pemilik, "99", 500000)
    kamar_berpenghuni = conn.execute(
        "SELECT p.kamar_id FROM penghuni p WHERE p.status='aktif' LIMIT 1"
    ).fetchone()[0]
    cek("penjaga ditolak saat menghapus kamar",
        isinstance(ditolak(lambda: sv.hapus_kamar(conn, penjaga, kamar_tanpa_penghuni)), str))
    cek("pemilik diterima saat menghapus kamar kosong",
        ditolak(lambda: sv.hapus_kamar(conn, pemilik, kamar_tanpa_penghuni)) is None)

    pid = conn.execute("SELECT id FROM penghuni WHERE status='keluar' LIMIT 1").fetchone()
    pid = pid[0] if pid else conn.execute("SELECT id FROM penghuni LIMIT 1").fetchone()[0]
    cek("penjaga ditolak saat menghapus penghuni",
        isinstance(ditolak(lambda: sv.hapus_penghuni(conn, penjaga, pid)), str))
    cek("penjaga ditolak saat membuka laporan",
        isinstance(ditolak(lambda: sl.laporan_bulanan(conn, penjaga, "2026-11")), str))
    cek("penjaga ditolak saat menambah pengguna",
        isinstance(ditolak(lambda: sl.tambah_pengguna(conn, penjaga, "x", "123456", "X", "penjaga")),
                str))

    print("\n[3] Aturan kamar")
    cek("tambah kamar menolak nomor dobel",
        "sudah dipakai" in (ditolak(lambda: sv.tambah_kamar(conn, pemilik, "01", 700000)) or ""))
    cek("tambah kamar menolak harga negatif",
        ditolak(lambda: sv.tambah_kamar(conn, pemilik, "77", -1)) is not None)
    cek("tambah kamar menolak harga bukan angka",
        ditolak(lambda: sv.tambah_kamar(conn, pemilik, "78", "seratus")) is not None)
    cek("tambah kamar menolak nomor kosong",
        ditolak(lambda: sv.tambah_kamar(conn, pemilik, "   ", 700000)) is not None)
    cek("hapus kamar berpenghuni aktif ditolak",
        "masih dihuni" in (ditolak(lambda: sv.hapus_kamar(conn, pemilik, kamar_berpenghuni)) or ""))
    cek("pencarian kamar menemukan nomor tertentu",
        len(sv.daftar_kamar(conn, pemilik, "03")) == 1)

    print("\n[4] Aturan penghuni")
    kamar_kosong = conn.execute(
        "SELECT k.id FROM kamar k WHERE NOT EXISTS (SELECT 1 FROM penghuni p"
        " WHERE p.kamar_id = k.id AND p.status = 'aktif') LIMIT 1"
    ).fetchone()[0]
    cek("tambah penghuni ke kamar kosong berhasil",
        ditolak(lambda: sv.tambah_penghuni(conn, penjaga, "Uji Masuk", "0811", kamar_kosong,
                                           "2026-01-15", 700000)) is None)
    status = conn.execute("SELECT status_pakai FROM kamar WHERE id = ?", (kamar_kosong,)).fetchone()[0]
    cek("status kamar otomatis menjadi 'terisi'", status == "terisi", f"status={status}")
    cek("penghuni kedua di kamar sama ditolak",
        "sudah ditempati" in (ditolak(lambda: sv.tambah_penghuni(
            conn, penjaga, "Uji Dua", "0812", kamar_kosong, "2026-02-01", 700000)) or ""))
    cek("tanggal masuk di masa depan ditolak",
        "masa depan" in (ditolak(lambda: sv.tambah_penghuni(
            conn, pemilik, "Uji Depan", "", kamar_kosong,
            (date.today() + timedelta(days=5)).isoformat(), 700000)) or ""))
    cek("nama kosong ditolak",
        ditolak(lambda: sv.tambah_penghuni(conn, pemilik, "  ", "", kamar_kosong,
                                           "2026-01-01", 700000)) is not None)
    cek("tarif negatif ditolak",
        ditolak(lambda: sv.tambah_penghuni(conn, pemilik, "Uji Neg", "", kamar_kosong,
                                           "2026-01-01", -5)) is not None)

    pid_baru = conn.execute("SELECT id FROM penghuni WHERE nama = 'Uji Masuk'").fetchone()[0]
    cek("tandai keluar berhasil",
        ditolak(lambda: sv.keluar_penghuni(conn, penjaga, pid_baru, "2026-03-10")) is None)
    status = conn.execute("SELECT status_pakai FROM kamar WHERE id = ?", (kamar_kosong,)).fetchone()[0]
    cek("kamar kembali 'kosong' setelah penghuni keluar", status == "kosong", f"status={status}")
    cek("menandai keluar dua kali ditolak",
        "sudah tercatat keluar" in (ditolak(lambda: sv.keluar_penghuni(
            conn, pemilik, pid_baru, "2026-03-11")) or ""))
    cek("tanggal keluar sebelum masuk ditolak",
        ditolak(lambda: sv.keluar_penghuni(conn, pemilik, pid_baru, "2025-01-01")) is not None)
    cek("penghuni dengan riwayat bayar tidak bisa dihapus",
        "riwayat pembayaran" in (ditolak(lambda: sv.hapus_penghuni(
            conn, pemilik,
            conn.execute("SELECT penghuni_id FROM pembayaran LIMIT 1").fetchone()[0])) or ""))
    cek("penghuni tanpa riwayat bayar bisa dihapus oleh pemilik",
        ditolak(lambda: sv.hapus_penghuni(conn, pemilik, pid_baru)) is None)

    print("\n[5] Jatuh tempo mengikuti tanggal masuk (termasuk 29/30/31)")
    kasus = [
        ("2026-01-20", "2026-02", "2026-02-20"),
        ("2026-01-31", "2026-02", "2026-02-28"),  # Februari dipadatkan
        ("2025-01-31", "2026-02", "2026-02-28"),
        ("2026-01-30", "2026-04", "2026-04-30"),
        ("2026-01-05", "2026-12", "2026-12-05"),
        ("2026-01-31", "2026-01", "2026-01-31"),
        ("2026-01-31", "2026-07", "2026-07-31"),
    ]
    for masuk, periode, harap in kasus:
        hasil = sv.tanggal_jatuh_tempo(masuk, periode).isoformat()
        cek(f"masuk {masuk} periode {periode} → {hasil}", hasil == harap, f"harap {harap}")

    print("\n[6] Pembayaran")
    aktif = conn.execute("SELECT id, tarif_sewa, nama FROM penghuni WHERE status='aktif' LIMIT 1").fetchone()
    pid, tarif = aktif["id"], aktif["tarif_sewa"]
    cek("catat pembayaran berhasil",
        ditolak(lambda: sl.catat_pembayaran(conn, penjaga, pid, "2030-01", tarif)) is None)
    cek("pembayaran dobel periode sama ditolak",
        "sudah tercatat" in (ditolak(lambda: sl.catat_pembayaran(
            conn, penjaga, pid, "2030-01", tarif)) or ""))
    cek("jumlah nol ditolak",
        ditolak(lambda: sl.catat_pembayaran(conn, penjaga, pid, "2030-02", 0)) is not None)
    cek("jumlah negatif ditolak",
        ditolak(lambda: sl.catat_pembayaran(conn, penjaga, pid, "2030-03", -500)) is not None)
    cek("periode salah format ditolak",
        ditolak(lambda: sl.catat_pembayaran(conn, penjaga, pid, "2030-13", tarif)) is not None)
    cek("periode sebelum tanggal masuk ditolak",
        "belum berlaku" in (ditolak(lambda: sl.catat_pembayaran(
            conn, penjaga, pid, "2019-05", tarif)) or ""))
    cek("metode tidak dikenal ditolak",
        ditolak(lambda: sl.catat_pembayaran(conn, penjaga, pid, "2030-04", tarif,
                                            metode="bitcoin")) is not None)
    cek("pembayaran tercatat atas nama pencatat",
        conn.execute("SELECT dicatat_oleh FROM pembayaran WHERE periode='2030-01'"
                     ).fetchone()[0] == penjaga.id)
    cek("penjaga bisa melihat daftar pembayaran",
        len(sl.daftar_pembayaran(conn, penjaga, "2030-01")) == 1)
    pay_id = conn.execute("SELECT id FROM pembayaran WHERE periode='2030-01'").fetchone()[0]
    cek("penjaga ditolak saat membatalkan pembayaran",
        isinstance(ditolak(lambda: sl.hapus_pembayaran(conn, penjaga, pay_id)), str))

    print("\n[7] Daftar penunggak")
    unggak = sv.daftar_penunggak(conn, penjaga, "2030-01")
    cek("penghuni yang sudah bayar tidak masuk daftar penunggak",
        all(u["id"] != pid for u in unggak), f"{len(unggak)} penunggak")
    unggak2 = sv.daftar_penunggak(conn, pemilik, "2030-02")
    cek("periode belum dibayar memunculkan penunggak", len(unggak2) >= 1, f"{len(unggak2)} baris")
    cek("penunggak membawa jatuh tempo sesuai tanggal masuk",
        all(u["jatuh_tempo"].endswith(
            f"-{min(date.fromisoformat(
                conn.execute('SELECT tanggal_masuk FROM penghuni WHERE id=?',
                             (u['id'],)).fetchone()[0]).day, 28):02d}")
            or u["jatuh_tempo"].endswith("-29") or u["jatuh_tempo"].endswith("-30")
            or u["jatuh_tempo"].endswith("-31") for u in unggak2))
    cek("penghuni yang masuk setelah periode tidak dianggap menunggak",
        all(date.fromisoformat(
            conn.execute("SELECT tanggal_masuk FROM penghuni WHERE id=?",
                         (u["id"],)).fetchone()[0]) <= date(2030, 2, 28) for u in unggak2))
    cek("status penunggak berupa belum bayar / kurang bayar",
        {u["status"] for u in unggak2} <= {"belum bayar", "kurang bayar"})
    cek("penunggak periode sebelum masuk tidak muncul",
        all(u["id"] != pid for u in sv.daftar_penunggak(conn, pemilik, "2019-05")))

    print("\n[8] Laporan pemasukan")
    lap = sl.laporan_bulanan(conn, pemilik, "2030-01")
    hitung_manual = conn.execute(
        "SELECT COALESCE(SUM(jumlah),0) FROM pembayaran WHERE periode='2030-01'"
    ).fetchone()[0]
    cek("total laporan sama dengan jumlah pembayaran di database",
        lap["total_masuk"] == hitung_manual, f"laporan={lap['total_masuk']} manual={hitung_manual}")
    cek("laporan memuat rincian per penghuni", len(lap["rincian"]) >= 1)
    path_csv = os.path.join(tempfile.mkdtemp(prefix="sikos_csv_"), "laporan.csv")
    sl.ekspor_laporan_csv(conn, pemilik, "2030-01", path_csv)
    isi = open(path_csv, encoding="utf-8").read()
    cek("ekspor CSV berhasil dan berisi nomor kamar",
        os.path.exists(path_csv) and "Kamar" in isi, f"{len(isi)} byte")

    print("\n[9] Manajemen pengguna")
    cek("pemilik menambah pengguna baru",
        ditolak(lambda: sl.tambah_pengguna(conn, pemilik, "penjaga2", "rahasia1",
                                           "Penjaga Dua", "penjaga")) is None)
    cek("username pengguna dobel ditolak",
        "sudah dipakai" in (ditolak(lambda: sl.tambah_pengguna(
            conn, pemilik, "PENJAGA2", "rahasia1", "X", "penjaga")) or ""))
    cek("password pendek ditolak",
        ditolak(lambda: sl.tambah_pengguna(conn, pemilik, "p3", "123", "X", "penjaga")) is not None)
    cek("role tidak dikenal ditolak",
        ditolak(lambda: sl.tambah_pengguna(conn, pemilik, "p4", "rahasia1", "X", "owner")) is not None)
    uid = conn.execute("SELECT id FROM users WHERE username='penjaga2'").fetchone()[0]
    sl.ubah_pengguna(conn, pemilik, uid, "Penjaga Dua", "penjaga", False)
    cek("akun yang dinonaktifkan tidak bisa login",
        "tidak aktif" in (ditolak(lambda: sv.login(conn, "penjaga2", "rahasia1")) or ""))
    cek("pemilik tidak bisa menonaktifkan akunnya sendiri",
        ditolak(lambda: sl.ubah_pengguna(conn, pemilik, pemilik.id, pemilik.nama,
                                         "pemilik", False)) is not None)
    cek("pemilik tetap aktif setelah percobaan di atas", sl.jumlah_pemilik_aktif(conn) >= 1)

    print("\n" + "=" * 50)
    print(f"HASIL: {lulus} PASS, {gagal} FAIL")
    print("=" * 50)
    conn.close()
    return 0 if gagal == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
