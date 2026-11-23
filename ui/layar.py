"""Tujuh layar kerja SI-Kos.

Setiap layar memanggil lapisan layanan; layar tidak pernah memutuskan sendiri
apakah sebuah aksi boleh dilakukan, hanya menanyakan sesi.
"""

from __future__ import annotations

import tkinter as tk
from datetime import date
from tkinter import filedialog, ttk

import services as sv
import services_lanjutan as sl

from . import tema
from .komponen import BilahAksi, Tabel, field, field_pilihan, nilai_pilihan


def rupiah(nilai) -> str:
    return "Rp" + f"{int(nilai or 0):,}".replace(",", ".")


def periode_sekarang() -> str:
    hari = date.today()
    return f"{hari.year:04d}-{hari.month:02d}"


def pilihan_periode(jumlah: int = 15) -> list[tuple[str, str]]:
    """Daftar periode enam bulan ke belakang sampai delapan bulan ke depan."""
    hari = date.today()
    hasil = []
    for selisih in range(-6, 9):
        bulan = hari.month + selisih
        tahun = hari.year
        while bulan <= 0:
            bulan += 12
            tahun -= 1
        while bulan > 12:
            bulan -= 12
            tahun += 1
        kunci = f"{tahun:04d}-{bulan:02d}"
        nama = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
                "Agustus", "September", "Oktober", "November", "Desember"][bulan - 1]
        hasil.append((kunci, f"{nama} {tahun}"))
    return hasil[:jumlah]


class LayarDasar(ttk.Frame):
    judul = "Layar"

    def __init__(self, induk, app):
        super().__init__(induk, style="Latar.TFrame")
        self.app = app
        self.conn = app.conn
        self.sesi = app.sesi
        self.kepala = ttk.Frame(self, style="Latar.TFrame")
        self.kepala.pack(fill="x")
        ttk.Label(self.kepala, text=self.judul, style="Judul.TLabel").pack(side="left")
        self.keterangan = ttk.Label(self.kepala, text="", style="Keterangan.TLabel")
        self.keterangan.pack(side="left", padx=(12, 0), pady=(6, 0))
        self.badan = ttk.Frame(self, style="Kartu.TFrame", padding=16)
        self.badan.pack(fill="both", expand=True, pady=(12, 0))

    def muat(self) -> None:
        raise NotImplementedError


class LayarDashboard(LayarDasar):
    judul = "Ringkasan"

    def __init__(self, induk, app):
        super().__init__(induk, app)
        self.barisan = ttk.Frame(self.badan, style="Kartu.TFrame")
        self.barisan.pack(fill="x")
        self.kartu: dict[str, tuple[ttk.Label, ttk.Label]] = {}
        for kunci, label in (("okupansi", "Kamar terisi"),
                             ("penghuni", "Penghuni aktif"),
                             ("pemasukan", "Pemasukan bulan ini"),
                             ("penunggak", "Belum bayar bulan ini")):
            kotak = ttk.Frame(self.barisan, style="Kartu.TFrame", padding=(0, 0, 24, 0))
            kotak.pack(side="left", anchor="n")
            angka = ttk.Label(kotak, text="-", style="Angka.TLabel")
            angka.pack(anchor="w")
            ttk.Label(kotak, text=label, style="AngkaLembut.TLabel").pack(anchor="w")
            self.kartu[kunci] = (angka, kotak)

        ttk.Separator(self.badan, orient="horizontal").pack(fill="x", pady=16)
        ttk.Label(self.badan, text="Yang perlu ditindaklanjuti bulan ini",
                  background=tema.LATAR, font=(tema.HURUF, 11, "bold")).pack(anchor="w")
        self.tabel = Tabel(self.badan, [
            ("kamar", "Kamar", 90), ("nama", "Penghuni", 200), ("tarif", "Sewa", 120),
            ("dibayar", "Sudah dibayar", 130), ("jatuh", "Jatuh tempo", 120),
            ("status", "Status", 130),
        ], tinggi=7)
        self.tabel.pack(fill="both", expand=True, pady=(10, 0))
        self.muat()

    def muat(self) -> None:
        semua_kamar = self.app.panggil(sv.daftar_kamar, self.conn, self.sesi) or []
        terisi = [k for k in semua_kamar if k["status_pakai"] == "terisi"]
        aktif = self.app.panggil(sv.daftar_penghuni, self.conn, self.sesi, "", True) or []
        periode = periode_sekarang()
        self.kartu["okupansi"][0].configure(
            text=f"{len(terisi)} dari {len(semua_kamar)}")
        self.kartu["penghuni"][0].configure(text=str(len(aktif)))
        self.kartu["penunggak"][0].configure(
            text=str(len(self.app.panggil(sv.daftar_penunggak, self.conn, self.sesi,
                                          periode) or [])))
        if self.sesi.boleh("laporan_lihat"):
            lap = self.app.panggil(sl.laporan_bulanan, self.conn, self.sesi, periode) or {}
            self.kartu["pemasukan"][0].configure(text=rupiah(lap.get("total_masuk", 0)))
        else:
            angka, kotak = self.kartu["pemasukan"]
            angka.configure(text="Hanya pemilik")
            angka.configure(font=(tema.HURUF, 12, "bold"), foreground=tema.TEKS_LEMBUT)

        baris = []
        for u in self.app.panggil(sv.daftar_penunggak, self.conn, self.sesi, periode) or []:
            tag = "bahaya" if u["status"] == "belum bayar" else "peringatan"
            baris.append((
                (u["nomor_kamar"], u["nama"], rupiah(u["tarif"]), rupiah(u["dibayar"]),
                 u["jatuh_tempo"], u["status"].capitalize()), tag))
        self.tabel.isi(baris,
                       "Semua penghuni aktif sudah membayar untuk bulan ini.")


