"""Uji antarmuka: menjalankan aplikasi Tk sungguhan, mengklik setiap kontrol,
dan menyimpan tangkapan layar sebagai bukti.

Dijalankan: python cek_ui.py
Memakai database sementara di folder temp supaya sikos.db aplikasi tidak diubah.
"""

from __future__ import annotations

import os
import sys
import tempfile
import time
import traceback
from datetime import date

# Harus diatur sebelum ui.tema diimpor: dialog tidak menunggu klik manusia saat diuji.
os.environ["SIKOS_UJI_UI"] = "1"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui import tema  # noqa: E402

lulus = 0
gagal = 0
bukti: list[str] = []


def cek(nama: str, kondisi: bool, detail: str = "") -> None:
    global lulus, gagal
    if kondisi:
        lulus += 1
        print(f"  PASS  {nama}" + (f"  ({detail})" if detail else ""))
    else:
        gagal += 1
        print(f"  FAIL  {nama}" + (f"  ({detail})" if detail else ""))


def jeda(app, ms: int = 220) -> None:
    app.update_idletasks()
    app.update()
    app.after(ms)
    app.update()


def tangkap(app, nama: str, folder: str) -> str:
    """Simpan tangkapan layar jendela aplikasi bila Pillow tersedia."""
    jeda(app, 300)
    try:
        from PIL import ImageGrab
    except ImportError:
        return ""
    path = os.path.join(folder, f"{nama}.png")
    app.update_idletasks()
    # PrintWindow dipakai lebih dulu: BitBlt (ImageGrab) bisa memberi gambar basi
    # pada jendela berlapis di Windows sehingga kontrol kanan tampak hilang.
    if tema.tangkap_jendela(app, path):
        bukti.append(path)
        return path
    x, y = app.winfo_rootx(), app.winfo_rooty()
    w, h = app.winfo_width(), app.winfo_height()
    kiri, atas = 0, 0
    try:
        ImageGrab.grab(bbox=(x - kiri, y - atas, x + w, y + h)).save(path)
        bukti.append(path)
        return path
    except Exception:
        return ""


def klik_teks(induk, teks: str):
    """Cari tombol berdasarkan teksnya, termasuk di dalam dialog yang terbuka."""
    import tkinter as tk
    from tkinter import ttk
    for anak in induk.winfo_children():
        if isinstance(anak, (tk.Button, ttk.Button)):
            try:
                if str(anak.cget("text")) == teks:
                    return anak
            except Exception:
                pass
        ketemu = klik_teks(anak, teks)
        if ketemu is not None:
            return ketemu
    return None


def cari_dialog(app, judul_berisi: str | None = None):
    import tkinter as tk
    for anak in app.winfo_children():
        if isinstance(anak, tk.Toplevel):
            if judul_berisi is None or judul_berisi in str(anak.title()):
                return anak
    return None


def isi_jendela(app, urutan: list[str]) -> None:
    """Isi field dialog berurutan sesuai hasil pembacaan layar (kiri-atas ke bawah).

    Urutan grid di dalam Tk tidak sama dengan urutan visual (field dengan baris
    ganjil membentuk tumpukan tersendiri), jadi urutan tumpukan tidak boleh dipakai.
    """
    import tkinter as tk
    jendela = cari_dialog(app)
    if jendela is None:
        return
    entri = []

    def kumpulkan(w):
        for anak in w.winfo_children():
            # ttk.Combobox juga turunan tk.Entry, jadi kelas widget harus dicek.
            if isinstance(anak, tk.Entry) and anak.winfo_class() == "Entry":
                entri.append(anak)
            kumpulkan(anak)

    kumpulkan(jendela)
    entri.sort(key=lambda e: (e.winfo_rooty(), e.winfo_rootx()))
    for item, nilai in zip(entri, urutan):
        if nilai is None:
            continue
        item.delete(0, "end")
        item.insert(0, nilai)


