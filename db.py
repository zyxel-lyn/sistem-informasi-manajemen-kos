"""Lapisan database SI-Kos: koneksi, skema, dan seed data demo.

Aturan yang ditegakkan di sini adalah aturan data (skema): unique, foreign key,
dan nilai status yang sah. Aturan bisnis (hak akses, hapus bersyarat) ada di
services.py.
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
from datetime import date, timedelta

DB_FILENAME = "sikos.db"

# Status yang sah. Dipakai juga oleh services.py agar tidak ada dua daftar.
STATUS_KAMAR = ("kosong", "terisi")
STATUS_PENGHUNI = ("aktif", "keluar")
ROLE_SAH = ("pemilik", "penjaga")
METODE_BAYAR = ("tunai", "transfer")

SKEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT    NOT NULL,
    nama          TEXT    NOT NULL,
    role          TEXT    NOT NULL CHECK (role IN ('pemilik', 'penjaga')),
    aktif         INTEGER NOT NULL DEFAULT 1 CHECK (aktif IN (0, 1)),
    dibuat_pada   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS kamar (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nomor_kamar TEXT    NOT NULL UNIQUE,
    harga_sewa  INTEGER NOT NULL CHECK (harga_sewa >= 0),
    status_pakai TEXT   NOT NULL DEFAULT 'kosong'
                        CHECK (status_pakai IN ('kosong', 'terisi')),
    fasilitas   TEXT    NOT NULL DEFAULT '',
    keterangan  TEXT    NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS penghuni (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    nama           TEXT    NOT NULL,
    no_hp          TEXT    NOT NULL DEFAULT '',
    kamar_id       INTEGER NOT NULL REFERENCES kamar(id) ON DELETE RESTRICT,
    tanggal_masuk  TEXT    NOT NULL,
    tanggal_keluar TEXT,
    tarif_sewa     INTEGER NOT NULL CHECK (tarif_sewa >= 0),
    status         TEXT    NOT NULL DEFAULT 'aktif'
                           CHECK (status IN ('aktif', 'keluar')),
    CHECK (tanggal_keluar IS NULL OR tanggal_keluar >= tanggal_masuk)
);

CREATE TABLE IF NOT EXISTS pembayaran (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    penghuni_id  INTEGER NOT NULL REFERENCES penghuni(id) ON DELETE RESTRICT,
    periode      TEXT    NOT NULL CHECK (periode GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]'),
    tanggal_bayar TEXT   NOT NULL,
    jumlah       INTEGER NOT NULL CHECK (jumlah > 0),
    metode       TEXT    NOT NULL DEFAULT 'tunai'
                         CHECK (metode IN ('tunai', 'transfer')),
    catatan      TEXT    NOT NULL DEFAULT '',
    dicatat_oleh INTEGER REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE (penghuni_id, periode)
);

CREATE INDEX IF NOT EXISTS idx_penghuni_kamar ON penghuni(kamar_id);
CREATE INDEX IF NOT EXISTS idx_pembayaran_periode ON pembayaran(periode);

-- Satu kamar hanya boleh punya satu penghuni aktif.
CREATE UNIQUE INDEX IF NOT EXISTS idx_satu_penghuni_aktif
    ON penghuni(kamar_id) WHERE status = 'aktif';
"""


def hash_password(password: str, salt: str | None = None) -> str:
    """Hash PBKDF2-SHA256 dengan salt acak. Format: pbkdf2$<salt>$<hash>."""
    if salt is None:
        salt = os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return f"pbkdf2${salt}${digest.hex()}"


def cek_password(password: str, tersimpan: str) -> bool:
    try:
        algo, salt, _ = tersimpan.split("$", 2)
    except ValueError:
        return False
    if algo != "pbkdf2":
        return False
    return hash_password(password, salt) == tersimpan


def path_db(folder: str | None = None) -> str:
    folder = folder or os.path.dirname(os.path.abspath(__file__))
    return os.path.join(folder, DB_FILENAME)


