# Panduan Pemakaian — Dashboard Cek Klaim Rafaksi Olaif

Panduan singkat untuk tim marketing & finance (bukan programmer).

---

## 1. Apa ini?

Dashboard untuk mengecek tagihan klaim rafaksi dari distributor **PT Filia** terhadap
kesepakatan disc rafaksi, lalu menampilkan mana yang:
- **Sesuai kesepakatan** — layak dibayar,
- **Perlu konfirmasi** — mis. Member Day, PPN ikut ditagih, klaim lewat 1 tahun,
- **Di luar kesepakatan** — tidak ada disc di periode itu.

Semua angka dihitung otomatis dari data, bukan diketik manual.

---

## 2. Cara membuka dashboard

Alamatnya (hanya aktif selama aplikasi dijalankan di PC ini, **bukan link internet**):

```
http://localhost:8531
```

**Penting:** buka di **browser biasa (Chrome/Edge) dan besarkan jendelanya (maximize)**.
- Jendela lebar → tampil **dua kolom** (Per supermarket di kiri, Temuan di kanan) seperti desain.
- Jendela/panel sempit → tampilan **menumpuk ke bawah** (otomatis, bukan rusak).

Kalau aplikasi sudah ditutup dan ingin dibuka lagi, minta bantuan lewat sesi Claude Code
untuk menjalankannya kembali.

---

## 3. Menaruh file baru

Ada **dua cara**:

**Cara A — lewat tombol di dashboard (paling mudah):**
- Klik **"Unggah kesepakatan"** atau **"Unggah invoice"** di kanan atas.
- Pilih file, lalu **Simpan**. File otomatis masuk ke folder yang benar.
- Untuk kesepakatan: centang "Izinkan mengganti file lama yang namanya sama" **hanya**
  bila memang ingin memperbarui file baku (kalau tidak dicentang, file lama aman dan yang
  baru disimpan sebagai salinan).

**Cara B — salin langsung ke folder** (jangan hapus/ubah file lama):

| Jenis file | Folder |
|---|---|
| Tagihan / invoice (PDF) | `data\invoice\` |
| Kesepakatan disc (Excel) | `data\kesepakatan\` |

Setelah menaruh **PDF invoice baru** (cara A maupun B), **beri tahu lewat sesi Claude Code**
("ada invoice baru di data/invoice"). PDF perlu **dibaca dulu** sebelum muncul di dashboard.
File kesepakatan (Excel) langsung terbaca setelah disimpan.

---

## 4. Soal biaya

- Untuk data yang **sudah dibaca** (batch Agustus 2026): **gratis**, langsung jalan.
- Untuk **PDF baru**: bisa **gratis** — kirim ke sesi Claude Code, dibaca di situ lalu
  hasilnya tersimpan dan muncul di dashboard.
- Pembacaan otomatis di dalam aplikasi (pakai API key berbayar) **opsional**, tidak wajib.

---

## 5. Memutuskan & mengekspor

- Di bagian **"Temuan yang perlu diputuskan"**, tiap temuan punya tombol
  **Terima / Tahan / Tolak** + kolom catatan. Keputusan tersimpan permanen.
  - **Terima** → nilainya pindah ke **Sesuai kesepakatan** (menambah "Layak dibayar
    sekarang"), dan kartunya pindah ke daftar kecil **"Diterima"** (bisa dibatalkan
    lewat tombol **Ubah**).
  - **Tahan** → kartu tetap tampil penuh (label "Ditahan"); nilainya tetap di
    **Perlu konfirmasi**.
  - **Tolak** → kartu jadi ringkas (judul + angka + alasan + **Ubah**); nilainya pindah
    ke **Di luar kesepakatan** (tidak dibayar).
  - Angka ringkasan di atas (Sesuai / Perlu konfirmasi / Di luar / Layak dibayar) **ikut
    berubah otomatis** mengikuti keputusan; totalnya selalu tetap Rp 52.049.072.
- Tombol **"Unduh Excel"** di kanan atas mengunduh hasil lengkap (ringkasan, per klaim,
  per supermarket, temuan + keputusan, dll).

---

## 6. Catatan aman

- File di folder `data\` jangan diubah/dihapus — cukup **tambah** file baru.
- Hasil (Excel, dll) keluar ke folder `output\`.
