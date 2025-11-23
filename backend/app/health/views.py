import logging
from django.conf import settings
from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from redis import Redis
from elasticsearch import Elasticsearch
import pymongo

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """
    Comprehensive health check endpoint.
    Returns detailed status of all dependencies.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        health_status = {
            'status': 'healthy',
            'version': settings.API_VERSION,
            'checks': {}
        }

        # Check Database (MongoDB)
        try:
            connection.ensure_connection()
            health_status['checks']['database'] = {
                'status': 'up',
                'type': 'mongodb'
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            health_status['checks']['database'] = {
                'status': 'down',
                'error': str(e)
            }
            health_status['status'] = 'unhealthy'

        # Check Redis
        try:
            redis_client = Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                socket_connect_timeout=settings.HEALTH_CHECK_TIMEOUT
            )
            redis_client.ping()
            health_status['checks']['redis'] = {'status': 'up'}
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            health_status['checks']['redis'] = {
                'status': 'down',
                'error': str(e)
            }
            health_status['status'] = 'unhealthy'

        # Check Elasticsearch
        try:
            es_config = settings.ELASTICSEARCH_DSL['default']
            es = Elasticsearch(
                hosts=es_config['hosts'],
                http_auth=es_config.get('http_auth'),
                timeout=settings.HEALTH_CHECK_TIMEOUT
            )
            es_health = es.cluster.health()
            health_status['checks']['elasticsearch'] = {
                'status': 'up',
                'cluster_status': es_health['status']
            }
        except Exception as e:
            logger.error(f"Elasticsearch health check failed: {e}")
            health_status['checks']['elasticsearch'] = {
                'status': 'down',
                'error': str(e)
            }
            health_status['status'] = 'unhealthy'

        # Return appropriate status code
        if health_status['status'] == 'healthy':
            return Response(health_status, status=status.HTTP_200_OK)
        else:
            return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class ReadinessCheckView(APIView):
    """
    Readiness probe for Kubernetes.
    Checks if the application is ready to serve traffic.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            # Check critical dependencies
            connection.ensure_connection()
            
            redis_client = Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                socket_connect_timeout=2
            )
            redis_client.ping()

            return Response({
                'status': 'ready',
                'message': 'Application is ready to serve traffic'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            return Response({
                'status': 'not_ready',
                'error': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class LivenessCheckView(APIView):
    """
    Liveness probe for Kubernetes.
    Checks if the application is alive (basic health).
    """
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            'status': 'alive',
            'message': 'Application is running'
        }, status=status.HTTP_200_OK)
