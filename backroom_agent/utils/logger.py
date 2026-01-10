import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional

# Define ANSI color codes for console output
class LogColors:
    RESET = "\033[0m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BOLD_RED = "\033[1;31m"
    BOLD_YELLOW = "\033[1;33m"

class ColoredFormatter(logging.Formatter):
    """
    Custom Formatter to add colors to console logs based on log level.
    Only applies colors to the levelname part, enabling easy reading.
    """

    # Format includes: Timestamp (ms), Level, Filename:Line, Module, Message
    FORMAT_STR = "%(asctime)s.%(msecs)03d | %(levelname)-8s | %(filename)s:%(lineno)d | %(name)s | %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    LEVEL_COLORS = {
        logging.DEBUG: LogColors.CYAN,
        logging.INFO: LogColors.GREEN,
        logging.WARNING: LogColors.YELLOW,
        logging.ERROR: LogColors.RED,
        logging.CRITICAL: LogColors.BOLD_RED,
    }

    def format(self, record: logging.LogRecord) -> str:
        # Create a copy so we don't alter the original record for other handlers
        log_fmt = self.FORMAT_STR
        
        # Apply color only if it's going to a stream that supports it (simulated logic here)
        # In this specific class, we assume we want colors.
        color = self.LEVEL_COLORS.get(record.levelno, LogColors.RESET)
        
        # We inject the color codes around the levelname in the format string dynamically
        # Or we can format the levelname attribute. 
        # Better approach: Override formatMessage or just modify levelname temporarily.
        original_levelname = record.levelname
        record.levelname = f"{color}{original_levelname}{LogColors.RESET}"
        
        formatter = logging.Formatter(log_fmt, self.DATE_FORMAT)
        result = formatter.format(record)
        
        # Restore original levelname
        record.levelname = original_levelname
        return result

class PlainFormatter(logging.Formatter):
    """
    Plain text formatter for file logs (no color codes).
    """
    FORMAT_STR = "%(asctime)s.%(msecs)03d | %(levelname)-8s | %(filename)s:%(lineno)d | %(name)s | %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self):
        super().__init__(self.FORMAT_STR, self.DATE_FORMAT)

class LogManager:
    """
    Manager class to setup and provide logger instances.
    """
    
    _instance: Optional[logging.Logger] = None
    
    @staticmethod
    def setup_logger(
        name: str = "backroom_agent",
        log_dir: str = "logs",
        log_file: str = "app.log",
        level: int = logging.INFO,
        console_output: bool = True,
        file_output: bool = True,
        backup_count: int = 30
    ) -> logging.Logger:
        """
        Creates and configures a logger instance.

        Args:
            name (str): The logger name.
            log_dir (str): Directory path to store log files.
            log_file (str): Base filename for the log.
            level (int): Logging level (logging.DEBUG, logging.INFO, etc).
            console_output (bool): Whether to output to console.
            file_output (bool): Whether to output to file.
            backup_count (int): Number of daily log files to keep.

        Returns:
            logging.Logger: Configured logger instance.
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Clear existing handlers to avoid duplicate logs if setup is called multiple times
        if logger.handlers:
            logger.handlers.clear()
            
        # Prevent propagation to root logger to avoid double printing if root is configured
        logger.propagate = False

        # 1. Console Handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(ColoredFormatter())
            logger.addHandler(console_handler)

        # 2. File Handler
        if file_output:
            # Ensure log directory exists
            log_path = Path(log_dir)
            log_path.mkdir(parents=True, exist_ok=True)
            
            file_path = log_path / log_file
            
            # TimedRotatingFileHandler: Rotates logs daily ('midnight')
            file_handler = TimedRotatingFileHandler(
                filename=file_path,
                when="midnight",
                interval=1,
                backupCount=backup_count,
                encoding="utf-8"
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(PlainFormatter())
            # Suffix for rotated files: YYYY-MM-DD
            file_handler.suffix = "%Y-%m-%d" 
            logger.addHandler(file_handler)

        return logger

    @classmethod
    def get_logger(cls, name: str = "backroom_agent") -> logging.Logger:
        """
        Get the singleton logger instance. If not initialized, initializes with defaults.
        """
        if cls._instance is None:
            # Default initialization
            cls._instance = cls.setup_logger(name=name, level=logging.DEBUG)
        return cls._instance

# --- Convenience Exports ---

# 1. Initialize the global default logger immediately
# This ensures 'from logger import logger' works out of the box
logger = LogManager.get_logger()

# 2. Function to re-configure the global logger if needed (e.g., from main config)
def configure_global_logger(log_dir: str = "logs", level: int = logging.INFO):
    global logger
    logger = LogManager.setup_logger(log_dir=log_dir, level=level)


# --- Example Usage (Run this file directly to test) ---
if __name__ == "__main__":
    # Test Setup: Create a specific logger for testing
    test_logger = LogManager.setup_logger(
        name="test_logger",
        log_dir="tmp/test_logs",
        log_file="test.log",
        level=logging.DEBUG
    )

    print(f"Testing logger. Checking logs in ./tmp/test_logs/test.log")
    
    # 1. Standard Levels
    test_logger.debug("This is a DEBUG message - only visible if level is DEBUG.")
    test_logger.info("This is an INFO message - standard operating info.")
    test_logger.warning("This is a WARNING message - verify something.")
    test_logger.error("This is an ERROR message - something went wrong.")
    test_logger.critical("This is a CRITICAL message - potential crash.")

    # 2. Variable Formatting
    user_id = 12345
    action = "login"
    test_logger.info(f"User {user_id} performed action: {action}")

    # 3. Exception Traceback
    try:
        x = 1 / 0
    except ZeroDivisionError:
        # logger.exception automatically includes the traceback
        test_logger.exception("Caught an expected ZeroDivisionError for demonstration:")
