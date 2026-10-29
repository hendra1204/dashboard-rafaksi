"""Penyimpanan keputusan finance (Terima / Tahan / Tolak + catatan).

Dua backend, dipilih OTOMATIS:
- Bila env ``SUPABASE_URL`` & ``SUPABASE_KEY`` ada -> **Supabase** lewat REST API
  (PostgREST), autentikasi dengan header ``apikey`` saja (cocok untuk kunci model
  baru ``sb_secret_...`` maupun legacy). Dipakai saat online (Streamlit Cloud).
- Bila tidak -> **SQLite** lokal di ``output/keputusan.db`` (pemakaian di PC).

API sama: ``init, simpan, simpan_catatan, hapus, muat``. Satu baris per (batch, temuan).
"""
from __future__ import annotations

import datetime as dt
import os
import sqlite3

from src import config

DB_PATH = config.OUTPUT_DIR / "keputusan.db"

STATUS_VALID = {"terima", "tahan", "tolak"}
TABEL = "keputusan"


# --------------------------------------------------------------------------- Supabase REST
def _rest_cfg():
    """(url, key) bila Supabase dikonfigurasi, selainnya None."""
    url = (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")
    key = (os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_KEY") or "").strip()
    return (url, key) if url and key else None


def _rest(method: str, params=None, body=None, prefer=None):
    import requests
    url, key = _rest_cfg()
    headers = {"apikey": key, "Content-Type": "application/json"}
    if prefer:
        headers["Prefer"] = prefer
    r = requests.request(method, f"{url}/rest/v1/{TABEL}",
                         headers=headers, params=params, json=body, timeout=20)
    r.raise_for_status()
    return r


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
    if _rest_cfg() is None:
        _init_sqlite()


def simpan(batch: str, temuan_id: str, status: str,
           catatan: str = "", oleh: str = "") -> None:
    """Simpan/timpa satu keputusan. status harus salah satu STATUS_VALID."""
    if status not in STATUS_VALID:
        raise ValueError(f"status tidak sah: {status}")
    waktu = dt.datetime.now().isoformat(timespec="seconds")
    row = dict(batch=batch, temuan_id=temuan_id, status=status,
               catatan=catatan, oleh=oleh, waktu=waktu)
    if _rest_cfg():
        _rest("POST", body=row, prefer="resolution=merge-duplicates,return=minimal")
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
    if _rest_cfg():
        _rest("PATCH", params={"batch": f"eq.{batch}", "temuan_id": f"eq.{temuan_id}"},
              body={"catatan": catatan}, prefer="return=minimal")
        return
    _init_sqlite()
    with _conn() as c:
        c.execute("UPDATE keputusan SET catatan=? WHERE batch=? AND temuan_id=?",
                  (catatan, batch, temuan_id))


def hapus(batch: str, temuan_id: str) -> None:
    if _rest_cfg():
        _rest("DELETE", params={"batch": f"eq.{batch}", "temuan_id": f"eq.{temuan_id}"},
              prefer="return=minimal")
        return
    _init_sqlite()
    with _conn() as c:
        c.execute("DELETE FROM keputusan WHERE batch=? AND temuan_id=?", (batch, temuan_id))


def muat(batch: str) -> dict[str, dict]:
    """temuan_id -> {status, catatan, oleh, waktu} untuk satu batch."""
    if _rest_cfg():
        r = _rest("GET", params={"batch": f"eq.{batch}",
                                 "select": "temuan_id,status,catatan,oleh,waktu"})
        rows = r.json() or []
        return {row["temuan_id"]: dict(status=row["status"], catatan=row.get("catatan") or "",
                                       oleh=row.get("oleh") or "", waktu=row.get("waktu") or "")
                for row in rows}
    _init_sqlite()
    with _conn() as c:
        rows = c.execute(
            "SELECT temuan_id, status, catatan, oleh, waktu FROM keputusan WHERE batch=?",
            (batch,)).fetchall()
    return {r["temuan_id"]: dict(status=r["status"], catatan=r["catatan"] or "",
                                 oleh=r["oleh"] or "", waktu=r["waktu"] or "") for r in rows}
