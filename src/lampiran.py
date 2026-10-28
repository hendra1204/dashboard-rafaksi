"""Muat hasil baca lampiran (JSON per invoice) menjadi daftar klaim.

Sumber JSON: cache hasil baca PDF (Tahap 4) atau folder contoh
``data/contoh/hasil_baca_lampiran`` untuk pengujian tanpa API.

Struktur JSON per invoice:
    { "invoice", "supermarket", "claim_lines": [
        { "filia_label", "filia_amount", "program", "periode_mulai",
          "periode_akhir", "includes_ppn", "rows": [
             {"store_code","store_name","product","qty","harga",
              "disc_pct","rafaksi_per_pcs","dpp","ppn","total"} ] } ] }
"""
from __future__ import annotations

import datetime as dt
import glob
import json
import os
from dataclasses import dataclass, field

from src.mapping import CUSTOMER_MAP

# PT kanonik -> toko (dari peta pelanggan).
_PT_TOKO = {pt: toko for (pt, toko) in CUSTOMER_MAP.values() if toko is not None}


def _norm_pt(s: str) -> str:
    s = str(s).lower()
    s = s.split("(")[0]                       # buang "(Hero Supermarket)"
    s = s.replace("pt.", " ").replace("pt ", " ").replace("tbk", " ")
    s = "".join(ch if ch.isalnum() or ch == " " else " " for ch in s)
    return " ".join(s.split())


_PT_INDEX = {_norm_pt(pt): pt for pt in _PT_TOKO}


def pt_toko_from_supermarket(name: str) -> tuple[str, str | None]:
    """Petakan nama 'supermarket' di JSON ke (PT kanonik, toko)."""
    key = _norm_pt(name)
    if key in _PT_INDEX:
        pt = _PT_INDEX[key]
        return pt, _PT_TOKO.get(pt)
    # cocok sebagian (nama JSON bisa punya embel-embel)
    for k, pt in _PT_INDEX.items():
        if k and (k in key or key in k):
            return pt, _PT_TOKO.get(pt)
    return str(name).strip(), None


def _date(s) -> dt.date | None:
    if not s:
        return None
    if isinstance(s, dt.date):
        return s
    return dt.date.fromisoformat(str(s)[:10])


@dataclass
class Claim:
    invoice: str
    supermarket: str
    pt: str
    toko: str | None
    filia_label: str
    filia_amount: float
    program: str
    periode_mulai: dt.date | None
    periode_akhir: dt.date | None
    includes_ppn: bool
    rows: list[dict] = field(default_factory=list)
    sumber_json: str = ""


def load_lampiran(path) -> list[Claim]:
    """Muat satu file JSON -> daftar Claim."""
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    inv = d.get("invoice")
    sm = d.get("supermarket", "")
    pt, toko = pt_toko_from_supermarket(sm)
    claims: list[Claim] = []
    for cl in d.get("claim_lines", []):
        claims.append(Claim(
            invoice=inv,
            supermarket=sm,
            pt=pt,
            toko=toko,
            filia_label=cl.get("filia_label", ""),
            filia_amount=float(cl.get("filia_amount") or 0),
            program=cl.get("program", "") or "",
            periode_mulai=_date(cl.get("periode_mulai")),
            periode_akhir=_date(cl.get("periode_akhir")),
            includes_ppn=bool(cl.get("includes_ppn")),
            rows=cl.get("rows", []) or [],
            sumber_json=os.path.basename(str(path)),
        ))
    return claims


def load_lampiran_dir(folder) -> list[Claim]:
    """Muat semua JSON di folder, urut nama file."""
    out: list[Claim] = []
    for f in sorted(glob.glob(os.path.join(str(folder), "*.json"))):
        out.extend(load_lampiran(f))
    return out
