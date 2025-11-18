@echo off
REM Database Setup Script for Writing Prompt Generator (Windows)
REM This script initializes the PostgreSQL database with required tables

echo Starting Database Setup...
echo.

REM Wait for PostgreSQL to be ready
echo Waiting for PostgreSQL to be ready...
:wait_for_postgres
docker exec writing-prompt-generator-postgres-1 pg_isready -U promptuser >nul 2>&1
if %errorlevel% neq 0 (
    echo|set /p="."
    timeout /t 1 /nobreak >nul
    goto wait_for_postgres
)
echo.
echo [32mPostgreSQL is ready![0m
echo.

REM Run the SQL script
echo Creating database tables...
docker exec -i writing-prompt-generator-postgres-1 psql -U promptuser -d writingprompts < scripts/init-db.sql

if %errorlevel% equ 0 (
    echo [32mDatabase tables created successfully![0m
) else (
    echo [31mFailed to create database tables[0m
    exit /b 1
)
echo.

REM Verify tables were created
echo Verifying database setup...
docker exec writing-prompt-generator-postgres-1 psql -U promptuser -d writingprompts -c "\dt"
echo.

echo [32mDatabase setup complete![0m
