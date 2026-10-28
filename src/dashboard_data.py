"""Siapkan semua data yang dibutuhkan tampilan dashboard.

Semua angka dihitung dari data (kesepakatan + lampiran + mesin pencocokan),
bukan ditulis langsung. Hasilnya berupa dict/list sederhana yang gampang
dirender oleh app.py.
"""
from __future__ import annotations

import datetime as dt
import re
from collections import defaultdict

from src import config
from src.kesepakatan import load_kesepakatan
from src.lampiran import Claim, load_lampiran_dir
from src.pencocokan import (BATCH_REF_DEFAULT, KONFIRMASI, LUAR, SESUAI,
                            cek_klaim_dobel, evaluate)
from src.referensi import (AEON_STORE_NAMES, bulan_panjang, fmt_rp, fmt_short,
                           iter_months, label_bulan, label_bulan_y4)

# status blok garis waktu
ST_SESUAI, ST_PPN, ST_KONF, ST_LUAR = "sesuai", "ppn", "konfirmasi", "luar"

_BULAN = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "mei": 5, "jun": 6,
    "juni": 6, "jul": 7, "juli": 7, "aug": 8, "agu": 8, "ags": 8, "sep": 9,
    "oct": 10, "okt": 10, "nov": 11, "dec": 12, "des": 12,
}


# ---------------------------------------------------------------------------
def _store_label(toko: str, kode: str, nama: str | None) -> str:
    if toko == "Aeon":
        return AEON_STORE_NAMES.get(str(kode), f"AEON toko {kode}")
    if nama:
        return str(nama)
    return str(kode) if kode and kode != "(total)" else (toko or "-")


def _filia_line_count(claims) -> int:
    """Jumlah baris klaim seperti di daftar Filia. Lampiran ber-PPN (Food Hall)
    dipecah per dokumen oleh supermarket -> digabung jadi 1 baris per
    (invoice, periode). Lampiran lain = 1 baris per claim_line."""
    ppn_lines = {(c.invoice, c.filia_label) for c in claims if c.includes_ppn}
    non_ppn = sum(1 for c in claims if not c.includes_ppn)
    return non_ppn + len(ppn_lines)


def _status_blok(h) -> str:
    if h.claim.includes_ppn:
        return ST_PPN
    if h.luar > 0:
        return ST_LUAR
    if h.konfirmasi > 0:
        return ST_KONF
    return ST_SESUAI


def _labeled_months(label: str) -> list[tuple[int, int | None]]:
    """Ambil (bulan, tahun?) yang disebut di keterangan Filia."""
    out = []
    for m in re.finditer(r"([A-Za-z]{3,})\s*'?(\d{2,4})?", label):
        mo = _BULAN.get(m.group(1)[:4].lower()) or _BULAN.get(m.group(1)[:3].lower())
        if not mo:
            continue
        yr = m.group(2)
        yr = (2000 + int(yr)) if yr and len(yr) == 2 else (int(yr) if yr else None)
        out.append((mo, yr))
    return out


# ---------------------------------------------------------------------------
def _sumber_lampiran():
    """Pakai cache hasil baca PDF (output/cache_lampiran) bila sudah ada
    isinya; jika belum, pakai contoh hasil baca untuk demo/uji."""
    if config.CACHE_DIR.exists() and any(config.CACHE_DIR.glob("*.json")):
        return config.CACHE_DIR
    return config.CONTOH_LAMPIRAN_DIR


