# Dashboard Cek Klaim Rafaksi Olaif

Konteks proyek untuk Claude Code. Baca file ini sebelum mengerjakan apa pun.

## Tujuan

Kami (PT Laif Untuk Indonesia, brand Olaif) menjual produk di supermarket lewat distributor
PT Filia Sukses Mandiri. Kami memberi disc rafraksi ke supermarket. Setelah periode promo,
supermarket memotong ke distributor, lalu distributor menagih (klaim) ke kami.

Dashboard ini mengecek setiap tagihan distributor terhadap disc rafraksi yang disepakati,
lalu menampilkan mana yang sesuai, perlu konfirmasi, atau di luar kesepakatan, supaya finance
bisa memutuskan berapa yang dibayar.

Pengguna: tim marketing dan finance (bukan programmer). Bahasa antarmuka: Indonesia.

## Isi folder data/

- `data/kesepakatan/` : file disc rafraksi (Excel, format matriks).
  - `Promo_Olaif_2026_1.xlsx` sheet `OLAIF ` (ada spasi di akhir nama sheet): kolom B Nama Pelanggan
    (nama PT), C Nama Barang, D CBP (harga, sebagian besar kosong), E–P bulan Jan–Des 2026, isi disc
    pecahan (0.1 = 10%). Di bawah tabel utama (baris 235 dst) ada tabel tambahan:
    - Lotte promo tambahan (baris 235–238). Kolom kedua berjudul "Apr 2026" tapi posisinya di kolom
      Juni; dianggap Juni.
    - GO Empo AEON 29 Mei–10 Jun 2026 (baris 242–248).
    - AEON Festival Citylink dan AEON Pakuwon Surabaya, Diskon 25%, Des 2026–6 Jan 2027 (baris 251–260).
  - `Olaif_Q2_2025.xlsx`: Jan–Jun 2025, nama TOKO (AEON, Lotte Mart, Foodhall, ...). Pakai sheet
    `OLAIF (2)`; sheet `OLAIF Q2` hanya beda di 5 baris Lotte Juni. Ada isian Rp/pcs ("13.000/ pc").
  - `Promo_Olaif_Q4_2025_1.xlsx`: Okt–Des 2025, nama TOKO.
  - Data Jul–Sep 2025 belum ada.
- `data/invoice/` : PDF tagihan Filia (hasil scan) dan `List_Invoice_-_Filia.pdf` (daftar tagihan
  yang dibuat tim kami, total Rp 52.049.072 untuk batch Agustus 2026).
- `data/contoh/Rekap_Klaim_Rafaksi_Filia_Agustus_2026_v5.xlsx` : hasil pengecekan manual yang BENAR
  untuk batch Agustus 2026. Pakai sebagai acuan struktur output dan untuk menguji hasil.
- `data/contoh/hasil_baca_lampiran/*.json` : isi lampiran 21 PDF yang sudah dibaca dan diverifikasi
  (1.147 baris, per toko/produk). Pakai untuk menguji logika pencocokan TANPA memanggil API, dan
  sebagai jawaban benar saat menguji pembacaan PDF.

## Pemetaan nama PT dan toko

| PT | Toko | Nama di file kesepakatan lama |
|---|---|---|
| PT. Lotte Mart Indonesia | Lottemart | Lotte Mart |
| PT. Gracia Mitra Selaras | Market City | Market City |
| PT. Paligies Internasional | Jakarta Fruit Market | JFM Pluit |
| PT. Sumber Karya Digital | Trufarm | Trufarm |
| PT. Duta Cahaya Sukses | Duta Buah | Duta Buah |
| PT. Kage Dwijaya | Diamond Supermarket | Diamond |
| PT. Supra Boga Lestari (Tbk) | Ranch Market | Farmers |
| PT. Aeon Indonesia | Aeon | AEON, AEON SBY, AEON Festival Citylink, AEON Pakuwon Surabaya |
| PT. Swalayan Sukses Abadi | Food Hall | Foodhall |
| PT. Hero Retail Nusantara | Hero Supermarket | Hero |

Pelanggan lain di file kesepakatan (Doki, Akar Panji, Kawanua, Green Fresh, Star Maju, Laba Indo,
GS Supermarket, Kemchik, Superhiro, Freshmart) belum punya tagihan di batch ini.

## Format lampiran per supermarket (penting untuk pembacaan PDF)

