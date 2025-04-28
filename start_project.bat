@echo off
REM Start backend server in a new command prompt window
start cmd /k "echo Starting backend server... & python backend_proxy.py"

REM Start frontend server in a new command prompt window
start cmd /k "echo Starting frontend server... & npm run dev"

echo Both backend and frontend servers are starting...
