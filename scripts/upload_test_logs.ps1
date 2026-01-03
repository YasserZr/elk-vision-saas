# Generate and Upload Test Logs with Varied Log Levels
# This script generates logs with different levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
# and uploads them to the ELK Vision platform

param(
    [int]$LogCount = 500,
    [string]$Token = "",
    [string]$Format = "all"  # json, csv, log, or all
)

Write-Host "=== ELK Vision Test Log Generator ===" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python detected: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Generate logs
Write-Host "`nGenerating $LogCount test logs with varied log levels..." -ForegroundColor Yellow
python scripts/generate_test_logs.py $LogCount

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to generate logs" -ForegroundColor Red
    exit 1
}

Write-Host "`nLogs generated successfully!" -ForegroundColor Green
Write-Host ""

# If no token provided, show instructions
if ([string]::IsNullOrWhiteSpace($Token)) {
    Write-Host "To upload these logs, you need an authentication token." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Get your token by logging into the frontend or using:" -ForegroundColor White
    Write-Host "   curl -X POST http://localhost:8000/api/v1/auth/login/ -H 'Content-Type: application/json' -d '{""username"":""your_username"",""password"":""your_password""}'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. Run this script again with the token:" -ForegroundColor White
    Write-Host "   .\scripts\upload_test_logs.ps1 -Token 'your_access_token_here'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "3. Or upload manually using curl:" -ForegroundColor White
    Write-Host ""
    Write-Host "   JSON:" -ForegroundColor Cyan
    Write-Host "   curl -X POST http://localhost:8000/api/v1/logs/upload/ \" -ForegroundColor Gray
    Write-Host "     -H 'Authorization: Bearer <token>' \" -ForegroundColor Gray
    Write-Host "     -F 'file=@test_logs_varied.json' \" -ForegroundColor Gray
    Write-Host "     -F 'environment=testing' \" -ForegroundColor Gray
    Write-Host "     -F 'service_name=test-service'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   CSV:" -ForegroundColor Cyan
    Write-Host "   curl -X POST http://localhost:8000/api/v1/logs/upload/ \" -ForegroundColor Gray
    Write-Host "     -H 'Authorization: Bearer <token>' \" -ForegroundColor Gray
    Write-Host "     -F 'file=@test_logs_varied.csv' \" -ForegroundColor Gray
    Write-Host "     -F 'environment=testing'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   Text/Log:" -ForegroundColor Cyan
    Write-Host "   curl -X POST http://localhost:8000/api/v1/logs/upload/ \" -ForegroundColor Gray
    Write-Host "     -H 'Authorization: Bearer <token>' \" -ForegroundColor Gray
    Write-Host "     -F 'file=@test_logs_varied.log' \" -ForegroundColor Gray
    Write-Host "     -F 'environment=testing'" -ForegroundColor Gray
    Write-Host ""
    exit 0
}

# Upload logs if token is provided
Write-Host "Uploading logs to ELK Vision platform..." -ForegroundColor Yellow
Write-Host ""

$uploadUrl = "http://localhost:8000/api/v1/logs/upload/"
$headers = @{
    "Authorization" = "Bearer $Token"
}

function Upload-LogFile {
    param(
        [string]$FilePath,
        [string]$FileType
    )
    
    if (-not (Test-Path $FilePath)) {
        Write-Host "WARNING: $FilePath not found, skipping..." -ForegroundColor Yellow
        return
    }
    
    Write-Host "Uploading $FileType logs from $FilePath..." -ForegroundColor Cyan
    
    $form = @{
        file = Get-Item -Path $FilePath
        environment = "testing"
        service_name = "test-service"
        source = "test-data-generator"
        tags = "test,varied-levels"
    }
    
    try {
        $response = Invoke-RestMethod -Uri $uploadUrl -Method Post -Headers $headers -Form $form
        Write-Host "✓ $FileType upload successful!" -ForegroundColor Green
        Write-Host "  Task ID: $($response.task_id)" -ForegroundColor Gray
        Write-Host "  Status: $($response.status)" -ForegroundColor Gray
        if ($response.filename) {
            Write-Host "  Filename: $($response.filename)" -ForegroundColor Gray
        }
        Write-Host ""
    } catch {
        Write-Host "✗ $FileType upload failed: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
    }
}

# Upload based on format parameter
switch ($Format.ToLower()) {
    "json" {
        Upload-LogFile -FilePath "test_logs_varied.json" -FileType "JSON"
    }
    "csv" {
        Upload-LogFile -FilePath "test_logs_varied.csv" -FileType "CSV"
    }
    "log" {
        Upload-LogFile -FilePath "test_logs_varied.log" -FileType "Text"
    }
    default {
        # Upload all formats
        Upload-LogFile -FilePath "test_logs_varied.json" -FileType "JSON"
        Upload-LogFile -FilePath "test_logs_varied.csv" -FileType "CSV"
        Upload-LogFile -FilePath "test_logs_varied.log" -FileType "Text"
    }
}

Write-Host "=== Upload Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Check the dashboard at: http://localhost:3000/dashboard" -ForegroundColor Cyan
Write-Host "View in Kibana at: http://localhost:5601" -ForegroundColor Cyan
