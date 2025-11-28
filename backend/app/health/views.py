import logging

from app.core.mongodb import health_check_mongodb
from app.core.redis_cache import health_check_redis
from django.conf import settings
from django.db import connection
from elasticsearch import Elasticsearch
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """
    Comprehensive health check endpoint.
    Returns detailed status of all dependencies.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        health_status = {
            "status": "healthy",
            "version": settings.API_VERSION,
            "checks": {},
        }

        # Check Django Database (SQLite)
        try:
            connection.ensure_connection()
            health_status["checks"]["database"] = {"status": "up", "type": "sqlite"}
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            health_status["checks"]["database"] = {"status": "down", "error": str(e)}
            health_status["status"] = "unhealthy"

        # Check MongoDB
        mongo_health = health_check_mongodb()
        health_status["checks"]["mongodb"] = mongo_health
        if mongo_health["status"] != "healthy":
            health_status["status"] = "unhealthy"

        # Check Redis
        redis_health = health_check_redis()
        health_status["checks"]["redis"] = redis_health
        if redis_health["status"] != "healthy":
            health_status["status"] = "unhealthy"

        # Check Elasticsearch
        try:
            es_config = settings.ELASTICSEARCH_DSL["default"]
            es = Elasticsearch(
                hosts=es_config["hosts"],
                http_auth=es_config.get("http_auth"),
                timeout=settings.HEALTH_CHECK_TIMEOUT,
            )
            es_health = es.cluster.health()
            health_status["checks"]["elasticsearch"] = {
                "status": "up",
                "cluster_status": es_health["status"],
            }
        except Exception as e:
            logger.error(f"Elasticsearch health check failed: {e}")
            health_status["checks"]["elasticsearch"] = {
                "status": "down",
                "error": str(e),
            }
            health_status["status"] = "unhealthy"

        # Return appropriate status code
        if health_status["status"] == "healthy":
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
            mongo_health = health_check_mongodb()
            redis_health = health_check_redis()

            if (
                mongo_health["status"] != "healthy"
                or redis_health["status"] != "healthy"
            ):
                return Response(
                    {
                        "status": "not_ready",
                        "mongodb": mongo_health,
                        "redis": redis_health,
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            return Response(
                {"status": "ready", "message": "Application is ready to serve traffic"},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            return Response(
                {"status": "not_ready", "error": str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


class LivenessCheckView(APIView):
    """
    Liveness probe for Kubernetes.
    Checks if the application is alive (basic health).
    """

    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {"status": "alive", "message": "Application is running"},
            status=status.HTTP_200_OK,
        )
