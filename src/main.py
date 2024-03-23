# Standard library imports
import logging
from logging import Logger
import os

# Third-party imports
from dotenv import load_dotenv
import openai

# Load environment
dotenv_path = os.path.join(os.path.dirname(__file__), "..", "data", "env")
load_dotenv(dotenv_path)

# Initialize OpenAI API
openai_api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=openai_api_key)
model = "gpt3.5-turbo-16k"


def configure_logger(logger_name: str, log_file_path: str) -> Logger:
    """
    Configure a logger with the given name and file path.

    Parameters:
    - logger_name (str): The name of the logger
    - log_file_path (str): Path to the log file

    Returns:
    - logger (Logger): The configured logger
    """

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(log_file_path)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    return logger


log_files = {
    "assistant_log": "assistant_log.txt",
}

loggers = {}

for logger_name, log_file_name in log_files.items():
    log_file_path = os.path.join(os.path.dirname(__file__), "..", "data", log_file_name)
    logger = configure_logger(logger_name, log_file_path)
    loggers[logger_name] = logger
