"""Mesin pencocokan klaim vs kesepakatan + penetapan status.

Tiap klaim dipecah menjadi tiga kantong yang jumlahnya = nilai ditagih Filia:
  - Sesuai kesepakatan
  - Perlu konfirmasi
  - Di luar kesepakatan

Urutan aturan (meniru pengecekan manual pada contoh v5):
  1. Lampiran memuat PPN (Food Hall): bagian PPN 11% -> perlu konfirmasi,
     sisa (DPP) -> sesuai.
  2. Program "Member Day" (AEON): seluruh klaim -> perlu konfirmasi.
  3. Klaim lebih dari 12 bulan saat ditagih -> perlu konfirmasi.
  4. Ada rincian produk: cek tiap produk ke kesepakatan (PT + produk +
     bulan yang beririsan). Produk dikenali tanpa disc di bulan itu ->
     di luar kesepakatan; produk belum dipetakan -> dipercaya (sesuai,
     ditandai).
  5. Tanpa rincian produk -> sesuai (dipercaya atas nilai total).
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

import pandas as pd

from src.lampiran import Claim
from src.produk import normkey, resolve

SESUAI = "Sesuai kesepakatan"
KONFIRMASI = "Perlu konfirmasi"
LUAR = "Di luar kesepakatan"

BATCH_REF_DEFAULT = dt.date(2026, 8, 31)   # bulan tagih batch Agustus 2026


# ---------------------------------------------------------------------------
# Indeks kesepakatan
# ---------------------------------------------------------------------------
def build_index(df: pd.DataFrame) -> dict[tuple[str, str], list[dict]]:
    """(pt, normkey(produk)) -> daftar {pm, pe, disc_pct, disc_rp}."""
    idx: dict[tuple[str, str], list[dict]] = {}
    for rec in df.itertuples(index=False):
        pm = rec.periode_mulai
        pe = rec.periode_akhir
        pm = pm.date() if hasattr(pm, "date") else pm
        pe = pe.date() if hasattr(pe, "date") else pe
        key = (rec.pt, normkey(rec.produk))
        idx.setdefault(key, []).append(dict(
            pm=pm, pe=pe,
            disc_pct=rec.disc_pct, disc_rp=rec.disc_rp_pcs,
        ))
    return idx


def _overlap(a0, a1, b0, b1) -> bool:
    if not (a0 and a1 and b0 and b1):
        return False
    return a0 <= b1 and b0 <= a1


def agreement_rows(index, pt, produk_kanonik, pm, pe) -> list[dict]:
    """Baris kesepakatan utk produk ini yang beririsan periode & punya disc."""
    key = (pt, normkey(produk_kanonik))
    out = []
    for row in index.get(key, []):
        if (row["disc_pct"] is not None or row["disc_rp"] is not None) and \
                _overlap(row["pm"], row["pe"], pm, pe):
            out.append(row)
    return out


def _product_known_for_pt(index, pt, produk_kanonik) -> bool:
    return (pt, normkey(produk_kanonik)) in index


# ---------------------------------------------------------------------------
# Klasifikasi per klaim
# ---------------------------------------------------------------------------
@dataclass
class Hasil:
    claim: Claim
    sesuai: float = 0.0
    konfirmasi: float = 0.0
    luar: float = 0.0
    status: str = SESUAI
    alasan: str = ""
    rincian: list[dict] = field(default_factory=list)


def _months_before(ref: dt.date, n: int = 12) -> dt.date:
    y, m = ref.year, ref.month
    y -= 1  # 12 bulan
    try:
        return dt.date(y, m, ref.day)
    except ValueError:
        return dt.date(y, m, 28)


def classify_claim(claim: Claim, index, ref_date: dt.date = BATCH_REF_DEFAULT) -> Hasil:
    amt = claim.filia_amount
    h = Hasil(claim=claim)

    # 1) PPN ikut ditagih (Food Hall)
    if claim.includes_ppn:
        ppn = sum((r.get("ppn") or 0) for r in claim.rows)
        h.konfirmasi = round(ppn, 2)
        h.sesuai = amt - h.konfirmasi
        h.status = KONFIRMASI
        h.alasan = "Nilai termasuk PPN 11%; bagian PPN perlu konfirmasi, DPP sesuai"
        return h

    # 2) Member Day
    if "member day" in (claim.program or "").lower():
        h.konfirmasi = amt
        h.status = KONFIRMASI
        h.alasan = "Program Member Day tidak tercantum di kesepakatan"
        return h

    # 3) Klaim > 12 bulan saat ditagih
    acuan = claim.periode_akhir or claim.periode_mulai
    if acuan and acuan < _months_before(ref_date, 12):
        h.konfirmasi = amt
        h.status = KONFIRMASI
        h.alasan = (f"Klaim lebih dari 12 bulan (periode s.d. {acuan:%d %b %Y}, "
                    f"ditagih {ref_date:%b %Y})")
        return h

    # 4) Rincian produk
    prod_rows = [r for r in claim.rows if r.get("product")]
    if prod_rows:
        luar = 0.0
        for r in prod_rows:
            amount = r.get("total")
            if amount is None:
                amount = r.get("dpp") or 0
            kanonik, dikenali = resolve(r.get("product"))
            if not dikenali:
                srow, note = SESUAI, "nama produk belum dipetakan (dipercaya)"
            else:
                match = agreement_rows(index, claim.pt, kanonik, claim.periode_mulai, claim.periode_akhir)
                if match:
                    srow, note = SESUAI, "cocok disc kesepakatan"
                elif _product_known_for_pt(index, claim.pt, kanonik):
                    srow, note = LUAR, "tidak ada disc untuk produk ini di bulan klaim"
                    luar += amount
                else:
                    srow, note = LUAR, "produk tidak ada di kesepakatan PT ini"
                    luar += amount
            h.rincian.append(dict(
                product=r.get("product"), kanonik=kanonik, dikenali=dikenali,
                store=r.get("store_code") or r.get("store_name"),
                amount=amount, status=srow, note=note,
            ))
        h.luar = round(luar, 2)
        h.sesuai = amt - h.luar
        if h.luar > 0 and h.sesuai > 0:
            h.status, h.alasan = LUAR, "Sebagian produk di luar kesepakatan"
        elif h.luar > 0:
            h.status, h.alasan = LUAR, "Produk di luar kesepakatan"
        else:
            h.status, h.alasan = SESUAI, "Semua produk cocok / dipercaya"
        return h

    # 5) Tanpa rincian produk
    h.sesuai = amt
    h.status = SESUAI
    h.alasan = "Tanpa rincian produk; dipercaya atas nilai total"
    return h


# ---------------------------------------------------------------------------
# Jalankan atas semua klaim + agregasi
# ---------------------------------------------------------------------------
def evaluate(df_kesepakatan: pd.DataFrame, claims: list[Claim],
             ref_date: dt.date = BATCH_REF_DEFAULT) -> tuple[list[Hasil], dict]:
    index = build_index(df_kesepakatan)
    hasil = [classify_claim(c, index, ref_date) for c in claims]
    agg = dict(
        ditagih=round(sum(c.filia_amount for c in claims)),
        sesuai=round(sum(h.sesuai for h in hasil)),
        konfirmasi=round(sum(h.konfirmasi for h in hasil)),
        luar=round(sum(h.luar for h in hasil)),
    )
    return hasil, agg


# ---------------------------------------------------------------------------
# Cek klaim dobel (toko + produk + periode beririsan)
# ---------------------------------------------------------------------------
def _is_member_day(c: Claim) -> bool:
    return "member day" in (c.program or "").lower()


def cek_klaim_dobel(claims: list[Claim]) -> list[dict]:
    """Deteksi potensi klaim dobel: PT+toko(store) sama, produk (kanonik)
    sama, dan periode beririsan di dua klaim berbeda.

    jenis = "Dobel" bila kedua klaim program sejenis (promo reguler yang
    sama) -> patut ditolak; "Bisa bertumpuk" bila beda jenis (mis. Member
    Day vs promo end user) -> cukup ditinjau, diskon bisa sah menumpuk.
    """
    entries = []  # (pt, store, produk_kanonik, pm, pe, claim)
    for c in claims:
        store_level = [r for r in c.rows if r.get("product")]
        if store_level:
            for r in store_level:
                kanonik, _ = resolve(r.get("product"))
                entries.append((c.pt, str(r.get("store_code") or c.toko or ""),
                                normkey(kanonik), c.periode_mulai, c.periode_akhir, c))
        else:
            entries.append((c.pt, str(c.toko or ""), "(total)",
                            c.periode_mulai, c.periode_akhir, c))

    seen = set()
    dobel = []
    for i in range(len(entries)):
        for j in range(i + 1, len(entries)):
            a, b = entries[i], entries[j]
            ca, cb = a[5], b[5]
            if ca is cb:
                continue
            if a[0] == b[0] and a[1] == b[1] and a[2] == b[2] and a[2] not in ("", "(total)"):
                if not _overlap(a[3], a[4], b[3], b[4]):
                    continue
                beda_program = _is_member_day(ca) != _is_member_day(cb)
                pair_id = (id(ca), id(cb)) if id(ca) < id(cb) else (id(cb), id(ca))
                key = (pair_id, a[2])
                if key in seen:
                    continue
                seen.add(key)
                dobel.append(dict(
                    pt=a[0], store=a[1], produk=a[2],
                    jenis="Bisa bertumpuk" if beda_program else "Dobel",
                    program_a=ca.program, program_b=cb.program,
                    klaim_a=f"{ca.invoice} {ca.filia_label}",
                    klaim_b=f"{cb.invoice} {cb.filia_label}",
                ))
    return dobel


if __name__ == "__main__":
    # Self-check: jalankan atas contoh hasil_baca_lampiran, bandingkan ke v5.
    from src import config
    from src.kesepakatan import load_kesepakatan
    from src.lampiran import load_lampiran_dir

    df = load_kesepakatan()
    claims = load_lampiran_dir(config.CONTOH_LAMPIRAN_DIR)
    hasil, agg = evaluate(df, claims)
    target = dict(ditagih=52049072, sesuai=38972012, konfirmasi=12072080, luar=1004980)
    print(f"{'':16}{'HASIL':>15}{'TARGET v5':>15}{'  OK?':>6}")
    allok = True
    for k in ("ditagih", "sesuai", "konfirmasi", "luar"):
        ok = agg[k] == target[k]
        allok = allok and ok
        print(f"{k:16}{agg[k]:>15,}{target[k]:>15,}{'  OK' if ok else '  XX':>6}")
    dobel = cek_klaim_dobel(claims)
    print(f"\nPotensi klaim dobel/tumpuk: {len(dobel)} "
          f"(Dobel={sum(1 for d in dobel if d['jenis']=='Dobel')}, "
          f"Bisa bertumpuk={sum(1 for d in dobel if d['jenis']=='Bisa bertumpuk')})")
    print("\nHASIL: " + ("SEMUA COCOK dengan acuan v5" if allok else "ADA SELISIH"))
