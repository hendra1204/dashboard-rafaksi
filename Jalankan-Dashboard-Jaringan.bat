@echo off
chcp 65001 >nul
cd /d "Z:\AI\Finance\claude-hendra\Olaif\dashboard-rafaksi-filia"
echo ============================================================
echo   DASHBOARD CEK KLAIM RAFAKSI OLAIF
echo ============================================================
echo.
echo   Buka di PC ini        : http://localhost:8531
echo   Buka di PC lain (LAN) : http://192.168.2.96:8531
echo                   atau  : http://HENDRA-PC:8531
echo.
echo   - Biarkan jendela hitam ini TERBUKA selama dashboard dipakai.
echo   - Tutup jendela ini untuk MEMATIKAN dashboard.
echo   - Jika muncul peringatan Windows Firewall saat pertama kali,
echo     klik "Allow access" / "Izinkan akses".
echo ============================================================
echo.
python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8531 --browser.gatherUsageStats false
echo.
echo (Dashboard berhenti. Tekan tombol apa saja untuk menutup.)
pause >nul
