"""Lapisan layanan SI-Kos.

Semua aturan bisnis dan penegakan hak akses berada di sini, bukan di UI.
UI hanya boleh mengatur tampilan; keputusan "boleh atau tidak" diambil di
modul ini agar menyembunyikan tombol tidak pernah menjadi satu-satunya
penjaga.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime

import db

# Hak akses per role. Satu sumber kebenaran, dipakai UI dan layanan.
HAK = {
    "pemilik": {
        "kamar_lihat", "kamar_ubah", "kamar_hapus",
        "penghuni_lihat", "penghuni_ubah", "penghuni_hapus",
        "pembayaran_catat", "pembayaran_batal", "penunggak_lihat",
        "laporan_lihat", "pengguna_kelola",
    },
    "penjaga": {
        "kamar_lihat", "kamar_ubah",
        "penghuni_lihat", "penghuni_ubah",
        "pembayaran_catat", "penunggak_lihat",
    },
}


class KesalahanAplikasi(Exception):
    """Kesalahan yang pesannya layak ditampilkan ke pengguna apa adanya."""


class AksesDitolak(KesalahanAplikasi):
    """Role aktif tidak punya hak untuk aksi ini."""


class BelumLogin(KesalahanAplikasi):
    """Belum ada sesi aktif."""


@dataclass(frozen=True)
class Sesi:
    id: int
    username: str
    nama: str
    role: str

    @property
    def hak(self) -> set[str]:
        return set(HAK[self.role])

    def boleh(self, hak: str) -> bool:
        return hak in self.hak


def _wajib(sesi: Sesi | None, hak: str) -> Sesi:
    if sesi is None:
        raise BelumLogin("Silakan login terlebih dahulu.")
    if not sesi.boleh(hak):
        raise AksesDitolak(f"Role {sesi.role} tidak berhak melakukan aksi ini.")
    return sesi


# --------------------------------------------------------------------------- #
# Login
# --------------------------------------------------------------------------- #

def login(conn: sqlite3.Connection, username: str, password: str) -> Sesi:
    username = (username or "").strip()
    if not username or not password:
        raise KesalahanAplikasi("Username dan password wajib diisi.")
    baris = conn.execute(
        "SELECT id, username, password_hash, nama, role, aktif FROM users"
        " WHERE username = ? COLLATE NOCASE",
        (username,),
    ).fetchone()
    if baris is None or not db.cek_password(password, baris["password_hash"]):
        raise KesalahanAplikasi("Username atau password salah.")
    if not baris["aktif"]:
        raise KesalahanAplikasi("Akun ini tidak aktif. Hubungi pemilik kos.")
    return Sesi(baris["id"], baris["username"], baris["nama"], baris["role"])


# --------------------------------------------------------------------------- #
# Kamar
# --------------------------------------------------------------------------- #

def daftar_kamar(conn: sqlite3.Connection, sesi: Sesi | None, cari: str = "") -> list[sqlite3.Row]:
    _wajib(sesi, "kamar_lihat")
    cari = (cari or "").strip()
    sql = (
        "SELECT k.*, (SELECT p.nama FROM penghuni p"
        " WHERE p.kamar_id = k.id AND p.status = 'aktif') AS penghuni_aktif"
        " FROM kamar k"
    )
    if cari:
        sql += " WHERE k.nomor_kamar LIKE ?"
        return conn.execute(sql + " ORDER BY k.nomor_kamar", (f"%{cari}%",)).fetchall()
    return conn.execute(sql + " ORDER BY k.nomor_kamar").fetchall()


def _validasi_kamar(conn: sqlite3.Connection, nomor: str, harga, kunci_id: int | None) -> tuple[str, int]:
    nomor = str(nomor or "").strip()
    if not nomor:
        raise KesalahanAplikasi("Nomor kamar wajib diisi.")
    try:
        harga = int(harga)
    except (TypeError, ValueError):
        raise KesalahanAplikasi("Harga sewa harus berupa angka.")
    if harga < 0:
        raise KesalahanAplikasi("Harga sewa tidak boleh negatif.")
    baris = conn.execute(
        "SELECT id FROM kamar WHERE nomor_kamar = ? AND id IS NOT ?", (nomor, kunci_id)
    ).fetchone()
    if baris is not None:
        raise KesalahanAplikasi(f"Nomor kamar {nomor} sudah dipakai. Gunakan nomor lain.")
    return nomor, harga


def tambah_kamar(conn: sqlite3.Connection, sesi: Sesi | None, nomor, harga,
                 fasilitas: str = "", keterangan: str = "") -> int:
    _wajib(sesi, "kamar_ubah")
    nomor, harga = _validasi_kamar(conn, nomor, harga, None)
    cur = conn.execute(
        "INSERT INTO kamar (nomor_kamar, harga_sewa, status_pakai, fasilitas, keterangan)"
        " VALUES (?, ?, 'kosong', ?, ?)",
        (nomor, harga, (fasilitas or "").strip(), (keterangan or "").strip()),
    )
    conn.commit()
    return cur.lastrowid


def ubah_kamar(conn: sqlite3.Connection, sesi: Sesi | None, kamar_id: int, nomor, harga,
               fasilitas: str = "", keterangan: str = "") -> None:
    _wajib(sesi, "kamar_ubah")
    if conn.execute("SELECT 1 FROM kamar WHERE id = ?", (kamar_id,)).fetchone() is None:
        raise KesalahanAplikasi("Kamar tidak ditemukan.")
    nomor, harga = _validasi_kamar(conn, nomor, harga, kamar_id)
    conn.execute(
        "UPDATE kamar SET nomor_kamar = ?, harga_sewa = ?, fasilitas = ?,"
        " keterangan = ? WHERE id = ?",
        (nomor, harga, (fasilitas or "").strip(), (keterangan or "").strip(), kamar_id),
    )
    conn.commit()


def hapus_kamar(conn: sqlite3.Connection, sesi: Sesi | None, kamar_id: int) -> None:
    _wajib(sesi, "kamar_hapus")
    if conn.execute("SELECT 1 FROM kamar WHERE id = ?", (kamar_id,)).fetchone() is None:
        raise KesalahanAplikasi("Kamar tidak ditemukan.")
    jumlah_aktif = conn.execute(
        "SELECT COUNT(*) FROM penghuni WHERE kamar_id = ? AND status = 'aktif'", (kamar_id,)
    ).fetchone()[0]
    if jumlah_aktif:
        raise KesalahanAplikasi(
            "Kamar masih dihuni. Keluarkan atau pindahkan penghuninya lebih dulu."
        )
    jumlah_riwayat = conn.execute(
        "SELECT COUNT(*) FROM penghuni WHERE kamar_id = ?", (kamar_id,)
    ).fetchone()[0]
    if jumlah_riwayat:
        raise KesalahanAplikasi(
            "Kamar ini punya riwayat penghuni sehingga tidak dihapus agar data pembayaran"
            " lama tetap utuh. Tandai kamar sebagai tidak dipakai lewat keterangan."
        )
    conn.execute("DELETE FROM kamar WHERE id = ?", (kamar_id,))
    conn.commit()


def _sinkron_status_kamar(conn: sqlite3.Connection, kamar_id: int) -> None:
    ada_aktif = conn.execute(
        "SELECT 1 FROM penghuni WHERE kamar_id = ? AND status = 'aktif'", (kamar_id,)
    ).fetchone()
    conn.execute(
        "UPDATE kamar SET status_pakai = ? WHERE id = ?",
        ("terisi" if ada_aktif else "kosong", kamar_id),
    )


# --------------------------------------------------------------------------- #
# Penghuni
# --------------------------------------------------------------------------- #

def daftar_penghuni(conn: sqlite3.Connection, sesi: Sesi | None, cari: str = "",
                    hanya_aktif: bool = False) -> list[sqlite3.Row]:
    _wajib(sesi, "penghuni_lihat")
    syarat, nilai = [], []
    cari = (cari or "").strip()
    if cari:
        syarat.append("(p.nama LIKE ? OR k.nomor_kamar LIKE ?)")
        nilai += [f"%{cari}%", f"%{cari}%"]
    if hanya_aktif:
        syarat.append("p.status = 'aktif'")
    sql = (
        "SELECT p.*, k.nomor_kamar FROM penghuni p JOIN kamar k ON k.id = p.kamar_id"
        + (" WHERE " + " AND ".join(syarat) if syarat else "")
        + " ORDER BY p.status = 'keluar', p.nama"
    )
    return conn.execute(sql, nilai).fetchall()


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


def _validasi_penghuni(conn, nama, kamar_id, tanggal_masuk, tarif, kunci_id=None) -> dict:
    nama = (nama or "").strip()
    if not nama:
        raise KesalahanAplikasi("Nama penghuni wajib diisi.")
    if conn.execute("SELECT 1 FROM kamar WHERE id = ?", (kamar_id,)).fetchone() is None:
        raise KesalahanAplikasi("Kamar yang dipilih tidak ditemukan.")
    try:
        tarif = int(tarif)
    except (TypeError, ValueError):
        raise KesalahanAplikasi("Tarif sewa harus berupa angka.")
    if tarif < 0:
        raise KesalahanAplikasi("Tarif sewa tidak boleh negatif.")
    masuk = _parse_tanggal(tanggal_masuk, "Tanggal masuk")
    if masuk > date.today():
        raise KesalahanAplikasi("Tanggal masuk tidak boleh di masa depan.")
    bentrok = conn.execute(
        "SELECT p.nama FROM penghuni p WHERE p.kamar_id = ? AND p.status = 'aktif'"
        " AND p.id IS NOT ?",
        (kamar_id, kunci_id),
    ).fetchone()
    if bentrok is not None:
        raise KesalahanAplikasi(
            f"Kamar ini sudah ditempati {bentrok['nama']}. Kosongkan dulu sebelum menambah penghuni."
        )
    return {"nama": nama, "tarif": tarif, "masuk": masuk}


def tambah_penghuni(conn: sqlite3.Connection, sesi: Sesi | None, nama, no_hp, kamar_id,
                    tanggal_masuk, tarif) -> int:
    _wajib(sesi, "penghuni_ubah")
    data = _validasi_penghuni(conn, nama, kamar_id, tanggal_masuk, tarif)
    cur = conn.execute(
        "INSERT INTO penghuni (nama, no_hp, kamar_id, tanggal_masuk, tarif_sewa, status)"
        " VALUES (?, ?, ?, ?, ?, 'aktif')",
        (data["nama"], (no_hp or "").strip(), kamar_id, data["masuk"].isoformat(), data["tarif"]),
    )
    _sinkron_status_kamar(conn, kamar_id)
    conn.commit()
    return cur.lastrowid


def ubah_penghuni(conn: sqlite3.Connection, sesi: Sesi | None, penghuni_id: int, nama, no_hp,
                  kamar_id, tanggal_masuk, tarif) -> None:
    _wajib(sesi, "penghuni_ubah")
    lama = conn.execute("SELECT * FROM penghuni WHERE id = ?", (penghuni_id,)).fetchone()
    if lama is None:
        raise KesalahanAplikasi("Penghuni tidak ditemukan.")
    if lama["status"] == "keluar":
        raise KesalahanAplikasi("Penghuni ini sudah keluar dan datanya tidak diubah lagi.")
    data = _validasi_penghuni(conn, nama, kamar_id, tanggal_masuk, tarif, kunci_id=penghuni_id)
    conn.execute(
        "UPDATE penghuni SET nama = ?, no_hp = ?, kamar_id = ?, tanggal_masuk = ?,"
        " tarif_sewa = ? WHERE id = ?",
        (data["nama"], (no_hp or "").strip(), kamar_id, data["masuk"].isoformat(),
         data["tarif"], penghuni_id),
    )
    _sinkron_status_kamar(conn, lama["kamar_id"])
    _sinkron_status_kamar(conn, kamar_id)
    conn.commit()


def keluar_penghuni(conn: sqlite3.Connection, sesi: Sesi | None, penghuni_id: int,
                    tanggal_keluar=None) -> None:
    _wajib(sesi, "penghuni_ubah")
    lama = conn.execute("SELECT * FROM penghuni WHERE id = ?", (penghuni_id,)).fetchone()
    if lama is None:
        raise KesalahanAplikasi("Penghuni tidak ditemukan.")
    if lama["status"] == "keluar":
        raise KesalahanAplikasi("Penghuni ini sudah tercatat keluar.")
    keluar = _parse_tanggal(tanggal_keluar or date.today(), "Tanggal keluar")
    masuk = date.fromisoformat(lama["tanggal_masuk"])
    if keluar < masuk:
        raise KesalahanAplikasi("Tanggal keluar tidak boleh sebelum tanggal masuk.")
    conn.execute(
        "UPDATE penghuni SET status = 'keluar', tanggal_keluar = ? WHERE id = ?",
        (keluar.isoformat(), penghuni_id),
    )
    _sinkron_status_kamar(conn, lama["kamar_id"])
    conn.commit()


def hapus_penghuni(conn: sqlite3.Connection, sesi: Sesi | None, penghuni_id: int) -> None:
    _wajib(sesi, "penghuni_hapus")
    lama = conn.execute("SELECT * FROM penghuni WHERE id = ?", (penghuni_id,)).fetchone()
    if lama is None:
        raise KesalahanAplikasi("Penghuni tidak ditemukan.")
    if conn.execute(
        "SELECT 1 FROM pembayaran WHERE penghuni_id = ?", (penghuni_id,)
    ).fetchone() is not None:
        raise KesalahanAplikasi(
            "Penghuni ini punya riwayat pembayaran sehingga tidak dihapus. Gunakan"
            " tombol Tandai keluar agar riwayat keuangan tetap utuh."
        )
    conn.execute("DELETE FROM penghuni WHERE id = ?", (penghuni_id,))
    _sinkron_status_kamar(conn, lama["kamar_id"])
    conn.commit()


# --------------------------------------------------------------------------- #
# Jatuh tempo & penunggak
# --------------------------------------------------------------------------- #

def tanggal_jatuh_tempo(tanggal_masuk: str, periode: str) -> date:
    """Jatuh tempo bulan tertentu mengikuti tanggal masuk.

    Tanggal 29/30/31 dipadatkan ke hari terakhir bulan itu supaya tidak
    melewati batas (Feb 31 tidak ada).
    """
    tahun, bulan = (int(x) for x in periode.split("-"))
    masuk = date.fromisoformat(tanggal_masuk)
    hari_terakhir = _hari_terakhir(tahun, bulan)
    return date(tahun, bulan, min(masuk.day, hari_terakhir))


def _hari_terakhir(tahun: int, bulan: int) -> int:
    if bulan == 12:
        return 31
    return (date(tahun, bulan + 1, 1) - date(tahun, bulan, 1)).days


def daftar_penunggak(conn: sqlite3.Connection, sesi: Sesi | None, periode: str) -> list[dict]:
    _wajib(sesi, "penunggak_lihat")
    _validasi_periode(periode)
    tahun, bulan = (int(x) for x in periode.split("-"))
    awal = date(tahun, bulan, 1)
    akhir = date(tahun, bulan, _hari_terakhir(tahun, bulan))
    baris = conn.execute(
        "SELECT p.id, p.nama, p.no_hp, p.tarif_sewa, p.tanggal_masuk, p.status,"
        " p.tanggal_keluar, k.nomor_kamar,"
        " (SELECT COALESCE(SUM(b.jumlah), 0) FROM pembayaran b"
        "   WHERE b.penghuni_id = p.id AND b.periode = ?) AS dibayar"
        " FROM penghuni p JOIN kamar k ON k.id = p.kamar_id"
        " ORDER BY k.nomor_kamar",
        (periode,),
    ).fetchall()
    hasil = []
    for r in baris:
        masuk = date.fromisoformat(r["tanggal_masuk"])
        if masuk > akhir:
            continue  # belum menempati kamar pada periode ini
        if r["status"] == "keluar" and r["tanggal_keluar"]:
            if date.fromisoformat(r["tanggal_keluar"]) < awal:
                continue  # sudah keluar sebelum periode ini mulai
        dibayar = r["dibayar"]
        if dibayar >= r["tarif_sewa"] and dibayar > 0:
            continue
        hasil.append({
            "id": r["id"], "nama": r["nama"], "no_hp": r["no_hp"],
            "nomor_kamar": r["nomor_kamar"], "tarif": r["tarif_sewa"],
            "dibayar": dibayar,
            "kurang": max(r["tarif_sewa"] - dibayar, 0),
            "jatuh_tempo": tanggal_jatuh_tempo(r["tanggal_masuk"], periode).isoformat(),
            "status": "belum bayar" if dibayar == 0 else "kurang bayar",
        })
    return hasil


def _validasi_periode(periode: str) -> tuple[int, int]:
    teks = str(periode or "").strip()
    try:
        tahun, bulan = (int(x) for x in teks.split("-"))
    except ValueError:
        raise KesalahanAplikasi("Periode harus berformat YYYY-MM, contoh 2026-11.")
    if not (2000 <= tahun <= 2100 and 1 <= bulan <= 12):
        raise KesalahanAplikasi("Periode tidak valid. Gunakan tahun 2000-2100 dan bulan 1-12.")
    return tahun, bulan
