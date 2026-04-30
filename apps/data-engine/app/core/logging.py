import logging
import sys
from logging.handlers import RotatingFileHandler
from app.core.config import get_settings

settings = get_settings()

def setup_logging():
    log_level = logging.DEBUG if settings.debug else logging.INFO
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler
    file_handler = RotatingFileHandler(
        "app.log", maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Silence some noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logger.info(f"Logging initialized with level: {logging.getLevelName(log_level)}")
