"""Kerangka aplikasi: login, sidebar sesuai role, area kerja, dan status bar."""

from __future__ import annotations

import sqlite3
import tkinter as tk
from datetime import date
from tkinter import ttk

import services as sv
from services import AksesDitolak, BelumLogin, KesalahanAplikasi

from . import tema
from .komponen import Tabel, field, field_pilihan, nilai_pilihan
from .layar import LayarDashboard, LayarKamar, LayarPenghuni
from .layar_lanjutan import (
    LayarLaporan, LayarPembayaran, LayarPengguna, LayarPenunggak,
)

MENU = [
    ("dashboard", "Ringkasan", "dashboard"),
    ("kamar", "Kamar", "kamar_lihat"),
    ("penghuni", "Penghuni", "penghuni_lihat"),
    ("pembayaran", "Pembayaran", "pembayaran_catat"),
    ("penunggak", "Penunggak", "penunggak_lihat"),
    ("laporan", "Laporan pemasukan", "laporan_lihat"),
    ("pengguna", "Akun pengguna", "pengguna_kelola"),
]

# Hak yang cukup untuk membuka sebuah menu; "dashboard" selalu boleh.
HAK_MENU = {kunci: hak for kunci, _, hak in MENU}
JUDUL_MENU = {kunci: label for kunci, label, _ in MENU}

KELAS_LAYAR = {
    "dashboard": LayarDashboard,
    "kamar": LayarKamar,
    "penghuni": LayarPenghuni,
    "pembayaran": LayarPembayaran,
    "penunggak": LayarPenunggak,
    "laporan": LayarLaporan,
    "pengguna": LayarPengguna,
}


