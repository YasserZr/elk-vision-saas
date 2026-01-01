import logging
import uuid

from django.conf import settings
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.websocket_utils import send_upload_status
from .logstash_forwarder import get_logstash_forwarder
from .parsers import LogParser, estimate_log_count
from .serializers import LogFileUploadSerializer, LogUploadResponseSerializer
from .tasks import process_and_ingest_logs

logger = logging.getLogger(__name__)


class LogUploadView(APIView):
    """
    API endpoint for uploading log files
    Accepts JSON, CSV, and text/log formats
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        """
        Upload and process log files

        Expected form-data:
        - file: Log file (required)
        - source: Source identifier (optional)
        - environment: Environment (production/staging/development/testing)
        - service_name: Service name (optional)
        - tags: Comma-separated tags (optional)
        """
        logger.info(f"Log upload request from user: {request.user.username}")

        # Validate request
        serializer = LogFileUploadSerializer(data=request.data)

        if not serializer.is_valid():
            logger.warning(f"Invalid upload request: {serializer.errors}")
            return Response(
                {"error": "Validation failed", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_data = serializer.validated_data
        uploaded_file = validated_data["file"]

        try:
            # Read file content
            file_content = uploaded_file.read().decode("utf-8")

            # Detect format
            format_type = LogParser.detect_format(uploaded_file.name)

            # Estimate log count
            estimated_count = estimate_log_count(file_content, format_type)

            # Prepare metadata
            upload_id = str(uuid.uuid4())
            metadata = {
                "upload_id": upload_id,
                "user_id": request.user.id,
                "source": validated_data.get("source", "manual_upload"),
                "environment": validated_data.get("environment", "production"),
                "service_name": validated_data.get("service_name", "unknown"),
                "tags": validated_data.get("tags", []),
                "tenant_id": self._get_tenant_id(request.user),
                "uploaded_by": request.user.username,
                "file_name": uploaded_file.name,
                "file_size": uploaded_file.size,
            }

            # Submit async task for processing
            task = process_and_ingest_logs.delay(
                content=file_content, format_type=format_type, metadata=metadata
            )

            logger.info(
                f"Log upload task created: {task.id} for file: {uploaded_file.name} "
                f"({uploaded_file.size} bytes, ~{estimated_count} entries)"
            )

            # Prepare response
            response_data = {
                "task_id": task.id,
                "message": "File uploaded successfully and queued for processing",
                "file_name": uploaded_file.name,
                "file_size": uploaded_file.size,
                "format": format_type,
                "estimated_entries": estimated_count,
                "status": "processing",
            }

            response_serializer = LogUploadResponseSerializer(data=response_data)
            response_serializer.is_valid(raise_exception=True)

            # Send WebSocket notification for upload status
            try:
                send_upload_status(
                    user_id=request.user.id,
                    upload_data={
                        'task_id': task.id,
                        'filename': uploaded_file.name,
                        'status': 'processing',
                        'progress': 0,
                        'estimated_entries': estimated_count,
                        'file_size': uploaded_file.size,
                        'message': 'File uploaded successfully and queued for processing'
                    }
                )
            except Exception as ws_error:
                logger.warning(f"Failed to send WebSocket notification: {ws_error}")

            return Response(response_serializer.data, status=status.HTTP_202_ACCEPTED)

        except UnicodeDecodeError:
            logger.error(f"File encoding error for {uploaded_file.name}")
            return Response(
                {
                    "error": "File encoding error",
                    "message": "File must be UTF-8 encoded",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            logger.error(f"Upload error: {e}", exc_info=True)
            return Response(
                {"error": "Upload failed", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _get_tenant_id(self, user):
        """Get tenant ID for the user (simplified - should come from user profile)"""
        # TODO: Implement proper tenant resolution from user profile
        return getattr(user, "tenant_id", "default")


class LogUploadStatusView(APIView):
    """Check status of log upload task"""

    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        """Get task status"""
        from celery.result import AsyncResult

        try:
            task = AsyncResult(task_id)

            response = {
                "task_id": task_id,
                "status": task.state,
            }

            if task.state == "PENDING":
                response["message"] = "Task is waiting to be processed"
            elif task.state == "STARTED":
                response["message"] = "Task is being processed"
            elif task.state == "SUCCESS":
                response["message"] = "Task completed successfully"
                response["result"] = task.result
            elif task.state == "FAILURE":
                response["message"] = "Task failed"
                response["error"] = str(task.info)
            elif task.state == "RETRY":
                response["message"] = "Task is being retried"

            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error checking task status: {e}")
            return Response(
                {"error": "Status check failed", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LogSearchView(APIView):
    """Search logs in Elasticsearch"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Search logs with query parameters

        Query params:
        - q: Search query
        - from: Start time
        - to: End time
        - level: Log level filter
        - service: Service name filter
        - size: Number of results (default 100)
        - page: Page number
        """
        from datetime import datetime, timedelta

        from elasticsearch import Elasticsearch

        query = request.query_params.get("q", "")
        log_level = request.query_params.get("level", "")
        service = request.query_params.get("service", "")
        size = int(request.query_params.get("size", 100))
        page = int(request.query_params.get("page", 1))

        # Time range
        time_to = request.query_params.get("to", datetime.utcnow().isoformat())
        time_from = request.query_params.get(
            "from", (datetime.utcnow() - timedelta(hours=24)).isoformat()
        )

        try:
            es_config = settings.ELASTICSEARCH_DSL["default"]
            es = Elasticsearch(
                hosts=es_config["hosts"], http_auth=es_config.get("http_auth")
            )

            # Build query
            tenant_id = self._get_tenant_id(request.user)
            must_clauses = [{"term": {"tenant_id": tenant_id}}]

            if query:
                must_clauses.append(
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["message", "raw_log", "original"],
                        }
                    }
                )

            if log_level:
                must_clauses.append({"term": {"level": log_level.upper()}})

            if service:
                must_clauses.append({"term": {"service_name": service}})

            search_body = {
                "query": {
                    "bool": {
                        "must": must_clauses,
                        "filter": [
                            {
                                "range": {
                                    "@timestamp": {"gte": time_from, "lte": time_to}
                                }
                            }
                        ],
                    }
                },
                "sort": [{"@timestamp": {"order": "desc"}}],
                "size": size,
                "from": (page - 1) * size,
            }

            # Execute search
            result = es.search(index=f"logs-{tenant_id}-*", body=search_body)

            # Format results
            hits = result["hits"]["hits"]
            logs = [hit["_source"] for hit in hits]

            return Response(
                {
                    "query": query,
                    "results": logs,
                    "total": result["hits"]["total"]["value"],
                    "page": page,
                    "size": size,
                    "took": result["took"],
                }
            )

        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            return Response(
                {
                    "error": "Search failed",
                    "message": str(e),
                    "results": [],
                    "total": 0,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        """
        Search logs with JSON body parameters
        
        Request body:
        - q: Search query
        - from: Start time
        - to: End time
        - level: Log level filter
        - service: Service name filter
        - source: Log source filter
        - environment: Environment filter
        - size: Number of results (default 100)
        - page: Page number
        """
        from datetime import datetime, timedelta

        from elasticsearch import Elasticsearch

        query = request.data.get("q", "")
        log_level = request.data.get("level", "")
        service = request.data.get("service", "")
        source = request.data.get("source", "")
        environment = request.data.get("environment", "")
        size = int(request.data.get("size", 100))
        page = int(request.data.get("page", 1))

        # Time range
        time_to = request.data.get("to", datetime.utcnow().isoformat())
        time_from = request.data.get(
            "from", (datetime.utcnow() - timedelta(days=7)).isoformat()
        )

        try:
            es_config = settings.ELASTICSEARCH_DSL["default"]
            es = Elasticsearch(
                hosts=es_config["hosts"], http_auth=es_config.get("http_auth")
            )

            # Build query
            tenant_id = self._get_tenant_id(request.user)
            must_clauses = [{"term": {"tenant_id": tenant_id}}]

            if query:
                must_clauses.append(
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["message", "raw_log", "original"],
                        }
                    }
                )

            if log_level:
                must_clauses.append({"term": {"level": log_level.upper()}})

            if service:
                must_clauses.append({"term": {"service_name": service}})
                
            if source:
                must_clauses.append({"term": {"source": source}})
                
            if environment:
                must_clauses.append({"term": {"environment": environment}})

            search_body = {
                "query": {
                    "bool": {
                        "must": must_clauses,
                        "filter": [
                            {
                                "range": {
                                    "@timestamp": {"gte": time_from, "lte": time_to}
                                }
                            }
                        ],
                    }
                },
                "sort": [{"@timestamp": {"order": "desc"}}],
                "size": size,
                "from": (page - 1) * size,
            }

            # Execute search
            result = es.search(index=f"logs-{tenant_id}-*", body=search_body)

            # Format results
            hits = result["hits"]["hits"]
            logs = [hit["_source"] for hit in hits]

            return Response(
                {
                    "query": query,
                    "results": logs,
                    "total": result["hits"]["total"]["value"],
                    "page": page,
                    "size": size,
                    "took": result["took"],
                }
            )

        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            return Response(
                {
                    "error": "Search failed",
                    "message": str(e),
                    "results": [],
                    "total": 0,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _get_tenant_id(self, user):
        """Get tenant ID for the user"""
        return getattr(user, "tenant_id", "default")


class LogstashMonitorView(APIView):
    """
    Monitor Logstash forwarder health and statistics
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get Logstash forwarder status and statistics

        Returns:
        - health: Connection health status
        - statistics: Success/failure counters
        - configuration: Current settings
        """
        try:
            forwarder = get_logstash_forwarder()

            # Get health status
            health = forwarder.health_check()

            # Get statistics
            stats = forwarder.get_statistics()

            # Configuration info
            config = {
                "host": forwarder.host,
                "port": forwarder.port,
                "protocol": forwarder.protocol,
                "timeout": forwarder.timeout,
                "max_retries": forwarder.max_retries,
                "retry_delay": forwarder.retry_delay,
                "enabled": getattr(settings, "USE_LOGSTASH", True),
            }

            response_data = {
                "health": health,
                "statistics": stats,
                "configuration": config,
                "timestamp": forwarder._stats.get("last_success"),
            }

            logger.info(
                f"Logstash monitor check - Status: {health['status']}, "
                f"Sent: {stats['total_sent']}, Failed: {stats['total_failed']}"
            )

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Logstash monitor error: {e}", exc_info=True)
            return Response(
                {
                    "error": "Monitor check failed",
                    "message": str(e),
                    "health": {"status": "unknown"},
                    "statistics": {},
                    "configuration": {},
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        """
        Send test message to Logstash
        """
        try:
            forwarder = get_logstash_forwarder()

            test_log = {
                "@timestamp": request.data.get("timestamp"),
                "message": request.data.get("message", "Test message from API"),
                "level": "INFO",
                "source": "monitor_test",
                "tenant_id": self._get_tenant_id(request.user),
                "test": True,
            }

            success = forwarder.send_log(test_log)

            if success:
                logger.info(f"Test message sent successfully to Logstash")
                return Response(
                    {
                        "success": True,
                        "message": "Test message sent successfully",
                        "log": test_log,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                logger.warning(f"Failed to send test message to Logstash")
                return Response(
                    {
                        "success": False,
                        "message": "Failed to send test message",
                        "error": forwarder._stats.get("last_error"),
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except Exception as e:
            logger.error(f"Test message error: {e}", exc_info=True)
            return Response(
                {"success": False, "error": "Test failed", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request):
        """
        Reset Logstash forwarder statistics
        """
        try:
            forwarder = get_logstash_forwarder()
            forwarder.reset_statistics()

            logger.info(f"Logstash statistics reset by {request.user.username}")

            return Response(
                {"message": "Statistics reset successfully"}, status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Statistics reset error: {e}")
            return Response(
                {"error": "Reset failed", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _get_tenant_id(self, user):
        """Get tenant ID for the user"""
        return getattr(user, "tenant_id", "default")
