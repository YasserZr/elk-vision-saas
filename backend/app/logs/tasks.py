import logging
import uuid
from datetime import datetime

from celery import shared_task
from django.conf import settings
from elasticsearch import Elasticsearch

from .logstash_forwarder import get_logstash_forwarder
from .models_mongo import LogMetadata
from .parsers import LogParser
from api.websocket_utils import send_upload_status

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_and_ingest_logs(self, content: str, format_type: str, metadata: dict):
    """
    Process uploaded logs and ingest into Elasticsearch

    Args:
        content: Raw log file content
        format_type: Log format (json, csv, text)
        metadata: Additional metadata (source, environment, etc.)

    Returns:
        dict: Processing results
    """
    task_id = self.request.id
    upload_id = metadata.get('upload_id') or str(uuid.uuid4())
    user_id = metadata.get('user_id', 0)
    
    logger.info(f"Task {task_id}: Starting log processing for format {format_type}")

    # Create MongoDB metadata record
    try:
        log_metadata = LogMetadata.create(
            upload_id=upload_id,
            task_id=task_id,
            tenant_id=metadata.get('tenant_id', 'default'),
            user_id=user_id,
            source=metadata.get('source', 'manual_upload'),
            environment=metadata.get('environment', 'production'),
            service_name=metadata.get('service_name', 'unknown'),
            file_name=metadata.get('file_name', 'unknown'),
            file_size=metadata.get('file_size', 0),
            format_type=format_type,
            tags=metadata.get('tags', []),
        )
        logger.info(f"Task {task_id}: Created MongoDB metadata for upload {upload_id}")
    except Exception as e:
        logger.error(f"Task {task_id}: Failed to create MongoDB metadata: {e}")
        # Continue processing even if metadata creation fails

    try:
        # Parse logs
        parsed_entries = LogParser.parse(content, format_type, metadata)
        total_entries = len(parsed_entries)

        if total_entries == 0:
            logger.warning(f"Task {task_id}: No entries parsed from log file")
            # Update metadata status
            try:
                LogMetadata.update_status(
                    upload_id=upload_id,
                    status='failed',
                    log_count=0,
                    errors=['No log entries found in file']
                )
            except Exception as e:
                logger.error(f"Failed to update metadata: {e}")
            
            return {
                "status": "warning",
                "message": "No log entries found",
                "total_entries": 0,
                "indexed_entries": 0,
            }

        logger.info(f"Task {task_id}: Parsed {total_entries} log entries")

        # Determine ingestion method (Logstash or direct Elasticsearch)
        use_logstash = getattr(settings, "USE_LOGSTASH", True)

        if use_logstash:
            # Forward to Logstash
            result = forward_to_logstash(task_id, parsed_entries, metadata)
        else:
            # Direct Elasticsearch ingestion
            result = ingest_to_elasticsearch(task_id, parsed_entries, metadata)

        # Update MongoDB metadata with results
        try:
            status = 'completed' if result.get('status') == 'success' else 'failed'
            errors = [result.get('message')] if status == 'failed' else []
            
            LogMetadata.update_status(
                upload_id=upload_id,
                status=status,
                log_count=result.get('indexed_entries', 0),
                ingestion_method=result.get('ingestion_method', 'unknown'),
                errors=errors,
                indexed_at=datetime.utcnow() if status == 'completed' else None
            )
            
            # Send WebSocket notification for completion
            try:
                send_upload_status(
                    user_id=user_id,
                    upload_data={
                        'task_id': task_id,
                        'upload_id': upload_id,
                        'filename': metadata.get('file_name', 'unknown'),
                        'status': status,
                        'progress': 100,
                        'total_entries': result.get('total_entries', 0),
                        'indexed_entries': result.get('indexed_entries', 0),
                        'failed_entries': result.get('failed_entries', 0),
                        'message': result.get('message', 'Upload completed')
                    }
                )
            except Exception as ws_error:
                logger.warning(f"Failed to send WebSocket notification: {ws_error}")
                
            logger.info(f"Task {task_id}: Updated MongoDB metadata - Status: {status}")
        except Exception as e:
            logger.error(f"Task {task_id}: Failed to update MongoDB metadata: {e}")

        logger.info(f"Task {task_id}: Completed - {result}")
        return result

    except Exception as exc:
        logger.error(f"Task {task_id}: Processing error: {exc}")

        # Update metadata with error
        try:
            LogMetadata.update_status(
                upload_id=upload_id,
                status='failed',
                errors=[str(exc)]
            )
            
            # Send WebSocket notification for failure
            try:
                send_upload_status(
                    user_id=user_id,
                    upload_data={
                        'task_id': task_id,
                        'upload_id': upload_id,
                        'filename': metadata.get('file_name', 'unknown'),
                        'status': 'failed',
                        'progress': 0,
                        'message': f'Upload failed: {str(exc)}'
                    }
                )
            except Exception as ws_error:
                logger.warning(f"Failed to send WebSocket notification: {ws_error}")
        except Exception as e:
            logger.error(f"Failed to update metadata with error: {e}")

        # Retry on failure
        if self.request.retries < self.max_retries:
            logger.info(
                f"Task {task_id}: Retrying (attempt {self.request.retries + 1})"
            )
            raise self.retry(exc=exc)

        return {
            "status": "error",
            "message": str(exc),
            "total_entries": 0,
            "indexed_entries": 0,
            "failed_entries": 0,
        }