class LayarKamar(LayarDasar):
    judul = "Data kamar"

    def __init__(self, induk, app):
        super().__init__(induk, app)
        self.data: list = []

        baris_cari = ttk.Frame(self.badan, style="Kartu.TFrame")
        baris_cari.pack(fill="x", pady=(0, 10))
        ttk.Label(baris_cari, text="Cari nomor kamar", style="Lembut.TLabel").pack(side="left")
        self.cari = tk.Entry(baris_cari, relief="solid", bd=1, highlightthickness=2,
                             highlightbackground=tema.LATAR, highlightcolor=tema.AKSEN, width=18)
        self.cari.pack(side="left", padx=(8, 8), ipady=3)
        self.cari.bind("<KeyRelease>", lambda e: self.muat())
        ttk.Button(baris_cari, text="Bersihkan", command=self.bersihkan_cari).pack(side="left")

        self.aksi = BilahAksi(self.badan, "Daftar kamar",
                              "Kamar bertanda terisi tidak dapat dihapus.")
        self.aksi.pack(fill="x", pady=(0, 10))
        if self.sesi.boleh("kamar_ubah"):
            self.aksi.tombol("Tambah kamar", self.tambah, "Utama.TButton")
            self.aksi.tombol("Ubah", self.ubah)
        if self.sesi.boleh("kamar_hapus"):
            self.aksi.tombol("Hapus kamar", self.hapus, "Hapus.TButton")

        # Total lebar 830 px, muat di area kerja 1120 px kurang sidebar dan padding.
        self.tabel = Tabel(self.badan, [
            ("nomor", "Nomor", 60), ("harga", "Sewa per bulan", 115),
            ("status", "Status", 75), ("penghuni", "Penghuni aktif", 140),
            ("fasilitas", "Fasilitas", 210), ("ket", "Keterangan", 120),
        ], tinggi=13)
        self.tabel.pack(fill="both", expand=True)
        self.tabel.pohon.bind("<Double-1>", lambda e: self.ubah() if self.sesi.boleh("kamar_ubah") else None)
        self.muat()

    def bersihkan_cari(self) -> None:
        self.cari.delete(0, "end")
        self.muat()

    def muat(self) -> None:
        self.data = self.app.panggil(sv.daftar_kamar, self.conn, self.sesi,
                                     self.cari.get()) or []
        baris = []
        for k in self.data:
            tag = "sukses" if k["status_pakai"] == "terisi" else None
            baris.append(((k["nomor_kamar"], rupiah(k["harga_sewa"]),
                           k["status_pakai"].capitalize(),
                           k["penghuni_aktif"] or "-", k["fasilitas"] or "-",
                           k["keterangan"] or "-"), tag))
        pesan = ("Belum ada kamar. Tambah kamar pertama dengan tombol Tambah kamar."
                 if not self.cari.get() else "Tidak ada kamar yang cocok dengan pencarian.")
        self.tabel.isi(baris, pesan)
        self.app.beri_status(f"{len(baris)} kamar ditampilkan.")

    def tambah(self) -> None:
        KamarDialog(self, None)

    def ubah(self) -> None:
        indeks = self.tabel.terpilih_index()
        if indeks is None:
            tema.pesan(self.app, "Belum ada yang dipilih",
                       "Pilih satu kamar pada tabel terlebih dahulu.", "info")
            return
        KamarDialog(self, self.data[indeks])

    def hapus(self) -> None:
        indeks = self.tabel.terpilih_index()
        if indeks is None:
            tema.pesan(self.app, "Belum ada yang dipilih",
                       "Pilih satu kamar pada tabel terlebih dahulu.", "info")
            return
        kamar = self.data[indeks]
        if not tema.konfirmasi(self.app, "Hapus kamar",
                               f"Hapus kamar {kamar['nomor_kamar']}? Kamar yang punya"
                               " riwayat penghuni akan ditolak sistem.", "Hapus kamar"):
            return
        if self.app.panggil(sv.hapus_kamar, self.conn, self.sesi, kamar["id"]) is not None:
            return
        self.app.beri_status(f"Kamar {kamar['nomor_kamar']} dihapus.")
        self.muat()


