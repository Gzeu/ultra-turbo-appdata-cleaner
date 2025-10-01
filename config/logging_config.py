"""
Logging configuration for the application
"""

import logging
import logging.handlers
import os
from pathlib import Path

def setup_logging(log_level=logging.INFO, log_file=None):
    """Setup application logging configuration"""
    
    if log_file is None:
        log_dir = os.path.join(os.path.expanduser("~"), ".ultra_turbo_cleaner", "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "cleaner.log")
    
    # Create formatters
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Set levels for specific loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    
    logging.info(f"Logging initialized - Level: {logging.getLevelName(log_level)}")
    logging.info(f"Log file: {log_file}")

def get_logger(name):
    """Get a logger instance for a specific module"""
    return logging.getLogger(name)