@echo off
set NODE_ENV=development
start npm run dev
timeout /t 3 /nobreak > NUL
.\node_modules\.bin\electron electron\main.cjs