def siapkan_data(ref_date: dt.date = BATCH_REF_DEFAULT,
                 lampiran_dir=None) -> dict:
    df = load_kesepakatan()
    claims = load_lampiran_dir(lampiran_dir or _sumber_lampiran())
    hasil, agg = evaluate(df, claims, ref_date)
    dobel = cek_klaim_dobel(claims)

    ditagih = agg["ditagih"]
    n_invoice = len({c.invoice for c in claims})
    n_supermarket = len({c.toko for c in claims if c.toko})
    # Jumlah "baris klaim" ala daftar Filia: Food Hall (lampiran ber-PPN,
    # dipecah per dokumen HABA/HOME/CLEANING) ditagih 1 baris per invoice-periode.
    baris_klaim_total = _filia_line_count(claims)

    # ---- ringkasan + bar ----
    ringkasan = dict(
        ditagih=ditagih, sesuai=agg["sesuai"],
        konfirmasi=agg["konfirmasi"], luar=agg["luar"],
        baris_klaim=baris_klaim_total, n_supermarket=n_supermarket,
        pct_sesuai=agg["sesuai"] / ditagih * 100,
        pct_konfirmasi=agg["konfirmasi"] / ditagih * 100,
        pct_luar=agg["luar"] / ditagih * 100,
        selisih_lampiran=round(
            ditagih - sum(sum((r.get("total") or 0) for r in c.rows)
                          for c in claims if c.rows)
        ),
    )

    # ---- per supermarket ----
    by_sm: dict[tuple[str, str], dict] = {}
    for h in hasil:
        c = h.claim
        key = (c.toko or c.pt, c.pt)
        d = by_sm.setdefault(key, dict(claims=[], ditagih=0.0, sesuai=0.0, konf=0.0, luar=0.0))
        d["claims"].append(c)
        d["ditagih"] += c.filia_amount
        d["sesuai"] += h.sesuai
        d["konf"] += h.konfirmasi
        d["luar"] += h.luar
    per_supermarket = []
    for (toko, pt), d in sorted(by_sm.items(), key=lambda kv: -kv[1]["ditagih"]):
        if d["konf"] == 0 and d["luar"] == 0:
            komposisi = "Semua sesuai"
        else:
            bits = [f"Sesuai {fmt_short(d['sesuai'])}"]
            if d["konf"] > 0:
                bits.append(f"konfirmasi {fmt_short(d['konf'])}")
            if d["luar"] > 0:
                bits.append(f"di luar {fmt_short(d['luar'])}")
            komposisi = ", ".join(bits)
        per_supermarket.append(dict(
            toko=toko, pt=pt, klaim=_filia_line_count(d["claims"]), ditagih=round(d["ditagih"]),
            sesuai=round(d["sesuai"]), konf=round(d["konf"]), luar=round(d["luar"]),
            komposisi=komposisi,
        ))

    # ---- temuan ----
    temuan = _buat_temuan(hasil)

    # ---- garis waktu per supermarket ----
    timelines = {row["toko"]: _timeline(row["toko"], hasil) for row in per_supermarket}

    # ---- stepper ----
    n_baris_kesepakatan = len(df)
    n_baris_lampiran = sum(len(c.rows) for c in claims)
    n_temuan = len(temuan)
    stepper = [
        dict(n=1, title="Kesepakatan rafraksi", sub=f"{df['sumber_file'].nunique()} file, {n_baris_kesepakatan:,} baris disc".replace(",", "."), state="done"),
        dict(n=2, title="Invoice dan lampiran", sub=f"{n_invoice} PDF, {n_baris_lampiran:,} baris dibaca".replace(",", "."), state="done"),
        dict(n=3, title="Pengecekan agent", sub=f"{n_temuan} temuan, selesai {ref_date:%d} Okt", state="done"),
        dict(n=4, title="Keputusan finance", sub=f"{n_temuan} temuan menunggu", state="wait"),
    ]

    return dict(
        batch_label=f"PT Filia Sukses Mandiri, Agustus 2026 ({n_invoice} invoice)",
        stepper=stepper, ringkasan=ringkasan, per_supermarket=per_supermarket,
        temuan=temuan, timelines=timelines, dobel=dobel,
        hasil=hasil, agg=agg,
    )


