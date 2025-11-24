"""
API views for log metadata management with MongoDB
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from app.logs.models_mongo import LogMetadata, create_log_metadata_indexes
from app.users.models_mongo import UserProfile
from app.core.redis_cache import QueryCache

logger = logging.getLogger(__name__)


class LogMetadataListView(APIView):
    """
    List log metadata for current user's tenant
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get log metadata list with filters
        
        Query params:
        - page: Page number (default 1)
        - size: Page size (default 20)
        - status: Filter by status (pending, processing, success, failed)
        - source: Filter by source
        - environment: Filter by environment
        - service_name: Filter by service name
        """
        try:
            # Get user's tenant
            profile = UserProfile.get_by_user_id(request.user.id)
            if not profile:
                return Response({
                    'error': 'Profile not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Pagination
            page = int(request.query_params.get('page', 1))
            size = min(int(request.query_params.get('size', 20)), 100)
            skip = (page - 1) * size
            
            # Build filters
            filters = {}
            if request.query_params.get('status'):
                filters['status'] = request.query_params['status']
            if request.query_params.get('source'):
                filters['source'] = request.query_params['source']
            if request.query_params.get('environment'):
                filters['environment'] = request.query_params['environment']
            if request.query_params.get('service_name'):
                filters['service_name'] = request.query_params['service_name']
            
            # Get metadata
            metadata_list = LogMetadata.get_by_tenant(
                tenant_id=profile.tenant_id,
                filters=filters,
                skip=skip,
                limit=size
            )
            
            results = [m.to_dict() for m in metadata_list]
            
            logger.info(
                f"Retrieved {len(results)} log metadata entries for tenant {profile.tenant_id}"
            )
            
            return Response({
                'metadata': results,
                'page': page,
                'size': size,
                'count': len(results),
                'filters': filters
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error retrieving log metadata: {e}", exc_info=True)
            return Response({
                'error': 'Failed to retrieve metadata',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LogMetadataDetailView(APIView):
    """
    Get detailed log metadata by upload ID
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, upload_id):
        """Get specific log metadata"""
        try:
            # Try cache first
            cache_key = f"log_metadata:{upload_id}"
            cached = QueryCache.get(cache_key)
            if cached:
                return Response(cached, status=status.HTTP_200_OK)
            
            # Get from MongoDB
            metadata = LogMetadata.get_by_upload_id(upload_id)
            
            if not metadata:
                return Response({
                    'error': 'Metadata not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Verify tenant access
            profile = UserProfile.get_by_user_id(request.user.id)
            if profile and metadata.tenant_id != profile.tenant_id:
                return Response({
                    'error': 'Access denied',
                    'message': 'You do not have access to this metadata'
                }, status=status.HTTP_403_FORBIDDEN)
            
            result = metadata.to_dict()
            
            # Cache for 2 minutes
            QueryCache.set(cache_key, result, ttl=120)
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error retrieving metadata detail: {e}", exc_info=True)
            return Response({
                'error': 'Failed to retrieve metadata',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, upload_id):
        """Delete log metadata"""
        try:
            # Get metadata first to verify ownership
            metadata = LogMetadata.get_by_upload_id(upload_id)
            
            if not metadata:
                return Response({
                    'error': 'Metadata not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Verify tenant access
            profile = UserProfile.get_by_user_id(request.user.id)
            if profile and metadata.tenant_id != profile.tenant_id:
                return Response({
                    'error': 'Access denied'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Delete
            success = LogMetadata.delete(upload_id)
            
            if not success:
                return Response({
                    'error': 'Delete failed'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Clear cache
            QueryCache.delete(f"log_metadata:{upload_id}")
            
            logger.info(f"Deleted log metadata {upload_id} by user {request.user.id}")
            
            return Response({
                'message': 'Metadata deleted successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error deleting metadata: {e}", exc_info=True)
            return Response({
                'error': 'Failed to delete metadata',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LogMetadataStatsView(APIView):
    """
    Get upload statistics for current user's tenant
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get statistics
        
        Query params:
        - days: Number of days (default 30)
        """
        try:
            # Get user's tenant
            profile = UserProfile.get_by_user_id(request.user.id)
            if not profile:
                return Response({
                    'error': 'Profile not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            days = int(request.query_params.get('days', 30))
            
            # Try cache
            cache_key = f"log_stats:{profile.tenant_id}:{days}"
            cached = QueryCache.get(cache_key)
            if cached:
                return Response(cached, status=status.HTTP_200_OK)
            
            # Get statistics
            stats = LogMetadata.get_statistics(profile.tenant_id, days=days)
            
            # Cache for 5 minutes
            QueryCache.set(cache_key, stats, ttl=300)
            
            return Response(stats, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error retrieving statistics: {e}", exc_info=True)
            return Response({
                'error': 'Failed to retrieve statistics',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LogMetadataRecentView(APIView):
    """
    Get recent log uploads
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get recent uploads
        
        Query params:
        - limit: Number of recent uploads (default 10, max 50)
        """
        try:
            # Get user's tenant
            profile = UserProfile.get_by_user_id(request.user.id)
            if not profile:
                return Response({
                    'error': 'Profile not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            limit = min(int(request.query_params.get('limit', 10)), 50)
            
            # Get recent uploads
            recent = LogMetadata.get_recent_uploads(profile.tenant_id, limit=limit)
            
            results = [m.to_dict() for m in recent]
            
            return Response({
                'recent_uploads': results,
                'count': len(results)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error retrieving recent uploads: {e}", exc_info=True)
            return Response({
                'error': 'Failed to retrieve recent uploads',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LogMetadataByTaskView(APIView):
    """
    Get log metadata by Celery task ID
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, task_id):
        """Get metadata by task ID"""
        try:
            metadata = LogMetadata.get_by_task_id(task_id)
            
            if not metadata:
                return Response({
                    'error': 'Metadata not found',
                    'message': 'No metadata found for this task ID'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Verify tenant access
            profile = UserProfile.get_by_user_id(request.user.id)
            if profile and metadata.tenant_id != profile.tenant_id:
                return Response({
                    'error': 'Access denied'
                }, status=status.HTTP_403_FORBIDDEN)
            
            return Response(metadata.to_dict(), status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error retrieving metadata by task: {e}", exc_info=True)
            return Response({
                'error': 'Failed to retrieve metadata',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InitializeLogMetadataIndexesView(APIView):
    """
    Initialize MongoDB indexes for log metadata (admin only)
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Create all log metadata indexes"""
        if not request.user.is_staff:
            return Response({
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            create_log_metadata_indexes()
            
            logger.info(f"Log metadata indexes created by admin {request.user.id}")
            
            return Response({
                'message': 'Log metadata indexes created successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error creating indexes: {e}", exc_info=True)
            return Response({
                'error': 'Failed to create indexes',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
