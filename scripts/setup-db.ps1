# Database Setup Script for Writing Prompt Generator (PowerShell)
# This script initializes the PostgreSQL database with required tables

Write-Host "🚀 Starting Database Setup..." -ForegroundColor Cyan
Write-Host ""

# Wait for PostgreSQL to be ready
Write-Host "⏳ Waiting for PostgreSQL to be ready..." -ForegroundColor Yellow
$ready = $false
while (-not $ready) {
    $result = docker exec writing-prompt-generator-postgres-1 pg_isready -U promptuser 2>&1
    if ($LASTEXITCODE -eq 0) {
        $ready = $true
    } else {
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 1
    }
}
Write-Host ""
Write-Host "✓ PostgreSQL is ready!" -ForegroundColor Green
Write-Host ""

# Run the SQL script
Write-Host "🔨 Creating database tables..." -ForegroundColor Cyan
Get-Content scripts/init-db.sql | docker exec -i writing-prompt-generator-postgres-1 psql -U promptuser -d writingprompts

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Database tables created successfully!" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to create database tables" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Verify tables were created
Write-Host "🔍 Verifying database setup..." -ForegroundColor Cyan
docker exec writing-prompt-generator-postgres-1 psql -U promptuser -d writingprompts -c "\dt"
Write-Host ""

Write-Host "✅ Database setup complete!" -ForegroundColor Green
