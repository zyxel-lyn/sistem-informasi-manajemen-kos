"""Layar Pembayaran, Penunggak, Laporan, dan Akun pengguna."""

from __future__ import annotations

import tkinter as tk
from datetime import date
from tkinter import filedialog, ttk

import services as sv
import services_lanjutan as sl

from . import tema
from .komponen import BilahAksi, Tabel, field, field_pilihan, nilai_pilihan
from .layar import LayarDasar, pilihan_periode, periode_sekarang, rupiah


def pilih_periode_widget(induk, nilai_awal: str, saat_ubah) -> ttk.Combobox:
    """Pemilih periode yang aman dipakai di dalam baris dengan pack()."""
    pilihan = pilihan_periode()
    com = ttk.Combobox(induk, values=[p[1] for p in pilihan], state="readonly", width=18)
    for kunci, teks in pilihan:
        if kunci == nilai_awal:
            com.set(teks)
    com._peta = {teks: kunci for kunci, teks in pilihan}
    com.bind("<<ComboboxSelected>>", lambda e: saat_ubah())
    return com


def baris_periode(induk, saat_ubah) -> ttk.Combobox:
    ttk.Label(induk, text="Periode", style="Lembut.TLabel").pack(side="left")
    com = pilih_periode_widget(induk, periode_sekarang(), saat_ubah)
    com.pack(side="left", padx=(8, 8))
    ttk.Button(induk, text="Tampilkan", command=saat_ubah).pack(side="left")
    return com


class LayarPembayaran(LayarDasar):
    judul = "Pembayaran sewa"

    def __init__(self, induk, app):
        super().__init__(induk, app)
        self.data: list = []

        baris = ttk.Frame(self.badan, style="Kartu.TFrame")
        baris.pack(fill="x", pady=(0, 10))
        self.pilih_periode = baris_periode(baris, lambda: self.muat())

        self.aksi = BilahAksi(self.badan, "Riwayat pembayaran",
                              "Satu penghuni hanya boleh punya satu pembayaran per bulan.")
        self.aksi.pack(fill="x", pady=(0, 10))
        if self.sesi.boleh("pembayaran_catat"):
            self.aksi.tombol("Catat pembayaran", self.catat, "Utama.TButton")
        if self.sesi.boleh("pembayaran_batal"):
            self.aksi.tombol("Batalkan", self.batalkan, "Hapus.TButton")

        self.tabel = Tabel(self.badan, [
            ("periode", "Periode", 85), ("nama", "Penghuni", 150), ("kamar", "Kamar", 65),
            ("tanggal", "Tanggal bayar", 100), ("jumlah", "Jumlah", 110),
            ("metode", "Metode", 85), ("pencatat", "Dicatat oleh", 120),
        ], tinggi=14)
        self.tabel.pack(fill="both", expand=True)
        self.muat()

    def muat(self) -> None:
        periode = nilai_pilihan(self.pilih_periode)
        self.data = self.app.panggil(sl.daftar_pembayaran, self.conn, self.sesi, periode) or []
        baris = []
        for b in self.data:
            baris.append(((b["periode"], b["nama"], b["nomor_kamar"], b["tanggal_bayar"],
                           rupiah(b["jumlah"]), b["metode"].capitalize(),
                           b["pencatat"] or "-"), "sukses"))
        self.tabel.isi(baris, "Belum ada pembayaran tercatat untuk periode ini."
                       " Gunakan tombol Catat pembayaran.")
        total = sum(b["jumlah"] for b in self.data)
        self.app.beri_status(f"{len(baris)} pembayaran, total {rupiah(total)}.")

    def catat(self) -> None:
        CatatPembayaranDialog(self)

    def batalkan(self) -> None:
        indeks = self.tabel.terpilih_index()
        if indeks is None:
            tema.pesan(self.app, "Belum ada yang dipilih",
                       "Pilih satu pembayaran pada tabel terlebih dahulu.", "info")
            return
        b = self.data[indeks]
        if not tema.konfirmasi(self.app, "Batalkan pembayaran",
                               f"Batalkan pembayaran {b['nama']} periode {b['periode']}"
                               f" sebesar {rupiah(b['jumlah'])}? Data akan dihapus permanen.",
                               "Batalkan pembayaran"):
            return
        if self.app.panggil(sl.hapus_pembayaran, self.conn, self.sesi, b["id"]) is not None:
            self.app.beri_status("Pembayaran dibatalkan.")
            self.muat()


