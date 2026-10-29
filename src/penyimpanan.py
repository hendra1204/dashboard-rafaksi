"""Penyimpanan file unggahan di Supabase Storage supaya PERMANEN.

Masalah: di Streamlit Cloud, file yang di-upload hanya tersimpan sementara di
kontainer -> hilang saat app tidur/restart. Modul ini menyimpan setiap file
unggahan (Excel kesepakatan / PDF invoice) ke sebuah "bucket" Supabase Storage,
lalu menariknya kembali saat app dibuka, jadi file tidak pernah hilang.

Autentikasi memakai header ``apikey`` + ``Authorization: Bearer`` (standar
Storage API). Bila Supabase tidak dikonfigurasi (pemakaian lokal), semua fungsi
jadi no-op dan aplikasi tetap jalan pakai file lokal seperti biasa.

Struktur di bucket:
    uploads/kesepakatan/<nama.xlsx>
    uploads/invoice/<nama.pdf>
"""
from __future__ import annotations

import os
from pathlib import Path

BUCKET = "uploads"
PLACEHOLDER = ".emptyFolderPlaceholder"


def _cfg():
    """(url, key) bila Supabase dikonfigurasi, selainnya None."""
    url = (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")
    key = (os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_KEY") or "").strip()
    return (url, key) if url and key else None


def aktif() -> bool:
    """True bila penyimpanan permanen (Supabase) tersedia."""
    return _cfg() is not None


def _headers(key: str, extra: dict | None = None) -> dict:
    h = {"apikey": key, "Authorization": f"Bearer {key}"}
    if extra:
        h.update(extra)
    return h


def unggah(prefix: str, nama: str, data: bytes,
           content_type: str = "application/octet-stream") -> None:
    """Simpan/timpa satu file ke uploads/<prefix>/<nama>."""
    cfg = _cfg()
    if not cfg:
        return
    import requests
    url, key = cfg
    path = f"{prefix}/{nama}"
    r = requests.post(
        f"{url}/storage/v1/object/{BUCKET}/{path}",
        headers=_headers(key, {"Content-Type": content_type, "x-upsert": "true"}),
        data=data, timeout=120)
    r.raise_for_status()


def daftar(prefix: str) -> list[str]:
    """Daftar nama file di uploads/<prefix>/ (tanpa path)."""
    cfg = _cfg()
    if not cfg:
        return []
    import requests
    url, key = cfg
    r = requests.post(
        f"{url}/storage/v1/object/list/{BUCKET}",
        headers=_headers(key, {"Content-Type": "application/json"}),
        json={"prefix": f"{prefix}/", "limit": 1000,
              "sortBy": {"column": "name", "order": "asc"}},
        timeout=60)
    r.raise_for_status()
    out = []
    for it in (r.json() or []):
        nama = it.get("name")
        # lewati folder (id null) & placeholder folder kosong
        if not nama or nama == PLACEHOLDER or nama.endswith("/") or not it.get("id"):
            continue
        out.append(nama)
    return out


def unduh(prefix: str, nama: str) -> bytes | None:
    """Ambil isi satu file; None bila tak ada."""
    cfg = _cfg()
    if not cfg:
        return None
    import requests
    url, key = cfg
    r = requests.get(f"{url}/storage/v1/object/{BUCKET}/{prefix}/{nama}",
                     headers=_headers(key), timeout=120)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.content


def sync_ke_lokal(prefix: str, folder) -> int:
    """Tarik semua file uploads/<prefix>/ ke folder lokal. Kembalikan jumlah
    file yang berhasil ditarik. Tidak menghapus file lokal yang sudah ada."""
    cfg = _cfg()
    if not cfg:
        return 0
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    n = 0
    for nama in daftar(prefix):
        data = unduh(prefix, nama)
        if data is None:
            continue
        (folder / nama).write_bytes(data)
        n += 1
    return n
