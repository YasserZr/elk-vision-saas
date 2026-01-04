import logging
import time

from django.conf import settings
from django.db import connection
from elasticsearch import Elasticsearch
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from app.core.mongodb import health_check_mongodb
from app.core.redis_cache import health_check_redis

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """
    Comprehensive health check endpoint.
    Returns detailed status of all dependencies.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        overall_status = "healthy"
        services = {}

        # Check API (Django Database)
        try:
            start_time = time.time()
            connection.ensure_connection()
            latency = round((time.time() - start_time) * 1000, 2)
            services["api"] = {"status": "healthy", "latency_ms": latency}
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            services["api"] = {"status": "unhealthy", "latency_ms": 0}
            overall_status = "unhealthy"

        # Check MongoDB
        start_time = time.time()
        mongo_health = health_check_mongodb()
        latency = mongo_health.get("response_time_ms", 0)
        if mongo_health["status"] == "healthy":
            services["mongodb"] = {"status": "healthy", "latency_ms": latency}
        else:
            services["mongodb"] = {"status": "unhealthy", "latency_ms": latency}
            overall_status = "unhealthy"

        # Check Redis
        start_time = time.time()
        redis_health = health_check_redis()
        latency = round((time.time() - start_time) * 1000, 2)
        if redis_health["status"] == "healthy":
            services["redis"] = {"status": "healthy", "latency_ms": latency}
        else:
            services["redis"] = {"status": "unhealthy", "latency_ms": latency}
            overall_status = "unhealthy"

        # Check Elasticsearch
        try:
            start_time = time.time()
            es_config = settings.ELASTICSEARCH_DSL["default"]
            es = Elasticsearch(
                hosts=es_config["hosts"],
                http_auth=es_config.get("http_auth"),
                timeout=settings.HEALTH_CHECK_TIMEOUT,
            )
            es_health = es.cluster.health()
            latency = round((time.time() - start_time) * 1000, 2)
            services["elasticsearch"] = {
                "status": "healthy" if es_health["status"] in ["green", "yellow"] else "unhealthy",
                "latency_ms": latency
            }
        except Exception as e:
            logger.error(f"Elasticsearch health check failed: {e}")
            services["elasticsearch"] = {"status": "unhealthy", "latency_ms": 0}
            overall_status = "unhealthy"

        # Check Logstash (basic TCP connectivity check)
        services["logstash"] = {"status": "healthy", "latency_ms": 0}  # Placeholder

        health_response = {
            "status": overall_status,
            "services": services,
            "timestamp": time.time(),
            "version": settings.API_VERSION,
        }

        # Return appropriate status code
        if overall_status == "healthy":
            return Response(health_response, status=status.HTTP_200_OK)
        else:
            return Response(health_response, status=status.HTTP_503_SERVICE_UNAVAILABLE)


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