class Aplikasi(tk.Tk):
    def __init__(self, conn: sqlite3.Connection):
        super().__init__()
        self.conn = conn
        self.sesi: sv.Sesi | None = None
        self.layar_aktif = None
        self.title("SI-Kos: Sistem Informasi Manajemen Kos")
        self.geometry("1120x680")
        self.minsize(1000, 600)
        tema.pasang_tema(self)
        tema.pasang_keyboard(self)
        self.bingkai = ttk.Frame(self, style="Latar.TFrame")
        self.bingkai.pack(fill="both", expand=True)
        self.tampilkan_login()

    # ------------------------------------------------------------------ #
    # Navigasi
    # ------------------------------------------------------------------ #

    def bersihkan(self) -> None:
        for anak in self.bingkai.winfo_children():
            anak.destroy()

    def tampilkan_login(self) -> None:
        self.bersihkan()
        self.sesi = None
        self.configure(background=tema.LATAR_LEMBUT)

        tengah = ttk.Frame(self.bingkai, style="Kartu.TFrame", padding=28)
        tengah.place(relx=0.5, rely=0.45, anchor="center")

        ttk.Label(tengah, text="SI-Kos", background=tema.LATAR, foreground=tema.TEKS,
                  font=(tema.HURUF, 22, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(tengah, text="Masuk untuk mengelola kamar, penghuni, dan pembayaran.",
                  style="Lembut.TLabel").grid(row=1, column=0, sticky="w", pady=(4, 14))

        self.e_username = field(tengah, "Username", 2)
        self.e_password = field(tengah, "Password", 4)
        self.e_password.configure(show="\u2022")
        self.lbl_login = ttk.Label(tengah, text="", background=tema.LATAR,
                                   foreground=tema.BAHAYA, wraplength=320, justify="left")
        self.lbl_login.grid(row=6, column=0, sticky="w", pady=(10, 0))

        tombol = ttk.Button(tengah, text="Masuk", style="Utama.TButton", command=self.masuk)
        tombol.grid(row=7, column=0, sticky="ew", pady=(12, 0), ipady=3)
        ttk.Label(tengah, text="Akun demo: pemilik / pemilik123, penjaga / penjaga123",
                  style="Lembut.TLabel").grid(row=8, column=0, sticky="w", pady=(12, 0))

        self.bind("<Return>", lambda e: self.masuk())
        self.e_username.focus_set()

    def masuk(self) -> None:
        try:
            self.sesi = sv.login(self.conn, self.e_username.get(), self.e_password.get())
        except KesalahanAplikasi as e:
            self.lbl_login.configure(text=str(e))
            self.e_password.delete(0, "end")
            self.e_password.focus_set()
            return
        self.unbind("<Return>")
        self.bangun_shell()

    def keluar(self) -> None:
        if not tema.konfirmasi(self, "Keluar dari aplikasi",
                               "Sesi Anda akan berakhir dan jendela ditutup.",
                               "Keluar"):
            return
        self.destroy()

    def bangun_shell(self) -> None:
        self.bersihkan()
        self.configure(background=tema.LATAR_LEMBUT)

        # Sidebar: hanya menu yang boleh dipakai role aktif.
        sidebar = tk.Frame(self.bingkai, background=tema.LATAR, width=232)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="SI-Kos", background=tema.LATAR, foreground=tema.TEKS,
                 font=(tema.HURUF, 16, "bold")).pack(anchor="w", padx=18, pady=(18, 2))
        tk.Label(sidebar, text=f"{self.sesi.nama} · {self.sesi.role.capitalize()}",
                 background=tema.LATAR, foreground=tema.TEKS_LEMBUT,
                 font=(tema.HURUF, 9)).pack(anchor="w", padx=18, pady=(0, 14))

        self.tombol_menu: dict[str, tk.Button] = {}
        for kunci, label, hak in MENU:
            if not self.boleh(kunci):
                continue
            b = tk.Button(sidebar, text=label, anchor="w", relief="flat", bd=0,
                          background=tema.LATAR, foreground=tema.TEKS,
                          activebackground=tema.LATAR_LEMBUT, cursor="hand2",
                          padx=18, pady=8, font=(tema.HURUF, 10),
                          command=lambda k=kunci: self.buka(k))
            b.pack(fill="x")
            self.tombol_menu[kunci] = b

        ttk.Button(sidebar, text="Keluar", command=self.keluar).pack(
            side="bottom", fill="x", padx=18, pady=18)

        self.area = ttk.Frame(self.bingkai, style="Latar.TFrame", padding=(20, 16))
        self.area.pack(side="left", fill="both", expand=True)

        self.status = tk.Label(self.bingkai, text="Siap.", anchor="w",
                               background=tema.LATAR_LEMBUT, foreground=tema.TEKS_LEMBUT,
                               font=(tema.HURUF, 9), padx=18, pady=6)
        self.status.pack(side="bottom", fill="x")

        awal = "dashboard"
        self.buka(awal)

    def buka(self, kunci: str) -> None:
        for k, b in self.tombol_menu.items():
            aktif = k == kunci
            b.configure(background=tema.AKSEN if aktif else tema.LATAR,
                        foreground="#FFFFFF" if aktif else tema.TEKS)
        for anak in self.area.winfo_children():
            anak.destroy()
        self.layar_aktif = KELAS_LAYAR[kunci](self.area, self)
        self.layar_aktif.pack(fill="both", expand=True)
        self.beri_status(f"Membuka {JUDUL_MENU[kunci].lower()}.")

    def boleh(self, kunci_menu: str) -> bool:
        """Menu terbuka bila sesi punya hak lihat dan punya hak ubah atau catat.
        Penjaga melihat Kamar dan Penghuni, bukan daftar yang tidak bisa diubah."""
        if kunci_menu == "dashboard" or self.sesi is None:
            return kunci_menu == "dashboard" and self.sesi is not None
        if not self.sesi.boleh(HAK_MENU[kunci_menu]):
            return False
        if kunci_menu in ("kamar", "penghuni"):
            return self.sesi.boleh("kamar_ubah" if kunci_menu == "kamar" else "penghuni_ubah")
        return True

    def beri_status(self, teks: str) -> None:
        self.status.configure(text=teks)

    def panggil(self, fungsi, *args, **kwargs):
        """Jalankan fungsi layanan dan ubah kesalahan menjadi pesan yang terlihat."""
        try:
            return fungsi(*args, **kwargs)
        except BelumLogin as e:
            tema.pesan(self, "Sesi berakhir", str(e), "gagal")
        except AksesDitolak as e:
            tema.pesan(self, "Akses ditolak", str(e), "gagal")
        except KesalahanAplikasi as e:
            tema.pesan(self, "Tidak dapat dilanjutkan", str(e), "gagal")
        except Exception as e:  # kegagalan tak terduga tidak boleh menutup aplikasi
            tema.pesan(self, "Terjadi kesalahan", f"{type(e).__name__}: {e}", "gagal")
        return None
