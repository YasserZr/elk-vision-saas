#!/usr/bin/env python3
"""
Simple script to send test logs to Logstash TCP input.
Usage: python send_test_log.py
"""
import socket
import json
from datetime import datetime

def send_log(host='localhost', port=5000):
    """Send a test log to Logstash."""
    log_data = {
        "level": "error",
        "message": "Test error from Python script - Real-time pipeline test",
        "service_name": "test-service",
        "environment": "development",
        "timestamp": datetime.utcnow().isoformat() + 'Z'
    }
    
    log_json = json.dumps(log_data) + '\n'
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        sock.sendall(log_json.encode('utf-8'))
        sock.close()
        print(f"✓ Sent log to Logstash: {log_data['message']}")
        return True
    except Exception as e:
        print(f"✗ Failed to send log: {e}")
        return False

if __name__ == '__main__':
    send_log()