def koneksi(path: str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or path_db(), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def buat_skema(conn: sqlite3.Connection) -> None:
    conn.executescript(SKEMA)
    conn.commit()


def _periode(tanggal: date) -> str:
    return f"{tanggal.year:04d}-{tanggal.month:02d}"


def _bulan_mundur(acuan: date, n: int) -> date:
    bulan = acuan.month - n
    tahun = acuan.year
    while bulan <= 0:
        bulan += 12
        tahun -= 1
    return date(tahun, bulan, 1)


def isi_seed(conn: sqlite3.Connection, acuan: date | None = None) -> bool:
    """Isi data demo sekali saja. Mengembalikan False bila database sudah berisi."""
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
        return False

    acuan = acuan or date.today()
    conn.executemany(
        "INSERT INTO users (username, password_hash, nama, role) VALUES (?, ?, ?, ?)",
        [
            ("pemilik", hash_password("pemilik123"), "Pak Salman", "pemilik"),
            ("penjaga", hash_password("penjaga123"), "Kak Ridho", "penjaga"),
        ],
    )

    kamar = [
        ("01", 750_000, "kosong", "Kasur, lemari, kipas", "Lantai 1"),
        ("02", 750_000, "terisi", "Kasur, lemari, kipas", "Lantai 1"),
        ("03", 850_000, "terisi", "Kasur, lemari, AC", "Lantai 1"),
        ("04", 850_000, "kosong", "Kasur, lemari, AC", "Lantai 2"),
        ("05", 900_000, "terisi", "Kasur, lemari, AC, kamar mandi dalam", "Lantai 2"),
        ("06", 900_000, "kosong", "Kasur, lemari, AC, kamar mandi dalam", "Lantai 2"),
        ("07", 650_000, "terisi", "Kasur, lemari, kipas", "Lantai 3"),
        ("08", 650_000, "kosong", "Kasur, lemari, kipas", "Lantai 3"),
    ]
    conn.executemany(
        "INSERT INTO kamar (nomor_kamar, harga_sewa, status_pakai, fasilitas, keterangan)"
        " VALUES (?, ?, ?, ?, ?)",
        kamar,
    )

    # (nama, no_hp, nomor kamar, bulan masuk yang lalu, tarif)
    penghuni = [
        ("Andi Pratama", "0812-1111-2222", "02", 4, 750_000),
        ("Siti Rahma", "0813-3333-4444", "03", 2, 850_000),
        ("Bayu Nugroho", "0814-5555-6666", "05", 3, 900_000),
        ("Nadia Putri", "0815-7777-8888", "07", 1, 650_000),
        ("Rizky Ananda", "0816-9999-0000", "02", 5, 750_000),  # sudah keluar
    ]
    for nama, hp, nomor, masuk_mundur, tarif in penghuni:
        kamar_id = conn.execute("SELECT id FROM kamar WHERE nomor_kamar = ?", (nomor,)).fetchone()[0]
        tgl_masuk = _bulan_mundur(acuan, masuk_mundur).replace(day=min(acuan.day, 28))
        keluar = None
        status = "aktif"
        if nama == "Rizky Ananda":
            keluar = (_bulan_mundur(acuan, 1).replace(day=10)).isoformat()
            status = "keluar"
        conn.execute(
            "INSERT INTO penghuni (nama, no_hp, kamar_id, tanggal_masuk, tanggal_keluar,"
            " tarif_sewa, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (nama, hp, kamar_id, tgl_masuk.isoformat(), keluar, tarif, status),
        )

    penjaga_id = conn.execute("SELECT id FROM users WHERE role = 'penjaga'").fetchone()[0]
    aktif = conn.execute("SELECT id, tarif_sewa, tanggal_masuk FROM penghuni WHERE status = 'aktif'").fetchall()
    for row in aktif:
        # Bayar dua bulan terakhir; bulan berjalan sengaja dibiarkan belum bayar
        # agar layar penunggak punya isi saat demo.
        for mundur in (2, 1):
            conn.execute(
                "INSERT INTO pembayaran (penghuni_id, periode, tanggal_bayar, jumlah, metode,"
                " catatan, dicatat_oleh) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    row["id"],
                    _periode(_bulan_mundur(acuan, mundur)),
                    _bulan_mundur(acuan, mundur).replace(day=5).isoformat(),
                    row["tarif_sewa"],
                    "transfer",
                    "Sewa bulanan",
                    penjaga_id,
                ),
            )

    conn.commit()
    return True


def siapkan_database(path: str | None = None, seed: bool = True) -> sqlite3.Connection:
    conn = koneksi(path)
    buat_skema(conn)
    if seed:
        isi_seed(conn)
    return conn


if __name__ == "__main__":
    conn = siapkan_database()
    print("Database siap:", path_db())
    for tabel in ("users", "kamar", "penghuni", "pembayaran"):
        jumlah = conn.execute(f"SELECT COUNT(*) FROM {tabel}").fetchone()[0]
        print(f"  {tabel:<11} {jumlah} baris")
