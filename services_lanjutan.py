"""Layanan pembayaran, laporan, dan pengguna. Dipisah agar services.py tidak
tumbuh menjadi satu berkas untuk semua fitur.
"""

from __future__ import annotations

import csv
import sqlite3
from datetime import date, datetime

import db
from services import (
    AksesDitolak, KesalahanAplikasi, Sesi, _hari_terakhir, _wajib, daftar_penunggak,
)


def _parse_tanggal(nilai, label: str) -> date:
    if isinstance(nilai, date):
        return nilai
    teks = str(nilai or "").strip()
    for format_ in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(teks, format_).date()
        except ValueError:
            continue
    raise KesalahanAplikasi(f"{label} harus berupa tanggal (contoh 2026-11-23).")


# --------------------------------------------------------------------------- #
# Pembayaran
# --------------------------------------------------------------------------- #

def catat_pembayaran(conn: sqlite3.Connection, sesi: Sesi | None, penghuni_id: int, periode: str,
                     jumlah, tanggal_bayar=None, metode: str = "tunai",
                     catatan: str = "") -> int:
    _wajib(sesi, "pembayaran_catat")
    tahun, bulan = _validasi_periode(periode)
    penghuni = conn.execute(
        "SELECT id, nama, tarif_sewa, tanggal_masuk, status FROM penghuni WHERE id = ?",
        (penghuni_id,),
    ).fetchone()
    if penghuni is None:
        raise KesalahanAplikasi("Penghuni tidak ditemukan.")
    masuk = date.fromisoformat(penghuni["tanggal_masuk"])
    if date(tahun, bulan, _hari_terakhir(tahun, bulan)) < masuk:
        raise KesalahanAplikasi(
            f"{penghuni['nama']} baru masuk {penghuni['tanggal_masuk']}, periode {periode}"
            " belum berlaku untuknya."
        )
    try:
        jumlah = int(jumlah)
    except (TypeError, ValueError):
        raise KesalahanAplikasi("Jumlah bayar harus berupa angka.")
    if jumlah <= 0:
        raise KesalahanAplikasi("Jumlah bayar harus lebih dari nol.")
    if metode not in db.METODE_BAYAR:
        raise KesalahanAplikasi("Metode pembayaran hanya tunai atau transfer.")
    bayar = _parse_tanggal(tanggal_bayar or date.today(), "Tanggal bayar")

    sudah = conn.execute(
        "SELECT id FROM pembayaran WHERE penghuni_id = ? AND periode = ?", (penghuni_id, periode)
    ).fetchone()
    if sudah is not None:
        raise KesalahanAplikasi(
            f"Pembayaran {penghuni['nama']} untuk periode {periode} sudah tercatat."
        )
    cur = conn.execute(
        "INSERT INTO pembayaran (penghuni_id, periode, tanggal_bayar, jumlah, metode,"
        " catatan, dicatat_oleh) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (penghuni_id, f"{tahun:04d}-{bulan:02d}", bayar.isoformat(), jumlah, metode,
         (catatan or "").strip(), sesi.id),
    )
    conn.commit()
    return cur.lastrowid


def daftar_pembayaran(conn: sqlite3.Connection, sesi: Sesi | None, periode: str = "") -> list:
    _wajib(sesi, "pembayaran_catat")
    if periode:
        _validasi_periode(periode)
        return conn.execute(
            "SELECT b.*, p.nama, k.nomor_kamar, u.nama AS pencatat"
            " FROM pembayaran b JOIN penghuni p ON p.id = b.penghuni_id"
            " JOIN kamar k ON k.id = p.kamar_id LEFT JOIN users u ON u.id = b.dicatat_oleh"
            " WHERE b.periode = ? ORDER BY b.tanggal_bayar, p.nama",
            (periode,),
        ).fetchall()
    return conn.execute(
        "SELECT b.*, p.nama, k.nomor_kamar, u.nama AS pencatat"
        " FROM pembayaran b JOIN penghuni p ON p.id = b.penghuni_id"
        " JOIN kamar k ON k.id = p.kamar_id LEFT JOIN users u ON u.id = b.dicatat_oleh"
        " ORDER BY b.periode DESC, b.tanggal_bayar, p.nama"
    ).fetchall()


def hapus_pembayaran(conn: sqlite3.Connection, sesi: Sesi | None, pembayaran_id: int) -> None:
    """Pembatalan salah catat. Hanya Pemilik."""
    _wajib(sesi, "pembayaran_batal")
    if conn.execute("SELECT 1 FROM pembayaran WHERE id = ?", (pembayaran_id,)).fetchone() is None:
        raise KesalahanAplikasi("Data pembayaran tidak ditemukan.")
    conn.execute("DELETE FROM pembayaran WHERE id = ?", (pembayaran_id,))
    conn.commit()


def _validasi_periode(periode: str) -> tuple[int, int]:
    teks = str(periode or "").strip()
    try:
        tahun, bulan = (int(x) for x in teks.split("-"))
    except ValueError:
        raise KesalahanAplikasi("Periode harus berformat YYYY-MM, contoh 2026-11.")
    if not (2000 <= tahun <= 2100 and 1 <= bulan <= 12):
        raise KesalahanAplikasi("Periode tidak valid. Gunakan tahun 2000-2100 dan bulan 1-12.")
    return tahun, bulan


