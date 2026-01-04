import csv
import io
import json
import logging

from django.core.exceptions import ValidationError
from rest_framework import serializers

logger = logging.getLogger(__name__)

# File size limits (in bytes)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = [".json", ".csv", ".txt", ".log"]
ALLOWED_CONTENT_TYPES = [
    "application/json",
    "text/csv",
    "text/plain",
    "application/octet-stream",
]


class LogFileUploadSerializer(serializers.Serializer):
    """Serializer for log file upload with validation"""

    file = serializers.FileField(required=True)
    source = serializers.CharField(
        max_length=255, required=False, default="manual_upload"
    )
    environment = serializers.ChoiceField(
        choices=["production", "staging", "development", "testing"],
        required=False,
        default="production",
    )
    service_name = serializers.CharField(
        max_length=255, required=False, default="unknown"
    )
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50), required=False, default=list
    )

    def validate_tags(self, value):
        """Handle tags as JSON string or list"""
        if isinstance(value, str):
            try:
                # Try to parse as JSON array
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
                return [value]  # Single string value
            except (json.JSONDecodeError, ValueError):
                # If not JSON, treat as comma-separated string
                return [tag.strip() for tag in value.split(',') if tag.strip()]
        return value

    def validate_file(self, file):
        """Validate uploaded file"""

        # Check file size
        if file.size > MAX_FILE_SIZE:
            raise serializers.ValidationError(
                f"File size exceeds maximum limit of {MAX_FILE_SIZE / (1024 * 1024)}MB"
            )

        if file.size == 0:
            raise serializers.ValidationError("Uploaded file is empty")

        # Check file extension
        file_name = file.name.lower()
        if not any(file_name.endswith(ext) for ext in ALLOWED_EXTENSIONS):
            raise serializers.ValidationError(
                f"File extension not allowed. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # Check content type
        content_type = file.content_type
        if content_type not in ALLOWED_CONTENT_TYPES:
            logger.warning(
                f"Unusual content type: {content_type} for file: {file.name}"
            )

        # Validate file format by attempting to read first few lines
        try:
            file.seek(0)
            # Read first 1KB for validation
            sample = file.read(1024)
            file.seek(0)  # Reset file pointer

            # Try to decode as UTF-8
            try:
                sample.decode("utf-8")
            except UnicodeDecodeError:
                raise serializers.ValidationError("File must be UTF-8 encoded text")

        except Exception as e:
            logger.error(f"File validation error: {e}")
            raise serializers.ValidationError(f"Error reading file: {str(e)}")

        return file

    def validate(self, attrs):
        """Additional validation"""
        file = attrs.get("file")

        if file:
            # Determine format and validate structure
            file_name = file.name.lower()

            try:
                file.seek(0)
                content = file.read().decode("utf-8")
                file.seek(0)  # Reset for later use

                if file_name.endswith(".json"):
                    self._validate_json_format(content)
                elif file_name.endswith(".csv"):
                    self._validate_csv_format(content)
                elif file_name.endswith((".txt", ".log")):
                    self._validate_text_format(content)

            except Exception as e:
                logger.error(f"Format validation error: {e}")
                raise serializers.ValidationError(f"Invalid file format: {str(e)}")

        return attrs

    def _validate_json_format(self, content):
        """Validate JSON format"""
        try:
            data = json.loads(content)

            # Check if it's an array of log entries or single entry
            if isinstance(data, list):
                if not data:
                    raise ValidationError("JSON array is empty")
                # Validate first entry has expected structure
                if not isinstance(data[0], dict):
                    raise ValidationError("JSON array must contain objects")
            elif isinstance(data, dict):
                # Single log entry is acceptable
                pass
            else:
                raise ValidationError("JSON must be an object or array of objects")

        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON format: {str(e)}")

    def _validate_csv_format(self, content):
        """Validate CSV format"""
        try:
            csv_file = io.StringIO(content)
            reader = csv.DictReader(csv_file)

            # Check if CSV has headers
            if not reader.fieldnames:
                raise ValidationError("CSV file must have headers")

            # Try to read first row
            first_row = next(reader, None)
            if first_row is None:
                raise ValidationError("CSV file has no data rows")

        except csv.Error as e:
            raise ValidationError(f"Invalid CSV format: {str(e)}")

    def _validate_text_format(self, content):
        """Validate text/log format"""
        lines = content.strip().split("\n")

        if not lines or all(not line.strip() for line in lines):
            raise ValidationError("Text file has no valid log entries")

        # Basic validation: check if lines are not suspiciously long
        for i, line in enumerate(lines[:10]):  # Check first 10 lines
            if len(line) > 10000:  # 10KB per line
                raise ValidationError(f"Line {i+1} is too long (max 10KB per line)")


class LogUploadResponseSerializer(serializers.Serializer):
    """Serializer for log upload response"""

    task_id = serializers.CharField()
    message = serializers.CharField()
    file_name = serializers.CharField()
    file_size = serializers.IntegerField()
    format = serializers.CharField()
    estimated_entries = serializers.IntegerField()
    status = serializers.CharField()
