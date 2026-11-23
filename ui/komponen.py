"""Komponen tabel, bilah aksi, dan field form yang dipakai ulang semua layar.

Halaman tidak membuat gaya tabel atau tombol sendiri; semuanya lewat berkas ini
agar tidak ada penyimpangan visual antar layar (antislop: satu sistem komponen).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from . import tema


class Tabel(ttk.Frame):
    """Tabel dengan header berlabel, pesan kosong, dan state terpilih."""

    def __init__(self, induk, kolom: list[tuple[str, str, int]], tinggi: int = 12):
        super().__init__(induk, style="Kartu.TFrame")
        self.kolom = kolom
        self.pesan_kosong = "Belum ada data."
        self.pesan_gagal = ""

        pembungkus = ttk.Frame(self, style="Kartu.TFrame")
        pembungkus.pack(fill="both", expand=True)

        self.pohon = ttk.Treeview(pembungkus, columns=[k[0] for k in kolom],
                                  show="headings", height=tinggi, selectmode="browse")
        # displaycolumns memastikan setiap kolom punya ruang; tanpa ini Tk bisa
        # menyembunyikan kolom terakhir bila total lebar melebihi area tabel.
        self.pohon.configure(displaycolumns=[k[0] for k in kolom])
        for kunci, judul, lebar in kolom:
            self.pohon.heading(kunci, text=judul, anchor="w")
            # stretch dimatikan supaya kolom tidak menyusut sampai terpotong;
            # bila total lebar melebihi jendela, pengguna menggeser lewat scrollbar.
            self.pohon.column(kunci, width=lebar, minwidth=lebar, anchor="w", stretch=False)
        gelombang = ttk.Scrollbar(pembungkus, orient="vertical", command=self.pohon.yview)
        geser = ttk.Scrollbar(pembungkus, orient="horizontal", command=self.pohon.xview)
        self.pohon.configure(yscrollcommand=gelombang.set, xscrollcommand=geser.set)
        gelombang.pack(side="right", fill="y")
        geser.pack(side="bottom", fill="x")
        self.pohon.pack(side="left", fill="both", expand=True)

        self.label_kosong = ttk.Label(self, text="", style="Lembut.TLabel",
                                      background=tema.LATAR, wraplength=520, justify="left")
        self.info_lebar = ttk.Label(self, text="", style="Lembut.TLabel",
                                    background=tema.LATAR)

        # Baris kosong tidak boleh tampak seperti tabel rusak: pesannya menjelaskan
        # langkah berikutnya, bukan sekadar "no data".
        self.pohon.tag_configure("sukses", foreground=tema.SUKSES)
        self.pohon.tag_configure("peringatan", foreground=tema.PERINGATAN)
        self.pohon.tag_configure("bahaya", foreground=tema.BAHAYA)

    def isi(self, baris: list[tuple], kosong: str | None = None) -> None:
        self.pohon.delete(*self.pohon.get_children())
        for item in baris:
            nilai, tag = item if isinstance(item, tuple) and len(item) == 2 else (item, None)
            self.pohon.insert("", "end", values=nilai, tags=(tag,) if tag else ())
        if baris:
            self.label_kosong.pack_forget()
        else:
            self.label_kosong.configure(text=kosong or self.pesan_kosong)
            self.label_kosong.pack(anchor="w", pady=(10, 0))

    def terpilih(self):
        pilihan = self.pohon.selection()
        if not pilihan:
            return None
        return self.pohon.item(pilihan[0], "values")

    def terpilih_index(self) -> int | None:
        pilihan = self.pohon.selection()
        if not pilihan:
            return None
        return self.pohon.index(pilihan[0])

    def bersihkan_pilihan(self) -> None:
        self.pohon.selection_remove(*self.pohon.selection())


class BilahAksi(ttk.Frame):
    """Baris tombol aksi. Tombol yang tidak diizinkan role tidak dibuat sama sekali,
    sehingga tidak ada kontrol mati yang bisa diklik."""

    def __init__(self, induk, judul: str, keterangan: str = ""):
        super().__init__(induk, style="Kartu.TFrame")
        kiri = ttk.Frame(self, style="Kartu.TFrame")
        kiri.pack(side="left", anchor="w")
        ttk.Label(kiri, text=judul, background=tema.LATAR,
                  font=(tema.HURUF, 11, "bold")).pack(anchor="w")
        if keterangan:
            ttk.Label(kiri, text=keterangan, style="Lembut.TLabel").pack(anchor="w")
        self.kanan = ttk.Frame(self, style="Kartu.TFrame")
        self.kanan.pack(side="right")

    def tombol(self, teks: str, aksi, gaya: str = "TButton") -> ttk.Button:
        b = ttk.Button(self.kanan, text=teks, command=aksi, style=gaya)
        b.pack(side="left", padx=(8, 0))
        return b


def field(induk, label: str, baris: int, nilai: str = "") -> tk.Entry:
    """Field dengan label nyata di atasnya, bukan placeholder sebagai label.

    ttk.Frame dipakai sebagai pembungkus: Tk selalu merender anak ttk sebelum
    anak klasik, sehingga tanpa pembungkus tk.Entry bisa tertimbun Combobox dan
    tampak sebagai field kosong yang tidak bisa diklik.
    """
    pembungkus = ttk.Frame(induk, style="Kartu.TFrame")
    pembungkus.grid(row=baris, column=0, columnspan=2, sticky="ew")
    ttk.Label(pembungkus, text=label, background=tema.LATAR,
              foreground=tema.TEKS_LEMBUT).pack(anchor="w", pady=(10, 2))
    entri = tk.Entry(pembungkus, background=tema.LATAR, foreground=tema.TEKS,
                     insertbackground=tema.TEKS, relief="solid", bd=1,
                     highlightthickness=2, highlightbackground=tema.LATAR,
                     highlightcolor=tema.AKSEN)
    entri.pack(fill="x", ipady=4)
    entri.insert(0, nilai)
    return entri


def field_pilihan(induk, label: str, baris: int, pilihan: list[tuple[str, str]],
                  awal: str = "") -> ttk.Combobox:
    ttk.Label(induk, text=label, background=tema.LATAR,
              foreground=tema.TEKS_LEMBUT).grid(row=baris, column=0, sticky="w", pady=(10, 2))
    com = ttk.Combobox(induk, values=[p[1] for p in pilihan], state="readonly")
    if awal:
        for nilai, teks in pilihan:
            if nilai == awal:
                com.set(teks)
    elif pilihan:
        com.current(0)
    com.grid(row=baris + 1, column=0, columnspan=2, sticky="ew")
    com._peta = {teks: nilai for nilai, teks in pilihan}
    return com


def nilai_pilihan(com: ttk.Combobox) -> str:
    return getattr(com, "_peta", {}).get(com.get(), "")
