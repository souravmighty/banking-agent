import logging
import sys
import json
import time
from typing import Any, Dict
from app.core.config import settings

class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        if hasattr(record, "caller_service"):
            log_obj["caller_service"] = record.caller_service
        if hasattr(record, "catalog_version"):
            log_obj["catalog_version"] = record.catalog_version
        if hasattr(record, "selected_tables"):
            log_obj["selected_tables"] = record.selected_tables
        if hasattr(record, "selected_metrics"):
            log_obj["selected_metrics"] = record.selected_metrics
        if hasattr(record, "context_size"):
            log_obj["context_size"] = record.context_size
        if hasattr(record, "metadata_lookup_latency"):
            log_obj["metadata_lookup_latency"] = record.metadata_lookup_latency
        if hasattr(record, "search_latency"):
            log_obj["search_latency"] = record.search_latency
        if hasattr(record, "validation_result"):
            log_obj["validation_result"] = record.validation_result
            
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

def setup_logging():
    logger = logging.getLogger("bankpilot_metadata")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    
    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
    return logger

logger = setup_logging()
