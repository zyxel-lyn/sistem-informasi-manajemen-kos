"""Tema dan binding keyboard bersama untuk seluruh aplikasi SI-Kos.

Satu sumber kebenaran untuk warna, huruf, dan ukuran. Nilai warna harus sama
dengan tabel token di DESIGN.md; rasio kontrasnya sudah diukur dengan
contrast-check.py dari skill antislop-human.
"""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

# Saat dijalankan otomatis (cek_ui.py), dialog tidak menunggu klik manusia.
# Setiap dialog dicatat namanya supaya uji bisa memeriksa isinya lalu menutupnya.
MODE_UJI = "1" if os.environ.get("SIKOS_UJI_UI") == "1" else None
DIALOG_TERAKHIR: list = []

LATAR = "#FFFFFF"
LATAR_LEMBUT = "#EFF3F6"
TEKS = "#1C2024"
TEKS_LEMBUT = "#5B6470"
GARIS = "#8C949C"
GARIS_HALUS = "#D8DCE0"
AKSEN = "#2F4858"
AKSEN_HOVER = "#3A5566"
SUKSES = "#1F6B4A"
PERINGATAN = "#8A6A1F"
BAHAYA = "#96331F"

HURUF = "Segoe UI"
UKURAN_ISI = 10
UKURAN_JUDUL = 17
UKURAN_ANGKA = 22
UKURAN_KECIL = 9

# Karakter yang tidak boleh muncul di teks antarmuka (antislop R-02/R-16).
TERLARANG = ("\u2014", "\u2013")


def pasang_tema(akar: tk.Tk) -> None:
    akar.configure(background=LATAR_LEMBUT)
    gaya = ttk.Style(akar)
    gaya.theme_use("clam")

    dasar = tkfont.nametofont("TkDefaultFont")
    dasar.configure(family=HURUF, size=UKURAN_ISI)
    akar.option_add("*Font", dasar)

    gaya.configure("TFrame", background=LATAR)
    gaya.configure("Latar.TFrame", background=LATAR_LEMBUT)
    gaya.configure("Kartu.TFrame", background=LATAR, relief="flat")
    gaya.configure("TLabel", background=LATAR, foreground=TEKS)
    gaya.configure("Lembut.TLabel", background=LATAR, foreground=TEKS_LEMBUT)
    gaya.configure("Judul.TLabel", background=LATAR_LEMBUT, foreground=TEKS,
                   font=(HURUF, UKURAN_JUDUL, "bold"))
    gaya.configure("Keterangan.TLabel", background=LATAR_LEMBUT, foreground=TEKS_LEMBUT,
                   font=(HURUF, UKURAN_KECIL))
    gaya.configure("Angka.TLabel", background=LATAR, foreground=TEKS,
                   font=(HURUF, UKURAN_ANGKA, "bold"))
    gaya.configure("AngkaLembut.TLabel", background=LATAR, foreground=TEKS_LEMBUT,
                   font=(HURUF, UKURAN_KECIL))
    gaya.configure("Sukses.TLabel", background=LATAR, foreground=SUKSES)
    gaya.configure("Peringatan.TLabel", background=LATAR, foreground=PERINGATAN)
    gaya.configure("Bahaya.TLabel", background=LATAR, foreground=BAHAYA)

    gaya.configure("TEntry", fieldbackground=LATAR, foreground=TEKS, bordercolor=GARIS,
                   lightcolor=GARIS, darkcolor=GARIS, insertcolor=TEKS, padding=5)
    gaya.map("TEntry", bordercolor=[("focus", AKSEN)], lightcolor=[("focus", AKSEN)])
    gaya.configure("TCombobox", fieldbackground=LATAR, foreground=TEKS, bordercolor=GARIS,
                   arrowcolor=TEKS, padding=4)
    gaya.map("TCombobox", bordercolor=[("focus", AKSEN)], fieldbackground=[("readonly", LATAR)])

    gaya.configure("TButton", background=LATAR, foreground=TEKS, bordercolor=GARIS,
                   focusthickness=2, focuscolor=AKSEN, padding=(10, 5), relief="flat")
    gaya.map("TButton",
             background=[("pressed", LATAR_LEMBUT), ("active", LATAR_LEMBUT)],
             bordercolor=[("focus", AKSEN)])
    gaya.configure("Utama.TButton", background=AKSEN, foreground="#FFFFFF", bordercolor=AKSEN)
    gaya.map("Utama.TButton",
             background=[("pressed", AKSEN), ("active", AKSEN_HOVER), ("disabled", "#9AA6AD")],
             foreground=[("disabled", "#FFFFFF")])
    gaya.configure("Hapus.TButton", background=LATAR, foreground=BAHAYA, bordercolor=GARIS)
    gaya.map("Hapus.TButton",
             foreground=[("active", BAHAYA), ("disabled", "#9AA6AD")],
             background=[("active", LATAR_LEMBUT)])

    gaya.configure("Treeview", background=LATAR, fieldbackground=LATAR, foreground=TEKS,
                   bordercolor=GARIS, rowheight=26)
    gaya.configure("Treeview.Heading", background=LATAR_LEMBUT, foreground=TEKS,
                   font=(HURUF, UKURAN_ISI, "bold"), relief="flat", borderwidth=1)
    gaya.map("Treeview", background=[("selected", "#DCE6EC")],
             foreground=[("selected", TEKS)])
    gaya.map("Treeview.Heading", relief=[("pressed", "flat")])

    gaya.configure("TNotebook", background=LATAR_LEMBUT, borderwidth=0)
    gaya.configure("TNotebook.Tab", background=LATAR_LEMBUT, foreground=TEKS_LEMBUT,
                   padding=(12, 6))
    gaya.map("TNotebook.Tab",
             background=[("selected", LATAR)], foreground=[("selected", TEKS)])
    gaya.configure("TSeparator", background=GARIS_HALUS)


