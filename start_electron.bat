@echo off
set NODE_ENV=development
powershell -Command "Stop-Process -Id (Get-NetTCPConnection -LocalPort 8088 -ErrorAction SilentlyContinue).OwningProcess -Force -ErrorAction SilentlyContinue" > NUL 2>&1
start npm run dev
timeout /t 3 /nobreak > NUL
.\node_modules\.bin\electron electron\main.cjs

