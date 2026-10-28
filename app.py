"""Dashboard Cek Klaim Rafaksi Olaif - tampilan Streamlit.

Semua angka dihitung dari data (lihat src/). Jalankan:
    streamlit run app.py
"""
from __future__ import annotations

import base64
import datetime as dt
import glob
import html
import os

import streamlit as st

from dotenv import load_dotenv

from src import config, ekspor, keputusan
from src.dashboard_data import siapkan_data
from src.referensi import fmt_rp

load_dotenv(config.BASE_DIR / ".env")

# Saat di-host online (Streamlit Cloud), kredensial datang dari st.secrets -> salin ke env.
try:
    for _k in ("DASHBOARD_PASSWORD", "SUPABASE_URL", "SUPABASE_KEY", "ANTHROPIC_API_KEY"):
        if not os.getenv(_k) and _k in st.secrets:
            os.environ[_k] = str(st.secrets[_k])
except Exception:
    pass

st.set_page_config(page_title="Cek Klaim Rafaksi Olaif", layout="wide",
                   initial_sidebar_state="collapsed")

REF_DATE = dt.date(2026, 10, 28)
BATCH_ID = "agustus-2026"

# --------------------------------------------------------------------------- CSS
CSS = """
<style>
:root{
  --bg:#e9f1ed; --card:#ffffff; --border:#e2e8e3; --ink:#1f2a30; --muted:#8b9299;
  --green:#2d7d5e; --amber:#b06f16; --red:#bc3b2d; --yellow:#e3b53f;
  --navy:#182a38; --brand:#059e8a;
}
.stApp{ background:var(--bg); }
#MainMenu,header[data-testid="stHeader"],footer{ visibility:hidden; height:0; }
.block-container{ padding:0.6rem 1.4rem 3rem; max-width:1280px; }
html,body,[class*="css"]{ font-family:-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  color:var(--ink); }

.card{ background:var(--card); border:1px solid var(--border); border-radius:14px;
  padding:18px 20px; }
.muted{ color:var(--muted); }
.small{ font-size:12.5px; }

/* header */
.appbar{ background:var(--navy); border-radius:14px; padding:16px 22px; color:#fff;
  display:flex; align-items:center; justify-content:space-between; gap:18px; margin-bottom:14px; }
.appbar .kicker{ color:#9fb0bd; font-size:12px; }
.appbar h1{ font-size:21px; margin:2px 0 0; font-weight:700; letter-spacing:.2px; }
.appbar .batch{ color:#9fb0bd; font-size:11px; margin-bottom:3px; }
.appbar .pill{ background:#223543; color:#dfe8ee; border:1px solid #32424f; border-radius:9px;
  padding:9px 14px; font-size:13px; min-width:300px; }
.appbar .btns{ display:flex; gap:8px; }
.appbar .btn{ border:1px solid #3a4a57; color:#e7edf1; border-radius:9px; padding:9px 14px;
  font-size:13px; white-space:nowrap; }
.appbar .btn.solid{ background:#fff; color:var(--navy); border-color:#fff; font-weight:600; }

/* stepper */
.steps{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:14px; }
.step{ background:var(--card); border:1px solid var(--border); border-radius:12px;
  padding:12px 14px; display:flex; gap:11px; align-items:center; }
.badge-n{ width:24px; height:24px; border-radius:50%; color:#fff; font-size:12px; font-weight:700;
  display:flex; align-items:center; justify-content:center; flex:0 0 auto; }
.badge-n.done{ background:var(--green); } .badge-n.wait{ background:#d9a441; }
.step .t{ font-size:13.5px; font-weight:600; } .step .s{ font-size:11.5px; color:var(--muted); }

/* hero */
.hero{ display:flex; justify-content:space-between; align-items:flex-start; }
.hero .big{ font-size:38px; font-weight:800; letter-spacing:.3px; }
.hero .biggreen{ font-size:34px; font-weight:800; color:var(--green); }
.bar{ display:flex; height:15px; border-radius:7px; overflow:hidden; margin:16px 0 12px; }
.bar>div{ height:100%; }
.legend{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-top:6px; }
.legend .lab{ font-size:12px; color:var(--muted); display:flex; align-items:center; gap:7px; }
.legend .val{ font-size:17px; font-weight:700; margin-top:3px; }
.dot{ width:10px; height:10px; border-radius:3px; display:inline-block; }
.sq{ width:10px; height:10px; border:1.5px solid #c3c8bf; border-radius:3px; display:inline-block; }

/* section titles */
.h2{ font-size:16px; font-weight:700; margin:0 0 2px; }

/* per-supermarket table */
.smrow{ display:grid; grid-template-columns:2.1fr .5fr 1.25fr 2.4fr; gap:10px; align-items:center;
  padding:11px 2px; border-top:1px solid #eef0ea; }
.smrow.head{ border-top:none; color:var(--muted); font-size:11.5px; padding-bottom:6px; }
.smname{ font-weight:600; font-size:14px; } .smpt{ color:var(--muted); font-size:11.5px; }
.smrow .num{ white-space:nowrap; }
.mini{ display:flex; height:7px; border-radius:4px; overflow:hidden; margin-bottom:5px; max-width:220px;}
.mini>div{ height:100%; }
.compx{ font-size:11.5px; color:#5c646b; }
.num{ text-align:right; font-variant-numeric:tabular-nums; }

/* findings */
.finding{ border:1px solid var(--border); border-radius:12px; padding:14px 15px; margin-bottom:12px; }
.finding .ttl{ font-weight:700; font-size:14px; display:flex; justify-content:space-between; gap:10px; }
.finding .ctx{ color:var(--muted); font-size:12px; margin:2px 0 8px; }
.finding .desc{ font-size:12.5px; color:#3f474d; line-height:1.5; }
.finding.compact{ padding:11px 13px; margin-bottom:9px; background:#faf9f5; }
.fbadge{ font-size:11.5px; font-weight:700; padding:3px 9px; border-radius:20px; white-space:nowrap; }
.fbadge.amber{ background:#f6e8cf; color:#8a5a10; }
.fbadge.red{ background:#f6d9d3; color:#a2342699; color:#a23426; }
.fbadge.grey{ background:#ecebe6; color:#6c7177; }

/* timeline */
.tl-legend{ display:flex; gap:18px; flex-wrap:wrap; font-size:11.5px; color:var(--muted); margin:2px 0 12px;}
.tlwrap{ width:100%; }
.tlhead{ display:grid; align-items:center; padding-bottom:5px; border-bottom:1px solid #e9ebe4; }
.tlm{ font-size:11px; color:var(--muted); text-align:center; }
.tlm.r{ text-align:right; }
.tl2row{ display:grid; align-items:center; height:44px; border-bottom:1px solid #f1f3ee; position:relative;}
.tl2row>div{ grid-row:1; }
.tl2row .l{ grid-column:1; }
.tl2row .store{ font-size:13px; font-weight:600; } .tl2row .code{ font-size:11px; color:var(--muted); }
.tlc{ height:44px; border-left:1px solid #f3f4ef; grid-row:1; }
.blk{ grid-row:1; height:26px; border-radius:6px; display:flex; align-items:center; justify-content:center;
  color:#fff; font-size:11px; font-weight:600; margin:0 3px; z-index:1; }
.blk.sesuai{ background:var(--green); } .blk.ppn{ background:var(--yellow); color:#5c4a12; }
.blk.konfirmasi{ background:var(--amber); } .blk.luar{ background:var(--red); }
.tot{ grid-row:1; font-weight:700; font-size:12.5px; text-align:right; font-variant-numeric:tabular-nums; }

/* streamlit buttons -> small outline; selected = navy */
.stButton>button{ border:1px solid #cfd4cb; background:#fff; color:#2a333a; border-radius:8px;
  padding:3px 12px; font-size:12.5px; font-weight:500; min-height:0; line-height:1.7; }
.stButton>button:hover{ border-color:#9aa29a; color:#11181e; }
.stButton>button[kind="primary"]{ background:var(--navy); color:#fff; border-color:var(--navy); }
div[data-testid="stHorizontalBlock"]{ gap:7px; }

/* HEADER dibuat dari kolom Streamlit; bar teal (warna logo) lewat :has(.hdr-marker) */
div[data-testid="stHorizontalBlock"]:has(.hdr-marker){ background:var(--brand); border-radius:14px;
  padding:12px 22px; margin-bottom:14px; align-items:center; }
.hdr.brand{ display:flex; align-items:center; gap:13px; }
.hdr .logo{ height:30px; width:auto; display:block; }
.hdr h1.apptitle{ color:#fff; font-size:18px; margin:0; font-weight:600; letter-spacing:.2px;
  padding-left:13px; border-left:1px solid rgba(255,255,255,.35); line-height:1.2; }
.hdr .batch{ color:#d6f0ea; font-size:11px; margin-bottom:2px; }
div[data-testid="stHorizontalBlock"]:has(.hdr-marker) .stButton>button,
div[data-testid="stHorizontalBlock"]:has(.hdr-marker) .stDownloadButton>button{
  width:100%; border:1px solid rgba(255,255,255,.45); background:rgba(255,255,255,.14); color:#fff;
  border-radius:9px; padding:9px 8px; font-size:12.5px; font-weight:500; }
div[data-testid="stHorizontalBlock"]:has(.hdr-marker) .stButton>button:hover{ background:rgba(255,255,255,.24); }
div[data-testid="stHorizontalBlock"]:has(.hdr-marker) .stDownloadButton>button{
  background:#fff; color:#037a6b; border-color:#fff; font-weight:600; }
div[data-testid="stHorizontalBlock"]:has(.hdr-marker) .stDownloadButton>button:hover{ background:#eef7f5; color:#037a6b; }
div[data-testid="stHorizontalBlock"]:has(.hdr-marker) div[data-baseweb="select"]>div{
  background:rgba(255,255,255,.15); border-color:rgba(255,255,255,.35); color:#fff; border-radius:9px; font-size:12.5px; }
div[data-testid="stHorizontalBlock"]:has(.hdr-marker) div[data-baseweb="select"] *{ color:#fff !important; }

/* catatan temuan */
.finding-note input{ font-size:12px !important; padding:5px 9px !important; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

COLORS = {"sesuai": "var(--green)", "ppn": "var(--yellow)",
          "konfirmasi": "var(--amber)", "luar": "var(--red)"}


def esc(s) -> str:
    return html.escape(str(s))


@st.cache_data(show_spinner=False)
def _logo_b64(nama: str = "olaif-putih.png") -> str:
    p = os.path.join(os.path.dirname(__file__), "assets", nama)
    with open(p, "rb") as fh:
        return base64.b64encode(fh.read()).decode("ascii")


# --------------------------------------------------------------------------- data + state
def _src_version() -> str:
    files = glob.glob(os.path.join(os.path.dirname(__file__), "src", "*.py")) + [__file__]
    return str(max(os.path.getmtime(f) for f in files))


@st.cache_data(show_spinner=False)
def _load(ref_iso: str, ver: str):
    return siapkan_data(dt.date.fromisoformat(ref_iso))


# --------------------------------------------------------------- gerbang kata sandi
def _gerbang_sandi():
    sandi = (os.getenv("DASHBOARD_PASSWORD") or "").strip()
    if not sandi or st.session_state.get("auth_ok"):
        return  # tanpa sandi di .env -> bebas (mis. pemakaian di LAN)
    st.markdown(
        '<div style="max-width:400px;margin:11vh auto 10px;text-align:center">'
        f'<img src="data:image/png;base64,{_logo_b64("olaif-teal.png")}" style="height:40px"/>'
        '<div style="font-weight:700;font-size:17px;color:var(--ink);margin-top:12px">Cek Klaim Rafaksi</div>'
        '<div class="muted small" style="margin:4px 0 2px">Masukkan kata sandi untuk membuka dashboard.</div>'
        '</div>', unsafe_allow_html=True)
    c = st.columns([1, 1.4, 1])[1]
    with c:
        pw = st.text_input("Kata sandi", type="password", label_visibility="collapsed",
                           placeholder="Kata sandi", key="pw_input")
        if st.button("Masuk", type="primary", use_container_width=True):
            if pw == sandi:
                st.session_state.auth_ok = True
                st.rerun()
            else:
                st.error("Kata sandi salah.")
    st.stop()


_gerbang_sandi()
D = _load(REF_DATE.isoformat(), _src_version())
if "sel_sm" not in st.session_state:
    st.session_state.sel_sm = "Aeon"

decisions = keputusan.muat(BATCH_ID)          # {temuan_id: {status, catatan, ...}}
n_diputus = sum(1 for t in D["temuan"] if decisions.get(t["id"]))
R = D["ringkasan"]


def _simpan_catatan(tid: str):
    keputusan.simpan_catatan(BATCH_ID, tid, st.session_state.get(f"cat_{tid}", ""))


# --------------------------------------------------------------------------- unggah
def _simpan_file_unggahan(folder, uf, timpa: bool):
    """Simpan satu file unggahan ke `folder`. Tidak menimpa file lain kecuali
    `timpa=True` (instruksi eksplisit user, mis. mengganti file kesepakatan baku).
    Kembalikan (path_tersimpan, status) -> status: 'baru' | 'diganti' | 'salinan'."""
    folder.mkdir(parents=True, exist_ok=True)
    tujuan = folder / os.path.basename(uf.name)
    if tujuan.exists() and not timpa:
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M")
        tujuan = folder / f"{tujuan.stem} (unggahan {stamp}){tujuan.suffix}"
        status = "salinan"
    else:
        status = "diganti" if tujuan.exists() else "baru"
    with open(tujuan, "wb") as fh:
        fh.write(uf.getbuffer())
    return tujuan, status


@st.dialog("Unggah file kesepakatan")
def _dlg_unggah_kesepakatan():
    st.caption("Pilih file Excel kesepakatan (.xlsx). Dashboard membaca 3 file baku: "
               "Promo_Olaif_2026_1.xlsx, Olaif_Q2_2025.xlsx, Promo_Olaif_Q4_2025_1.xlsx. "
               "Unggah file dengan nama sama untuk memperbaruinya.")
    ufs = st.file_uploader("Kesepakatan", type=["xlsx"], accept_multiple_files=True,
                           key="up_kes_file", label_visibility="collapsed")
    timpa = st.checkbox("Izinkan mengganti file lama yang namanya sama", value=False,
                        key="up_kes_timpa")
    if st.button("Simpan", key="up_kes_save", type="primary", disabled=not ufs):
        hasil = [_simpan_file_unggahan(config.KESEPAKATAN_DIR, uf, timpa) for uf in ufs]
        st.cache_data.clear()
        n_ganti = sum(1 for _, s in hasil if s == "diganti")
        n_salin = sum(1 for _, s in hasil if s == "salinan")
        pesan = f"{len(hasil)} file kesepakatan tersimpan"
        if n_ganti:
            pesan += f", {n_ganti} diganti"
        if n_salin:
            pesan += f", {n_salin} disimpan sebagai salinan (nama sudah ada)"
        st.toast(pesan + ".", icon="✅")
        st.rerun()


@st.dialog("Unggah invoice (PDF)")
def _dlg_unggah_invoice():
    st.caption("Pilih PDF tagihan Filia (.pdf), boleh beberapa sekaligus. "
               "File disimpan ke data/invoice/.")
    st.info("Setelah diunggah, PDF **perlu dibaca dulu** agar muncul di dashboard. "
            "Cara gratis: buka sesi Claude Code lalu bilang "
            "“ada invoice baru di data/invoice, tolong dibaca”.")
    ufs = st.file_uploader("Invoice", type=["pdf"], accept_multiple_files=True,
                           key="up_inv_file", label_visibility="collapsed")
    if st.button("Simpan ke data/invoice/", key="up_inv_save", type="primary",
                 disabled=not ufs):
        for uf in ufs:
            _simpan_file_unggahan(config.INVOICE_DIR, uf, timpa=False)
        st.toast(f"{len(ufs)} PDF tersimpan di data/invoice/. "
                 "Minta Claude Code membacanya agar muncul di dashboard.", icon="✅")
        st.rerun()


# --------------------------------------------------------------------------- header
_excel = ekspor.bangun_excel_bytes(D, decisions, "Agustus 2026")
h = st.columns([2.7, 2.1, 1.2, 1.2, 1.05], vertical_alignment="center")
with h[0]:
    st.markdown('<span class="hdr-marker"></span>'
                '<div class="hdr brand">'
                f'<img class="logo" src="data:image/png;base64,{_logo_b64()}" alt="Olaif"/>'
                '<h1 class="apptitle">Cek klaim rafaksi</h1></div>', unsafe_allow_html=True)
with h[1]:
    st.markdown('<div class="hdr"><div class="batch">Batch tagihan</div></div>', unsafe_allow_html=True)
    st.selectbox("Batch", [D["batch_label"]], label_visibility="collapsed", key="batch_sel")
with h[2]:
    if st.button("Unggah kesepakatan", key="up_kes", use_container_width=True):
        _dlg_unggah_kesepakatan()
with h[3]:
    if st.button("Unggah invoice", key="up_inv", use_container_width=True):
        _dlg_unggah_invoice()
with h[4]:
    st.download_button("Unduh Excel", data=_excel,
                       file_name="Rekap_Klaim_Rafaksi_Agustus_2026.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       key="dl_excel", use_container_width=True)

# stepper (langkah 4 dinamis sesuai keputusan tersimpan)
steps = [dict(s) for s in D["stepper"]]
n_temuan = len(D["temuan"])
steps[3]["sub"] = (f"{n_temuan} temuan menunggu" if n_diputus == 0
                   else f"{n_diputus} dari {n_temuan} diputuskan")
steps[3]["state"] = "done" if n_diputus >= n_temuan else "wait"
steps_html = '<div class="steps">'
for s in steps:
    steps_html += (f'<div class="step"><div class="badge-n {s["state"]}">{s["n"]}</div>'
                   f'<div><div class="t">{esc(s["title"])}</div>'
                   f'<div class="s">{esc(s["sub"])}</div></div></div>')
steps_html += "</div>"
st.markdown(steps_html, unsafe_allow_html=True)


# ------------------------------------------------------ ringkasan dinamis (ikut keputusan)
def _ringkasan_dinamis():
    """Angka ringkasan mengikuti keputusan finance:
    - Terima      -> nilai temuan pindah ke 'Sesuai kesepakatan' (layak dibayar)
    - Tolak       -> nilai pindah ke 'Di luar kesepakatan' (tidak dibayar)
    - Tahan/belum -> tetap di kategori asalnya (konfirmasi/luar).
    Jumlah ketiganya selalu sama dengan total ditagih."""
    sesuai = R["sesuai"]          # klaim sesuai tanpa temuan
    konfirmasi = 0
    luar = 0
    for t in D["temuan"]:
        a = t.get("nilai") or 0
        d = (decisions.get(t["id"]) or {}).get("status")
        if d == "terima":
            sesuai += a
        elif d == "tolak":
            luar += a
        elif t["badge_type"] == "amber":   # belum/tahan, kategori konfirmasi
            konfirmasi += a
        elif t["badge_type"] == "red":     # belum/tahan, kategori luar
            luar += a
    return sesuai, konfirmasi, luar


SES, KONF, LUAR = _ringkasan_dinamis()
DITAGIH = R["ditagih"]
def _pct(x):
    return (x / DITAGIH * 100) if DITAGIH else 0


# --------------------------------------------------------------------------- hero
selisih_txt = f"Cocok, selisih {fmt_rp(abs(R['selisih_lampiran']))}"
st.markdown(f"""
<div class="card">
  <div class="hero">
    <div>
      <div class="muted small">Total ditagih Filia, {R['baris_klaim']} baris klaim dari {R['n_supermarket']} supermarket</div>
      <div class="big">{fmt_rp(R['ditagih'])}</div>
    </div>
    <div style="text-align:right">
      <div class="muted small">Layak dibayar sekarang</div>
      <div class="biggreen">{fmt_rp(SES)}</div>
      <div class="muted small">Sisanya ditahan sampai temuan diputuskan</div>
    </div>
  </div>
  <div class="bar">
    <div style="width:{_pct(SES)}%;background:var(--green)"></div>
    <div style="width:{_pct(KONF)}%;background:var(--amber)"></div>
    <div style="width:{_pct(LUAR)}%;background:var(--red)"></div>
  </div>
  <div class="legend">
    <div><div class="lab"><span class="dot" style="background:var(--green)"></span>Sesuai kesepakatan</div>
         <div class="val">{fmt_rp(SES)}</div></div>
    <div><div class="lab"><span class="dot" style="background:var(--amber)"></span>Perlu konfirmasi</div>
         <div class="val">{fmt_rp(KONF)}</div></div>
    <div><div class="lab"><span class="dot" style="background:var(--red)"></span>Di luar kesepakatan</div>
         <div class="val">{fmt_rp(LUAR)}</div></div>
    <div><div class="lab"><span class="sq"></span>Lampiran vs tagihan Filia</div>
         <div class="val" style="font-size:14px">{esc(selisih_txt)}</div></div>
  </div>