class KamarDialog:
    def __init__(self, layar: LayarKamar, kamar):
        self.layar = layar
        self.kamar = kamar
        judul = "Ubah kamar" if kamar else "Tambah kamar"
        self.jendela = tema.dialog_modal(layar.app, judul, 470, 420)
        isi = ttk.Frame(self.jendela, style="Kartu.TFrame", padding=20)
        isi.pack(fill="both", expand=True)
        isi.columnconfigure(0, weight=1)

        ttk.Label(isi, text=judul, background=tema.LATAR,
                  font=(tema.HURUF, 13, "bold")).grid(row=0, column=0, sticky="w")
        awal = kamar or {}
        self.f_nomor = field(isi, "Nomor kamar", 1, awal.get("nomor_kamar", ""))
        self.f_harga = field(isi, "Sewa per bulan (angka saja)", 3,
                             str(awal.get("harga_sewa", "")))
        self.f_fasilitas = field(isi, "Fasilitas", 5, awal.get("fasilitas", ""))
        self.f_ket = field(isi, "Keterangan", 7, awal.get("keterangan", ""))

        baris = ttk.Frame(isi, style="Kartu.TFrame")
        baris.grid(row=9, column=0, sticky="e", pady=(18, 0))
        ttk.Button(baris, text="Batal", command=self.jendela.destroy).pack(side="left")
        simpan = ttk.Button(baris, text="Simpan perubahan" if kamar else "Simpan kamar",
                            style="Utama.TButton", command=self.simpan)
        simpan.pack(side="left", padx=(8, 0))
        simpan.focus_set()
        self.jendela.bind("<Return>", lambda e: self.simpan())
        self.f_nomor.focus_set()

    def simpan(self) -> None:
        layar = self.layar
        if self.kamar:
            hasil = layar.app.panggil(sv.ubah_kamar, layar.conn, layar.sesi, self.kamar["id"],
                                      self.f_nomor.get(), self.f_harga.get(),
                                      self.f_fasilitas.get(), self.f_ket.get())
            pesan = "Perubahan kamar disimpan."
        else:
            hasil = layar.app.panggil(sv.tambah_kamar, layar.conn, layar.sesi,
                                      self.f_nomor.get(), self.f_harga.get(),
                                      self.f_fasilitas.get(), self.f_ket.get())
            pesan = "Kamar baru disimpan."
        if hasil is None:
            return
        layar.app.beri_status(pesan)
        self.jendela.destroy()
        layar.muat()


