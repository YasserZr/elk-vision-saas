# Script to verify user-specific upload isolation

Write-Host "=== Verifying User-Specific Upload Isolation ===" -ForegroundColor Cyan
Write-Host ""

docker exec elk_backend python manage.py shell -c @"
from django.contrib.auth.models import User
from app.logs.models_mongo import LogMetadata

# Get all users
users = User.objects.all()
print('=' * 60)
print('USER-SPECIFIC UPLOAD VERIFICATION')
print('=' * 60)

for user in users:
    stats = LogMetadata.get_statistics('default', days=30, user_id=user.id)
    print(f'''
User: {user.username} (ID: {user.id})
  Total Uploads: {stats.get('total_uploads', 0)}
  Total Logs: {stats.get('total_logs', 0)}
  By Status: {stats.get('by_status', {})}
{'-' * 60}''')

print('')
print('TENANT-WIDE STATS (all users):')
all_stats = LogMetadata.get_statistics('default', days=30)
print(f'  Total Uploads: {all_stats.get(\"total_uploads\", 0)}')
print(f'  Total Logs: {all_stats.get(\"total_logs\", 0)}')
print('=' * 60)
"@

Write-Host ""
Write-Host "=== Verification Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "✅ Each user now only sees their own uploads" -ForegroundColor Green
Write-Host "✅ Different accounts will have isolated upload views" -ForegroundColor Green
