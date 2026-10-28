"""Baca PDF tagihan Filia (hasil scan) -> JSON terstruktur, via Claude API.

Tiap PDF = halaman 1 invoice Filia + halaman lampiran dokumen supermarket.
PDF dikirim langsung sebagai blok ``document`` (Claude membaca teks & gambar
hasil scan), lalu hasilnya disimpan ke cache JSON per invoice supaya PDF yang
sama tidak dibaca dua kali (hemat biaya API).

API key dibaca dari ``.env`` (ANTHROPIC_API_KEY) lewat python-dotenv; tidak
pernah ditulis di kode. Model bisa diganti lewat ``.env`` (ANTHROPIC_MODEL),
default ``claude-opus-5-5``.
"""
from __future__ import annotations

import base64
import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv

from src import config

load_dotenv(config.BASE_DIR / ".env")

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-5-5")

SKEMA = """{
  "invoice": "<nomor invoice Filia, mis. 26/VIII/027>",
  "supermarket": "<nama PT supermarket, mis. PT Lotte Mart Indonesia>",
  "claim_lines": [
    {
      "filia_label": "<keterangan baris di sampul Filia, apa adanya>",
      "filia_amount": <angka nilai ditagih baris ini, tanpa titik/koma>,
      "supermarket_doc": "<nomor/jenis dokumen supermarket, mis. Debit Note 00009000>",
      "program": "<nama program/promo di lampiran, mis. Member Day / Promo end user / KOMPENSASI ...>",
      "periode_mulai": "<YYYY-MM-DD dari LAMPIRAN supermarket>",
      "periode_akhir": "<YYYY-MM-DD dari LAMPIRAN supermarket>",
      "periode_text": "<tulisan periode apa adanya>",
      "includes_ppn": <true bila nilai per baris sudah termasuk PPN 11% (Food Hall), selain itu false>,
      "rows": [
        {
          "store_code": "<kode toko/site, mis. 04001 / XY02 / 1001, atau null>",
          "store_name": "<nama toko bila ada, atau null>",
          "product": "<nama produk di lampiran, atau null bila tak dirinci per produk>",
          "qty": <angka atau null>,
          "harga": <harga satuan atau null>,
          "disc_pct": <pecahan disc mis. 0.1 atau null>,
          "rafaksi_per_pcs": <rafaksi per pcs atau null>,
          "dpp": <nilai DPP baris atau null>,
          "ppn": <nilai PPN baris atau null>,
          "total": <nilai total baris (dpp+ppn)>
        }
      ],
      "lampiran_total": <jumlah seluruh baris>,
      "check": "<catatan singkat pengecekan jumlah>",
      "notes": "<catatan penting lain>"
    }
  ]
}"""

PROMPT = f"""Kamu membaca satu PDF tagihan dari distributor PT Filia Sukses Mandiri ke PT Laif
(merek Olaif). Halaman 1 = sampul invoice Filia; halaman berikutnya = dokumen asli
supermarket (debit note / kwitansi / laporan). Ekstrak datanya menjadi JSON PERSIS
dengan bentuk berikut (jangan tambah/ubah nama field):

{SKEMA}

Aturan penting:
- HANYA baris produk Olaif/Laif yang ditagih ke kami. Abaikan baris merek lain
  (Clara, Yuuka, Bara, Zozo, dll) yang kadang ikut tercetak di kwitansi.
- "periode_mulai/akhir" diambil dari LAMPIRAN supermarket (periode promo sebenarnya),
  BUKAN dari keterangan Filia yang kadang menulis bulan tagih. Untuk AEON, "Period:
  Monthly (JUN-2026)" di invoice adalah bulan tagih, bukan periode promo.
- Satu PDF bisa punya beberapa claim_lines (mis. beberapa debit note / dokumen).
  Food Hall sering memecah satu klaim jadi dokumen HABA/HOME/CLEANING -> tiap dokumen
  jadi satu claim_line, dan nilai per site SUDAH termasuk PPN 11% (includes_ppn=true).
- Format per supermarket: Lotte = Debit Note, kolom HARGA/SALE_QTY/SUPPORT(%)/RAFAKSI;
  AEON = "Detail Calculation" per toko, kolom Remark = rafaksi per pcs, program bisa
  "Member Day" (semua toko) atau "Promo end user" (per toko); Food Hall = "Rincian
  Potongan" per site (XY..), termasuk PPN 11%; Market City = laporan "Sales Performance
  by Supplier" (tanpa PPN, toko berupa rentang); Hero = debit note, toko MITRA dirinci;
  JFM/Trufarm/Duta Buah/Diamond = kwitansi (sering bercampur merek lain); Ranch Market =
  debit note total saja.
- Isi field dengan null bila datanya memang tidak ada. Angka tanpa pemisah ribuan.
- Jika scan buram dan suatu angka tak terbaca pasti, isi sebisanya dan jelaskan di "notes".

Keluarkan HANYA JSON itu, tanpa penjelasan, tanpa pembungkus ```.
"""


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # ambil blok { ... } terbesar
        i, j = text.find("{"), text.rfind("}")
        if i != -1 and j != -1:
            return json.loads(text[i:j + 1])
        raise


def _client():
    import anthropic  # impor lokal supaya modul lain tak wajib punya SDK
    key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")
    if not key or "xxxx" in key.lower():
        raise RuntimeError(
            "ANTHROPIC_API_KEY belum diisi (masih kosong/placeholder). Buka file .env "
            "dan ganti baris ANTHROPIC_API_KEY= dengan key asli (sk-ant-...).")
    return anthropic.Anthropic()


def baca_pdf(pdf_path, use_cache: bool = True) -> dict:
    """Baca satu PDF -> dict (skema lampiran). Pakai cache bila ada."""
    pdf_path = Path(pdf_path)
    config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache = config.CACHE_DIR / (pdf_path.stem.replace(" ", "_") + ".json")
    if use_cache and cache.exists():
        with open(cache, encoding="utf-8") as fh:
            return json.load(fh)

    data_b64 = base64.standard_b64encode(pdf_path.read_bytes()).decode("ascii")
    client = _client()
    with client.messages.stream(
        model=MODEL,
        max_tokens=32000,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        messages=[{
            "role": "user",
            "content": [
                {"type": "document",
                 "source": {"type": "base64", "media_type": "application/pdf", "data": data_b64}},
                {"type": "text", "text": PROMPT},
            ],
        }],
    ) as stream:
        msg = stream.get_final_message()

    text = "".join(b.text for b in msg.content if b.type == "text")
    hasil = _extract_json(text)
    with open(cache, "w", encoding="utf-8") as fh:
        json.dump(hasil, fh, ensure_ascii=False, indent=1)
    return hasil


def baca_folder(folder=None, use_cache: bool = True) -> dict[str, dict]:
    """Baca semua PDF 'Laif*' di folder (default data/invoice) -> {nama: hasil}."""
    folder = Path(folder) if folder else config.INVOICE_DIR
    out = {}
    for pdf in sorted(folder.glob("*.pdf")):
        if "list_invoice" in pdf.name.lower():
            continue
        out[pdf.stem] = baca_pdf(pdf, use_cache=use_cache)
    return out