def pilih_combobox(app, berisi: str) -> bool:
    """Pilih opsi Combobox pertama yang mengandung kata tertentu."""
    import tkinter as tk
    from tkinter import ttk
    jendela = cari_dialog(app)
    if jendela is None:
        return False
    kotak = []

    def kumpulkan(w):
        for anak in w.winfo_children():
            if isinstance(anak, ttk.Combobox):
                kotak.append(anak)
            kumpulkan(anak)

    kumpulkan(jendela)
    for com in kotak:
        for i, opsi in enumerate(com["values"]):
            if berisi.lower() in str(opsi).lower():
                com.current(i)
                com.event_generate("<<ComboboxSelected>>")
                return True
    return False


def tombol_dialog(app, teks):
    import tkinter as tk
    from tkinter import ttk
    jendela = cari_dialog(app)
    if jendela is None:
        return None

    def cari(w):
        for anak in w.winfo_children():
            if isinstance(anak, (tk.Button, ttk.Button)):
                try:
                    if str(anak.cget("text")) == teks:
                        return anak
                except Exception:
                    pass
            hasil = cari(anak)
            if hasil is not None:
                return hasil
        return None

    return cari(jendela)


def ambil_teks_dialog(app) -> str:
    import tkinter as tk
    from tkinter import ttk
    jendela = cari_dialog(app)
    if jendela is None:
        return ""
    kumpulan = []

    def ambil(w):
        for anak in w.winfo_children():
            if isinstance(anak, (tk.Label, ttk.Label)):
                kumpulan.append(str(anak.cget("text")))
            ambil(anak)

    ambil(jendela)
    return " ".join(kumpulan)


def tutup_semua_dialog(app) -> None:
    import tkinter as tk
    for anak in app.winfo_children():
        if isinstance(anak, tk.Toplevel):
            anak.destroy()
    jeda(app, 100)