# ---------------------------------------------------------------------------
def _buat_temuan(hasil) -> list[dict]:
    t: list[dict] = []

    # 1) Member Day per PT
    md = defaultdict(list)
    for h in hasil:
        if "Member Day" in h.alasan:
            md[(h.claim.toko, h.claim.pt)].append(h)
    for (toko, pt), hs in md.items():
        total = sum(h.konfirmasi for h in hs)
        pm = min(h.claim.periode_mulai for h in hs)
        pe = max(h.claim.periode_akhir for h in hs)
        t.append(dict(
            id=f"md-{toko}", judul=f"Member Day {toko} tidak ada di kesepakatan",
            badge=fmt_rp(total), badge_type="amber", nilai=round(total), kategori="member_day",
            konteks=f"{toko}, {len(hs)} klaim ({label_bulan_y4(pm)} - {label_bulan_y4(pe)})",
            deskripsi=(f"Pastikan apakah Olaif ikut menanggung diskon Member Day. "
                       f"Bila tidak, tolak ketiga klaim ini."),
        ))

    # 2) PPN per PT
    ppn = defaultdict(list)
    for h in hasil:
        if "PPN" in h.alasan:
            ppn[(h.claim.toko, h.claim.pt)].append(h)
    for (toko, pt), hs in ppn.items():
        total = sum(h.konfirmasi for h in hs)
        sebelum = sum(h.sesuai for h in hs)
        n_inv = len({h.claim.invoice for h in hs})
        t.append(dict(
            id=f"ppn-{toko}", judul="PPN 11% ikut ditagihkan",
            badge=fmt_rp(total), badge_type="amber", nilai=round(total), kategori="ppn",
            konteks=f"{toko}, {n_inv} invoice",
            deskripsi=(f"Putuskan apakah PPN atas rafaksi boleh diklaim. "
                       f"Nilai sebelum PPN {fmt_rp(sebelum)}."),
        ))

    # 3) Di luar kesepakatan (per produk)
    luar = defaultdict(lambda: dict(amount=0.0, store=None, pm=None, pe=None, pt=None, toko=None))
    for h in hasil:
        for d in h.rincian:
            if d["status"] == LUAR:
                kanonik = d["kanonik"] or d["product"]
                g = luar[(h.claim.toko, kanonik)]
                g["amount"] += d["amount"]
                g["store"] = d["store"]
                g["pm"] = h.claim.periode_mulai
                g["pe"] = h.claim.periode_akhir
                g["pt"] = h.claim.pt
                g["toko"] = h.claim.toko
    for (toko, kanonik), g in luar.items():
        nama = _nama_pendek_produk(kanonik)
        store_nm = AEON_STORE_NAMES.get(str(g["store"]), f"{toko} {g['store']}") if toko == "Aeon" else f"{toko}"
        if g["pm"] and g["pe"]:
            konteks = f"{store_nm}, {g['pm'].day} {label_bulan_y4(g['pm'])} - {g['pe'].day} {label_bulan_y4(g['pe'])}"
        else:
            konteks = store_nm
        t.append(dict(
            id=f"luar-{toko}-{g['store']}", judul=f"{nama} di luar kesepakatan",
            badge=fmt_rp(g["amount"]), badge_type="red", nilai=round(g["amount"]), kategori="luar",
            konteks=konteks,
            deskripsi=(f"Tidak ada disc {nama} pada periode klaim. "
                       f"Minta dasar klaim ke Filia atau potong dari pembayaran."),
        ))

    # 4) Klaim > 12 bulan
    for h in hasil:
        if "12 bulan" in h.alasan:
            pm = h.claim.periode_mulai
            t.append(dict(
                id=f"umur-{h.claim.invoice}", judul=f"Klaim periode {bulan_panjang(pm)}",
                badge=fmt_rp(h.konfirmasi), badge_type="amber", nilai=round(h.konfirmasi), kategori="umur",
                konteks=f"{h.claim.toko}, invoice {h.claim.invoice}",
                deskripsi=("Ditagih lebih dari satu tahun setelah periode promo. "
                           "Konfirmasi tahun dan kelengkapan lampiran ke Filia."),
            ))

    # 5) Keterangan periode di invoice Filia keliru (per invoice)
    keliru = defaultdict(list)
    for h in hasil:
        c = h.claim
        if not (c.periode_mulai and c.periode_akhir):
            continue
        labs = _labeled_months(c.filia_label)
        if not labs:
            continue
        cocok = any(c.periode_mulai <= dt.date(yr or c.periode_mulai.year, mo, 1) <= c.periode_akhir
                    or c.periode_mulai.month <= mo <= c.periode_akhir.month
                    for mo, yr in labs)
        if not cocok:
            keliru[(c.toko, c.invoice)].append(c)
    for (toko, inv), cs in keliru.items():
        t.append(dict(
            id=f"label-{inv}", judul="Keterangan periode di invoice Filia keliru",
            badge="Tanpa selisih", badge_type="grey", nilai=0, kategori="label",
            konteks=f"{toko}, invoice {inv}",
            deskripsi=("Bulan yang tertulis di keterangan Filia tidak sesuai periode "
                       "promo di lampiran. Minta Filia memperbaiki keterangan."),
        ))

    # urutkan: amber & merah (ada nilai) dulu, grey terakhir
    order = {"amber": 0, "red": 1, "grey": 2}
    t.sort(key=lambda x: order.get(x["badge_type"], 3))
    return t


def _nama_pendek_produk(kanonik: str) -> str:
    s = kanonik or ""
    if "women" in s.lower() and "shaver" in s.lower():
        return "Women Shaver"
    if "men" in s.lower() and "shaver" in s.lower():
        return "Men Shaver"
    return s.replace("Olaif ", "").strip() or s