class LayarPenghuni(LayarDasar):
    judul = "Data penghuni"

    def __init__(self, induk, app):
        super().__init__(induk, app)
        self.data: list = []

        baris_cari = ttk.Frame(self.badan, style="Kartu.TFrame")
        baris_cari.pack(fill="x", pady=(0, 10))
        ttk.Label(baris_cari, text="Cari nama atau nomor kamar",
                  style="Lembut.TLabel").pack(side="left")
        self.cari = tk.Entry(baris_cari, relief="solid", bd=1, highlightthickness=2,
                             highlightbackground=tema.LATAR, highlightcolor=tema.AKSEN, width=22)
        self.cari.pack(side="left", padx=(8, 8), ipady=3)
        self.cari.bind("<KeyRelease>", lambda e: self.muat())
        ttk.Button(baris_cari, text="Bersihkan", command=self.bersihkan_cari).pack(side="left")

        self.aksi = BilahAksi(self.badan, "Daftar penghuni",
                              "Penghuni dengan riwayat pembayaran tidak dapat dihapus.")
        self.aksi.pack(fill="x", pady=(0, 10))
        if self.sesi.boleh("penghuni_ubah"):
            self.aksi.tombol("Tambah penghuni", self.tambah, "Utama.TButton")
            self.aksi.tombol("Ubah", self.ubah)
            self.aksi.tombol("Tandai keluar", self.keluar)
        if self.sesi.boleh("penghuni_hapus"):
            self.aksi.tombol("Hapus penghuni", self.hapus, "Hapus.TButton")

        self.tabel = Tabel(self.badan, [
            ("nama", "Nama", 145), ("kamar", "Kamar", 65), ("hp", "No. HP", 110),
            ("masuk", "Masuk", 90), ("keluar", "Keluar", 90),
            ("tarif", "Sewa", 105), ("status", "Status", 75),
        ], tinggi=13)
        self.tabel.pack(fill="both", expand=True)
        self.tabel.pohon.bind("<Double-1>", lambda e: self.ubah() if self.sesi.boleh("penghuni_ubah") else None)
        self.muat()

    def bersihkan_cari(self) -> None:
        self.cari.delete(0, "end")
        self.muat()

    def muat(self) -> None:
        self.data = self.app.panggil(sv.daftar_penghuni, self.conn, self.sesi,
                                     self.cari.get()) or []
        baris = []
        for p in self.data:
            aktif = p["status"] == "aktif"
            baris.append(((p["nama"], p["nomor_kamar"], p["no_hp"] or "-",
                           p["tanggal_masuk"], p["tanggal_keluar"] or "-",
                           rupiah(p["tarif_sewa"]), p["status"].capitalize()),
                          "sukses" if aktif else None))
        pesan = ("Belum ada penghuni. Tambah penghuni pertama, atau tambah kamar lebih dulu"
                 " bila daftar kamar masih kosong."
                 if not self.cari.get() else "Tidak ada penghuni yang cocok dengan pencarian.")
        self.tabel.isi(baris, pesan)
        self.app.beri_status(f"{len(baris)} penghuni ditampilkan.")

    def _pilih(self):
        indeks = self.tabel.terpilih_index()
        if indeks is None:
            tema.pesan(self.app, "Belum ada yang dipilih",
                       "Pilih satu penghuni pada tabel terlebih dahulu.", "info")
            return None
        return self.data[indeks]

    def tambah(self) -> None:
        PenghuniDialog(self, None)

    def ubah(self) -> None:
        data = self._pilih()
        if data:
            PenghuniDialog(self, data)

    def keluar(self) -> None:
        data = self._pilih()
        if not data:
            return
        if not tema.konfirmasi(self.app, "Tandai keluar",
                               f"{data['nama']} akan ditandai keluar hari ini dan kamar"
                               f" {data['nomor_kamar']} menjadi kosong.", "Tandai keluar"):
            return
        if self.app.panggil(sv.keluar_penghuni, self.conn, self.sesi, data["id"]) is not None:
            self.app.beri_status(f"{data['nama']} ditandai keluar.")
            self.muat()

    def hapus(self) -> None:
        data = self._pilih()
        if not data:
            return
        if not tema.konfirmasi(self.app, "Hapus penghuni",
                               f"Hapus {data['nama']} secara permanen? Penghuni dengan"
                               " riwayat pembayaran akan ditolak sistem.", "Hapus penghuni"):
            return
        if self.app.panggil(sv.hapus_penghuni, self.conn, self.sesi, data["id"]) is not None:
            self.app.beri_status(f"{data['nama']} dihapus.")
            self.muat()


