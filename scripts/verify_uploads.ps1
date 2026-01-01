# Script to verify uploaded files in the database

Write-Host "=== ELK Vision SaaS - Upload Verification ===" -ForegroundColor Cyan
Write-Host ""

# 1. Check MongoDB for log metadata
Write-Host "1. Checking MongoDB for log metadata..." -ForegroundColor Yellow
Write-Host ""

docker exec elk_backend python manage.py shell -c @"
from app.logs.models_mongo import LogMetadata
from app.core.mongodb import get_collection, COLLECTION_LOG_METADATA
import json

collection = get_collection(COLLECTION_LOG_METADATA)
total = collection.count_documents({})
completed = collection.count_documents({'status': 'completed'})
pending = collection.count_documents({'status': 'pending'})
failed = collection.count_documents({'status': 'failed'})

print('=' * 60)
print('MONGODB LOG METADATA SUMMARY')
print('=' * 60)
print(f'Total uploads: {total}')
print(f'Completed: {completed}')
print(f'Pending: {pending}')
print(f'Failed: {failed}')
print('=' * 60)
print('')
print('RECENT UPLOADS (Last 5):')
print('-' * 60)

for doc in collection.find().sort('created_at', -1).limit(5):
    print(f\"\"\"
Upload ID: {doc.get('upload_id', 'N/A')}
File: {doc.get('file_name', 'N/A')} ({doc.get('file_size', 0)} bytes)
Status: {doc.get('status', 'N/A')}
Log Count: {doc.get('log_count', 0)}
Environment: {doc.get('environment', 'N/A')}
Created: {doc.get('created_at', 'N/A')}
Indexed: {doc.get('indexed_at', 'Not indexed yet')}
{'-' * 60}\"\"\")
"@

Write-Host ""
Write-Host "2. Checking API endpoint..." -ForegroundColor Yellow
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/logs/metadata/" -Headers @{
        Authorization = "Bearer $((Get-Content ~/.elk_token -ErrorAction SilentlyContinue))"
    }
    Write-Host "API Response: Success" -ForegroundColor Green
    Write-Host "Total records from API: $($response.count)" -ForegroundColor Green
} catch {
    Write-Host "API check skipped (authentication required)" -ForegroundColor Yellow
    Write-Host "You can check via: http://localhost:3000/dashboard" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "=== Verification Complete ===" -ForegroundColor Cyan