Halaman 1 setiap PDF = invoice Filia. Halaman berikutnya = dokumen supermarket.
- Lotte: Debit Note + tabel per produk x toko (STR_CD 04001 dst, HARGA, SALE_QTY, SUPPORT %, RAFAKSI).
- Aeon: Invoice/Confirmation for Deduction + "Detail Calculation" per toko (kolom Remark = rafaksi
  per pcs). Ada program MEMBER DAY (diskon member, semua toko, per kuartal) yang TIDAK ada di
  kesepakatan. "Period: Monthly (JUN-2026)" di invoice AEON adalah bulan tagih, BUKAN periode promo;
  periode promo ada di deskripsi dan kolom Periode.
- Food Hall: Kwitansi + "Rincian Potongan" per site (XY02 dst), nilai SUDAH termasuk PPN 11%.
  Satu kwitansi bisa berisi beberapa dokumen (HABA, HOME, CLEANING). Selisih pembulatan Rp 1–39 wajar.
- Market City: laporan "Sales Performance by Supplier"; toko hanya rentang; baris yang diklaim
  ditandai/dicentang. Tanpa PPN.
- Hero: debit note bisa bercampur merek lain; lampiran per transaksi, toko MITRA dirinci.
- JFM, Trufarm, Duta Buah, Diamond: kwitansi sering memuat merek lain (Clara, Yuuka, Bara, Zozo);
  hanya baris Olaif yang ditagih ke kami.
- Ranch Market: debit note hanya total.

## Aturan pengecekan

1. Total lampiran (baris Olaif) harus sama dengan nilai di invoice Filia. Toleransi pembulatan < Rp 50.
2. Periode diambil dari lampiran supermarket, bukan dari keterangan Filia (Filia kadang menulis bulan tagih).
3. Disc acuan: cari baris kesepakatan dengan PT yang sama, produk yang sama (nama di lampiran berupa
   singkatan, perlu pencocokan nama), dan bulan yang beririsan dengan periode promo. Tahun 2025 Jan–Jun
   pakai Olaif_Q2_2025, Okt–Des 2025 pakai Promo_Olaif_Q4_2025_1, 2026 pakai Promo_Olaif_2026_1.
4. Bila lampiran memuat harga dan disc: rafaksi seharusnya = qty x harga x disc kesepakatan.
   Bila hanya rafaksi/pcs: hitung harga implisit = rafaksi per pcs / disc, bandingkan dengan CBP bila ada.
5. Status: Sesuai kesepakatan / Perlu konfirmasi (mis. Member Day, PPN ikut ditagih, klaim lebih dari
   12 bulan) / Di luar kesepakatan (produk tidak punya disc di bulan itu).
6. Cek klaim dobel: toko sama + produk sama + tanggal beririsan.
7. Kesepakatan khusus yang sudah dikonfirmasi: Laundry Pods Lotte 15% di Mei 2026 (barang mendekati expired).

## Hasil batch Agustus 2026 (acuan uji)

- Ditagih Rp 52.049.072 (36 baris klaim, 21 invoice, 10 supermarket).
- Perlu konfirmasi Rp 12.072.080: Member Day Aeon Rp 8.768.570, PPN Food Hall Rp 2.580.603,
  Market City periode Maret 2025 Rp 722.907.
- Di luar kesepakatan Rp 1.004.980: Women Shaver 3s, AEON BSD City (toko 1001), 8 Des 2025–4 Jan 2026.
- Sesuai Rp 38.972.012.

## Teknologi

- Python + Streamlit, berjalan lokal di PC Windows pengguna.
- Excel: openpyxl/pandas. PDF scan: halaman dikirim sebagai gambar ke Claude API (vision);
  API key dibaca dari file `.env` (ANTHROPIC_API_KEY), jangan pernah ditulis di kode.
- Simpan hasil baca PDF ke cache (JSON per invoice) supaya PDF yang sama tidak dibaca dua kali.
- Keputusan finance (Terima/Tahan/Tolak + catatan) disimpan ke file lokal (SQLite atau JSON).
- Ekspor hasil ke Excel dengan struktur seperti contoh v5.

## Cara kerja

- Kerjakan bertahap, tunjukkan hasil tiap tahap. Pengguna bukan programmer: jelaskan dengan bahasa
  sederhana dan beri perintah yang tinggal disalin bila perlu menjalankan sesuatu.
- Jangan mengubah atau menghapus file di `data/`. Output ke folder `output/`.