# --------------------------------------------------------------------------- #
# Laporan
# --------------------------------------------------------------------------- #

def laporan_bulanan(conn: sqlite3.Connection, sesi: Sesi | None, periode: str) -> dict:
    _wajib(sesi, "laporan_lihat")
    tahun, bulan = _validasi_periode(periode)
    baris = conn.execute(
        "SELECT p.nama, k.nomor_kamar, p.tarif_sewa, COALESCE(SUM(b.jumlah), 0) AS dibayar,"
        " COUNT(b.id) AS jumlah_transaksi"
        " FROM penghuni p JOIN kamar k ON k.id = p.kamar_id"
        " LEFT JOIN pembayaran b ON b.penghuni_id = p.id AND b.periode = ?"
        " WHERE p.tanggal_masuk <= ?"
        " GROUP BY p.id ORDER BY k.nomor_kamar",
        (periode, f"{tahun:04d}-{bulan:02d}-{_hari_terakhir(tahun, bulan):02d}"),
    ).fetchall()
    rincian = [dict(r) for r in baris]
    total = sum(r["dibayar"] for r in rincian)
    tertagih = sum(r["tarif_sewa"] for r in rincian if r["jumlah_transaksi"] == 0)
    return {
        "periode": f"{tahun:04d}-{bulan:02d}",
        "rincian": rincian,
        "total_masuk": total,
        "jumlah_transaksi": sum(r["jumlah_transaksi"] for r in rincian),
        "belum_bayar": tertagih,
        "jumlah_penunggak": len(daftar_penunggak(conn, sesi, periode)),
    }


def ekspor_laporan_csv(conn: sqlite3.Connection, sesi: Sesi | None, periode: str,
                       path: str) -> str:
    _wajib(sesi, "laporan_lihat")
    laporan = laporan_bulanan(conn, sesi, periode)
    with open(path, "w", newline="", encoding="utf-8") as f:
        tulis = csv.writer(f)
        tulis.writerow(["Periode", laporan["periode"]])
        tulis.writerow(["Kamar", "Nama", "Tarif", "Dibayar", "Transaksi"])
        for r in laporan["rincian"]:
            tulis.writerow([r["nomor_kamar"], r["nama"], r["tarif_sewa"], r["dibayar"],
                            r["jumlah_transaksi"]])
        tulis.writerow([])
        tulis.writerow(["Total pemasukan", laporan["total_masuk"]])
        tulis.writerow(["Belum dibayar", laporan["belum_bayar"]])
        tulis.writerow(["Jumlah penunggak", laporan["jumlah_penunggak"]])
    return path


# --------------------------------------------------------------------------- #
# Pengguna
# --------------------------------------------------------------------------- #

def daftar_pengguna(conn: sqlite3.Connection, sesi: Sesi | None) -> list:
    _wajib(sesi, "pengguna_kelola")
    return conn.execute(
        "SELECT id, username, nama, role, aktif, dibuat_pada FROM users ORDER BY role, username"
    ).fetchall()


def tambah_pengguna(conn: sqlite3.Connection, sesi: Sesi | None, username: str, password: str,
                    nama: str, role: str) -> int:
    _wajib(sesi, "pengguna_kelola")
    username = (username or "").strip()
    nama = (nama or "").strip()
    if not username or not nama:
        raise KesalahanAplikasi("Username dan nama wajib diisi.")
    if len(password or "") < 6:
        raise KesalahanAplikasi("Password minimal 6 karakter.")
    if role not in db.ROLE_SAH:
        raise KesalahanAplikasi("Role hanya pemilik atau penjaga.")
    if conn.execute("SELECT 1 FROM users WHERE username = ? COLLATE NOCASE",
                    (username,)).fetchone() is not None:
        raise KesalahanAplikasi(f"Username {username} sudah dipakai.")
    cur = conn.execute(
        "INSERT INTO users (username, password_hash, nama, role) VALUES (?, ?, ?, ?)",
        (username, db.hash_password(password), nama, role),
    )
    conn.commit()
    return cur.lastrowid


def ubah_pengguna(conn: sqlite3.Connection, sesi: Sesi | None, user_id: int, nama: str,
                  role: str, aktif: bool, password_baru: str = "") -> None:
    _wajib(sesi, "pengguna_kelola")
    lama = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if lama is None:
        raise KesalahanAplikasi("Pengguna tidak ditemukan.")
    if role not in db.ROLE_SAH:
        raise KesalahanAplikasi("Role hanya pemilik atau penjaga.")
    if user_id == sesi.id and (role != "pemilik" or not aktif):
        raise KesalahanAplikasi(
            "Anda tidak dapat menurunkan peran atau menonaktifkan akun sendiri."
        )
    if password_baru:
        if len(password_baru) < 6:
            raise KesalahanAplikasi("Password minimal 6 karakter.")
        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                     (db.hash_password(password_baru), user_id))
    conn.execute(
        "UPDATE users SET nama = ?, role = ?, aktif = ? WHERE id = ?",
        ((nama or "").strip() or lama["nama"], role, 1 if aktif else 0, user_id),
    )
    conn.commit()


def jumlah_pemilik_aktif(conn: sqlite3.Connection) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM users WHERE role = 'pemilik' AND aktif = 1"
    ).fetchone()[0]
