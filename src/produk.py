"""Pencocokan nama produk antara lampiran supermarket dan kesepakatan.

Nama produk di lampiran disingkat dan berbeda-beda per supermarket
(mis. "OLAIF FLOSS SMOOTH ULTRA"), sedangkan di kesepakatan panjang
(mis. "Olaif Smooth Ultra Floss 50m"). Keputusan desain (dipilih user):
peta alias MANUAL -> akurat & bisa diperiksa, bukan fuzzy.

ALIAS: nama lampiran (HURUF BESAR) -> nama kesepakatan (kanonik).
Disemai dari sheet rincian terverifikasi pada contoh Rekap v5
(Rincian Aeon kolom J->K, Rincian Lotte 027 kolom B->C). Tambahkan entri
baru di sini bila muncul nama produk lampiran yang belum terdaftar.
"""
from __future__ import annotations

import re

ALIAS: dict[str, str] = {
    "OLAIF ACTIVE LAUNDRY PODS 240 GR": "Olaif Active Clean Laundry Pods 30 Pods",
    "OLAIF ALCOHOL WET WIPES 10S": "Olaif Alcohol Wet Wipes 10's",
    "OLAIF ANTISEPTIC WET WIPES 20S": "Olaif Antiseptic Wet Wipes 20 Sheets",
    "OLAIF DENTAL SENSITIVE TOOTHPASTE 200GR": "Olaif Dental Sensitive Toothpaste 200gr",
    "OLAIF DET ACTIVE CLEAN LAUNDRY PODS 30S": "Olaif Active Clean Laundry Pods 30 Pods",
    "OLAIF FLOSS SMOOTH ULTRA": "Olaif Smooth Ultra Floss 50m",
    "OLAIF GENTLE CARE BABY WIPES 80S": "Olaif Gentle Care Baby Wipes 80 Sheets",
    "OLAIF LIQ DET POWERFUL CLEANING REF 1L": "Olaif Powerful Cleaning Liquid Detergent Refill Pack 1 Liter",
    "OLAIF MEN SHAVER TRIPLE BLADE 5S": "Olaif Triple Blade Men's Shaver 5 Pcs",
    "OLAIF MULTI SURFACE ANTIBACTERIAL CLEANER 500 ML": "Olaif Multi-Surface Antibacterial Cleaner 500ml",
    "OLAIF MULTI SURFACE ANTIBACTERIAL CLEANER REF 500ML": "Olaif Multi-Surface Antibacterial Cleaner 500ml Refill Pack",
    "OLAIF POWER BLEACH TOILET CLEANER 500 ML": "Olaif Power Bleach Toilet Cleaner 500ml",
    "OLAIF POWERFUL CLEANING LIQUID DETERGENT 1000 ML": "Olaif Powerful Cleaning Liquid Detergent 1 Liter",
    "OLAIF PURPLE TOOTHPASTE 200GR": "Olaif Purple Toothpaste 200gr",
    "OLAIF TOOTHBRUSH PRO CLEAN SOFT": "Olaif Pro Clean Toothbrush Soft 1 Pcs",
    "OLAIF TOOTHBRUSH PRO CLEAN SOFT 3PCS": "Olaif Pro Clean Toothbrush Soft 3 Pcs",
    "OLAIF TOOTHPASTE COMPLETE CARE": "Olaif Complete Care Toothpaste 200gr",
    "OLAIF TOOTHPICK FLOSS CLASSIC": "Olaif Classic Floss Toothpick 50 Pcs",
    "OLAIF WOMEN SHAVER TRIPLE BLADE 3S": "Olaif Triple Blade Women's Shaver 3 Pcs",
}

# Penyatuan varian nama kanonik yang merujuk SKU sama tetapi beda tulisan
# antar file/tahun. Kunci & nilai dalam bentuk ter-normalisasi (lihat normkey).
SKU_CANON: dict[str, str] = {
    # Laundry Pods: 2025 "Olaif Active Laundry Pods" == 2026 "Olaif Active Clean Laundry Pods 30 Pods"
    "olaif active laundry pods": "olaif active clean laundry pods 30 pods",
    # Powerful Cleaning Liquid Detergent (non-refill) antar tahun
    "olaif powerful cleaning liquid detergent": "olaif powerful cleaning liquid detergent 1 liter",
    # Refill variants
    "olaif powerful cleaning liquid detergent refill": "olaif powerful cleaning liquid detergent refill pack 1 liter",
    "olaif powerful cleaning liquid detergent refill pack": "olaif powerful cleaning liquid detergent refill pack 1 liter",
    # Purple Toothpaste: 2025 "Olaif Purple Toothpaste" == 2026 "Olaif Dental Purple Toothpaste"
    "olaif purple toothpaste 200gr": "olaif dental purple toothpaste 200gr",
}


def normkey(name: str | None) -> str:
    """Kunci pencocokan: huruf kecil, tanpa tanda baca, spasi dirapatkan,
    lalu disatukan via SKU_CANON bila ada varian lintas-tahun."""
    if not name:
        return ""
    s = str(name).lower()
    s = s.replace("'", "")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = " ".join(s.split())
    return SKU_CANON.get(s, s)


def resolve(nama_lampiran: str | None) -> tuple[str | None, bool]:
    """Kembalikan (nama_kanonik, dikenali).

    dikenali=True bila nama lampiran ada di peta ALIAS. Bila tidak,
    nama dikembalikan apa adanya dengan dikenali=False (diperlakukan
    'dipercaya' oleh mesin pencocokan, bukan dituduh di luar kesepakatan).
    """
    if not nama_lampiran:
        return None, False
    key = " ".join(str(nama_lampiran).split()).upper()
    if key in ALIAS:
        return ALIAS[key], True
    return str(nama_lampiran).strip(), False
