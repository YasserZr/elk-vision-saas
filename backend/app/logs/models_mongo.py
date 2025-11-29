"""
MongoDB models/schemas for log metadata
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId

from app.core.mongodb import COLLECTION_LOG_METADATA, get_collection


class LogMetadata:
    """
    Log Metadata model stored in MongoDB
    Stores metadata about log uploads and processing
    """

    def __init__(self, data: dict):
        self._id = data.get("_id")
        self.upload_id = data.get("upload_id")  # Unique upload identifier
        self.task_id = data.get("task_id")  # Celery task ID
        self.tenant_id = data.get("tenant_id")
        self.user_id = data.get("user_id")
        self.source = data.get("source")
        self.environment = data.get("environment")
        self.service_name = data.get("service_name")
        self.file_name = data.get("file_name")
        self.file_size = data.get("file_size")
        self.format_type = data.get("format_type")
        self.log_count = data.get("log_count", 0)
        self.status = data.get("status", "pending")
        self.processing_time = data.get("processing_time")
        self.ingestion_method = data.get("ingestion_method")
        self.tags = data.get("tags", [])
        self.created_at = data.get("created_at")
        self.updated_at = data.get("updated_at")
        self.indexed_at = data.get("indexed_at")
        self.errors = data.get("errors", [])
        self.metadata = data.get("metadata", {})

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "_id": str(self._id) if self._id else None,
            "upload_id": self.upload_id,
            "task_id": self.task_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "source": self.source,
            "environment": self.environment,
            "service_name": self.service_name,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "format_type": self.format_type,
            "log_count": self.log_count,
            "status": self.status,
            "processing_time": self.processing_time,
            "ingestion_method": self.ingestion_method,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "indexed_at": self.indexed_at,
            "errors": self.errors,
            "metadata": self.metadata,
        }

    @staticmethod
    def create(
        upload_id: str, task_id: str, tenant_id: str, user_id: int, **kwargs
    ) -> "LogMetadata":
        """
        Create log metadata entry

        Args:
            upload_id: Unique upload identifier
            task_id: Celery task ID
            tenant_id: Tenant ID
            user_id: User ID
            **kwargs: Additional metadata

        Returns:
            LogMetadata: Created metadata
        """
        collection = get_collection(COLLECTION_LOG_METADATA)

        now = datetime.utcnow()
        metadata = {
            "upload_id": upload_id,
            "task_id": task_id,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "source": kwargs.get("source", "unknown"),
            "environment": kwargs.get("environment", "production"),
            "service_name": kwargs.get("service_name", "unknown"),
            "file_name": kwargs.get("file_name"),
            "file_size": kwargs.get("file_size", 0),
            "format_type": kwargs.get("format_type", "json"),
            "log_count": kwargs.get("log_count", 0),
            "status": "pending",
            "processing_time": None,
            "ingestion_method": kwargs.get("ingestion_method", "logstash"),
            "tags": kwargs.get("tags", []),
            "created_at": now,
            "updated_at": now,
            "indexed_at": None,
            "errors": [],
            "metadata": kwargs.get("metadata", {}),
        }

        result = collection.insert_one(metadata)
        metadata["_id"] = result.inserted_id

        return LogMetadata(metadata)

    @staticmethod
    def get_by_id(metadata_id: str) -> Optional["LogMetadata"]:
        """Get metadata by MongoDB ID"""
        collection = get_collection(COLLECTION_LOG_METADATA)

        try:
            data = collection.find_one({"_id": ObjectId(metadata_id)})
            return LogMetadata(data) if data else None
        except Exception:
            return None

    @staticmethod
    def get_by_upload_id(upload_id: str) -> Optional["LogMetadata"]:
        """Get metadata by upload ID"""
        collection = get_collection(COLLECTION_LOG_METADATA)
        data = collection.find_one({"upload_id": upload_id})

        return LogMetadata(data) if data else None

    @staticmethod
    def get_by_task_id(task_id: str) -> Optional["LogMetadata"]:
        """Get metadata by task ID"""
        collection = get_collection(COLLECTION_LOG_METADATA)
        data = collection.find_one({"task_id": task_id})

        return LogMetadata(data) if data else None

    @staticmethod
    def get_by_tenant(
        tenant_id: str,
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "created_at",
        sort_order: int = -1,
    ) -> List["LogMetadata"]:
        """
        Get log metadata for a tenant with optional filters

        Args:
            tenant_id: Tenant ID
            filters: Additional query filters
            skip: Number to skip
            limit: Maximum results
            sort_by: Field to sort by
            sort_order: 1 for ascending, -1 for descending

        Returns:
            List of LogMetadata objects
        """
        collection = get_collection(COLLECTION_LOG_METADATA)

        query = {"tenant_id": tenant_id}
        if filters:
            query.update(filters)

        cursor = (
            collection.find(query).sort(sort_by, sort_order).skip(skip).limit(limit)
        )

        return [LogMetadata(data) for data in cursor]

    @staticmethod
    def update_status(
        upload_id: str,
        status: str,
        log_count: Optional[int] = None,
        processing_time: Optional[float] = None,
        errors: Optional[List[str]] = None,
    ) -> bool:
        """
        Update metadata status

        Args:
            upload_id: Upload ID
            status: New status (pending, processing, success, failed)
            log_count: Number of logs processed
            processing_time: Processing time in seconds
            errors: List of error messages

        Returns:
            bool: True if updated
        """
        collection = get_collection(COLLECTION_LOG_METADATA)

        updates = {"status": status, "updated_at": datetime.utcnow()}

        if log_count is not None:
            updates["log_count"] = log_count

        if processing_time is not None:
            updates["processing_time"] = processing_time

        if errors:
            updates["errors"] = errors

        if status == "success":
            updates["indexed_at"] = datetime.utcnow()

        result = collection.update_one({"upload_id": upload_id}, {"$set": updates})

        return result.modified_count > 0

    @staticmethod
    def delete(upload_id: str) -> bool:
        """Delete metadata entry"""
        collection = get_collection(COLLECTION_LOG_METADATA)
        result = collection.delete_one({"upload_id": upload_id})

        return result.deleted_count > 0

    @staticmethod
    def get_statistics(tenant_id: str, days: int = 30) -> dict:
        """
        Get upload statistics for tenant

        Args:
            tenant_id: Tenant ID
            days: Number of days to analyze

        Returns:
            dict: Statistics
        """
        collection = get_collection(COLLECTION_LOG_METADATA)

        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        pipeline = [
            {"$match": {"tenant_id": tenant_id, "created_at": {"$gte": cutoff_date}}},
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "total_logs": {"$sum": "$log_count"},
                    "total_size": {"$sum": "$file_size"},
                    "avg_processing_time": {"$avg": "$processing_time"},
                }
            },
        ]

        results = list(collection.aggregate(pipeline))

        stats = {
            "period_days": days,
            "total_uploads": sum(r["count"] for r in results),
            "total_logs": sum(r["total_logs"] for r in results),
            "total_size_bytes": sum(r["total_size"] for r in results),
            "by_status": {},
        }

        for result in results:
            status = result["_id"]
            stats["by_status"][status] = {
                "count": result["count"],
                "total_logs": result["total_logs"],
                "avg_processing_time": result["avg_processing_time"],
            }

        return stats

    @staticmethod
    def get_recent_uploads(tenant_id: str, limit: int = 10) -> List["LogMetadata"]:
        """Get most recent uploads for tenant"""
        return LogMetadata.get_by_tenant(
            tenant_id, skip=0, limit=limit, sort_by="created_at", sort_order=-1
        )


# Create indexes for log metadata
def create_log_metadata_indexes():
    """Create MongoDB indexes for log metadata collection"""
    collection = get_collection(COLLECTION_LOG_METADATA)

    # Unique index on upload_id
    collection.create_index("upload_id", unique=True)

    # Index on task_id for status lookups
    collection.create_index("task_id")

    # Index on tenant_id for multi-tenancy
    collection.create_index("tenant_id")

    # Compound index for tenant and status queries
    collection.create_index([("tenant_id", 1), ("status", 1)])

    # Compound index for tenant and date queries
    collection.create_index([("tenant_id", 1), ("created_at", -1)])

    # Index for user uploads
    collection.create_index([("tenant_id", 1), ("user_id", 1), ("created_at", -1)])

    # Index for source and environment filtering
    collection.create_index([("tenant_id", 1), ("source", 1), ("environment", 1)])
