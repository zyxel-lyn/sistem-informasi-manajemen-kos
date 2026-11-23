# DESIGN

Arah visual v0.1. Status: PROPOSED BY AI — wajib dinyatakan draft tanpa arah bila client belum menyetujui bagian ini.

## Tujuan Visual

Aplikasi ini alat kerja admin yang dipakai sambil berdiri atau sambil melayani penghuni, sering di laptop panas dan terang. Prioritasnya **keterbacaan dan kecepatan menemukan data**, bukan keindahan. Tampilan harus terasa seperti buku catatan kerja yang rapi: netral, tenang, angka jelas, tanpa dekorasi yang mencuri perhatian. Kesannya harus seperti aplikasi kasir/administrasi kecil di kantor, bukan dashboard startup.

Arah ini ditetapkan AI sebagai usulan karena brief client belum menyebut referensi visual. Konsekuensinya: tampilan dapat diganti setelah client melihat versi pertama.

## Tiga Keputusan Visual yang Mengikat

1. **Tipografi.** Satu keluarga huruf sans-serif bawaan sistem (Segoe UI di Windows) untuk semua teks, dengan **dua ukuran kerja** saja: 11pt untuk isi dan 18pt untuk judul layar. Angka nominal dan nomor kamar ditampilkan **semibold** agar bisa dibandingkan sekilas. Tidak ada huruf dekoratif, tidak ada monospace dekoratif.
2. **Skala spasi.** Kelipatan 8: 8 / 16 / 24 / 32 px. Padding sel 8 px, jarak antar blok 16 px, jarak antar section 24 px. Tidak ada nilai spasi acak di satu layar dan berbeda di layar lain.
3. **Batasan pembeda produk.** **Warna dipakai fungsional, bukan dekoratif.** Hanya tiga warna status yang diizinkan muncul: hijau tua untuk "lunas/aktif", kuning kecokelatan untuk "belum bayar", merah bata untuk "menunggak/kurang bayar". Selain itu hanya netral (putih, abu-abu) plus satu warna aksen gelap untuk tombol utama. Tidak ada gradien, tidak ada glow, tidak ada kartu berbingkai tebal, tidak ada ilustrasi. Setiap layar terasa seperti lembar tabel yang tenang.

## Yang Sengaja Tidak Dipakai

- Gradien, glassmorphism, bayangan menyala.
- Ikon sparkle/magic/robot dan emoji dekoratif.
- Bagan donut atau grafik animasi; rekap ditampilkan sebagai angka dan tabel.
- Tema gelap sebagai default (pengguna kantor kecil lebih akrab dengan latar terang; tema gelap tidak diminta).
- Splash screen animasi.
- Menampilkan foto/avatar orang. Inisial nama sudah cukup.

## Token (ringkas)

Warna: hanya netral plus satu aksen gelap. Rasio kontras diukur dengan `contrast-check.py` dari skill antislop-human, bukan dikira-kira.

| Token | Nilai | Dipakai untuk | Kontras terukur |
|---|---|---|---|
| `surface.default` | #FFFFFF | latar tabel dan form | — |
| `surface.subtle` | #EFF3F6 | area kepala tabel, status bar | teks #1C2024 = 14.69:1 |
| `text.primary` | #1C2024 | isi utama | 16.39:1 di putih |
| `text.secondary` | #5B6470 | label, keterangan | 6.00:1 di putih |
| `border.default` | #8C949C | garis batas kontrol dan tabel | 3.07:1 (batas non-teks 3:1) |
| `border.subtle` | #D8DCE0 | garis antar baris tabel | dekoratif, bukan pembawa info |
| `action.primary` | #2F4858 | tombol utama, menu aktif | putih di atasnya 9.59:1 |
| `action.primary.hover` | #3A5566 | hover tombol utama | putih 7.86:1 |
| `status.success` | #1F6B4A | lunas/aktif | 6.44:1 di putih |
| `status.warning` | #8A6A1F | belum bayar | 5.05:1 di putih |
| `status.danger` | #96331F | menunggak, hapus | 7.53:1 di putih |
| `focus.ring` | #2F4858 | fokus keyboard | 9.59:1, tebal 2 px |

Radius 3 px untuk kontrol (konsisten, bukan pil). Tinggi kontrol 32 px, tinggi tombol baris 28 px. Tidak ada bayangan sama sekali: kedalaman dibawa oleh garis dan warna permukaan, bukan bayangan.

## Keputusan Visual yang Ditulis Alasannya

- **Satu aksen gelap biru-tinta (#2F4858)** untuk tombol utama dan menu aktif saja. Alasan: halaman berisi tabel data; aksen yang tersebar membuat angka kalah dari warna.
- **Warna hanya muncul pada kolom status** (lunas, belum bayar, menunggak) dan pada tombol hapus. Alasan: warna adalah informasi, bukan hiasan.
- **Tanpa ikon sama sekali di versi pertama.** Alasan: setiap ikon butuh alasan relevansi; label teks sudah cukup dan lebih cepat dibaca di tabel.
- **Tanpa grafik.** Rekap disajikan sebagai angka besar dan tabel. Alasan: pemilik kos butuh total dan nama, bukan tren.
- **Satu elemen yang memimpin tiap layar**: angka okupansi di dashboard, dan nama tabel di layar data. Alasan: mata harus punya tempat pertama mendarat.
- **Hierarki tipe 2 tingkat saja**: judul layar 18 pt, isi 11 pt. Alasan: aplikasi kerja, bukan halaman pemasaran.

## Dials

- **ENERGY 1**: alat kerja, tidak menyapa.
- **RHYTHM 2**: susunan seragam dalam satu layar, tetapi layar berbeda punya komposisi berbeda (dashboard angka, layar data tabel, laporan tabel plus total).
- **MOTION 1**: hanya perubahan state hover dan fokus. Tidak ada animasi masuk.

## Struktur Layar

- Jendela tunggal: sidebar kiri berisi menu sesuai role, area kerja kanan, status bar bawah.
- Tabel data di tengah; form tambah/ubah memakai dialog modal kecil dengan label di atas field (bukan placeholder sebagai satu-satunya label).
- Status bar menyebut nama pengguna, role, dan pesan hasil aksi terakhir.

## Copywriting

Bahasa Indonesia, kalimat perintah pendek. Tombol menyebut aksi konkret ("Simpan perubahan", "Catat pembayaran", "Tandai keluar"), bukan "Submit". Pesan kesalahan menyebut apa yang salah dan apa yang harus dilakukan ("Nomor kamar 01 sudah dipakai. Gunakan nomor lain."). Tidak ada em dash di seluruh teks antarmuka.

## State yang Wajib Ada

Kosong, terisi, dan gagal, ditambah state kontrol: hover, fokus, nonaktif. Setiap tabel punya pesan kosong yang menyebut langkah berikutnya ("Belum ada kamar. Tambah kamar pertama dengan tombol di atas."). Setiap kegagalan muncul sebagai pesan dialog yang bisa ditutup dengan Escape.

## Aksesibilitas

Fokus keyboard terlihat (garis 2 px #2F4858) di semua kontrol; urutan Tab mengikuti urutan baca; Enter mengaktifkan tombol utama dialog, Escape menutup dialog; setiap tabel punya header berlabel; status tidak hanya bergantung pada warna karena selalu ada kata "Lunas", "Belum bayar", "Kurang bayar".

