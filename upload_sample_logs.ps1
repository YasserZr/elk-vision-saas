# Upload Sample Logs Script
# This script uploads sample logs to populate the dashboard

$baseUrl = "http://localhost:8000/api"
$username = "testuser"
$password = "testpass123"
$logFile = "sample_logs.log"

Write-Host "`n=== ELK Vision - Upload Sample Logs ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Login and get token
Write-Host "1. Logging in..." -ForegroundColor Yellow
try {
    $loginBody = @{
        username = $username
        password = $password
    } | ConvertTo-Json

    $loginResponse = Invoke-RestMethod -Uri "$baseUrl/auth/login/" -Method POST -Body $loginBody -ContentType "application/json"
    $token = $loginResponse.access
    Write-Host "   ✓ Login successful" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Login failed: $_" -ForegroundColor Red
    exit 1
}

# Step 2: Check if log file exists
Write-Host "`n2. Checking log file..." -ForegroundColor Yellow
if (-not (Test-Path $logFile)) {
    Write-Host "   ✗ Log file not found: $logFile" -ForegroundColor Red
    exit 1
}
Write-Host "   ✓ Log file found: $logFile" -ForegroundColor Green

# Step 3: Upload log file
Write-Host "`n3. Uploading logs..." -ForegroundColor Yellow
try {
    # Create multipart form data
    $boundary = [System.Guid]::NewGuid().ToString()
    $fileContent = [System.IO.File]::ReadAllBytes((Resolve-Path $logFile).Path)
    $fileName = [System.IO.Path]::GetFileName($logFile)
    
    # Build multipart body
    $LF = "`r`n"
    $bodyLines = @(
        "--$boundary",
        "Content-Disposition: form-data; name=`"file`"; filename=`"$fileName`"",
        "Content-Type: text/plain",
        "",
        [System.Text.Encoding]::UTF8.GetString($fileContent),
        "--$boundary",
        "Content-Disposition: form-data; name=`"source`"",
        "",
        "sample-app",
        "--$boundary",
        "Content-Disposition: form-data; name=`"environment`"",
        "",
        "production",
        "--$boundary",
        "Content-Disposition: form-data; name=`"service_name`"",
        "",
        "web-server",
        "--$boundary--"
    ) -join $LF

    $headers = @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "multipart/form-data; boundary=$boundary"
    }

    $uploadResponse = Invoke-RestMethod -Uri "$baseUrl/v1/logs/upload/" -Method POST -Headers $headers -Body $bodyLines
    
    Write-Host "   ✓ Upload successful!" -ForegroundColor Green
    Write-Host "     - Upload ID: $($uploadResponse.upload_id)" -ForegroundColor Gray
    Write-Host "     - Logs processed: $($uploadResponse.total_logs)" -ForegroundColor Gray
    Write-Host "     - Processing time: $($uploadResponse.processing_time_seconds)s" -ForegroundColor Gray
} catch {
    Write-Host "   ✗ Upload failed: $_" -ForegroundColor Red
    Write-Host "     Response: $($_.Exception.Response)" -ForegroundColor Gray
    exit 1
}

# Step 4: Verify data
Write-Host "`n4. Verifying uploaded data..." -ForegroundColor Yellow
try {
    Start-Sleep -Seconds 2  # Wait for processing
    $statsResponse = Invoke-RestMethod -Uri "$baseUrl/v1/logs/metadata/stats/" -Method GET -Headers @{"Authorization"="Bearer $token"}
    
    Write-Host "   ✓ Data verified!" -ForegroundColor Green
    Write-Host "     - Total logs: $($statsResponse.total_logs)" -ForegroundColor Gray
    Write-Host "     - Total uploads: $($statsResponse.total_uploads)" -ForegroundColor Gray
    Write-Host "     - INFO logs: $($statsResponse.by_level.info)" -ForegroundColor Gray
    Write-Host "     - ERROR logs: $($statsResponse.by_level.error)" -ForegroundColor Gray
    Write-Host "     - WARNING logs: $($statsResponse.by_level.warning)" -ForegroundColor Gray
    Write-Host "     - DEBUG logs: $($statsResponse.by_level.debug)" -ForegroundColor Gray
} catch {
    Write-Host "   ! Could not fetch stats (this is okay)" -ForegroundColor Yellow
}

Write-Host "`n=== Upload Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Dashboard should now display:" -ForegroundColor Green
Write-Host "  ✓ System Health (all services)" -ForegroundColor White
Write-Host "  ✓ Log Level Distribution (chart)" -ForegroundColor White
Write-Host "  ✓ Log Activity Timeline (sparkline)" -ForegroundColor White
Write-Host "  ✓ Log Sources (table)" -ForegroundColor White
Write-Host ""
Write-Host "Refresh your dashboard at: http://localhost:3000/dashboard" -ForegroundColor Cyan
Write-Host ""
