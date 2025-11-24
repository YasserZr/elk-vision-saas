# Log Upload API Documentation

## Overview
Secure API endpoint for uploading log files to the ELK Vision SaaS platform. Supports multiple formats with validation, parsing, and asynchronous processing.

## Endpoint

```
POST /api/v1/logs/upload/
```

### Authentication
Requires JWT authentication token in the Authorization header:
```
Authorization: Bearer <access_token>
```

## Supported File Formats

- **JSON** (.json) - Single object or array of log objects
- **CSV** (.csv) - Comma-separated values with headers
- **Text** (.txt, .log) - Plain text logs

## File Limitations

- **Maximum file size**: 50MB
- **Encoding**: UTF-8 only
- **Content types**: application/json, text/csv, text/plain

## Request Format

**Content-Type**: `multipart/form-data`

### Form Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | File | Yes | Log file to upload |
| source | String | No | Source identifier (default: "manual_upload") |
| environment | String | No | Environment: production/staging/development/testing |
| service_name | String | No | Service name (default: "unknown") |
| tags | Array | No | Array of tags for categorization |

## Example Requests

### cURL - JSON Log Upload

```bash
curl -X POST http://localhost:8000/api/v1/logs/upload/ \
  -H "Authorization: Bearer <your_token>" \
  -F "file=@logs.json" \
  -F "source=api_server" \
  -F "environment=production" \
  -F "service_name=user_service" \
  -F "tags=authentication,api"
```

### cURL - CSV Log Upload

```bash
curl -X POST http://localhost:8000/api/v1/logs/upload/ \
  -H "Authorization: Bearer <your_token>" \
  -F "file=@server_logs.csv" \
  -F "environment=staging"
```

### Python - Requests Library

```python
import requests

url = "http://localhost:8000/api/v1/logs/upload/"
headers = {
    "Authorization": "Bearer <your_token>"
}

files = {
    'file': open('logs.json', 'rb')
}

data = {
    'source': 'python_app',
    'environment': 'production',
    'service_name': 'data_processor',
    'tags': ['batch', 'etl']
}

response = requests.post(url, headers=headers, files=files, data=data)
print(response.json())
```

### JavaScript - Fetch API

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('source', 'web_app');
formData.append('environment', 'production');
formData.append('service_name', 'frontend');

