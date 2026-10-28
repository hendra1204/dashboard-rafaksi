"""Uji pembacaan PDF via Claude API dengan membandingkan ke JSON contoh.

Jalankan setelah PDF ada di data/invoice/ dan ANTHROPIC_API_KEY ada di .env:

    python uji_baca_pdf.py            # uji 2 PDF default (027 & 040)
    python uji_baca_pdf.py 027 043    # uji nomor tertentu

Catatan: ini MEMANGGIL API (berbiaya). Hasil baca disimpan ke output/cache_lampiran/.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src import config

load_dotenv(config.BASE_DIR / ".env")


def _cari_pdf(nomor: str) -> Path | None:
    for pola in (f"Laif VIII-{nomor}.pdf", f"Laif_VIII-{nomor}.pdf", f"*{nomor}*.pdf"):
        hit = sorted(config.INVOICE_DIR.glob(pola))
        hit = [h for h in hit if "list_invoice" not in h.name.lower()]
        if hit:
            return hit[0]
    return None


def _contoh(nomor: str) -> dict | None:
    p = config.CONTOH_LAMPIRAN_DIR / f"Laif_VIII-{nomor}.json"
    if p.exists():
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    return None


def _ringkas(d: dict) -> dict:
    cls = d.get("claim_lines", [])
    return dict(
        supermarket=d.get("supermarket"),
        n_claim=len(cls),
        filia_total=sum(c.get("filia_amount") or 0 for c in cls),
        per_claim=[dict(filia=c.get("filia_amount"), lampiran=c.get("lampiran_total"),
                        n_rows=len(c.get("rows", [])),
                        sum_total=round(sum((r.get("total") or 0) for r in c.get("rows", []))))
                   for c in cls],
    )


def main(nomor_list):
    key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")
    if key and "xxxx" in key.lower():
        key = None  # masih placeholder
    missing = []
    for n in nomor_list:
        if _cari_pdf(n) is None:
            missing.append(n)
    print("=" * 70)
    print("CEK PRASYARAT")
    print("=" * 70)
    print(f"ANTHROPIC_API_KEY di .env : {'ADA' if key else 'TIDAK ADA'}")
    print(f"Model                     : {os.getenv('ANTHROPIC_MODEL', 'claude-opus-5-5')}")
    for n in nomor_list:
        p = _cari_pdf(n)
        print(f"PDF {n}                   : {'ADA (' + p.name + ')' if p else 'TIDAK ADA'}")
    if not key or missing:
        print("\nBelum bisa uji. Lengkapi dulu:")
        if not key:
            print("  - Buat .env berisi: ANTHROPIC_API_KEY=sk-ant-...")
        if missing:
            print(f"  - Taruh PDF ke data/invoice/ untuk: {', '.join(missing)}")
        return

    from src.baca_pdf import baca_pdf
    print("\n" + "=" * 70)
    print("MEMBACA PDF (via Claude API) & MEMBANDINGKAN KE CONTOH")
    print("=" * 70)
    for n in nomor_list:
        pdf = _cari_pdf(n)
        print(f"\n--- {n}: baca {pdf.name} ...")
        hasil = baca_pdf(pdf, use_cache=False)
        rh = _ringkas(hasil)
        contoh = _contoh(n)
        print(f"  HASIL : {rh['supermarket']} | {rh['n_claim']} claim | total {rh['filia_total']:,}")
        for i, c in enumerate(rh["per_claim"]):
            print(f"     claim {i}: filia={c['filia']:,} lampiran={c['lampiran']} "
                  f"rows={c['n_rows']} sum_total={c['sum_total']:,}")
        if contoh:
            rc = _ringkas(contoh)
            ok_total = rh["filia_total"] == rc["filia_total"]
            ok_claims = rh["n_claim"] == rc["n_claim"]
            print(f"  CONTOH: {rc['supermarket']} | {rc['n_claim']} claim | total {rc['filia_total']:,}")
            print(f"  COCOK?  total={'YA' if ok_total else 'TIDAK'} "
                  f"jumlah_claim={'YA' if ok_claims else 'TIDAK'}")
        else:
            print("  (tidak ada JSON contoh untuk dibandingkan)")


if __name__ == "__main__":
    nomor = sys.argv[1:] or ["027", "040"]
    main(nomor)
