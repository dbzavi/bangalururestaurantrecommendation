@echo off
echo Starting RecommendRestaurant Platform...

:: Start the FastAPI Backend
echo [1/2] Starting FastAPI Backend on port 8000...
start cmd /k "cd backend && call venv\Scripts\activate && uvicorn main:app --port 8000"

:: Start the Frontend Server
echo [2/2] Starting Frontend Web Server on port 3000...
start cmd /k "cd frontend && python -m http.server 3000"

echo.
echo ====================================================
echo Project is running successfully!
echo.
echo - Frontend Application: http://localhost:3000
echo - Backend API: http://localhost:8000/docs
echo ====================================================
echo.
pause
