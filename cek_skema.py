"""Cek skema database SI-Kos: struktur tabel, unique, foreign key, CHECK, dan seed.

Dijalankan dengan: python cek_skema.py
Memakai database sementara di folder temp, TIDAK menyentuh sikos.db milik aplikasi.
"""

from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import db  # noqa: E402

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


def main() -> int:
    folder = tempfile.mkdtemp(prefix="sikos_cek_")
    path = os.path.join(folder, "uji.db")
    conn = db.siapkan_database(path)
    print(f"Database uji: {path}\n")

    print("[1] Struktur tabel")
    tabel = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for nama in ("users", "kamar", "penghuni", "pembayaran"):
        cek(f"tabel {nama} ada", nama in tabel)
    indeks = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='index'")}
    cek("index unik satu penghuni aktif ada", "idx_satu_penghuni_aktif" in indeks)
    cek("index periode pembayaran ada", "idx_pembayaran_periode" in indeks)

    print("\n[2] Foreign key aktif")
    fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    cek("PRAGMA foreign_keys = ON", fk == 1, f"nilai={fk}")

    print("\n[3] Unique constraint (harus ditolak)")
    try:
        conn.execute(
            "INSERT INTO kamar (nomor_kamar, harga_sewa) VALUES (?, ?)", ("01", 750_000)
        )
        cek("nomor kamar dobel ditolak", False, "insert berhasil padahal seharusnya gagal")
    except sqlite3.IntegrityError as e:
        cek("nomor kamar dobel ditolak", True, str(e))

    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, nama, role)"
            " VALUES ('PEMILIK', 'x', 'Dobel', 'pemilik')"
        )
        cek("username dobel (beda kapital) ditolak", False, "insert berhasil")
    except sqlite3.IntegrityError as e:
        cek("username dobel (beda kapital) ditolak", True, str(e))

    print("\n[4] Satu kamar satu penghuni aktif")
    kamar_id = conn.execute("SELECT id FROM kamar WHERE nomor_kamar='01'").fetchone()[0]
    conn.execute(
        "INSERT INTO penghuni (nama, kamar_id, tanggal_masuk, tarif_sewa)"
        " VALUES ('Uji A', ?, '2026-01-05', 750000)",
        (kamar_id,),
    )
    try:
        conn.execute(
            "INSERT INTO penghuni (nama, kamar_id, tanggal_masuk, tarif_sewa)"
            " VALUES ('Uji B', ?, '2026-02-05', 750000)",
            (kamar_id,),
        )
        cek("penghuni aktif kedua di kamar sama ditolak", False, "insert berhasil")
    except sqlite3.IntegrityError as e:
        cek("penghuni aktif kedua di kamar sama ditolak", True, str(e))

    print("\n[5] CHECK constraint (harus ditolak)")
    kasus = [
        ("role di luar daftar", "INSERT INTO users (username, password_hash, nama, role)"
                               " VALUES ('x1', 'h', 'X', 'tamu')"),
        ("harga sewa negatif", "INSERT INTO kamar (nomor_kamar, harga_sewa) VALUES ('99', -1)"),
        ("periode bukan YYYY-MM", "INSERT INTO pembayaran (penghuni_id, periode, tanggal_bayar,"
                                  " jumlah) VALUES (1, '2026-1', '2026-01-05', 1000)"),
        ("jumlah bayar nol", "INSERT INTO pembayaran (penghuni_id, periode, tanggal_bayar,"
                            " jumlah) VALUES (1, '2026-09', '2026-09-05', 0)"),
        ("tanggal keluar sebelum masuk", "INSERT INTO penghuni (nama, kamar_id, tanggal_masuk,"
                                         " tanggal_keluar, tarif_sewa) VALUES ('Uji C', 2,"
                                         " '2026-05-10', '2026-05-01', 700000)"),
    ]
    for nama, sql in kasus:
        try:
            conn.execute(sql)
            cek(f"{nama} ditolak", False, "berhasil, seharusnya gagal")
        except sqlite3.IntegrityError as e:
            cek(f"{nama} ditolak", True, str(e))

    print("\n[6] Foreign key menolak referensi yatim")
    try:
        conn.execute(
            "INSERT INTO penghuni (nama, kamar_id, tanggal_masuk, tarif_sewa)"
            " VALUES ('Uji D', 9999, '2026-01-05', 500000)"
        )
        cek("kamar_id tidak ada ditolak", False, "insert berhasil")
    except sqlite3.IntegrityError as e:
        cek("kamar_id tidak ada ditolak", True, str(e))

    print("\n[7] Pembayaran dobel per periode ditolak")
    pid = conn.execute("SELECT id FROM penghuni WHERE status='aktif' LIMIT 1").fetchone()[0]
    conn.execute(
        "INSERT INTO pembayaran (penghuni_id, periode, tanggal_bayar, jumlah)"
        " VALUES (?, '2030-01', '2030-01-05', 750000)",
        (pid,),
    )
    try:
        conn.execute(
            "INSERT INTO pembayaran (penghuni_id, periode, tanggal_bayar, jumlah)"
            " VALUES (?, '2030-01', '2030-01-20', 750000)",
            (pid,),
        )
        cek("pembayaran periode sama ditolak", False, "insert berhasil")
    except sqlite3.IntegrityError as e:
        cek("pembayaran periode sama ditolak", True, str(e))

    print("\n[8] Hapus kamar yang masih punya penghuni ditolak (ON DELETE RESTRICT)")
    try:
        conn.execute("DELETE FROM kamar WHERE id = ?", (kamar_id,))
        cek("hapus kamar berpenghuni ditolak", False, "delete berhasil")
    except sqlite3.IntegrityError as e:
        cek("hapus kamar berpenghuni ditolak", True, str(e))

    print("\n[9] Hash password")
    hash1 = db.hash_password("rahasia")
    cek("format hash pbkdf2$salt$hash", hash1.startswith("pbkdf2$") and hash1.count("$") == 2)
    cek("password benar diterima", db.cek_password("rahasia", hash1))
    cek("password salah ditolak", not db.cek_password("salah", hash1))
    cek("salt berbeda tiap hash", db.hash_password("rahasia") != hash1)
    cek("tidak ada password plain text di database",
        conn.execute("SELECT COUNT(*) FROM users WHERE password_hash IN"
                     " ('pemilik123','penjaga123')").fetchone()[0] == 0)

    print("\n[10] Isi data demo (seed)")
    # Seed diperiksa dari database bersih yang terpisah, supaya baris uji di atas
    # tidak mengacaukan hitungan.
    path_seed = os.path.join(folder, "seed.db")
    conn_seed = db.siapkan_database(path_seed)
    users = conn_seed.execute("SELECT username, role, aktif FROM users ORDER BY username").fetchall()
    cek("2 akun demo", len(users) == 2, str([tuple(u) for u in users]))
    cek("ada role pemilik dan penjaga", {u["role"] for u in users} == {"pemilik", "penjaga"})
    jumlah_kamar = conn_seed.execute("SELECT COUNT(*) FROM kamar").fetchone()[0]
    cek("8 kamar demo", jumlah_kamar == 8, f"{jumlah_kamar} kamar")
    aktif = conn_seed.execute("SELECT COUNT(*) FROM penghuni WHERE status='aktif'").fetchone()[0]
    keluar = conn_seed.execute("SELECT COUNT(*) FROM penghuni WHERE status='keluar'").fetchone()[0]
    cek("4 penghuni aktif + 1 keluar", (aktif, keluar) == (4, 1), f"aktif={aktif}, keluar={keluar}")
    yatim = conn_seed.execute(
        "SELECT COUNT(*) FROM kamar k WHERE k.status_pakai='terisi'"
        " AND NOT EXISTS (SELECT 1 FROM penghuni p WHERE p.kamar_id=k.id AND p.status='aktif')"
    ).fetchone()[0]
    cek("tidak ada kamar 'terisi' tanpa penghuni aktif", yatim == 0, f"temuan={yatim}")
    dua_penghuni = conn_seed.execute(
        "SELECT COUNT(*) FROM (SELECT kamar_id FROM penghuni WHERE status='aktif'"
        " GROUP BY kamar_id HAVING COUNT(*) > 1)"
    ).fetchone()[0]
    cek("tidak ada kamar dengan dua penghuni aktif", dua_penghuni == 0, f"temuan={dua_penghuni}")

    lagi = db.isi_seed(conn_seed, acuan=date.today())
    cek("seed idempoten (tidak dobel saat dijalankan ulang)", lagi is False)
    conn_seed.close()

    print("\n" + "=" * 46)
    print(f"HASIL: {lulus} PASS, {gagal} FAIL")
    print("=" * 46)
    conn.close()
    return 0 if gagal == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
