@echo off
chcp 65001 >nul
net session >nul 2>&1
if %errorlevel% neq 0 (
  echo ============================================================
  echo   HARUS DIJALANKAN SEBAGAI ADMINISTRATOR
  echo ============================================================
  echo.
  echo   Klik KANAN file ini, lalu pilih "Run as administrator".
  echo.
  pause
  exit /b
)
echo Menambahkan izin firewall untuk port 8531 (TCP, masuk)...
netsh advfirewall firewall delete rule name="Olaif Dashboard 8531" >nul 2>&1
netsh advfirewall firewall add rule name="Olaif Dashboard 8531" dir=in action=allow protocol=TCP localport=8531
echo.
echo ============================================================
echo   SELESAI. Port 8531 kini diizinkan di firewall.
echo   PC lain bisa buka: http://192.168.2.96:8531
echo ============================================================
echo.
pause
