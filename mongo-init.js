// MongoDB initialization script
// This runs automatically when MongoDB container starts for the first time

db = db.getSiblingDB('elk_vision');

// Create collections with validation
db.createCollection('logs', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['timestamp', 'level', 'message'],
      properties: {
        timestamp: {
          bsonType: 'date',
          description: 'must be a date and is required'
        },
        level: {
          enum: ['debug', 'info', 'warning', 'error', 'critical'],
          description: 'must be one of the enum values and is required'
        },
        message: {
          bsonType: 'string',
          description: 'must be a string and is required'
        },
        source: {
          bsonType: 'string',
          description: 'optional source identifier'
        },
        environment: {
          bsonType: 'string',
          description: 'optional environment (dev, staging, production)'
        },
        service_name: {
          bsonType: 'string',
          description: 'optional service name'
        },
        metadata: {
          bsonType: 'object',
          description: 'optional metadata object'
        }
      }
    }
  }
});

db.createCollection('uploads', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['filename', 'uploaded_at', 'status'],
      properties: {
        filename: {
          bsonType: 'string',
          description: 'must be a string and is required'
        },
        uploaded_at: {
          bsonType: 'date',
          description: 'must be a date and is required'
        },
        status: {
          enum: ['pending', 'processing', 'completed', 'failed'],
          description: 'must be one of the enum values and is required'
        },
        file_size: {
          bsonType: 'int',
          description: 'file size in bytes'
        },
        log_count: {
          bsonType: 'int',
          description: 'number of logs processed'
        }
      }
    }
  }
});

// Create indexes for better query performance
db.logs.createIndex({ 'timestamp': -1 });
db.logs.createIndex({ 'level': 1 });
db.logs.createIndex({ 'source': 1 });
db.logs.createIndex({ 'environment': 1 });
db.logs.createIndex({ 'service_name': 1 });
db.logs.createIndex({ 'timestamp': -1, 'level': 1 });

db.uploads.createIndex({ 'uploaded_at': -1 });
db.uploads.createIndex({ 'status': 1 });

print('MongoDB initialization completed successfully');
