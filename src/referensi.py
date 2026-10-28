"""Data acuan kecil untuk tampilan: nama toko AEON & util format/bulan."""
from __future__ import annotations

import datetime as dt

# Kode toko AEON -> nama (dari lampiran AEON, disalin ke contoh v5).
AEON_STORE_NAMES: dict[str, str] = {
    "1001": "AEON BSD City",
    "1005": "AEON Deltamas",
    "1006": "AEON toko 1006",
    "1009": "AEON toko 1009",
    "1010": "AEON Eastvara",
    "7002": "AEON toko 7002",
    "7003": "AEON Health & Beauty BXC",
}

_BULAN_SINGKAT = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
                  "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
_BULAN_PANJANG = ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
                  "Juli", "Agustus", "September", "Oktober", "November", "Desember"]


def label_bulan(d: dt.date) -> str:
    return f"{_BULAN_SINGKAT[d.month - 1]} {d.year % 100:02d}"


def label_bulan_y4(d: dt.date) -> str:
    return f"{_BULAN_SINGKAT[d.month - 1]} {d.year}"


def bulan_panjang(d: dt.date) -> str:
    return f"{_BULAN_PANJANG[d.month - 1]} {d.year}"


def fmt_rp(n: float) -> str:
    """1234567 -> 'Rp 1.234.567'."""
    return "Rp " + f"{round(n):,}".replace(",", ".")


def fmt_short(n: float) -> str:
    """Nilai ringkas: >=1 jt -> 'X,XX jt' (nol di belakang dibuang),
    >=1 rb -> 'XXX rb', selain itu angka utuh."""
    n = round(n)
    if abs(n) >= 1_000_000:
        v = round(n / 1_000_000, 2)
        s = f"{v:.2f}".rstrip("0").rstrip(".").replace(".", ",")
        return f"{s} jt"
    if abs(n) >= 1_000:
        return f"{round(n / 1_000)} rb"
    return str(n)


def iter_months(start: dt.date, end: dt.date) -> list[dt.date]:
    """Daftar awal-bulan dari bulan start s.d. bulan end (inklusif)."""
    out = []
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        out.append(dt.date(y, m, 1))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return out