def forward_to_logstash(task_id: str, entries: list, metadata: dict) -> dict:
    """
    Forward parsed logs to Logstash

    Args:
        task_id: Celery task ID
        entries: Parsed log entries
        metadata: Additional metadata

    Returns:
        dict: Processing results
    """
    try:
        forwarder = get_logstash_forwarder()

        # Add metadata to each entry
        enriched_entries = []
        for entry in entries:
            enriched_entry = entry.copy()
            enriched_entry.update(
                {
                    "tenant_id": metadata.get("tenant_id", "default"),
                    "source": metadata.get("source", "api_upload"),
                    "task_id": task_id,
                }
            )
            enriched_entries.append(enriched_entry)

        # Send to Logstash in batches
        batch_size = getattr(settings, "LOGSTASH_BATCH_SIZE", 100)
        result = forwarder.send_batch(enriched_entries, batch_size=batch_size)

        logger.info(
            f"Task {task_id}: Forwarded to Logstash - "
            f"Sent: {result['sent']}, Failed: {result['failed']}"
        )

        return {
            "status": "success" if result["failed"] == 0 else "partial",
            "message": f"Forwarded {result['sent']} entries to Logstash",
            "total_entries": result["total"],
            "indexed_entries": result["sent"],
            "failed_entries": result["failed"],
            "ingestion_method": "logstash",
        }

    except Exception as e:
        logger.error(f"Task {task_id}: Logstash forwarding error: {e}")
        return {
            "status": "error",
            "message": f"Logstash forwarding failed: {str(e)}",
            "total_entries": len(entries),
            "indexed_entries": 0,
            "failed_entries": len(entries),
            "ingestion_method": "logstash",
        }


def ingest_to_elasticsearch(task_id: str, entries: list, metadata: dict) -> dict:
    """
    Direct ingestion to Elasticsearch (fallback method)

    Args:
        task_id: Celery task ID
        entries: Parsed log entries
        metadata: Additional metadata

    Returns:
        dict: Processing results
    """
    try:
        # Connect to Elasticsearch
        es_config = settings.ELASTICSEARCH_DSL["default"]
        es = Elasticsearch(
            hosts=es_config["hosts"], http_auth=es_config.get("http_auth")
        )

        # Bulk index logs
        indexed_count = 0
        failed_count = 0
        batch_size = 500

        for i in range(0, len(entries), batch_size):
            batch = entries[i : i + batch_size]

            try:
                success, failed = bulk_index_logs(
                    es, batch, metadata.get("tenant_id", "default")
                )
                indexed_count += success
                failed_count += failed

                logger.info(
                    f"Task {task_id}: Batch {i//batch_size + 1}: "
                    f"Indexed {success}, Failed {failed}"
                )

            except Exception as e:
                logger.error(f"Task {task_id}: Batch indexing error: {e}")
                failed_count += len(batch)

        result = {
            "status": "success" if failed_count == 0 else "partial",
            "message": f"Processed {len(entries)} entries via Elasticsearch",
            "total_entries": len(entries),
            "indexed_entries": indexed_count,
            "failed_entries": failed_count,
            "ingestion_method": "elasticsearch",
        }

        logger.info(f"Task {task_id}: Elasticsearch ingestion - {result}")
        return result

    except Exception as e:
        logger.error(f"Task {task_id}: Elasticsearch ingestion error: {e}")
        return {
            "status": "error",
            "message": f"Elasticsearch ingestion failed: {str(e)}",
            "total_entries": len(entries),
            "indexed_entries": 0,
            "failed_entries": len(entries),
            "ingestion_method": "elasticsearch",
        }


def bulk_index_logs(es: Elasticsearch, entries: list, tenant_id: str) -> tuple:
    """
    Bulk index log entries into Elasticsearch

    Args:
        es: Elasticsearch client
        entries: List of parsed log entries
        tenant_id: Tenant identifier

    Returns:
        tuple: (success_count, failed_count)
    """
    from elasticsearch.helpers import bulk

    # Prepare bulk actions
    actions = []
    for entry in entries:
        action = {
            "_index": f'logs-{tenant_id}-{entry.get("@timestamp", "")[:7]}',  # Monthly indices
            "_source": entry,
        }
        actions.append(action)

    try:
        success, failed = bulk(
            es, actions, raise_on_error=False, raise_on_exception=False, stats_only=True
        )
        return success, len(entries) - success

    except Exception as e:
        logger.error(f"Bulk indexing error: {e}")
        return 0, len(entries)


@shared_task
def cleanup_old_logs(days: int = 90):
    """
    Clean up old log indices

    Args:
        days: Number of days to retain logs
    """
    from datetime import datetime, timedelta

    logger.info(f"Starting cleanup of logs older than {days} days")

    try:
        es_config = settings.ELASTICSEARCH_DSL["default"]
        es = Elasticsearch(
            hosts=es_config["hosts"], http_auth=es_config.get("http_auth")
        )

        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_month = cutoff_date.strftime("%Y-%m")

        # Get all indices
        indices = es.indices.get_alias(index="logs-*")

        deleted_count = 0
        for index_name in indices:
            # Extract date from index name (format: logs-{tenant}-YYYY-MM)
            parts = index_name.split("-")
            if len(parts) >= 3:
                index_month = parts[-1]
                if index_month < cutoff_month:
                    try:
                        es.indices.delete(index=index_name)
                        logger.info(f"Deleted old index: {index_name}")
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"Error deleting index {index_name}: {e}")

        logger.info(f"Cleanup completed. Deleted {deleted_count} indices")
        return {"status": "success", "deleted_indices": deleted_count}

    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        return {"status": "error", "message": str(e)}
