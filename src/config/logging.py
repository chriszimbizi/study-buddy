import logging
from logging import Logger
from logging.handlers import RotatingFileHandler
import os


def configure_logger(logger_name: str, log_file_path: str) -> Logger:
    """
    Configure a logger with the given name and file path, including a console handler.

    Parameters:
    - logger_name (str): The name of the logger
    - log_file_path (str): The full path to the log file

    Returns:
    - logger (Logger): The configured logger
    """

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
    )
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(file_formatter)
    logger.addHandler(console_handler)

    return logger


def configure_loggers() -> dict:
    """
    Configure loggers.

    Returns:
    - loggers (dict): A dictionary of loggers.
    """
    # Log directories and files
    log_config = {
        "assistant_logger": ("assistant_logs", "assistant_log.txt"),
        "thread_logger": ("thread_logs", "thread_log.txt"),
        "run_logger": ("run_logs", "run_log.txt"),
        "file_logger": ("file_logs", "file_log.txt"),
    }

    loggers = {}

    for logger_name, (log_directory_name, log_file_name) in log_config.items():
        log_directory = os.path.join(
            os.path.dirname(__file__), "..", "..", "logs", log_directory_name
        )
        log_file_path = os.path.join(log_directory, log_file_name)

        # Ensure the directory exists
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)

        logger = configure_logger(logger_name, log_file_path)
        loggers[logger_name] = logger

    return loggers
