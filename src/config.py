"""Lokasi folder & file acuan.

Semua path diturunkan dari folder proyek, jadi aplikasi bisa dipindah tanpa
mengubah kode. Folder ``data/`` diperlakukan read-only (acuan); semua hasil
ditulis ke ``output/``.
"""
from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
KESEPAKATAN_DIR = DATA_DIR / "kesepakatan"
INVOICE_DIR = DATA_DIR / "invoice"
CONTOH_DIR = DATA_DIR / "contoh"

OUTPUT_DIR = BASE_DIR / "output"
CACHE_DIR = OUTPUT_DIR / "cache_lampiran"   # cache hasil baca PDF (JSON per invoice)

# File kesepakatan bawaan (bisa ditimpa lewat unggahan di aplikasi).
FILE_2026 = KESEPAKATAN_DIR / "Promo_Olaif_2026_1.xlsx"
FILE_Q2_2025 = KESEPAKATAN_DIR / "Olaif_Q2_2025.xlsx"
FILE_Q4_2025 = KESEPAKATAN_DIR / "Promo_Olaif_Q4_2025_1.xlsx"

# Acuan uji (hasil pengecekan manual yang benar untuk batch Agustus 2026).
CONTOH_REKAP_V5 = CONTOH_DIR / "Rekap_Klaim_Rafaksi_Filia_Agustus_2026_v5.xlsx"
CONTOH_LAMPIRAN_DIR = CONTOH_DIR / "hasil_baca_lampiran"
