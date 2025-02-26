import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Define color codes for console output
class LogColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to levelname in console output."""
    
    COLORS = {
        'DEBUG': LogColors.OKBLUE,
        'INFO': LogColors.OKGREEN,
        'WARNING': LogColors.WARNING,
        'ERROR': LogColors.FAIL,
        'CRITICAL': LogColors.FAIL + LogColors.BOLD,
    }
    
    def format(self, record):
        # Add colors if it's going to the console
        if hasattr(record, 'color') and record.color:
            record.levelname = f"{self.COLORS.get(record.levelname, '')}{record.levelname}{LogColors.ENDC}"
        return super().format(record)

def setup_logging():
    """Configure logging settings for the application."""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Use a single log file with date in name
    log_file = os.path.join('logs', 'podcast_finder.log')
    
    # Set up the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Create rotating file handler (10MB per file, keep 5 backup files)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        fmt='%(asctime)s.%(msecs)03d - %(levelname)-8s - %(name)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # Create console handler with colors
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = ColoredFormatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Remove any existing handlers
    root_logger.handlers = []
    
    # Add the handlers to the root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Create and return logger for this module
    logger = logging.getLogger(__name__)
    
    # Log startup message
    logger.info('='*50)
    logger.info(f'Logging initialized at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    logger.info(f'Log file: {log_file}')
    logger.info('='*50)
    
    return logger 