class CatatPembayaranDialog:
    def __init__(self, layar: LayarPembayaran):
        self.layar = layar
        self.jendela = tema.dialog_modal(layar.app, "Catat pembayaran", 500, 470)
        isi = ttk.Frame(self.jendela, style="Kartu.TFrame", padding=20)
        isi.pack(fill="both", expand=True)
        isi.columnconfigure(0, weight=1)
        ttk.Label(isi, text="Catat pembayaran", background=tema.LATAR,
                  font=(tema.HURUF, 13, "bold")).grid(row=0, column=0, sticky="w")

        aktif = layar.app.panggil(sv.daftar_penghuni, layar.conn, layar.sesi, "", True) or []
        pilihan = [(str(p["id"]), f"{p['nama']} · kamar {p['nomor_kamar']} ·"
                    f" {rupiah(p['tarif_sewa'])}") for p in aktif]
        self.tarif = {str(p["id"]): p["tarif_sewa"] for p in aktif}

        self.f_penghuni = field_pilihan(isi, "Penghuni", 1, pilihan)
        self.f_periode = field_pilihan(isi, "Periode", 3, pilihan_periode(), periode_sekarang())
        self.f_jumlah = field(isi, "Jumlah dibayar", 5)
        self.f_tanggal = field(isi, "Tanggal bayar (YYYY-MM-DD)", 7, date.today().isoformat())
        self.f_metode = field_pilihan(isi, "Metode", 9,
                                      [("tunai", "Tunai"), ("transfer", "Transfer")])
        self.f_catatan = field(isi, "Catatan (opsional)", 11)
        self.f_penghuni.bind("<<ComboboxSelected>>", lambda e: self.isi_jumlah())
        self.isi_jumlah()

        baris = ttk.Frame(isi, style="Kartu.TFrame")
        baris.grid(row=13, column=0, sticky="e", pady=(18, 0))
        ttk.Button(baris, text="Batal", command=self.jendela.destroy).pack(side="left")
        simpan = ttk.Button(baris, text="Simpan pembayaran", style="Utama.TButton",
                            command=self.simpan)
        simpan.pack(side="left", padx=(8, 0))
        simpan.focus_set()

    def isi_jumlah(self) -> None:
        harga = self.tarif.get(nilai_pilihan(self.f_penghuni))
        if harga is not None:
            self.f_jumlah.delete(0, "end")
            self.f_jumlah.insert(0, str(harga))

    def simpan(self) -> None:
        layar = self.layar
        pid = nilai_pilihan(self.f_penghuni)
        if not pid:
            tema.pesan(layar.app, "Penghuni belum dipilih",
                       "Tambahkan penghuni aktif terlebih dahulu.", "gagal")
            return
        hasil = layar.app.panggil(sl.catat_pembayaran, layar.conn, layar.sesi, int(pid),
                                  nilai_pilihan(self.f_periode), self.f_jumlah.get(),
                                  self.f_tanggal.get(), nilai_pilihan(self.f_metode) or "tunai",
                                  self.f_catatan.get())
        if hasil is None:
            return
        layar.app.beri_status("Pembayaran tersimpan.")
        self.jendela.destroy()
        layar.muat()