class PenghuniDialog:
    def __init__(self, layar: LayarPenghuni, data):
        self.layar = layar
        self.data = data
        judul = "Ubah penghuni" if data else "Tambah penghuni"
        self.jendela = tema.dialog_modal(layar.app, judul, 500, 520)
        isi = ttk.Frame(self.jendela, style="Kartu.TFrame", padding=20)
        isi.pack(fill="both", expand=True)
        isi.columnconfigure(0, weight=1)

        ttk.Label(isi, text=judul, background=tema.LATAR,
                  font=(tema.HURUF, 13, "bold")).grid(row=0, column=0, sticky="w")

        kamar = layar.app.panggil(sv.daftar_kamar, layar.conn, layar.sesi) or []
        pilihan = [(str(k["id"]), f"{k['nomor_kamar']} · {rupiah(k['harga_sewa'])}"
                    f" · {k['status_pakai']}") for k in kamar]
        self.harga_kamar = {str(k["id"]): k["harga_sewa"] for k in kamar}

        awal = dict(data) if data else {}
        self.f_nama = field(isi, "Nama lengkap", 1, awal.get("nama", ""))
        self.f_hp = field(isi, "No. HP", 3, awal.get("no_hp", ""))
        self.f_kamar = field_pilihan(isi, "Kamar", 5, pilihan,
                                     str(awal.get("kamar_id", "")))
        self.f_masuk = field(isi, "Tanggal masuk (YYYY-MM-DD)", 7,
                             awal.get("tanggal_masuk", date.today().isoformat()))
        self.f_tarif = field(isi, "Sewa per bulan", 9, str(awal.get("tarif_sewa", "")))
        self.f_kamar.bind("<<ComboboxSelected>>", lambda e: self.isi_tarif())
        if not data:
            self.isi_tarif()

        baris = ttk.Frame(isi, style="Kartu.TFrame")
        baris.grid(row=11, column=0, sticky="e", pady=(18, 0))
        ttk.Button(baris, text="Batal", command=self.jendela.destroy).pack(side="left")
        simpan = ttk.Button(baris, text="Simpan perubahan" if data else "Simpan penghuni",
                            style="Utama.TButton", command=self.simpan)
        simpan.pack(side="left", padx=(8, 0))
        simpan.focus_set()
        self.jendela.bind("<Return>", lambda e: self.simpan())
        self.f_nama.focus_set()

    def isi_tarif(self) -> None:
        if self.data:
            return
        harga = self.harga_kamar.get(nilai_pilihan(self.f_kamar))
        if harga is not None:
            self.f_tarif.delete(0, "end")
            self.f_tarif.insert(0, str(harga))

    def simpan(self) -> None:
        layar = self.layar
        kamar_id = nilai_pilihan(self.f_kamar)
        if not kamar_id:
            tema.pesan(layar.app, "Kamar belum dipilih",
                       "Pilih kamar terlebih dahulu. Bila daftar kosong, tambah kamar dulu.",
                       "gagal")
            return
        arg = (layar.conn, layar.sesi)
        if self.data:
            hasil = layar.app.panggil(sv.ubah_penghuni, *arg, self.data["id"],
                                      self.f_nama.get(), self.f_hp.get(), int(kamar_id),
                                      self.f_masuk.get(), self.f_tarif.get())
            pesan = "Perubahan penghuni disimpan."
        else:
            hasil = layar.app.panggil(sv.tambah_penghuni, *arg, self.f_nama.get(),
                                      self.f_hp.get(), int(kamar_id), self.f_masuk.get(),
                                      self.f_tarif.get())
            pesan = "Penghuni baru disimpan."
        if hasil is None:
            return
        layar.app.beri_status(pesan)
        self.jendela.destroy()
        layar.muat()
