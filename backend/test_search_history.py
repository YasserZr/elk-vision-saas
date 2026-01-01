#!/usr/bin/env python
"""Test script to verify search history endpoint"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

# Create test client
client = Client()

# Login as user 1
user = User.objects.get(id=1)
client.force_login(user)

# Test GET request
print("Testing GET /api/v1/logs/search/history/?limit=10")
response = client.get('/api/v1/logs/search/history/', {'limit': 10})
print(f"Status Code: {response.status_code}")
print(f"Response: {response.content[:500]}")

# Test POST request  
print("\nTesting POST /api/v1/logs/search/history/")
response = client.post('/api/v1/logs/search/history/', 
                      {'query': 'test', 'filters': {}, 'results_count': 5},
                      content_type='application/json')
print(f"Status Code: {response.status_code}")
print(f"Response: {response.content[:500]}")
