#!/usr/bin/env python3
"""
Generate test logs with different log levels for testing Kibana visualizations.
Creates JSON, CSV, and text format log files with varied log levels.
"""

import json
import random
from datetime import datetime, timedelta
import csv

# Log levels with their distribution weights
LOG_LEVELS = [
    ("DEBUG", 0.00),    # 0%
    ("INFO", 0.00),     # 0%
    ("WARNING", 0.90),  # 90%
    ("ERROR", 0.10),    # 10%
    ("CRITICAL", 0.00)  # 0%
]

# Sample services
SERVICES = [
    "api-gateway",
    "auth-service",
    "user-service",
    "payment-service",
    "notification-service",
    "database-service"
]

# Sample messages by log level
MESSAGES = {
    "DEBUG": [
        "Debug: Cache lookup for key: {key}",
        "Debug: Query execution time: {time}ms",
        "Debug: Function called with parameters: {params}",
        "Debug: Memory usage: {memory}MB",
        "Debug: Database connection pool status: {status}"
    ],
    "INFO": [
        "User {user} logged in successfully",
        "Request processed successfully in {time}ms",
        "Background job {job} completed",
        "Cache refreshed for {service}",
        "Health check passed for {service}"
    ],
    "WARNING": [
        "High memory usage detected: {percent}%",
        "Slow query detected: {time}ms",
        "Connection pool near capacity: {percent}%",
        "Rate limit approaching for user {user}",
        "Deprecated API endpoint called: {endpoint}"
    ],
    "ERROR": [
        "Database connection failed: {error}",
        "Failed to process payment: {error}",
        "Authentication failed for user {user}",
        "API request timeout: {endpoint}",
        "Failed to send notification: {error}"
    ],
    "CRITICAL": [
        "System out of memory!",
        "Database cluster unreachable",
        "All API endpoints returning 500 errors",
        "Security breach detected: {alert}",
        "Critical service {service} crashed"
    ]
}

def weighted_choice(choices):
    """Select item from list of (value, weight) tuples."""
    total = sum(w for c, w in choices)
    r = random.uniform(0, total)
    upto = 0
    for c, w in choices:
        if upto + w >= r:
            return c
        upto += w
    return choices[-1][0]

def generate_log_entry(timestamp):
    """Generate a single log entry."""
    level = weighted_choice(LOG_LEVELS)
    service = random.choice(SERVICES)
    message_template = random.choice(MESSAGES[level])
    
    # Fill in placeholders
    message = message_template.format(
        key=f"user_{random.randint(1000, 9999)}",
        time=random.randint(50, 5000),
        params=f"param1=value, param2=value",
        memory=random.randint(100, 4000),
        status=random.choice(["healthy", "busy", "idle"]),
        user=f"user_{random.randint(1000, 9999)}",
        job=f"job_{random.randint(100, 999)}",
        service=service,
        percent=random.randint(70, 95),
        endpoint=f"/api/v1/{random.choice(['users', 'orders', 'products'])}",
        error=random.choice(["timeout", "connection refused", "invalid credentials", "not found"]),
        alert=f"alert_{random.randint(100, 999)}"
    )
    
    return {
        "timestamp": timestamp.isoformat() + "Z",
        "level": level,
        "message": message,
        "service": service,
        "environment": random.choice(["production", "staging", "development"]),
        "host": f"server-{random.randint(1, 10)}",
        "user_id": f"user_{random.randint(1000, 9999)}",
        "request_id": f"req_{random.randint(10000, 99999)}"
    }

def generate_json_logs(count=1000, output_file="test_logs.json"):
    """Generate JSON format logs."""
    print(f"Generating {count} JSON log entries...")
    
    logs = []
    start_time = datetime.now() - timedelta(hours=24)
    
    for i in range(count):
        # Distribute logs across 24 hours
        timestamp = start_time + timedelta(seconds=i * 86400 / count)
        logs.append(generate_log_entry(timestamp))
    
    with open(output_file, 'w') as f:
        json.dump(logs, f, indent=2)
    
    # Print statistics
    level_counts = {}
    for log in logs:
        level_counts[log['level']] = level_counts.get(log['level'], 0) + 1
    
    print(f"\nJSON logs saved to: {output_file}")
    print("Log level distribution:")
    for level, count in sorted(level_counts.items()):
        print(f"  {level}: {count} ({count/len(logs)*100:.1f}%)")

def generate_csv_logs(count=1000, output_file="test_logs.csv"):
    """Generate CSV format logs."""
    print(f"\nGenerating {count} CSV log entries...")
    
    start_time = datetime.now() - timedelta(hours=24)
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'level', 'message', 'service', 'environment', 'host', 'user_id'])
        
        level_counts = {}
        for i in range(count):
            timestamp = start_time + timedelta(seconds=i * 86400 / count)
            log = generate_log_entry(timestamp)
            writer.writerow([
                log['timestamp'],
                log['level'],
                log['message'],
                log['service'],
                log['environment'],
                log['host'],
                log['user_id']
            ])
            level_counts[log['level']] = level_counts.get(log['level'], 0) + 1
    
    print(f"CSV logs saved to: {output_file}")
    print("Log level distribution:")
    for level, count in sorted(level_counts.items()):
        print(f"  {level}: {count} ({count/len(level_counts)*100:.1f}%)")

def generate_text_logs(count=1000, output_file="test_logs.log"):
    """Generate text format logs."""
    print(f"\nGenerating {count} text log entries...")
    
    start_time = datetime.now() - timedelta(hours=24)
    
    with open(output_file, 'w') as f:
        level_counts = {}
        for i in range(count):
            timestamp = start_time + timedelta(seconds=i * 86400 / count)
            log = generate_log_entry(timestamp)
            # Format: timestamp - service - level - message
            line = f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {log['service']} - {log['level']} - {log['message']}\n"
            f.write(line)
            level_counts[log['level']] = level_counts.get(log['level'], 0) + 1
    
    print(f"Text logs saved to: {output_file}")
    print("Log level distribution:")
    for level, count in sorted(level_counts.items()):
        print(f"  {level}: {count} ({count/count*100 if count else 0:.1f}%)")

if __name__ == "__main__":
    import sys
    
    # Default to 1000 logs, or accept count from command line
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    
    print(f"=== Generating Test Logs with Varied Log Levels ===\n")
    print(f"Total logs per file: {count}")
    print(f"Expected distribution:")
    for level, weight in LOG_LEVELS:
        print(f"  {level}: ~{weight*100:.0f}%")
    print()
    
    generate_json_logs(count, "test_logs_varied.json")
    generate_csv_logs(count, "test_logs_varied.csv")
    generate_text_logs(count, "test_logs_varied.log")
    
    print(f"\n=== Generation Complete ===")
    print(f"\nTo upload these logs, use:")
    print(f"  JSON:  curl -X POST http://localhost:8000/api/v1/logs/upload/ -H 'Authorization: Bearer <token>' -F 'file=@test_logs_varied.json' -F 'environment=testing'")
    print(f"  CSV:   curl -X POST http://localhost:8000/api/v1/logs/upload/ -H 'Authorization: Bearer <token>' -F 'file=@test_logs_varied.csv' -F 'environment=testing'")
    print(f"  Text:  curl -X POST http://localhost:8000/api/v1/logs/upload/ -H 'Authorization: Bearer <token>' -F 'file=@test_logs_varied.log' -F 'environment=testing'")
