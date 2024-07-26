import os

# Third-party imports
from dotenv import load_dotenv


def load_environment() -> str | None:
    """
    Load the environment variables from the .env file.

    Returns:
    - str | None: The OpenAI API key. None if the key is not found.
    """
    dotenv_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "data",
        ".env",
    )
    load_dotenv(dotenv_path)

    return os.getenv("OPENAI_API_KEY")