class LayarPenunggak(LayarDasar):
    judul = "Penunggak"

    def __init__(self, induk, app):
        super().__init__(induk, app)
        self.data: list = []
        baris = ttk.Frame(self.badan, style="Kartu.TFrame")
        baris.pack(fill="x", pady=(0, 10))
        self.pilih_periode = baris_periode(baris, lambda: self.muat())

        self.aksi = BilahAksi(self.badan, "Belum lunas",
                              "Jatuh tempo mengikuti tanggal masuk penghuni.")
        self.aksi.pack(fill="x", pady=(0, 10))
        self.aksi.tombol("Salin teks pengingat", self.salin, "Utama.TButton")

        self.tabel = Tabel(self.badan, [
            ("kamar", "Kamar", 65), ("nama", "Penghuni", 150), ("hp", "No. HP", 115),
            ("tarif", "Sewa", 100), ("dibayar", "Dibayar", 100),
            ("kurang", "Kurang", 100), ("jatuh", "Jatuh tempo", 100),
            ("status", "Status", 100),
        ], tinggi=14)
        self.tabel.pack(fill="both", expand=True)
        self.muat()

    def muat(self) -> None:
        periode = nilai_pilihan(self.pilih_periode)
        self.data = self.app.panggil(sv.daftar_penunggak, self.conn, self.sesi, periode) or []
        baris = []
        for u in self.data:
            tag = "bahaya" if u["status"] == "belum bayar" else "peringatan"
            baris.append(((u["nomor_kamar"], u["nama"], u["no_hp"] or "-", rupiah(u["tarif"]),
                           rupiah(u["dibayar"]), rupiah(u["kurang"]), u["jatuh_tempo"],
                           u["status"].capitalize()), tag))
        self.tabel.isi(baris, "Tidak ada yang menunggak pada periode ini."
                       " Semua penghuni aktif sudah lunas.")
        self.app.beri_status(f"{len(baris)} penghuni belum lunas.")

    def salin(self) -> None:
        if not self.data:
            tema.pesan(self.app, "Tidak ada yang perlu diingatkan",
                       "Daftar penunggak untuk periode ini kosong.", "info")
            return
        indeks = self.tabel.terpilih_index()
        if indeks is None:
            teks = "\n".join(
                f"{u['nama']} (kamar {u['nomor_kamar']}) sewa {rupiah(u['kurang'])}"
                f" jatuh tempo {u['jatuh_tempo']}" for u in self.data)
        else:
            u = self.data[indeks]
            teks = (f"Pengingat: {u['nama']}, kamar {u['nomor_kamar']}, sewa {rupiah(u['kurang'])}"
                    f" jatuh tempo {u['jatuh_tempo']}.")
        self.app.clipboard_clear()
        self.app.clipboard_append(teks)
        self.app.beri_status("Teks pengingat disalin ke clipboard.")


class LayarLaporan(LayarDasar):
    judul = "Laporan pemasukan"

    def __init__(self, induk, app):
        super().__init__(induk, app)
        baris = ttk.Frame(self.badan, style="Kartu.TFrame")
        baris.pack(fill="x", pady=(0, 10))
        self.pilih_periode = baris_periode(baris, lambda: self.muat())
        ttk.Button(baris, text="Simpan laporan CSV", command=self.ekspor).pack(side="left",
                                                                             padx=(8, 0))

        angka = ttk.Frame(self.badan, style="Kartu.TFrame")
        angka.pack(fill="x", pady=(0, 12))
        self.total = ttk.Label(angka, text="Rp0", style="Angka.TLabel")
        self.total.pack(anchor="w")
        self.rincian_total = ttk.Label(angka, text="Total pemasukan periode ini",
                                       style="AngkaLembut.TLabel")
        self.rincian_total.pack(anchor="w")
        self.belum = ttk.Label(angka, text="", style="Peringatan.TLabel")
        self.belum.pack(anchor="w", pady=(8, 0))

        self.tabel = Tabel(self.badan, [
            ("kamar", "Kamar", 75), ("nama", "Penghuni", 180), ("tarif", "Sewa", 115),
            ("dibayar", "Dibayar", 115), ("transaksi", "Transaksi", 130),
        ], tinggi=13)
        self.tabel.pack(fill="both", expand=True)
        self.muat()

    def muat(self) -> None:
        periode = nilai_pilihan(self.pilih_periode)
        laporan = self.app.panggil(sl.laporan_bulanan, self.conn, self.sesi, periode)
        if not laporan:
            return
        self.total.configure(text=rupiah(laporan["total_masuk"]))
        self.belum.configure(
            text=f"Belum dibayar: {rupiah(laporan['belum_bayar'])} dari"
                 f" {laporan['jumlah_penunggak']} penghuni, {laporan['jumlah_transaksi']}"
                 " transaksi pada periode ini.")
        baris = [((r["nomor_kamar"], r["nama"], rupiah(r["tarif_sewa"]),
                   rupiah(r["dibayar"]), str(r["jumlah_transaksi"])), None)
                 for r in laporan["rincian"]]
        self.tabel.isi(baris, "Belum ada penghuni terdaftar pada periode ini.")
        self.app.beri_status("Laporan dimuat.")

    def ekspor(self) -> None:
        periode = nilai_pilihan(self.pilih_periode)
        tujuan = filedialog.asksaveasfilename(
            title="Simpan laporan", defaultextension=".csv",
            initialfile=f"laporan-{periode}.csv",
            filetypes=[("Berkas CSV", "*.csv")])
        if not tujuan:
            return
        if self.app.panggil(sl.ekspor_laporan_csv, self.conn, self.sesi, periode,
                            tujuan) is None:
            return
        tema.pesan(self.app, "Laporan disimpan", f"Berkas tersimpan di:\n{tujuan}", "sukses")
        self.app.beri_status("Laporan CSV disimpan.")


