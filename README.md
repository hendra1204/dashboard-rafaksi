# Dashboard Cek Klaim Rafaksi Olaif

Mengecek tagihan klaim rafaksi dari distributor (PT Filia) terhadap kesepakatan
disc rafaksi, lalu menampilkan mana yang **Sesuai / Perlu konfirmasi / Di luar
kesepakatan** supaya finance bisa memutuskan berapa yang dibayar.

Semua angka **dihitung dari data** (file kesepakatan + lampiran invoice), bukan
ditulis langsung.

## Cara menjalankan

Pertama kali, pasang kebutuhannya:

```bash
pip install -r requirements.txt
```

Jalankan dashboard:

```bash
streamlit run app.py
```

Nanti terbuka di browser (biasanya http://localhost:8501).

## Cara cek cepat (tanpa buka dashboard)

```bash
python -m src.kesepakatan     # ringkasan file kesepakatan (1.814 baris)
python -m src.pencocokan      # uji pencocokan vs acuan v5 (harus SEMUA COCOK)
```

## Struktur

```
app.py                     tampilan Streamlit (dashboard)
src/
  config.py                lokasi folder & file
  mapping.py               peta nama pelanggan -> PT + toko
  kesepakatan.py           baca 3 file kesepakatan -> 1 tabel panjang
  produk.py                peta alias nama produk (lampiran <-> kesepakatan)
  lampiran.py              baca hasil baca PDF (JSON) -> daftar klaim
  pencocokan.py            mesin status + cek klaim dobel
  referensi.py             nama toko AEON, util format/bulan
  dashboard_data.py        siapkan data untuk tampilan
data/                      acuan (JANGAN diubah) - kesepakatan, invoice, contoh
output/                    hasil (Excel, cache baca PDF)
```

## Status pengerjaan

- Tahap 1 — baca & normalisasi kesepakatan: **selesai** (cocok 100% dgn acuan v5).
- Tahap 2 — mesin pencocokan + status + cek dobel: **selesai** (angka cocok v5).
- Tahap 3 — tampilan dashboard sesuai desain: **selesai** (ringkasan, tabel per
  supermarket, temuan + tombol Terima/Tahan/Tolak, garis waktu per toko x periode).
- Tahap 5 — simpan keputusan finance (SQLite) + ekspor Excel: **selesai**.
  Keputusan Terima/Tahan/Tolak + catatan tersimpan permanen ke `output/keputusan.db`
  dan tetap ada setelah aplikasi ditutup. Tombol "Unduh Excel" aktif: mengekspor
  ringkasan, per klaim, per supermarket, temuan + keputusan, di luar, perlu
  konfirmasi, cek klaim dobel — plus hitungan dibayar/ditahan/ditolak.
- Tahap 4 — baca PDF scan via Claude API (vision) + cache: **kode siap**, tinggal
  dijalankan. PDF dikirim langsung sebagai dokumen ke Claude, hasilnya disimpan ke
  `output/cache_lampiran/`. Dashboard otomatis memakai cache itu bila sudah ada.

### Menjalankan pembacaan PDF (Tahap 4)

1. Salin `.env.example` menjadi `.env`, isi `ANTHROPIC_API_KEY`.
2. Taruh 21 PDF (`Laif VIII-027.pdf` … `Laif VIII-047.pdf`) di `data/invoice/`.
3. Uji dulu 2 PDF dan bandingkan ke contoh:

   ```bash
   python uji_baca_pdf.py 027 040
   ```

4. Baca semua lalu buka dashboard:

   ```bash
   python -c "from src.baca_pdf import baca_folder; baca_folder()"
   streamlit run app.py
   ```

Pembacaan memanggil Claude API (berbiaya); hasil di-cache agar PDF yang sama tidak
dibaca dua kali.

Tombol **"Unggah kesepakatan"** & **"Unggah invoice"** aktif: membuka jendela unggah yang
menyimpan file ke `data/kesepakatan/` atau `data/invoice/` (tanpa menimpa file lama kecuali
dicentang). Kesepakatan (Excel) langsung terbaca; PDF invoice baru masih perlu dibaca dulu
(lewat sesi Claude Code atau API) agar muncul.

Belum tersambung: pemilih batch (saat ini satu batch: Agustus 2026).