</div>
""", unsafe_allow_html=True)

st.write("")
col_kiri, col_kanan = st.columns([1.35, 1], gap="medium")


# --------------------------------------------------------------------------- kiri: per supermarket
def mini_bar(p):
    tot = max(p["ditagih"], 1)
    segs = [("sesuai", p["sesuai"]), ("konfirmasi", p["konf"]), ("luar", p["luar"])]
    inner = "".join(
        f'<div style="width:{v/tot*100}%;background:{COLORS[k]}"></div>' for k, v in segs if v > 0)
    return f'<div class="mini">{inner}</div>'


with col_kiri:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="h2">Per supermarket</div>'
                '<div class="muted small" style="margin-bottom:8px">Pilih supermarket untuk '
                'melihat rincian per toko dan periode di bawah.</div>', unsafe_allow_html=True)
    st.markdown('<div class="smrow head"><div>Supermarket</div><div class="num">Klaim</div>'
                '<div class="num">Ditagih</div><div>Komposisi</div></div>', unsafe_allow_html=True)
    for p in D["per_supermarket"]:
        c1, c2 = st.columns([5.3, 1.1])
        with c1:
            st.markdown(
                f'<div class="smrow"><div><div class="smname">{esc(p["toko"])}</div>'
                f'<div class="smpt">{esc(p["pt"])}</div></div>'
                f'<div class="num">{p["klaim"]}</div>'
                f'<div class="num" style="font-weight:600">{fmt_rp(p["ditagih"])}</div>'
                f'<div>{mini_bar(p)}<div class="compx">{esc(p["komposisi"])}</div></div></div>',
                unsafe_allow_html=True)
        with c2:
            st.write("")
            if st.button("Per toko", key=f"sm_{p['toko']}",
                         type="primary" if st.session_state.sel_sm == p["toko"] else "secondary"):
                st.session_state.sel_sm = p["toko"]
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# --------------------------------------------------------------------------- kanan: temuan
with col_kanan:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="h2">Temuan yang perlu diputuskan</div>'
                f'<div class="muted small" style="margin-bottom:10px">{n_diputus} dari {len(D["temuan"])} '
                f'temuan sudah diputuskan. Keputusan tersimpan dan terlihat oleh finance.</div>',
                unsafe_allow_html=True)
    def _tombol_keputusan(t, dec):
        pilihan = dec.get("status")
        b1, b2, b3, _ = st.columns([1, 1, 1, 2.0])
        for col, lab, val in ((b1, "Terima", "terima"), (b2, "Tahan", "tahan"), (b3, "Tolak", "tolak")):
            with col:
                if st.button(lab, key=f"d_{t['id']}_{val}",
                             type="primary" if pilihan == val else "secondary"):
                    if pilihan == val:
                        keputusan.hapus(BATCH_ID, t["id"])
                    else:
                        keputusan.simpan(BATCH_ID, t["id"], val,
                                         st.session_state.get(f"cat_{t['id']}", dec.get("catatan", "")),
                                         oleh="finance")
                    st.rerun()

    def _kartu_penuh(t, dec, ditahan=False):
        tag = ' <span class="fbadge grey">Ditahan</span>' if ditahan else ""
        st.markdown(
            f'<div class="finding"><div class="ttl"><span>{esc(t["judul"])}{tag}</span>'
            f'<span class="fbadge {t["badge_type"]}">{esc(t["badge"])}</span></div>'
            f'<div class="ctx">{esc(t["konteks"])}</div>'
            f'<div class="desc">{esc(t["deskripsi"])}</div></div>', unsafe_allow_html=True)
        _tombol_keputusan(t, dec)
        st.markdown('<div class="finding-note">', unsafe_allow_html=True)
        st.text_input("Catatan", key=f"cat_{t['id']}", value=dec.get("catatan", ""),
                      placeholder="Catatan (opsional) - tersimpan saat ada keputusan",
                      label_visibility="collapsed", on_change=_simpan_catatan, args=(t["id"],))
        st.markdown('</div>', unsafe_allow_html=True)

    # kelompokkan berdasarkan keputusan
    grup = {"belum": [], "tahan": [], "tolak": [], "terima": []}
    for t in D["temuan"]:
        s = (decisions.get(t["id"]) or {}).get("status")
        grup[s if s in ("tahan", "tolak", "terima") else "belum"].append(t)

    # 1) belum diputuskan & 2) ditahan -> kartu penuh (tetap muncul)
    for t in grup["belum"]:
        _kartu_penuh(t, decisions.get(t["id"]) or {})
    for t in grup["tahan"]:
        _kartu_penuh(t, decisions.get(t["id"]) or {}, ditahan=True)

    # 3) ditolak -> ringkas: judul + angka + alasan
    for t in grup["tolak"]:
        dec = decisions.get(t["id"]) or {}
        alasan = (dec.get("catatan") or "").strip() or t["deskripsi"]
        st.markdown(
            f'<div class="finding compact"><div class="ttl">'
            f'<span>{esc(t["judul"])} <span class="fbadge red">Ditolak</span></span>'
            f'<span class="fbadge {t["badge_type"]}">{esc(t["badge"])}</span></div>'
            f'<div class="desc"><b>Alasan:</b> {esc(alasan)}</div></div>', unsafe_allow_html=True)
        _, ub = st.columns([3, 1])
        with ub:
            if st.button("Ubah", key=f"ubah_{t['id']}"):
                keputusan.hapus(BATCH_ID, t["id"])
                st.rerun()

    # 4) diterima -> disembunyikan, bisa dilihat/dibatalkan lewat daftar kecil
    if grup["terima"]:
        with st.expander(f"Diterima ({len(grup['terima'])}) - sudah disetujui, "
                         "tidak ditampilkan di daftar"):
            for t in grup["terima"]:
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f'<div class="desc" style="padding-top:5px">{esc(t["judul"])} '
                                f'&middot; {esc(t["badge"])}</div>', unsafe_allow_html=True)
                with c2:
                    if st.button("Ubah", key=f"ubah_{t['id']}"):
                        keputusan.hapus(BATCH_ID, t["id"])
                        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# --------------------------------------------------------------------------- timeline
st.write("")
sel = st.session_state.sel_sm
tl = D["timelines"].get(sel, {"months": [], "rows": [], "catatan": ""})
months = tl["months"]
ncol = len(months)

st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown(f'<div class="h2">Per toko dan periode: {esc(sel)}</div>'
            f'<div class="muted small">{esc(tl.get("subjudul",""))}</div>'
            '<div class="tl-legend">'
            '<span><span class="dot" style="background:var(--green)"></span> Sesuai</span>'
            '<span><span class="dot" style="background:var(--yellow)"></span> Sesuai, termasuk PPN</span>'
            '<span><span class="dot" style="background:var(--amber)"></span> Perlu konfirmasi</span>'
            '<span><span class="dot" style="background:var(--red)"></span> Ada bagian di luar kesepakatan</span>'
            '</div>', unsafe_allow_html=True)

# chip selector (fungsional)
chips = st.columns(len(D["per_supermarket"]))
for i, p in enumerate(D["per_supermarket"]):
    with chips[i]:
        if st.button(p["toko"], key=f"chip_{p['toko']}",
                     type="primary" if sel == p["toko"] else "secondary"):
            st.session_state.sel_sm = p["toko"]
            st.rerun()

# grid (CSS grid; tiap baris memakai template kolom yang sama agar sejajar)
if ncol:
    tmpl = f"grid-template-columns:172px repeat({ncol},1fr) 104px;"
    # header
    head = f'<div class="tlhead" style="{tmpl}"><div></div>'
    for m in months:
        head += f'<div class="tlm">{esc(m)}</div>'
    head += '<div class="tlm r">Total</div></div>'

    body = ""
    for row in tl["rows"]:
        r = f'<div class="tl2row" style="{tmpl}">'
        r += (f'<div class="l"><div class="store">{esc(row["nama"])}</div>'
              f'<div class="code">{esc(row["kode_tampil"])}</div></div>')
        for i in range(ncol):
            r += f'<div class="tlc" style="grid-column:{i+2}"></div>'
        for b in sorted(row["blocks"], key=lambda x: x["start"]):
            span = b["end"] - b["start"] + 1
            lab = b["label"] if b["amount"] >= 1_000_000 else ""
            r += (f'<div class="blk {b["status"]}" title="{esc(b["judul"])}" '
                  f'style="grid-column:{b["start"]+2} / span {span}">{esc(lab)}</div>')
        r += f'<div class="tot" style="grid-column:{ncol+2}">{esc(row["total_fmt"])}</div>'
        r += '</div>'
        body += r
    st.markdown(f'<div class="tlwrap">{head}{body}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="muted small" style="margin-top:10px">{esc(tl["catatan"])}</div>',
                unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
