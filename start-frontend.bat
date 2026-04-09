@echo off
title Concentration Detection System - All Services

echo ========================================
echo   Concentration Detection System
echo   Starting All Services
echo ========================================
echo.

cd /d "%~dp0"

echo [INFO] Starting Unified API Server (Port 5000)...
start "Unified API Server" cmd /k "python unified_api_server.py"
timeout /t 3 /nobreak >nul

echo [INFO] Starting YOLO Test API Server (Port 5003)...
start "YOLO Test API Server" cmd /k "python test_yolo.py"
timeout /t 3 /nobreak >nul

echo [INFO] Starting YOLO Train API Server (Port 5004)...
start "YOLO Train API Server" cmd /k "python yolo_train_api.py"
timeout /t 3 /nobreak >nul

echo [INFO] Starting Dataset API Server (Port 5006)...
start "Dataset API Server" cmd /k "python dataset_api.py"
timeout /t 3 /nobreak >nul

echo.
echo [INFO] All Backend Servers Started!
echo [INFO] Starting Frontend Server...
echo.

cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo [INFO] First run detected, installing dependencies...
    echo.
    npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
    echo.
    echo [INFO] Dependencies installed successfully
    echo.
)

echo [INFO] Starting frontend server...
echo.
npm run dev

pause
