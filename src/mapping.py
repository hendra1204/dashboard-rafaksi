"""Peta nama pelanggan di file kesepakatan -> (PT resmi, Toko).

File kesepakatan 2026 memakai nama PT lengkap ("PT. AEON Indonesia"),
sedangkan file 2025 memakai nama toko singkat ("AEON", "Lotte Mart").
Tabel ini menyatukan keduanya ke satu PT + toko resmi.

Sumber: tabel "Pemetaan nama PT dan toko" di CLAUDE.md dan sheet
"Mapping PT-Toko" pada contoh Rekap v5. Pelanggan yang belum punya tagihan
di batch ini tetap dipetakan ke PT-nya sendiri dengan toko = None.
"""
from __future__ import annotations

# nama_di_file -> (pt, toko)
CUSTOMER_MAP: dict[str, tuple[str, str | None]] = {
    "AEON": ("PT. Aeon Indonesia", "Aeon"),
    "AEON Festival Citylink": ("PT. Aeon Indonesia", "Aeon"),
    "AEON Pakuwon Surabaya": ("PT. Aeon Indonesia", "Aeon"),
    "CV. Laba Indo Unggul": ("CV. Laba Indo Unggul", None),
    "Diamond": ("PT. Kage Dwijaya", "Diamond Supermarket"),
    "Duta Buah": ("PT. Duta Cahaya Sukses", "Duta Buah"),
    "Farmers": ("PT. Supra Boga Lestari", "Ranch Market"),
    "Foodhall": ("PT. Swalayan Sukses Abadi", "Food Hall"),
    "Freshmart": ("Freshmart", None),
    "GS Supermarket": ("GS Supermarket", None),
    "Hero": ("PT. Hero Retail Nusantara", "Hero Supermarket"),
    "JFM Pluit": ("PT. Paligies Internasional", "Jakarta Fruit Market"),
    "Kemchik": ("Kemchik", None),
    "Lotte Mart": ("PT. Lotte Mart Indonesia", "Lottemart"),
    "Market City": ("PT. Gracia Mitra Selaras", "Market City"),
    "PT. AEON Indonesia": ("PT. Aeon Indonesia", "Aeon"),
    "PT. Akar Panji Ulung": ("PT. Akar Panji Ulung", None),
    "PT. Doki Market Indonesia": ("PT. Doki Market Indonesia", None),
    "PT. Duta Cahaya Sukses": ("PT. Duta Cahaya Sukses", "Duta Buah"),
    "PT. Gracia Mitra Selaras": ("PT. Gracia Mitra Selaras", "Market City"),
    "PT. Green Fresh": ("PT. Green Fresh", None),
    "PT. Hero Retail Nusantara": ("PT. Hero Retail Nusantara", "Hero Supermarket"),
    "PT. Kage Dwijaya": ("PT. Kage Dwijaya", "Diamond Supermarket"),
    "PT. Kawanua Dasa Pratama": ("PT. Kawanua Dasa Pratama", None),
    "PT. Lotte Mart Indonesia": ("PT. Lotte Mart Indonesia", "Lottemart"),
    "PT. Paligies Internasional": ("PT. Paligies Internasional", "Jakarta Fruit Market"),
    "PT. Star Maju Sentosa": ("PT. Star Maju Sentosa", None),
    "PT. Sumber Karya Digital": ("PT. Sumber Karya Digital", "Trufarm"),
    "PT. Supra Boga Lestari Tbk": ("PT. Supra Boga Lestari", "Ranch Market"),
    "PT. Swalayan Sukses Abadi": ("PT. Swalayan Sukses Abadi", "Food Hall"),
    "Superhiro": ("Superhiro", None),
    "Trufarm": ("PT. Sumber Karya Digital", "Trufarm"),
}

# Nama toko -> PT (dipakai saat mencocokkan lampiran supermarket ke klaim).
TOKO_TO_PT: dict[str, str] = {
    toko: pt for (pt, toko) in CUSTOMER_MAP.values() if toko is not None
}


def _norm(name: str) -> str:
    return " ".join(str(name).split()).strip()


def map_customer(name: str) -> tuple[str, str | None]:
    """Kembalikan (pt, toko) untuk nama pelanggan di file kesepakatan.

    Jika nama tak dikenal, PT = nama itu sendiri dan toko = None (ditandai
    supaya bisa dilaporkan sebagai "perlu dipetakan").
    """
    if name is None:
        return ("(kosong)", None)
    key = _norm(name)
    if key in CUSTOMER_MAP:
        return CUSTOMER_MAP[key]
    # cocokkan tanpa membedakan huruf besar/kecil
    for k, v in CUSTOMER_MAP.items():
        if _norm(k).lower() == key.lower():
            return v
    return (key, None)


def is_unmapped(name: str) -> bool:
    """True bila nama pelanggan belum ada di tabel pemetaan."""
    key = _norm(name)
    if key in CUSTOMER_MAP:
        return False
    return not any(_norm(k).lower() == key.lower() for k in CUSTOMER_MAP)
