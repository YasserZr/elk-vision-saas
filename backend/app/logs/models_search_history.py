"""
MongoDB model for search history
"""

from datetime import datetime
from typing import List, Optional

from bson import ObjectId

from app.core.mongodb import get_collection

COLLECTION_SEARCH_HISTORY = "search_history"


class SearchHistory:
    """
    Search History model stored in MongoDB
    Stores user search queries for quick access
    """

    def __init__(self, data: dict):
        self._id = data.get("_id")
        self.search_id = data.get("search_id")
        self.user_id = data.get("user_id")
        self.tenant_id = data.get("tenant_id")
        self.query = data.get("query", "")
        self.filters = data.get("filters", {})
        self.results_count = data.get("results_count", 0)
        self.created_at = data.get("created_at")

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "_id": str(self._id) if self._id else None,
            "search_id": self.search_id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "query": self.query,
            "filters": self.filters,
            "results_count": self.results_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @staticmethod
    def create(
        user_id: int,
        tenant_id: str,
        query: str,
        filters: dict = None,
        results_count: int = 0,
    ) -> "SearchHistory":
        """
        Create a search history entry

        Args:
            user_id: User ID
            tenant_id: Tenant ID
            query: Search query string
            filters: Applied filters
            results_count: Number of results returned

        Returns:
            SearchHistory: Created entry
        """
        collection = get_collection(COLLECTION_SEARCH_HISTORY)

        now = datetime.utcnow()
        search_id = str(ObjectId())

        entry = {
            "search_id": search_id,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "query": query,
            "filters": filters or {},
            "results_count": results_count,
            "created_at": now,
        }

        result = collection.insert_one(entry)
        entry["_id"] = result.inserted_id

        return SearchHistory(entry)

    @staticmethod
    def get_user_history(
        user_id: int, tenant_id: str, limit: int = 10
    ) -> List["SearchHistory"]:
        """
        Get recent search history for a user

        Args:
            user_id: User ID
            tenant_id: Tenant ID
            limit: Maximum number of entries to return

        Returns:
            List[SearchHistory]: Recent searches
        """
        collection = get_collection(COLLECTION_SEARCH_HISTORY)

        cursor = collection.find(
            {"user_id": user_id, "tenant_id": tenant_id}
        ).sort("created_at", -1).limit(limit)

        return [SearchHistory(doc) for doc in cursor]

    @staticmethod
    def delete_entry(search_id: str, user_id: int) -> bool:
        """
        Delete a search history entry

        Args:
            search_id: Search ID to delete
            user_id: User ID (for verification)

        Returns:
            bool: True if deleted
        """
        collection = get_collection(COLLECTION_SEARCH_HISTORY)
        result = collection.delete_one({"search_id": search_id, "user_id": user_id})
        return result.deleted_count > 0

    @staticmethod
    def clear_user_history(user_id: int, tenant_id: str) -> int:
        """
        Clear all search history for a user

        Args:
            user_id: User ID
            tenant_id: Tenant ID

        Returns:
            int: Number of entries deleted
        """
        collection = get_collection(COLLECTION_SEARCH_HISTORY)
        result = collection.delete_many({"user_id": user_id, "tenant_id": tenant_id})
        return result.deleted_count


def create_search_history_indexes():
    """Create MongoDB indexes for search history collection"""
    collection = get_collection(COLLECTION_SEARCH_HISTORY)

    # Index on user_id and tenant_id for user queries
    collection.create_index([("user_id", 1), ("tenant_id", 1)])

    # Index on created_at for sorting
    collection.create_index([("user_id", 1), ("created_at", -1)])

    # Unique index on search_id
    collection.create_index("search_id", unique=True)
