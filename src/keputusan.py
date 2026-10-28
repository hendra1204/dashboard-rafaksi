"""Penyimpanan keputusan finance (Terima / Tahan / Tolak + catatan).

Dua backend, dipilih OTOMATIS:
- Bila env ``SUPABASE_URL`` & ``SUPABASE_KEY`` ada  -> simpan ke **Supabase**
  (Postgres). Dipakai saat dashboard di-host online (mis. Streamlit Cloud) agar
  keputusan tersimpan permanen walau PC dimatikan.
- Bila tidak ada                                   -> **SQLite** lokal di
  ``output/keputusan.db`` (pemakaian di PC sendiri).

API sama untuk kedua backend: ``init, simpan, simpan_catatan, hapus, muat``.
Satu baris per (batch, temuan).
"""
from __future__ import annotations

import datetime as dt
import os
import sqlite3

from src import config

DB_PATH = config.OUTPUT_DIR / "keputusan.db"

STATUS_VALID = {"terima", "tahan", "tolak"}
TABEL = "keputusan"

_client = None  # cache client Supabase


def _supabase():
    """Client Supabase bila dikonfigurasi (env SUPABASE_URL & SUPABASE_KEY), selainnya None."""
    global _client
    if _client is not None:
        return _client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        return None
    from supabase import create_client  # impor lokal: hanya perlu di mode online
    _client = create_client(url, key)
    return _client


# --------------------------------------------------------------------------- SQLite lokal
def _conn() -> sqlite3.Connection:
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_sqlite() -> None:
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS keputusan (
                batch     TEXT NOT NULL,
                temuan_id TEXT NOT NULL,
                status    TEXT NOT NULL,
                catatan   TEXT,
                oleh      TEXT,
                waktu     TEXT,
                PRIMARY KEY (batch, temuan_id)
            )
        """)


# --------------------------------------------------------------------------- API publik
def init() -> None:
    if _supabase() is None:
        _init_sqlite()


def simpan(batch: str, temuan_id: str, status: str,
           catatan: str = "", oleh: str = "") -> None:
    """Simpan/timpa satu keputusan. status harus salah satu STATUS_VALID."""
    if status not in STATUS_VALID:
        raise ValueError(f"status tidak sah: {status}")
    waktu = dt.datetime.now().isoformat(timespec="seconds")
    sb = _supabase()
    if sb is not None:
        sb.table(TABEL).upsert({
            "batch": batch, "temuan_id": temuan_id, "status": status,
            "catatan": catatan, "oleh": oleh, "waktu": waktu,
        }, on_conflict="batch,temuan_id").execute()
        return
    _init_sqlite()
    with _conn() as c:
        c.execute("""
            INSERT INTO keputusan (batch, temuan_id, status, catatan, oleh, waktu)
            VALUES (?,?,?,?,?,?)
            ON CONFLICT(batch, temuan_id) DO UPDATE SET
                status=excluded.status, catatan=excluded.catatan,
                oleh=excluded.oleh, waktu=excluded.waktu
        """, (batch, temuan_id, status, catatan, oleh, waktu))


def simpan_catatan(batch: str, temuan_id: str, catatan: str) -> None:
    """Perbarui catatan saja (tanpa mengubah status) bila keputusan sudah ada."""
    sb = _supabase()
    if sb is not None:
        sb.table(TABEL).update({"catatan": catatan}) \
            .eq("batch", batch).eq("temuan_id", temuan_id).execute()
        return
    _init_sqlite()
    with _conn() as c:
        c.execute("UPDATE keputusan SET catatan=? WHERE batch=? AND temuan_id=?",
                  (catatan, batch, temuan_id))


def hapus(batch: str, temuan_id: str) -> None:
    sb = _supabase()
    if sb is not None:
        sb.table(TABEL).delete().eq("batch", batch).eq("temuan_id", temuan_id).execute()
        return
    _init_sqlite()
    with _conn() as c:
        c.execute("DELETE FROM keputusan WHERE batch=? AND temuan_id=?", (batch, temuan_id))


def muat(batch: str) -> dict[str, dict]:
    """temuan_id -> {status, catatan, oleh, waktu} untuk satu batch."""
    sb = _supabase()
    if sb is not None:
        res = sb.table(TABEL).select("temuan_id,status,catatan,oleh,waktu") \
            .eq("batch", batch).execute()
        rows = res.data or []
        return {r["temuan_id"]: dict(status=r["status"], catatan=r.get("catatan") or "",
                                     oleh=r.get("oleh") or "", waktu=r.get("waktu") or "")
                for r in rows}
    _init_sqlite()
    with _conn() as c:
        rows = c.execute(
            "SELECT temuan_id, status, catatan, oleh, waktu FROM keputusan WHERE batch=?",
            (batch,)).fetchall()
    return {r["temuan_id"]: dict(status=r["status"], catatan=r["catatan"] or "",
                                 oleh=r["oleh"] or "", waktu=r["waktu"] or "") for r in rows}
