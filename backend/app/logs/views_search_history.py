"""
API views for search history management
"""

import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from app.logs.models_search_history import SearchHistory
from app.users.models_mongo import UserProfile

logger = logging.getLogger(__name__)


class SearchHistoryListView(APIView):
    """
    List and create search history entries
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get user's search history

        Query params:
        - limit: Number of entries (default 10, max 50)
        """
        try:
            profile = UserProfile.get_by_user_id(request.user.id)
            if not profile:
                # Auto-create profile for new user
                profile = UserProfile.create(
                    user_id=request.user.id,
                    tenant_id="default",
                    organization=getattr(request.user, 'username', 'default'),
                    role="admin"
                )
                logger.info(f"Auto-created profile for user {request.user.id}")

            limit = min(int(request.query_params.get("limit", 10)), 50)

            history = SearchHistory.get_user_history(
                user_id=request.user.id,
                tenant_id=profile.tenant_id,
                limit=limit,
            )

            results = [h.to_dict() for h in history]

            return Response(
                {"history": results, "count": len(results)},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error retrieving search history: {e}", exc_info=True)
            return Response(
                {"error": "Failed to retrieve search history", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        """
        Save a search to history

        Request body:
        - query: Search query string
        - filters: Applied filters (optional)
        - results_count: Number of results (optional)
        """
        try:
            profile = UserProfile.get_by_user_id(request.user.id)
            if not profile:
                # Auto-create profile for new user
                profile = UserProfile.create(
                    user_id=request.user.id,
                    tenant_id="default",
                    organization=getattr(request.user, 'username', 'default'),
                    role="admin"
                )
                logger.info(f"Auto-created profile for user {request.user.id}")

            query = request.data.get("query", "")
            filters = request.data.get("filters", {})
            results_count = request.data.get("results_count", 0)

            # Don't save empty queries
            if not query and not filters:
                return Response(
                    {"error": "Query or filters required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            entry = SearchHistory.create(
                user_id=request.user.id,
                tenant_id=profile.tenant_id,
                query=query,
                filters=filters,
                results_count=results_count,
            )

            logger.info(f"Search history saved for user {request.user.id}")

            return Response(entry.to_dict(), status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error saving search history: {e}", exc_info=True)
            return Response(
                {"error": "Failed to save search history", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request):
        """
        Clear all search history for the user
        """
        try:
            profile = UserProfile.get_by_user_id(request.user.id)
            if not profile:
                return Response(
                    {"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND
                )

            deleted_count = SearchHistory.clear_user_history(
                user_id=request.user.id, tenant_id=profile.tenant_id
            )

            logger.info(f"Cleared {deleted_count} search history entries for user {request.user.id}")

            return Response(
                {"message": f"Cleared {deleted_count} entries"},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error clearing search history: {e}", exc_info=True)
            return Response(
                {"error": "Failed to clear search history", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SearchHistoryDetailView(APIView):
    """
    Delete individual search history entry
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, search_id):
        """Delete a specific search history entry"""
        try:
            deleted = SearchHistory.delete_entry(
                search_id=search_id, user_id=request.user.id
            )

            if not deleted:
                return Response(
                    {"error": "Entry not found"}, status=status.HTTP_404_NOT_FOUND
                )

            return Response(
                {"message": "Entry deleted"}, status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error deleting search history entry: {e}", exc_info=True)
            return Response(
                {"error": "Failed to delete entry", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