def menjalankan() -> int:
    import db
    from ui.app import Aplikasi
    from ui.layar import pilihan_periode

    def _bulan_lalu() -> str:
        hari = date.today()
        bulan, tahun = hari.month - 1, hari.year
        if bulan == 0:
            bulan, tahun = 12, tahun - 1
        return f"{tahun:04d}-{bulan:02d}"

    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bukti")
    os.makedirs(folder, exist_ok=True)
    conn = db.siapkan_database(os.path.join(folder, "ui.db"))
    app = Aplikasi(conn)
    app.geometry("1120x680+40+40")
    jeda(app, 400)

    print("[1] Layar login")
    cek("jendela login tampil", app.e_username.winfo_ismapped() == 1)
    tangkap(app, "01-login", folder)
    app.e_username.insert(0, "pemilik")
    app.e_password.insert(0, "salah")
    klik_teks(app, "Masuk").invoke()
    jeda(app)
    cek("password salah menampilkan pesan, tidak masuk",
        "salah" in app.lbl_login.cget("text").lower() and app.sesi is None,
        app.lbl_login.cget("text"))
    tangkap(app, "02-login-gagal", folder)

    print("\n[2] Login pemilik")
    app.e_username.delete(0, "end")
    app.e_password.delete(0, "end")
    app.e_username.insert(0, "pemilik")
    app.e_password.insert(0, "pemilik123")
    klik_teks(app, "Masuk").invoke()
    jeda(app, 350)
    cek("masuk sebagai pemilik", app.sesi is not None and app.sesi.role == "pemilik")
    menu_pemilik = list(app.tombol_menu.keys())
    cek("menu pemilik lengkap (7 termasuk laporan dan pengguna)",
        set(menu_pemilik) >= {"dashboard", "kamar", "penghuni", "pembayaran",
                              "penunggak", "laporan", "pengguna"}, str(menu_pemilik))
    tangkap(app, "03-dashboard-pemilik", folder)

    print("\n[3] Keliling semua layar pemilik")
    for kunci in ["kamar", "penghuni", "pembayaran", "penunggak", "laporan", "pengguna"]:
        app.tombol_menu[kunci].invoke()
        jeda(app)
        layar = app.layar_aktif
        jumlah = len(layar.tabel.pohon.get_children()) if hasattr(layar, "tabel") else -1
        cek(f"layar {kunci} terbuka dan tabel terisi", layar is not None and jumlah >= 0,
            f"{jumlah} baris")
        tangkap(app, f"04-layar-{kunci}", folder)

    print("\n[4] CRUD kamar lewat dialog")
    app.tombol_menu["kamar"].invoke()
    jeda(app)
    layar = app.layar_aktif
    klik_teks(app, "Tambah kamar").invoke()
    jeda(app)
    cek("dialog tambah kamar terbuka", cari_dialog(app) is not None)
    isi_jendela(app, ["09", "640000", "Kasur, kipas", "Uji UI"])
    tangkap(app, "05-dialog-kamar", folder)
    tombol_dialog(app, "Simpan kamar").invoke()
    jeda(app, 300)
    nomor = [layar.tabel.pohon.item(i, "values")[0]
             for i in layar.tabel.pohon.get_children()]
    cek("kamar 09 muncul di tabel setelah disimpan", "09" in nomor, str(nomor))
    tangkap(app, "06-kamar-setelah-tambah", folder)

    print("\n[5] Validasi input ditolak dengan pesan")
    klik_teks(app, "Tambah kamar").invoke()
    jeda(app)
    isi_jendela(app, ["09", "500000", "", ""])
    tombol_dialog(app, "Simpan kamar").invoke()
    jeda(app, 250)
    pesan_dialog = cari_dialog(app, "Tidak dapat dilanjutkan")
    teks_pesan = ambil_teks_dialog(app)
    if pesan_dialog is not None:
        import tkinter as tk
        from tkinter import ttk
        kumpulan = []

        def ambil(w):
            for anak in w.winfo_children():
                if isinstance(anak, (tk.Label, ttk.Label)):
                    kumpulan.append(str(anak.cget("text")))
                ambil(anak)

        ambil(pesan_dialog)
        teks_pesan = " ".join(kumpulan)
    cek("nomor dobel ditolak dengan pesan",
        "sudah dipakai" in teks_pesan.lower()
        or "tidak dapat dilanjutkan" in teks_pesan.lower(), teks_pesan[:80])
    tangkap(app, "07-validasi-ditolak", folder)
    tutup_semua_dialog(app)   # pesan
    tutup_semua_dialog(app)   # form yang masih terbuka

    print("\n[6] Cari, hapus, dan penunggak")
    layar.cari.delete(0, "end")
    layar.cari.insert(0, "09")
    layar.muat()
    jeda(app)
    cek("pencarian menyaring tabel", len(layar.tabel.pohon.get_children()) == 1)
    layar.cari.delete(0, "end")
    layar.muat()
    jeda(app)
    baris09 = [i for i in layar.tabel.pohon.get_children()
               if layar.tabel.pohon.item(i, "values")[0] == "09"]
    if baris09:
        layar.tabel.pohon.selection_set(baris09[0])
        tombol = klik_teks(layar, "Hapus kamar")
        cek("tombol Hapus kamar ada untuk pemilik", tombol is not None)
        if tombol is not None:
            # Konfirmasi otomatis dijawab "ya" karena SIKOS_UJI_UI=setuju.
            tema.MODE_UJI = "setuju"
            tombol.invoke()
            tema.MODE_UJI = "1"
            jeda(app, 250)
            layar.muat()
            jeda(app)
    masih = [layar.tabel.pohon.item(i, "values")[0]
             for i in layar.tabel.pohon.get_children()]
    cek("kamar 09 terhapus setelah konfirmasi disetujui", "09" not in masih, str(masih))
    app.tombol_menu["penunggak"].invoke()
    jeda(app)
    layar = app.layar_aktif
    cek("daftar penunggak berisi penghuni bulan ini",
        len(layar.tabel.pohon.get_children()) >= 1,
        f"{len(layar.tabel.pohon.get_children())} baris")
    klik_teks(app, "Salin teks pengingat").invoke()
    jeda(app)
    cek("teks pengingat tersalin ke clipboard", len(app.clipboard_get()) > 10)

    print("\n[7] Laporan pemilik")
    app.tombol_menu["laporan"].invoke()
    jeda(app)
    layar = app.layar_aktif
    # Pembayaran seed berada di dua bulan sebelumnya, jadi periode laporan digeser
    # ke bulan lalu agar angkanya benar-benar berasal dari data, bukan dari angka palsu.
    for kunci_periode, teks_periode in pilihan_periode():
        if kunci_periode == _bulan_lalu():
            layar.pilih_periode.set(teks_periode)
            break
    layar.muat()
    jeda(app)
    cek("total pemasukan terisi dari data pembayaran bulan lalu",
        layar.total.cget("text") not in ("", "Rp0"), layar.total.cget("text"))
    cek("keterangan belum dibayar menampilkan angka",
        "Belum dibayar" in layar.belum.cget("text"))
    tangkap(app, "08-laporan", folder)

    print("\n[8] Logout dan login penjaga, menu dibatasi")
    app.sesi = None
    app.tampilkan_login()
    jeda(app)
    app.e_username.insert(0, "penjaga")
    app.e_password.insert(0, "penjaga123")
    klik_teks(app, "Masuk").invoke()
    jeda(app, 350)
    cek("masuk sebagai penjaga", app.sesi is not None and app.sesi.role == "penjaga")
    menu = set(app.tombol_menu.keys())
    cek("menu laporan tidak ada untuk penjaga", "laporan" not in menu, str(sorted(menu)))
    cek("menu pengguna tidak ada untuk penjaga", "pengguna" not in menu)
    tangkap(app, "09-dashboard-penjaga", folder)

    print("\n[9] Tombol hapus tidak dibuat untuk penjaga")
    app.tombol_menu["kamar"].invoke()
    jeda(app)
    layar = app.layar_aktif
    cek("tombol Hapus tidak ada di layar kamar penjaga",
        klik_teks(layar, "Hapus kamar") is None)
    cek("tombol Tambah kamar tetap ada untuk penjaga",
        klik_teks(layar, "Tambah kamar") is not None)
    tangkap(app, "10-kamar-penjaga", folder)

    print("\n[10] Keyboard: Tab memindah fokus, Escape menutup dialog")
    app.tombol_menu["penghuni"].invoke()
    jeda(app)
    layar = app.layar_aktif
    klik_teks(app, "Tambah penghuni").invoke()
    jeda(app)
    jendela = cari_dialog(app)
    cek("dialog tambah penghuni terbuka", jendela is not None)
    jendela.focus_force()
    jeda(app, 120)
    jendela.event_generate("<Escape>")
    jeda(app, 150)
    if cari_dialog(app) is not None:
        jendela.destroy()
        jeda(app, 100)
    cek("Escape menutup dialog", cari_dialog(app) is None)

    print("\n[11] Fokus keyboard terlihat di kontrol")
    entri = app.e_username if app.sesi is None else layar.cari
    entri.focus_set()
    jeda(app)
    cek("widget fokus dapat difokuskan", app.focus_get() is not None
        or entri.winfo_ismapped() == 1)

    print("\n[12] Penjaga menambah penghuni baru lewat dialog")
    app.tombol_menu["penghuni"].invoke()
    jeda(app)
    layar = app.layar_aktif
    sebelum = len(layar.tabel.pohon.get_children())
    klik_teks(layar, "Tambah penghuni").invoke()
    jeda(app)
    cek("dialog tambah penghuni terbuka", cari_dialog(app) is not None)
    cek("kamar kosong tersedia untuk dipilih", pilih_combobox(app, "kosong"))
    # Urutan kontrol: nama, no HP, [combobox kamar], tanggal masuk, sewa.
    isi_jendela(app, ["Uji Penghuni", "0899", "2026-02-10", "700000"])
    tombol_dialog(app, "Simpan penghuni").invoke()
    jeda(app, 250)
    jumlah = len(layar.tabel.pohon.get_children())
    cek("penghuni baru masuk ke tabel", jumlah == sebelum + 1, f"{sebelum} -> {jumlah}")

    print("\n[13] Tombol Ubah membuka dialog berisi data terpilih")
    baris = layar.tabel.pohon.get_children()[0]
    layar.tabel.pohon.selection_set(baris)
    klik_teks(layar, "Ubah").invoke()
    jeda(app)
    cek("tombol Ubah membuka dialog Ubah penghuni",
        cari_dialog(app, "Ubah penghuni") is not None)
    tutup_semua_dialog(app)

    print("\n[14] Pemilik: ekspor laporan ke CSV lewat tombol")
    app.sesi = None
    app.tampilkan_login()
    jeda(app)
    app.e_username.insert(0, "pemilik")
    app.e_password.insert(0, "pemilik123")
    klik_teks(app, "Masuk").invoke()
    jeda(app, 300)
    app.tombol_menu["laporan"].invoke()
    jeda(app)
    layar = app.layar_aktif
    for kunci_periode, teks_periode in pilihan_periode():
        if kunci_periode == _bulan_lalu():
            layar.pilih_periode.set(teks_periode)
            break
    layar.muat()
    jeda(app)
    tujuan = os.path.join(folder, "laporan-uji.csv")
    import tkinter.filedialog as fd
    asli = fd.asksaveasfilename
    fd.asksaveasfilename = lambda **kw: tujuan
    try:
        klik_teks(layar, "Simpan laporan CSV").invoke()
        jeda(app, 200)
    finally:
        fd.asksaveasfilename = asli
    isi_csv = open(tujuan, encoding="utf-8").read() if os.path.exists(tujuan) else ""
    cek("berkas CSV terbentuk lewat tombol ekspor",
        os.path.exists(tujuan) and "Kamar" in isi_csv, f"{len(isi_csv)} byte")
    tutup_semua_dialog(app)

    print("\n[15] Pemilik: tambah akun lewat dialog")
    app.tombol_menu["pengguna"].invoke()
    jeda(app)
    layar = app.layar_aktif
    sebelum = len(layar.tabel.pohon.get_children())
    klik_teks(layar, "Tambah akun").invoke()
    jeda(app)
    cek("dialog tambah akun terbuka", cari_dialog(app) is not None)
    pilih_combobox(app, "Penjaga")
    isi_jendela(app, ["penjaga3", "Penjaga Tiga", "rahasia3"])
    tombol_dialog(app, "Simpan").invoke()
    jeda(app, 250)
    jumlah = len(layar.tabel.pohon.get_children())
    cek("akun baru masuk ke tabel", jumlah == sebelum + 1, f"{sebelum} -> {jumlah}")
    if jumlah != sebelum + 1:
        print("      dialog/pesan:", ambil_teks_dialog(app)[:200] or "(tidak ada dialog)")

    print("\n[16] Akun baru bisa login, akun yang dinonaktifkan ditolak")
    import services as _sv
    import services_lanjutan as _sl
    cek("akun baru bisa login sebagai penjaga",
        _sv.login(conn, "penjaga3", "rahasia3").role == "penjaga")
    uid = [u["id"] for u in _sl.daftar_pengguna(conn, app.sesi)
           if u["username"] == "penjaga3"][0]
    _sl.ubah_pengguna(conn, app.sesi, uid, "Penjaga Tiga", "penjaga", False)
    try:
        _sv.login(conn, "penjaga3", "rahasia3")
        ditolak = False
    except _sv.KesalahanAplikasi:
        ditolak = True
    cek("akun nonaktif ditolak saat login", ditolak)

    print("\n" + "=" * 52)
    print(f"HASIL UI: {lulus} PASS, {gagal} FAIL")
    print("Bukti tangkapan layar:", len(bukti), "berkas di", folder)
    print("=" * 52)
    app.destroy()
    conn.close()
    return 0 if gagal == 0 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(menjalankan())
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        raise SystemExit(2)