def pasang_keyboard(akar: tk.Tk) -> None:
    """Escape menutup dialog yang sedang terbuka.

    Fokus keyboard di Tk sudah tampil sebagai cincin fokus dari style.
    """
    def _escape(event):
        w = akar.focus_get()
        while w is not None:
            if isinstance(w, (tk.Toplevel,)):
                w.grab_release() if w.grab_current() == w else None
                w.destroy()
                return "break"
            w = w.master
        return None

    akar.bind_all("<Escape>", _escape)


def dialog_modal(akar: tk.Tk, judul: str, lebar: int = 420, tinggi: int = 320) -> tk.Toplevel:
    jendela = tk.Toplevel(akar)
    jendela.title(judul)
    jendela.configure(background=LATAR)
    jendela.resizable(False, False)
    jendela.transient(akar)
    akar.update_idletasks()
    x = akar.winfo_rootx() + max((akar.winfo_width() - lebar) // 2, 0)
    y = akar.winfo_rooty() + max((akar.winfo_height() - tinggi) // 3, 0)
    jendela.geometry(f"{lebar}x{tinggi}+{x}+{y}")
    jendela.grab_set()
    DIALOG_TERAKHIR.append(judul)
    if MODE_UJI is not None:
        jendela.transient(None)
    return jendela


def pesan(akar: tk.Tk, judul: str, isi: str, jenis: str = "info") -> None:
    jendela = dialog_modal(akar, judul, 460, 200)
    warna = {"info": TEKS, "gagal": BAHAYA, "sukses": SUKSES}.get(jenis, TEKS)
    ttk.Label(jendela, text=judul, style="Judul.TLabel", background=LATAR,
              font=(HURUF, 12, "bold")).pack(anchor="w", padx=20, pady=(18, 6))
    ttk.Label(jendela, text=isi, background=LATAR, foreground=warna, wraplength=420,
              justify="left").pack(anchor="w", padx=20)
    tombol = ttk.Button(jendela, text="Tutup", style="Utama.TButton",
                        command=jendela.destroy)
    tombol.pack(side="bottom", anchor="e", padx=20, pady=16)
    tombol.focus_set()
    jendela.bind("<Return>", lambda e: jendela.destroy())
    if MODE_UJI is not None:
        return
    akar.wait_window(jendela)


def konfirmasi(akar: tk.Tk, judul: str, isi: str, label_aksi: str) -> bool:
    jendela = dialog_modal(akar, judul, 460, 210)
    hasil = {"ya": False}
    ttk.Label(jendela, text=judul, background=LATAR, foreground=TEKS,
              font=(HURUF, 12, "bold")).pack(anchor="w", padx=20, pady=(18, 6))
    ttk.Label(jendela, text=isi, background=LATAR, foreground=TEKS_LEMBUT, wraplength=420,
              justify="left").pack(anchor="w", padx=20)

    def ya():
        hasil["ya"] = True
        jendela.destroy()

    baris = ttk.Frame(jendela)
    baris.pack(side="bottom", fill="x", padx=20, pady=16)
    ttk.Button(baris, text="Batal", command=jendela.destroy).pack(side="right")
    t = ttk.Button(baris, text=label_aksi, style="Hapus.TButton", command=ya)
    t.pack(side="right", padx=(0, 8))
    t.focus_set()
    jendela.bind("<Return>", lambda e: ya())
    if MODE_UJI == "setuju":
        ya()
        return True
    if MODE_UJI is not None:
        jendela.destroy()
        return False
    akar.wait_window(jendela)
    return hasil["ya"]

def tangkap_jendela(jendela: tk.Misc, path: str) -> bool:
    """Simpan gambar jendela lewat PrintWindow Win32, dengan ImageGrab sebagai cadangan.

    ImageGrab (BitBlt) bisa mengembalikan gambar basi pada jendela berlapis di Windows,
    sehingga kontrol di sisi kanan bisa tampak hilang padahal ada di dalam layout.
    """
    try:
        import ctypes
        import ctypes.wintypes as wt
        from PIL import Image
    except ImportError:
        return False
    try:
        hwnd = ctypes.windll.user32.GetParent(jendela.winfo_id()) or jendela.winfo_id()
        rect = wt.RECT()
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        w, h = rect.right - rect.left, rect.bottom - rect.top
        if w <= 0 or h <= 0:
            return False
        hdc = ctypes.windll.user32.GetWindowDC(hwnd)
        mdc = ctypes.windll.gdi32.CreateCompatibleDC(hdc)
        bmp = ctypes.windll.gdi32.CreateCompatibleBitmap(hdc, w, h)
        ctypes.windll.gdi32.SelectObject(mdc, bmp)
        ok = ctypes.windll.user32.PrintWindow(hwnd, mdc, 2)

        class _Info(ctypes.Structure):
            _fields_ = [("biSize", wt.DWORD), ("biWidth", wt.LONG), ("biHeight", wt.LONG),
                        ("biPlanes", wt.WORD), ("biBitCount", wt.WORD),
                        ("biCompression", wt.DWORD), ("biSizeImage", wt.DWORD),
                        ("biXPelsPerMeter", wt.LONG), ("biYPelsPerMeter", wt.LONG),
                        ("biClrUsed", wt.DWORD), ("biClrImportant", wt.DWORD)]

        buf = ctypes.create_string_buffer(w * h * 4)
        info = _Info(ctypes.sizeof(_Info), w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
        ctypes.windll.gdi32.GetDIBits(mdc, bmp, 0, h, buf, ctypes.byref(info), 0)
        Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("RGB").save(path)
        ctypes.windll.gdi32.DeleteObject(bmp)
        ctypes.windll.gdi32.DeleteDC(mdc)
        ctypes.windll.user32.ReleaseDC(hwnd, hdc)
        return bool(ok)
    except Exception:
        return False
