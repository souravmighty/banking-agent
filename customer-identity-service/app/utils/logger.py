import logging
import sys
from pythonjsonlogger import jsonlogger
from app.config import settings

def setup_logger():
    logger = logging.getLogger()
    log_handler = logging.StreamHandler(sys.stdout)
    
    # Custom fields for structured logging
    formatter = jsonlogger.JsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s %(endpoint)s %(firebase_uid)s %(customer_id)s %(request_id)s %(execution_time)s'
    )
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)
    logger.setLevel(settings.LOG_LEVEL)
    return logger

logger = setup_logger()
