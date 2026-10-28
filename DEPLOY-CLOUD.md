# Deploy Dashboard ke Cloud (gratis, 24 jam)

Tujuan: dashboard bisa dibuka dari mana saja, **walau PC dimatikan**, tanpa biaya.

Susunan: **Streamlit Community Cloud** (menjalankan aplikasi) + **Supabase** (menyimpan
keputusan, permanen) + **GitHub** (menyimpan kode, repo privat).

Kode sudah disiapkan: `src/keputusan.py` otomatis memakai Supabase bila ada
`SUPABASE_URL` & `SUPABASE_KEY`; sandi dibaca dari `DASHBOARD_PASSWORD`. Di cloud,
ketiganya diisi lewat **Secrets** Streamlit (bukan file).

---

## Langkah 1 — Akun GitHub (gratis)
Daftar di https://github.com/signup (kalau belum punya).

## Langkah 2 — Akun + project Supabase (gratis)
1. Daftar di https://supabase.com → **New project** (pilih region terdekat, mis. Singapore).
   Simpan **Database password** (tidak dipakai langsung, tapi jangan hilang).
2. Buka menu **SQL Editor** → tempel SQL ini → **Run**:

   ```sql
   create table if not exists public.keputusan (
     batch text not null,
     temuan_id text not null,
     status text not null,
     catatan text,
     oleh text,
     waktu text,
     primary key (batch, temuan_id)
   );
   ```
3. Buka **Project Settings → API**, catat dua ini (untuk dipakai di Langkah 4):
   - **Project URL** (mis. `https://abcd.supabase.co`) → jadi `SUPABASE_URL`
   - **service_role** key (bagian "Project API keys") → jadi `SUPABASE_KEY`
   > service_role bersifat RAHASIA. Hanya ditaruh di Secrets Streamlit (Langkah 4),
   > jangan pernah di-commit atau dibagikan.

## Langkah 3 — Kirim kode ke GitHub (repo privat)
Dibantu lewat `gh` CLI (Claude yang jalankan setelah Anda login sekali):
```
gh auth login        # Anda ikuti di browser (sekali saja)
```
Lalu Claude membuat repo privat & push. (Alternatif: buat repo privat di web GitHub,
lalu unggah file — tapi cara gh lebih cepat.)

File yang TIDAK ikut (sudah diatur di .gitignore): `.env`, `output/`, `tools/`,
`data/invoice/` (PDF besar, tidak dipakai dashboard), secrets.

## Langkah 4 — Deploy di Streamlit Community Cloud (gratis)
1. Buka https://share.streamlit.io → **Sign in with GitHub**.
2. **Create app** → pilih repo tadi → **Main file**: `app.py` → **Deploy**.
3. Buka **Settings → Secrets**, tempel (ganti nilainya):
   ```toml
   DASHBOARD_PASSWORD = "OlaifRafaksi2026"
   SUPABASE_URL = "https://abcd.supabase.co"
   SUPABASE_KEY = "eyJ...service_role..."
   ```
4. Simpan. Aplikasi otomatis restart. Anda dapat link tetap:
   `https://<nama>.streamlit.app` — inilah link yang dibagikan (24 jam, PC boleh mati).

---

## Catatan
- Link `.streamlit.app` **tetap** (tidak berubah-ubah seperti Cloudflare).
- Aplikasi gratis bisa "tidur" bila lama tak dibuka; bangun ~beberapa detik saat dikunjungi.
- Data keuangan tersimpan di GitHub privat + Supabase (sudah Anda setujui).
- Pembacaan PDF baru tetap lewat sesi Claude Code (hasil JSON di-commit ke repo).
