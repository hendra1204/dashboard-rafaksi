@echo off
chcp 65001 >nul
cd /d "Z:\AI\Finance\claude-hendra\Olaif\dashboard-rafaksi-filia"
echo ============================================================
echo   DASHBOARD CEK KLAIM RAFAKSI - MODE ONLINE (LINK INTERNET)
echo ============================================================
echo.
echo   1) Menyalakan server dashboard...
start "Dashboard Server - JANGAN DITUTUP" /min cmd /c python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8531 --server.headless true --browser.gatherUsageStats false
echo      (berjalan di jendela terpisah yang diperkecil)
echo   Menunggu server siap...
timeout /t 10 /nobreak >nul
echo.
echo   2) Menyalakan link publik (Cloudflare)...
echo ============================================================
echo   CARI baris berisi:  https://....trycloudflare.com
echo   Itulah LINK yang Anda bagikan ke orang lain.
echo   Kata sandi: lihat DASHBOARD_PASSWORD di file .env
echo.
echo   JANGAN tutup jendela ini selama dashboard dipakai.
echo   (Tiap kali dijalankan, link-nya BERUBAH.)
echo ============================================================
echo.
"Z:\AI\Finance\claude-hendra\Olaif\dashboard-rafaksi-filia\tools\cloudflared.exe" tunnel --url http://localhost:8531 --no-autoupdate
echo.
echo (Tunnel berhenti. Tekan tombol apa saja untuk menutup.)
pause >nul