fetch('http://localhost:8000/api/v1/logs/upload/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  },
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

## Response Format

### Success Response (202 Accepted)

```json
{
  "task_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "message": "File uploaded successfully and queued for processing",
  "file_name": "server_logs.json",
  "file_size": 1048576,
  "format": "json",
  "estimated_entries": 1500,
  "status": "processing"
}
```

### Error Response (400 Bad Request)

```json
{
  "error": "Validation failed",
  "details": {
    "file": [
      "File size exceeds maximum limit of 50.0MB"
    ]
  }
}
```

## File Format Examples

### JSON Format

**Single Entry:**
```json
{
  "timestamp": "2025-11-24T10:00:00Z",
  "level": "ERROR",
  "message": "Database connection failed",
  "service": "api",
  "error_code": "DB_CONN_001"
}
```

**Multiple Entries:**
```json
[
  {
    "timestamp": "2025-11-24T10:00:00Z",
    "level": "INFO",
    "message": "Application started"
  },
  {
    "timestamp": "2025-11-24T10:01:00Z",
    "level": "ERROR",
    "message": "Connection timeout"
  }
]
```

### CSV Format

```csv
timestamp,level,message,service,user_id
2025-11-24T10:00:00Z,INFO,User login successful,auth,user123
2025-11-24T10:01:00Z,WARNING,Invalid token,auth,user456
2025-11-24T10:02:00Z,ERROR,Authentication failed,auth,user789
```

### Text/Log Format

```
2025-11-24 10:00:00 - app - INFO - Application started
2025-11-24 10:01:00 - app - ERROR - Connection failed: timeout
2025-11-24 10:02:00 - app - INFO - Retry successful
```

## Checking Upload Status

### Endpoint
```
GET /api/v1/logs/upload/status/<task_id>/
```

### Example Request

```bash
curl http://localhost:8000/api/v1/logs/upload/status/a1b2c3d4-5678-90ab-cdef-1234567890ab/ \
  -H "Authorization: Bearer <your_token>"
```

### Response

```json
{
  "task_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "status": "SUCCESS",
  "message": "Task completed successfully",
  "result": {
    "status": "success",
    "message": "Processed 1500 entries",
    "total_entries": 1500,
    "indexed_entries": 1500,
    "failed_entries": 0
  }
}
```

### Task States

- **PENDING**: Task waiting to be processed
- **STARTED**: Task is being processed
- **SUCCESS**: Task completed successfully
- **FAILURE**: Task failed
- **RETRY**: Task is being retried

## Security Features

### Input Validation
- File size limits (50MB max)
- File extension whitelist
- Content type validation
- UTF-8 encoding check
- Format structure validation

### Authentication & Authorization
- JWT token required
- User-based tenant isolation
- Rate limiting (configured at infrastructure level)

### Data Security
- Files processed in memory (not saved to disk)
- Automatic tenant_id tagging
- User attribution for audit trail

### Error Handling
- Comprehensive validation errors
- Sanitized error messages (no sensitive info leaked)
- Failed uploads logged for investigation

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 202 | Upload accepted and queued |
| 400 | Validation error |
| 401 | Authentication required |
| 413 | File too large |
| 415 | Unsupported file format |
| 500 | Server error during processing |

## Best Practices

### File Preparation
1. Ensure UTF-8 encoding
2. Validate JSON/CSV structure before upload
3. Keep files under 50MB (split large files)
4. Include timestamps in logs
5. Use consistent field names

### Metadata Usage
- Use `source` to identify log origin
- Set correct `environment` for filtering
- Specify `service_name` for service-level analysis
- Use `tags` for custom categorization

### Performance Tips
- Upload during off-peak hours for large files
- Use batch uploads for multiple files
- Monitor task status for long-running uploads
- Consider streaming for very large log sets

## Integration Examples

### CI/CD Pipeline (GitHub Actions)

```yaml
- name: Upload Build Logs
  run: |
    curl -X POST $API_URL/api/v1/logs/upload/ \
      -H "Authorization: Bearer ${{ secrets.API_TOKEN }}" \
      -F "file=@build.log" \
      -F "source=github_actions" \
      -F "environment=ci" \
      -F "service_name=${{ github.repository }}"
```

### Python Application

```python
import logging
import requests
from datetime import datetime

class ELKUploadHandler(logging.Handler):
    def __init__(self, api_url, token):
        super().__init__()
        self.api_url = api_url
        self.token = token
        self.buffer = []
    
    def emit(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'logger': record.name,
            'module': record.module
        }
        self.buffer.append(log_entry)
        
        if len(self.buffer) >= 100:  # Batch upload
            self.flush()
    
    def flush(self):
        if not self.buffer:
            return
        
        import tempfile
        import json
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.buffer, f)
            temp_file = f.name
        
        with open(temp_file, 'rb') as f:
            requests.post(
                f'{self.api_url}/api/v1/logs/upload/',
                headers={'Authorization': f'Bearer {self.token}'},
                files={'file': f},
                data={'source': 'python_app', 'environment': 'production'}
            )
        
        self.buffer = []
```

## Troubleshooting

### Common Issues

**"File encoding error"**
- Ensure file is UTF-8 encoded
- Convert with: `iconv -f ISO-8859-1 -t UTF-8 input.log > output.log`

**"File size exceeds maximum"**
- Split large files: `split -b 40M large.log small_`
- Compress before upload (not recommended for logs)

**"Invalid JSON format"**
- Validate JSON: `cat file.json | jq .`
- Check for trailing commas, unquoted keys

**"Task status stuck in PENDING"**
- Check Celery worker is running
- Verify Redis connection
- Review worker logs

## Support

For issues or questions:
- Check logs: `docker-compose logs backend`
- Review task status endpoint
- Contact: support@elkvision.com