class LayarPengguna(LayarDasar):
    judul = "Akun pengguna"

    def __init__(self, induk, app):
        super().__init__(induk, app)
        self.data: list = []
        self.aksi = BilahAksi(self.badan, "Akun yang bisa masuk aplikasi",
                              "Hanya pemilik yang dapat mengelola akun.")
        self.aksi.pack(fill="x", pady=(0, 10))
        self.aksi.tombol("Tambah akun", self.tambah, "Utama.TButton")
        self.aksi.tombol("Ubah", self.ubah)

        self.tabel = Tabel(self.badan, [
            ("username", "Username", 130), ("nama", "Nama", 175),
            ("role", "Peran", 95), ("aktif", "Status", 95),
            ("dibuat", "Dibuat", 145),
        ], tinggi=14)
        self.tabel.pack(fill="both", expand=True)
        self.muat()

    def muat(self) -> None:
        self.data = self.app.panggil(sl.daftar_pengguna, self.conn, self.sesi) or []
        baris = []
        for u in self.data:
            baris.append(((u["username"], u["nama"], u["role"].capitalize(),
                           "Aktif" if u["aktif"] else "Nonaktif", u["dibuat_pada"]),
                          "sukses" if u["aktif"] else "bahaya"))
        self.tabel.isi(baris, "Belum ada akun. Tambah akun pertama dengan tombol di atas.")
        self.app.beri_status(f"{len(baris)} akun terdaftar.")

    def tambah(self) -> None:
        PenggunaDialog(self, None)

    def ubah(self) -> None:
        indeks = self.tabel.terpilih_index()
        if indeks is None:
            tema.pesan(self.app, "Belum ada yang dipilih",
                       "Pilih satu akun pada tabel terlebih dahulu.", "info")
            return
        PenggunaDialog(self, self.data[indeks])


class PenggunaDialog:
    def __init__(self, layar: LayarPengguna, data):
        self.layar = layar
        self.data = data
        judul = "Ubah akun" if data else "Tambah akun"
        self.jendela = tema.dialog_modal(layar.app, judul, 470, 440)
        isi = ttk.Frame(self.jendela, style="Kartu.TFrame", padding=20)
        isi.pack(fill="both", expand=True)
        isi.columnconfigure(0, weight=1)
        ttk.Label(isi, text=judul, background=tema.LATAR,
                  font=(tema.HURUF, 13, "bold")).grid(row=0, column=0, sticky="w")

        awal = dict(data) if data else {}
        self.f_username = field(isi, "Username", 1, awal.get("username", ""))
        if data:
            self.f_username.configure(state="readonly")
        self.f_nama = field(isi, "Nama", 3, awal.get("nama", ""))
        self.f_role = field_pilihan(isi, "Peran", 5,
                                    [("pemilik", "Pemilik"), ("penjaga", "Penjaga")],
                                    awal.get("role", "penjaga"))
        label_password = ("Password baru (kosongkan bila tidak diubah)"
                          if data else "Password (minimal 6 karakter)")
        self.f_password = field(isi, label_password, 7)
        self.f_password.configure(show="\u2022")
        self.f_aktif = field_pilihan(isi, "Status", 9, [("1", "Aktif"), ("0", "Nonaktif")],
                                     str(awal.get("aktif", 1)))

        baris = ttk.Frame(isi, style="Kartu.TFrame")
        baris.grid(row=11, column=0, sticky="e", pady=(16, 0))
        ttk.Button(baris, text="Batal", command=self.jendela.destroy).pack(side="left")
        simpan = ttk.Button(baris, text="Simpan", style="Utama.TButton", command=self.simpan)
        simpan.pack(side="left", padx=(8, 0))
        simpan.focus_set()

    def simpan(self) -> None:
        layar = self.layar
        if self.data:
            hasil = layar.app.panggil(
                sl.ubah_pengguna, layar.conn, layar.sesi, self.data["id"],
                self.f_nama.get(), nilai_pilihan(self.f_role) or self.data["role"],
                nilai_pilihan(self.f_aktif) == "1", self.f_password.get())
            pesan = "Perubahan akun disimpan."
        else:
            hasil = layar.app.panggil(
                sl.tambah_pengguna, layar.conn, layar.sesi, self.f_username.get(),
                self.f_password.get(), self.f_nama.get(),
                nilai_pilihan(self.f_role) or "penjaga")
            pesan = "Akun baru dibuat."
        if hasil is None:
            return
        layar.app.beri_status(pesan)
        self.jendela.destroy()
        layar.muat()