# ---------------------------------------------------------------------------
_TOP_STORE = 8   # toko ditampilkan; sisanya digabung "Site lainnya"


def _timeline(toko: str, hasil) -> dict:
    hs = [h for h in hasil if (h.claim.toko or h.claim.pt) == toko]
    if not hs:
        return dict(months=[], rows=[], catatan="", subjudul="")

    pm = min(h.claim.periode_mulai for h in hs if h.claim.periode_mulai)
    pe = max(h.claim.periode_akhir for h in hs if h.claim.periode_akhir)
    months = iter_months(pm, pe)
    mindex = {(d.year, d.month): i for i, d in enumerate(months)}

    def _blk(c, status, amount):
        cs = mindex.get((c.periode_mulai.year, c.periode_mulai.month), 0)
        ce = mindex.get((c.periode_akhir.year, c.periode_akhir.month), cs)
        return dict(start=cs, end=ce, status=status, amount=round(amount),
                    label=fmt_short(amount), judul=c.filia_label, program=c.program)

    rows: dict[str, dict] = {}
    ada_md = False
    for h in hs:
        c = h.claim
        if not (c.periode_mulai and c.periode_akhir):
            continue
        status = _status_blok(h)
        if "member day" in (c.program or "").lower():
            ada_md = True
            row = rows.setdefault("MD", dict(kode="MD", nama="Member Day",
                                             kode_tampil="Semua toko", total=0.0, blocks=[], sort=-1))
            row["total"] += c.filia_amount
            row["blocks"].append(_blk(c, status, c.filia_amount))
            continue
        # pecah nilai klaim per toko (store_code / store_name)
        store_amt: dict[str, float] = defaultdict(float)
        store_nm: dict[str, str] = {}
        for r in c.rows:
            key = str(r.get("store_code") or r.get("store_name") or "(total)")
            store_amt[key] += (r.get("total") or 0)
            if r.get("store_name"):
                store_nm[key] = str(r.get("store_name"))
        if not store_amt:
            store_amt["(total)"] = c.filia_amount
        for key, amt in store_amt.items():
            row = rows.setdefault(key, dict(
                kode=key, nama=_store_label(toko, key, store_nm.get(key)),
                kode_tampil=("" if key == "(total)" else key), total=0.0, blocks=[], sort=0))
            row["total"] += amt
            row["blocks"].append(_blk(c, status, amt))

    md_rows = [r for r in rows.values() if r["sort"] == -1]
    others = sorted((r for r in rows.values() if r["sort"] != -1), key=lambda r: -r["total"])
    shown, rest = others[:_TOP_STORE], others[_TOP_STORE:]
    if rest:
        comb: dict[tuple, float] = defaultdict(float)
        for r in rest:
            for b in r["blocks"]:
                comb[(b["start"], b["end"], b["status"])] += b["amount"]
        lain = dict(kode="lain", nama="Site lainnya", kode_tampil=f"{len(rest)} site",
                    total=sum(r["total"] for r in rest), sort=2,
                    blocks=[dict(start=s, end=e, status=st, amount=round(a),
                                 label="", judul="Gabungan site lainnya", program="")
                            for (s, e, st), a in comb.items()])
        shown = shown + [lain]

    out_rows = md_rows + shown
    for r in out_rows:
        # gabungkan blok dengan periode & status sama (mis. Food Hall HABA/HOME/CLEANING)
        merged: dict[tuple, float] = defaultdict(float)
        meta: dict[tuple, dict] = {}
        for b in r["blocks"]:
            k = (b["start"], b["end"], b["status"])
            merged[k] += b["amount"]
            meta.setdefault(k, b)
        r["blocks"] = [dict(start=k[0], end=k[1], status=k[2], amount=round(v),
                            label=fmt_short(v), judul=meta[k]["judul"], program=meta[k]["program"])
                       for k, v in sorted(merged.items())]
        r["total_fmt"] = fmt_rp(r["total"])

    n_store = len([r for r in out_rows if r["sort"] != -1 and r["kode"] != "lain"])
    subjudul = f"{n_store} toko" + (" ditambah program Member Day di semua toko." if ada_md else ".")
    if rest:
        subjudul += f" {_TOP_STORE} site terbesar ditampilkan; sisanya digabung."
    catatan = "Klik salah satu blok periode untuk melihat dokumen, program dan catatan agent."
    return dict(months=[label_bulan(d) for d in months], rows=out_rows,
                catatan=catatan, subjudul=subjudul)
