import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status


class TestHealthChecks(TestCase):
    """Test health check endpoints"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_liveness_check(self):
        """Test liveness probe"""
        response = self.client.get('/health/live/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'alive')
    
    def test_readiness_check(self):
        """Test readiness probe"""
        response = self.client.get('/health/ready/')
        # May fail if dependencies are not running
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_503_SERVICE_UNAVAILABLE
        ])
    
    def test_health_check(self):
        """Test comprehensive health check"""
        response = self.client.get('/health/')
        self.assertIn('status', response.data)
        self.assertIn('version', response.data)
        self.assertIn('checks', response.data)
