import json
import io
from django.contrib.auth.models import User
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status


class LogUploadTestCase(TestCase):
    """Test log upload functionality"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_upload_json_log(self):
        """Test uploading a JSON log file"""
        json_content = json.dumps([
            {
                "timestamp": "2025-11-24T10:00:00Z",
                "level": "INFO",
                "message": "Test log message 1"
            },
            {
                "timestamp": "2025-11-24T10:01:00Z",
                "level": "ERROR",
                "message": "Test error message"
            }
        ])
        
        file = SimpleUploadedFile(
            "test_logs.json",
            json_content.encode('utf-8'),
            content_type="application/json"
        )
        
        response = self.client.post(
            '/api/v1/logs/upload/',
            {
                'file': file,
                'source': 'test_source',
                'environment': 'testing',
                'service_name': 'test_service'
            },
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('task_id', response.data)
        self.assertEqual(response.data['format'], 'json')
        self.assertEqual(response.data['estimated_entries'], 2)
    
    def test_upload_csv_log(self):
        """Test uploading a CSV log file"""
        csv_content = """timestamp,level,message,service
2025-11-24T10:00:00Z,INFO,Test message 1,api
2025-11-24T10:01:00Z,ERROR,Test error,api
2025-11-24T10:02:00Z,WARNING,Test warning,worker"""
        
        file = SimpleUploadedFile(
            "test_logs.csv",
            csv_content.encode('utf-8'),
            content_type="text/csv"
        )
        
        response = self.client.post(
            '/api/v1/logs/upload/',
            {'file': file},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data['format'], 'csv')
        self.assertEqual(response.data['estimated_entries'], 3)
    
    def test_upload_text_log(self):
        """Test uploading a text log file"""
        text_content = """2025-11-24 10:00:00 - app - INFO - Application started
2025-11-24 10:01:00 - app - ERROR - Connection failed
2025-11-24 10:02:00 - app - INFO - Retry successful"""
        
        file = SimpleUploadedFile(
            "test_logs.log",
            text_content.encode('utf-8'),
            content_type="text/plain"
        )
        
        response = self.client.post(
            '/api/v1/logs/upload/',
            {'file': file},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data['format'], 'text')
    
    def test_upload_without_authentication(self):
        """Test that upload requires authentication"""
        self.client.force_authenticate(user=None)
        
        file = SimpleUploadedFile(
            "test.json",
            b'{"test": "data"}',
            content_type="application/json"
        )
        
        response = self.client.post(
            '/api/v1/logs/upload/',
            {'file': file},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_upload_empty_file(self):
        """Test uploading an empty file"""
        file = SimpleUploadedFile(
            "empty.json",
            b'',
            content_type="application/json"
        )
        
        response = self.client.post(
            '/api/v1/logs/upload/',
            {'file': file},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file', response.data['details'])
    
    def test_upload_oversized_file(self):
        """Test uploading a file that's too large"""
        # Create a file larger than 50MB
        large_content = 'x' * (51 * 1024 * 1024)
        
        file = SimpleUploadedFile(
            "large.json",
            large_content.encode('utf-8'),
            content_type="application/json"
        )
        
        response = self.client.post(
            '/api/v1/logs/upload/',
            {'file': file},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_upload_invalid_extension(self):
        """Test uploading a file with invalid extension"""
        file = SimpleUploadedFile(
            "test.exe",
            b'some binary data',
            content_type="application/octet-stream"
        )
        
        response = self.client.post(
            '/api/v1/logs/upload/',
            {'file': file},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_upload_invalid_json(self):
        """Test uploading invalid JSON"""
        file = SimpleUploadedFile(
            "invalid.json",
            b'{invalid json content',
            content_type="application/json"
        )
        
        response = self.client.post(
            '/api/v1/logs/upload/',
            {'file': file},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_get_upload_status(self):
        """Test checking upload task status"""
        task_id = "test-task-id-12345"
        
        response = self.client.get(f'/api/v1/logs/upload/status/{task_id}/')
        
        # Should return a status even if task doesn't exist (PENDING)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)


class LogSearchTestCase(TestCase):
    """Test log search functionality"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_search_logs(self):
        """Test searching logs"""
        response = self.client.get(
            '/api/v1/logs/search/',
            {'q': 'error', 'level': 'ERROR'}
        )
        
        # Should return results structure even if ES is not available
        self.assertIn('results', response.data)
        self.assertIn('total', response.data)
    
    def test_search_without_authentication(self):
        """Test that search requires authentication"""
        self.client.force_authenticate(user=None)
        
        response = self.client.get('/api/v1/logs/search/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
