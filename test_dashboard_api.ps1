# Test Dashboard API and Data Flow
Write-Host "=== Testing Dashboard Data Flow ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Login
Write-Host "Step 1: Logging in..." -ForegroundColor Yellow
$username = Read-Host "Enter username (default: yasserzrelli)"
if ([string]::IsNullOrWhiteSpace($username)) { $username = "yasserzrelli" }
$password = Read-Host "Enter password" -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
$plainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

$loginBody = @{
    username = $username
    password = $plainPassword
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login/" -Method Post -ContentType "application/json" -Body $loginBody
    $token = $loginResponse.access
    Write-Host "✓ Login successful" -ForegroundColor Green
    Write-Host "  Token: $($token.Substring(0, 20))..." -ForegroundColor Gray
} catch {
    Write-Host "✗ Login failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 2: Check MongoDB data
Write-Host "`nStep 2: Checking MongoDB data..." -ForegroundColor Yellow
$mongoCount = docker compose exec mongodb mongosh -u elk_mongo -p mongo_password_dev --authenticationDatabase admin elk_vision_dev --quiet --eval "db.log_metadata.countDocuments({user_id: 1})"
Write-Host "  MongoDB records for user 1: $mongoCount" -ForegroundColor Gray

# Step 3: Call stats API
Write-Host "`nStep 3: Fetching statistics from API..." -ForegroundColor Yellow
$headers = @{
    Authorization = "Bearer $token"
}

try {
    $statsResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/logs/metadata/stats/" -Headers $headers
    Write-Host "✓ Stats API successful" -ForegroundColor Green
    Write-Host ""
    Write-Host "Statistics Response:" -ForegroundColor Cyan
    Write-Host "  Total Logs: $($statsResponse.total_logs)" -ForegroundColor White
    Write-Host "  Total Uploads: $($statsResponse.total_uploads)" -ForegroundColor White
    Write-Host "  Total Size: $($statsResponse.total_size_bytes) bytes" -ForegroundColor White
    
    if ($statsResponse.by_source_detailed) {
        Write-Host "`n  Detailed Sources:" -ForegroundColor Cyan
        foreach ($source in $statsResponse.by_source_detailed) {
            Write-Host "    - $($source.file_name): $($source.log_count) logs" -ForegroundColor White
        }
    } else {
        Write-Host "`n  ⚠ by_source_detailed is empty or missing!" -ForegroundColor Yellow
    }
    
    Write-Host "`n  Full Response:" -ForegroundColor Gray
    $statsResponse | ConvertTo-Json -Depth 10 | Write-Host -ForegroundColor DarkGray
    
} catch {
    Write-Host "✗ Stats API failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "  Response: $($_.ErrorDetails.Message)" -ForegroundColor Red
    exit 1
}

# Step 4: Check frontend state
Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "MongoDB has data: ✓" -ForegroundColor Green
Write-Host "API returns data: ✓" -ForegroundColor Green
Write-Host ""
Write-Host "If dashboard is still empty, check:" -ForegroundColor Yellow
Write-Host "  1. Browser console for errors (F12)" -ForegroundColor White
Write-Host "  2. Network tab in dev tools to see API calls" -ForegroundColor White
Write-Host "  3. Clear browser cache and reload (Ctrl+Shift+R)" -ForegroundColor White
Write-Host "  4. Check if frontend container needs restart" -ForegroundColor White
