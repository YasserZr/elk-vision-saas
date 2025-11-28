import csv
import io
import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class LogParser:
    """Base class for log parsing"""

    @staticmethod
    def detect_format(file_name: str) -> str:
        """Detect log format from file extension"""
        file_name = file_name.lower()
        if file_name.endswith(".json"):
            return "json"
        elif file_name.endswith(".csv"):
            return "csv"
        elif file_name.endswith((".txt", ".log")):
            return "text"
        return "unknown"

    @staticmethod
    def parse(
        content: str, format_type: str, metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Parse log content based on format"""
        if format_type == "json":
            return JSONLogParser.parse(content, metadata)
        elif format_type == "csv":
            return CSVLogParser.parse(content, metadata)
        elif format_type == "text":
            return TextLogParser.parse(content, metadata)
        else:
            raise ValueError(f"Unsupported format: {format_type}")


class JSONLogParser:
    """Parser for JSON format logs"""

    @staticmethod
    def parse(content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse JSON logs"""
        try:
            data = json.loads(content)

            # Handle both single object and array
            if isinstance(data, dict):
                entries = [data]
            elif isinstance(data, list):
                entries = data
            else:
                raise ValueError("JSON must be an object or array")

            # Enrich each entry with metadata
            enriched_entries = []
            for entry in entries:
                if not isinstance(entry, dict):
                    logger.warning(f"Skipping non-dict entry: {type(entry)}")
                    continue

                enriched = JSONLogParser._enrich_entry(entry, metadata)
                enriched_entries.append(enriched)

            logger.info(f"Parsed {len(enriched_entries)} JSON log entries")
            return enriched_entries

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            raise ValueError(f"Invalid JSON: {str(e)}")

    @staticmethod
    def _enrich_entry(
        entry: Dict[str, Any], metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enrich log entry with metadata"""
        enriched = {
            "@timestamp": entry.get("timestamp")
            or entry.get("@timestamp")
            or datetime.utcnow().isoformat(),
            "message": entry.get("message", ""),
            "level": entry.get("level", "INFO").upper(),
            "source": metadata.get("source", "manual_upload"),
            "environment": metadata.get("environment", "production"),
            "service_name": metadata.get("service_name", "unknown"),
            "tags": metadata.get("tags", []),
            "tenant_id": metadata.get("tenant_id", "default"),
            "uploaded_by": metadata.get("uploaded_by", "unknown"),
            "original": entry,  # Keep original data
        }

        # Add any additional fields from original entry
        for key, value in entry.items():
            if key not in enriched:
                enriched[key] = value

        return enriched


class CSVLogParser:
    """Parser for CSV format logs"""

    @staticmethod
    def parse(content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse CSV logs"""
        try:
            csv_file = io.StringIO(content)
            reader = csv.DictReader(csv_file)

            entries = []
            for row_num, row in enumerate(reader, start=1):
                try:
                    enriched = CSVLogParser._process_row(row, metadata, row_num)
                    entries.append(enriched)
                except Exception as e:
                    logger.warning(f"Error processing CSV row {row_num}: {e}")
                    continue

            logger.info(f"Parsed {len(entries)} CSV log entries")
            return entries

        except csv.Error as e:
            logger.error(f"CSV parse error: {e}")
            raise ValueError(f"Invalid CSV: {str(e)}")

    @staticmethod
    def _process_row(
        row: Dict[str, str], metadata: Dict[str, Any], row_num: int
    ) -> Dict[str, Any]:
        """Process CSV row into log entry"""

        # Try to find timestamp field
        timestamp = None
        for possible_ts_field in [
            "timestamp",
            "time",
            "datetime",
            "date",
            "@timestamp",
        ]:
            if possible_ts_field in row:
                timestamp = row[possible_ts_field]
                break

        if not timestamp:
            timestamp = datetime.utcnow().isoformat()

        # Try to find message field
        message = row.get("message") or row.get("msg") or row.get("log") or ""

        # Try to find level field
        level = row.get("level") or row.get("severity") or row.get("loglevel") or "INFO"

        enriched = {
            "@timestamp": timestamp,
            "message": message,
            "level": level.upper(),
            "source": metadata.get("source", "manual_upload"),
            "environment": metadata.get("environment", "production"),
            "service_name": metadata.get("service_name", "unknown"),
            "tags": metadata.get("tags", []),
            "tenant_id": metadata.get("tenant_id", "default"),
            "uploaded_by": metadata.get("uploaded_by", "unknown"),
            "row_number": row_num,
            "original": row,
        }

        # Add other fields from CSV
        for key, value in row.items():
            if key not in enriched and value:
                enriched[key] = value

        return enriched


class TextLogParser:
    """Parser for plain text/log format"""

    # Common log patterns
    PATTERNS = {
        "apache_combined": re.compile(
            r'(?P<ip>[\d.]+) - - \[(?P<timestamp>[^\]]+)\] "(?P<method>\w+) (?P<path>[^\s]+) HTTP/[\d.]+" (?P<status>\d+) (?P<size>\d+)'
        ),
        "nginx": re.compile(
            r'(?P<ip>[\d.]+) - - \[(?P<timestamp>[^\]]+)\] "(?P<method>\w+) (?P<path>[^\s]+) HTTP/[\d.]+" (?P<status>\d+) (?P<size>\d+)'
        ),
        "syslog": re.compile(
            r"(?P<timestamp>\w+\s+\d+\s+[\d:]+) (?P<host>\S+) (?P<process>\S+): (?P<message>.*)"
        ),
        "python_logging": re.compile(
            r"(?P<timestamp>[\d-]+ [\d:,]+) - (?P<name>\S+) - (?P<level>\w+) - (?P<message>.*)"
        ),
        "generic": re.compile(
            r"(?P<timestamp>[\d-]+ [\d:]+)[\s\|,:-]*(?P<level>DEBUG|INFO|WARNING|ERROR|CRITICAL|WARN|FATAL)?[\s\|,:-]*(?P<message>.*)"
        ),
    }

    @staticmethod
    def parse(content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse text logs"""
        lines = content.strip().split("\n")
        entries = []

        for line_num, line in enumerate(lines, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                parsed = TextLogParser._parse_line(line, metadata, line_num)
                entries.append(parsed)
            except Exception as e:
                logger.warning(f"Error parsing line {line_num}: {e}")
                # Create basic entry for unparseable lines
                entries.append(
                    {
                        "@timestamp": datetime.utcnow().isoformat(),
                        "message": line,
                        "level": "INFO",
                        "source": metadata.get("source", "manual_upload"),
                        "environment": metadata.get("environment", "production"),
                        "service_name": metadata.get("service_name", "unknown"),
                        "tags": metadata.get("tags", []),
                        "tenant_id": metadata.get("tenant_id", "default"),
                        "uploaded_by": metadata.get("uploaded_by", "unknown"),
                        "line_number": line_num,
                        "parse_error": str(e),
                    }
                )

        logger.info(f"Parsed {len(entries)} text log entries")
        return entries

    @staticmethod
    def _parse_line(
        line: str, metadata: Dict[str, Any], line_num: int
    ) -> Dict[str, Any]:
        """Parse a single log line"""

        # Try each pattern
        parsed_data = None
        matched_pattern = None

        for pattern_name, pattern in TextLogParser.PATTERNS.items():
            match = pattern.match(line)
            if match:
                parsed_data = match.groupdict()
                matched_pattern = pattern_name
                break

        # If no pattern matched, use the line as message
        if not parsed_data:
            parsed_data = {"message": line, "level": "INFO"}

        # Build enriched entry
        enriched = {
            "@timestamp": parsed_data.get("timestamp", datetime.utcnow().isoformat()),
            "message": parsed_data.get("message", line),
            "level": (parsed_data.get("level") or "INFO").upper(),
            "source": metadata.get("source", "manual_upload"),
            "environment": metadata.get("environment", "production"),
            "service_name": metadata.get("service_name", "unknown"),
            "tags": metadata.get("tags", []),
            "tenant_id": metadata.get("tenant_id", "default"),
            "uploaded_by": metadata.get("uploaded_by", "unknown"),
            "line_number": line_num,
            "raw_log": line,
        }

        if matched_pattern:
            enriched["log_pattern"] = matched_pattern

        # Add additional parsed fields
        for key, value in parsed_data.items():
            if key not in enriched and value:
                enriched[key] = value

        return enriched


def estimate_log_count(content: str, format_type: str) -> int:
    """Estimate number of log entries in content"""
    try:
        if format_type == "json":
            data = json.loads(content)
            return len(data) if isinstance(data, list) else 1
        elif format_type == "csv":
            return len(content.strip().split("\n")) - 1  # Subtract header
        elif format_type == "text":
            return len([line for line in content.strip().split("\n") if line.strip()])
        return 0
    except Exception as e:
        logger.error(f"Error estimating log count: {e}")
        return 0
