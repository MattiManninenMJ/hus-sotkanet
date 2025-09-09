"""Logging configuration for the application."""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Default configuration
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logging(
    log_dir: Path = LOG_DIR,
    log_level: str = LOG_LEVEL,
    log_format: str = LOG_FORMAT,
    date_format: str = DATE_FORMAT
):
    """
    Configure logging for the application.
    
    Args:
        log_dir: Directory for log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format string for log messages
        date_format: Format string for timestamps
    """
    
    # Create logs directory if it doesn't exist
    log_dir.mkdir(exist_ok=True, parents=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(log_format, datefmt=date_format)
    simple_formatter = logging.Formatter(
        '%(levelname)s - %(message)s', 
        datefmt=date_format
    )
    
    # Console handler (simple format for readability)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(simple_formatter)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(console_handler)
    
    # File handlers with rotation
    file_handlers = [
        {
            'filename': 'app.log',
            'level': logging.INFO,
            'formatter': detailed_formatter
        },
        {
            'filename': 'api.log',
            'level': logging.DEBUG,
            'formatter': detailed_formatter
        },
        {
            'filename': 'error.log',
            'level': logging.ERROR,
            'formatter': detailed_formatter
        }
    ]
    
    for handler_config in file_handlers:
        file_handler = RotatingFileHandler(
            log_dir / handler_config['filename'],
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(handler_config['formatter'])
        file_handler.setLevel(handler_config['level'])
        root_logger.addHandler(file_handler)
    
    # Log startup message
    root_logger.info("="*60)
    root_logger.info(f"Logging initialized at {datetime.now()}")
    root_logger.info(f"Log level: {log_level}")
    root_logger.info(f"Log directory: {log_dir}")
    root_logger.info("="*60)

def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger instance.
    
    Args:
        name: Logger name (e.g., 'api', 'data', 'app')
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

def log_function_call(func):
    """
    Decorator to log function calls.
    
    Usage:
        @log_function_call
        def my_function(arg1, arg2):
            return result
    """
    logger = get_logger(func.__module__)
    
    def wrapper(*args, **kwargs):
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} returned successfully")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} raised {e.__class__.__name__}: {e}")
            raise
    
    return wrapper

def log_api_call(url: str, method: str = "GET", response_code: int = None):
    """
    Log an API call.
    
    Args:
        url: API endpoint URL
        method: HTTP method
        response_code: HTTP response code
    """
    logger = get_logger('api')
    
    if response_code:
        if 200 <= response_code < 300:
            logger.info(f"{method} {url} -> {response_code}")
        elif 400 <= response_code < 500:
            logger.warning(f"{method} {url} -> {response_code} (Client Error)")
        else:
            logger.error(f"{method} {url} -> {response_code} (Server Error)")
    else:
        logger.debug(f"{method} {url}")

def log_data_processing(operation: str, records: int, duration: float = None):
    """
    Log data processing operations.
    
    Args:
        operation: Description of the operation
        records: Number of records processed
        duration: Time taken in seconds
    """
    logger = get_logger('data')
    
    if duration:
        logger.info(f"{operation}: {records} records in {duration:.2f}s ({records/duration:.0f} records/s)")
    else:
        logger.info(f"{operation}: {records} records")

# Color support for console output (optional)
try:
    import colorlog
    
    def setup_color_logging():
        """Setup colored console logging if colorlog is available."""
        
        handler = colorlog.StreamHandler()
        handler.setFormatter(
            colorlog.ColoredFormatter(
                '%(log_color)s%(levelname)-8s%(reset)s %(message)s',
                datefmt=DATE_FORMAT,
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            )
        )
        
        logger = colorlog.getLogger()
        logger.addHandler(handler)
        logger.setLevel(LOG_LEVEL)
        
        return logger
        
except ImportError:
    # colorlog not available, use standard logging
    pass

if __name__ == "__main__":
    # Test logging setup
    setup_logging()
    
    # Test different loggers
    app_logger = get_logger('app')
    api_logger = get_logger('api')
    data_logger = get_logger('data')
    
    app_logger.info("Application logger test")
    api_logger.debug("API logger test")
    data_logger.warning("Data logger test")
    
    # Test helper functions
    log_api_call("https://api.example.com/data", "GET", 200)
    log_data_processing("Data validation", 1000, 2.5)
    
    # Test error logging
    try:
        raise ValueError("Test error")
    except ValueError as e:
        app_logger.error(f"Caught error: {e}", exc_info=True)
    
    print(f"\nLog files created in: {LOG_DIR}")
    print("Check the logs directory for output files.")