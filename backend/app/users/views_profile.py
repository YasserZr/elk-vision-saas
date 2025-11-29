"""
API views for user profile management with MongoDB
"""

import logging

from django.core.cache import cache
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from app.core.redis_cache import QueryCache, SessionCache
from app.users.models_mongo import UserProfile, create_user_profile_indexes

logger = logging.getLogger(__name__)


class UserProfileView(APIView):
    """
    Get or update current user's profile
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get current user's profile

        Returns user profile from MongoDB with preferences and quota info.
        If no MongoDB profile exists, returns basic Django user info.
        """
        try:
            # Try cache first
            cached_profile = QueryCache.get(f"user_profile:{request.user.id}")
            if cached_profile:
                return Response(cached_profile, status=status.HTTP_200_OK)

            # Get from MongoDB
            profile = UserProfile.get_by_user_id(request.user.id)

            if profile:
                profile_data = profile.to_dict()
            else:
                # Return basic profile from Django user if no MongoDB profile exists
                profile_data = {
                    "user_id": request.user.id,
                    "preferences": {},
                    "quota": {
                        "max_logs_per_day": 10000,
                        "max_storage_mb": 1000,
                        "max_retention_days": 30,
                    },
                }

            # Add Django user info
            profile_data["username"] = request.user.username
            profile_data["email"] = request.user.email
            profile_data["is_active"] = request.user.is_active

            # Cache for 5 minutes
            QueryCache.set(f"user_profile:{request.user.id}", profile_data, ttl=300)

            logger.info(f"Retrieved profile for user {request.user.id}")

            return Response(profile_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error retrieving user profile: {e}", exc_info=True)
            return Response(
                {"error": "Failed to retrieve profile", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def patch(self, request):
        """
        Update current user's profile

        Allowed updates: preferences, metadata
        """
        try:
            allowed_fields = ["preferences", "metadata", "organization"]
            updates = {}

            for field in allowed_fields:
                if field in request.data:
                    updates[field] = request.data[field]

            if not updates:
                return Response(
                    {
                        "error": "No valid fields to update",
                        "allowed_fields": allowed_fields,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Update in MongoDB
            success = UserProfile.update(request.user.id, updates)

            if not success:
                return Response(
                    {
                        "error": "Update failed",
                        "message": "Profile not found or no changes made",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Invalidate cache
            QueryCache.delete(f"user_profile:{request.user.id}")

            # Get updated profile
            profile = UserProfile.get_by_user_id(request.user.id)

            logger.info(f"Updated profile for user {request.user.id}")

            return Response(
                {
                    "message": "Profile updated successfully",
                    "profile": profile.to_dict(),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error updating user profile: {e}", exc_info=True)
            return Response(
                {"error": "Failed to update profile", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserProfileCreateView(APIView):
    """
    Create user profile (called during registration)
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Create profile for current user

        Required: tenant_id
        Optional: organization, role, preferences
        """
        try:
            # Check if profile already exists
            existing = UserProfile.get_by_user_id(request.user.id)
            if existing:
                return Response(
                    {"error": "Profile already exists", "profile": existing.to_dict()},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            tenant_id = request.data.get("tenant_id")
            if not tenant_id:
                return Response(
                    {"error": "Validation error", "message": "tenant_id is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Create profile
            profile = UserProfile.create(
                user_id=request.user.id,
                tenant_id=tenant_id,
                organization=request.data.get("organization"),
                role=request.data.get("role", "viewer"),
                preferences=request.data.get("preferences"),
                metadata=request.data.get("metadata", {}),
            )

            logger.info(
                f"Created profile for user {request.user.id}, tenant {tenant_id}"
            )

            return Response(
                {
                    "message": "Profile created successfully",
                    "profile": profile.to_dict(),
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.error(f"Error creating user profile: {e}", exc_info=True)
            return Response(
                {"error": "Failed to create profile", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserQuotaView(APIView):
    """
    Get API quota usage for current user
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get quota usage and limits"""
        try:
            quota = UserProfile.get_quota_usage(request.user.id)

            if not quota:
                return Response(
                    {"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND
                )

            return Response(
                {"quota": quota, "user_id": request.user.id}, status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error retrieving quota: {e}", exc_info=True)
            return Response(
                {"error": "Failed to retrieve quota", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TenantUsersView(APIView):
    """
    List all users in current user's tenant
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get all users in tenant

        Query params:
        - page: Page number (default 1)
        - size: Page size (default 20)
        """
        try:
            # Get current user's profile to find tenant
            current_profile = UserProfile.get_by_user_id(request.user.id)

            if not current_profile:
                return Response(
                    {"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND
                )

            # Pagination
            page = int(request.query_params.get("page", 1))
            size = int(request.query_params.get("size", 20))
            skip = (page - 1) * size

            # Get tenant users
            profiles = UserProfile.get_by_tenant(
                tenant_id=current_profile.tenant_id, skip=skip, limit=size
            )

            # Convert to dict list
            users_list = [p.to_dict() for p in profiles]

            return Response(
                {
                    "tenant_id": current_profile.tenant_id,
                    "users": users_list,
                    "page": page,
                    "size": size,
                    "count": len(users_list),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error retrieving tenant users: {e}", exc_info=True)
            return Response(
                {"error": "Failed to retrieve users", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserProfileAdminView(APIView):
    """
    Admin view to manage any user profile
    Requires admin/superuser permissions
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        """Get specific user's profile (admin only)"""
        if not request.user.is_staff:
            return Response(
                {"error": "Permission denied", "message": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            profile = UserProfile.get_by_user_id(user_id)

            if not profile:
                return Response(
                    {"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND
                )

            return Response(profile.to_dict(), status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error retrieving profile: {e}", exc_info=True)
            return Response(
                {"error": "Failed to retrieve profile", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, user_id):
        """Delete user profile (admin only)"""
        if not request.user.is_staff:
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        try:
            success = UserProfile.delete(user_id)

            if not success:
                return Response(
                    {"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND
                )

            # Clear cache
            QueryCache.delete(f"user_profile:{user_id}")

            logger.info(
                f"Deleted profile for user {user_id} by admin {request.user.id}"
            )

            return Response(
                {"message": "Profile deleted successfully"}, status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error deleting profile: {e}", exc_info=True)
            return Response(
                {"error": "Failed to delete profile", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class InitializeIndexesView(APIView):
    """
    Initialize MongoDB indexes (admin only)
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Create all MongoDB indexes"""
        if not request.user.is_staff:
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        try:
            create_user_profile_indexes()

            logger.info(f"MongoDB indexes created by admin {request.user.id}")

            return Response(
                {"message": "Indexes created successfully"}, status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error creating indexes: {e}", exc_info=True)
            return Response(
                {"error": "Failed to create indexes", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
