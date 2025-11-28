"""
MongoDB connection and utility functions
"""

import logging
from typing import Optional

from django.conf import settings
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

logger = logging.getLogger(__name__)

# Global MongoDB client instance
_mongo_client: Optional[MongoClient] = None
_mongo_db: Optional[Database] = None


def get_mongo_client() -> MongoClient:
    """
    Get or create MongoDB client (singleton pattern)

    Returns:
        MongoClient: MongoDB client instance
    """
    global _mongo_client

    if _mongo_client is None:
        mongo_config = settings.MONGODB

        connection_string = (
            f"mongodb://{mongo_config['username']}:{mongo_config['password']}"
            f"@{mongo_config['host']}:{mongo_config['port']}"
            f"/{mongo_config['database']}?authSource={mongo_config['authSource']}"
        )

        try:
            _mongo_client = MongoClient(
                connection_string,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
            )
            # Verify connection
            _mongo_client.admin.command("ping")
            logger.info(
                f"Connected to MongoDB: {mongo_config['host']}:{mongo_config['port']}"
            )
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    return _mongo_client


def get_mongo_db() -> Database:
    """
    Get MongoDB database instance

    Returns:
        Database: MongoDB database
    """
    global _mongo_db

    if _mongo_db is None:
        client = get_mongo_client()
        _mongo_db = client[settings.MONGODB["database"]]
        logger.info(f"Using MongoDB database: {settings.MONGODB['database']}")

    return _mongo_db


def get_collection(collection_name: str) -> Collection:
    """
    Get MongoDB collection

    Args:
        collection_name: Name of the collection

    Returns:
        Collection: MongoDB collection
    """
    db = get_mongo_db()
    return db[collection_name]


def close_mongo_connection():
    """Close MongoDB connection"""
    global _mongo_client, _mongo_db

    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None
        _mongo_db = None
        logger.info("MongoDB connection closed")


def health_check_mongodb() -> dict:
    """
    Check MongoDB connection health

    Returns:
        dict: Health status
    """
    try:
        client = get_mongo_client()
        result = client.admin.command("ping")

        return {
            "status": "healthy",
            "connected": True,
            "response_time_ms": result.get("ok", 0) * 1000,
        }
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}")
        return {"status": "unhealthy", "connected": False, "error": str(e)}


# Collection names (constants)
COLLECTION_USER_PROFILES = "user_profiles"
COLLECTION_LOG_METADATA = "log_metadata"
COLLECTION_DASHBOARDS = "dashboards"
COLLECTION_ALERTS = "alerts"
COLLECTION_API_KEYS = "api_keys"
COLLECTION_AUDIT_LOGS = "audit_logs"
