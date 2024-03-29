# Standard library imports
import logging
from logging import Logger
import os
import time
from typing import BinaryIO, Literal
import streamlit as st

# Third-party imports
from dotenv import load_dotenv
import openai

# Load environment
dotenv_path = os.path.join(
    os.path.dirname(__file__),
    "..",
    "data",
    ".env",
)
load_dotenv(dotenv_path)

# Initialize OpenAI API
openai_api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=openai_api_key)
model = "gpt-4-1106-preview"


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


# Configure loggers
log_files = {
    "assistant_logger": "assistant_log.txt",
    "thread_logger": "thread_log.txt",
    "run_logger": "run_log.txt",
}

loggers = {}

for logger_name, log_file_name in log_files.items():
    log_file_path = os.path.join(os.path.dirname(__file__), "..", "logs", log_file_name)
    logger = configure_logger(logger_name, log_file_path)
    loggers[logger_name] = logger


class AssistantManager:
    """
    Manages an OpenAI Assistant to have conversations and call functions.

    Creates an assistant and thread, sends messages to the thread, runs the
    assistant, calls functions based on the assistant's requests, waits for
    completion, and retrieves the summary.
    """

    assistant_id = "asst_htPPJ3OoFsxFNmbpSXq25HXq"
    thread_id = "thread_Dh20rz1miZ9L5q0wJhUKNosz"

    def __init__(self, model: str = model) -> None:
        self.client = client
        self.model = model
        self.assistant = None
        self.thread = None
        self.run = None

        # Check for existing assistant and thread
        if AssistantManager.assistant_id:
            self.assistant = self.client.beta.assistants.retrieve(
                assistant_id=AssistantManager.assistant_id
            )
            loggers["assistant_logger"].info(
                f"Found existing assistant with ID: {AssistantManager.assistant_id}"
            )
        if AssistantManager.thread_id:
            self.thread = self.client.beta.threads.retrieve(
                thread_id=AssistantManager.thread_id
            )
            loggers["thread_logger"].info(
                f"Found existing thread with ID: {AssistantManager.thread_id}"
            )

    def create_assistant(self, name: str, instructions: str, tools: list, files: list):
        """
        Create an assistant using the given model and file.

        Parameters:
        - name (str): The name of the Assistant
        - instructions (str): The Instructions to use
        - tools (list): The Tools to use
        - files: The Files to use
        """

        if not self.assistant:
            loggers["assistant_logger"].info("Creating assistant...")
            assistant = client.beta.assistants.create(
                model=self.model,
                name=name,
                instructions=instructions,
                tools=tools,
                file_ids=[file.id for file in files],
            )
            self.assistant = assistant
            self.assistant_id = assistant.id
            loggers["assistant_logger"].info(
                f"Created new Assistant with ID: {self.assistant_id}"
            )

    def create_thread(self):
        """
        Create a thread for the Assistant to use.

        Returns:
        - str: The created thread.
        """
        if not self.thread:
            loggers["thread_logger"].info("Creating thread...")
            thread = client.beta.threads.create()
            self.thread = thread
            self.thread_id = thread.id
            loggers["thread_logger"].info(
                f"Created new Thread with ID: {self.thread_id}"
            )

    def add_message_to_thread(
        self,
        role: Literal["user"],
        content: str,
    ) -> None:
        """
        Add a message to the Assistant's Thread.

        Parameters:
        - thread_id (str): The ID of the thread where the message will be posted.
        - role (Literal["user"]): The role of the message.
        - content (str): The content of the message.
        """
        if self.thread:
            loggers["thread_logger"].info("Adding message to Thread...")
            client.beta.threads.messages.create(
                thread_id=self.thread_id,
                role=role,
                content=content,
            )
            loggers["thread_logger"].info("Message added.")

    def run_assistant(self, instructions: str) -> None:
        """
        Run the Assistant.

        Parameters:
        - instructions (str): Instructions for the Assistant.
        """
        if self.assistant and self.thread:
            self.run = self.client.beta.threads.runs.create(
                thread_id=self.thread_id,
                assistant_id=self.assistant_id,
                instructions=instructions,
            )

    def wait_for_run_completion(self, sleep_interval=5):
        """
        Waits for a run to complete by checking its status periodically.

        Parameters:
        - sleep_interval: Time in seconds to wait between checks.
        """
        while True:
            try:
                if self.run:
                    run = client.beta.threads.runs.retrieve(
                        thread_id=self.thread_id, run_id=self.run.id
                    )
                    if run.completed_at:
                        elapsed_time = run.completed_at - run.created_at
                        formatted_elapsed_time = time.strftime(
                            "%H:%M:%S", time.gmtime(elapsed_time)
                        )
                        loggers["run_logger"].info(
                            f"Run completed in {formatted_elapsed_time}"
                        )
                        # Retrieve messages at Run completion
                        messages = client.beta.threads.messages.list(
                            thread_id=self.thread_id
                        )
                        last_message = messages.data[0]
                        response = last_message.content[0].text.value
                        print(f"Assistant Response: {response}")
                        break
            except Exception as e:
                loggers["run_logger"].error(
                    f"An error occurred while retrieving the run: {e}"
                )
                break
            loggers["run_logger"].info("Waiting for run to complete...")
            time.sleep(sleep_interval)

    # FIXME: Buggy
    def log_run_steps(self):
        """
        Log steps of a run.
        """

        run_steps = client.beta.threads.runs.list(thread_id=self.thread_id)
        for step in run_steps["data"]:
            step_type = step["step_details"]["type"]
            loggers["run_logger"].info(f"Run Step: {step_type}")


def main():
    manager = AssistantManager()

    # Upload file to OpenAI embeddings
    file_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "files",
        "Black Study, Black Struggle - Boston Review.pdf",
    )
    file = client.files.create(
        file=open(file_path, "rb"),
        purpose="assistants",
    )

    # Create Assistant
    manager.create_assistant(
        name="Study Assistant",
        instructions="""You are a helpful study assistant who knows a lot about understanding research papers. Your role is to summarize papers, clarify terminology within context, and extract key figures and data. Cross-reference information for additional insights and answer related questions comprehensively. Analyze the papers, noting strengths and limitations. Respond to queries effectively, incorporating feedback to enhance your accuracy. Handle data securely and update your knowledge base with the latest research. Adhere to ethical standards, respect intellectual property, and provide users with guidance on any limitations. Maintain a feedback loop for continuous improvement and user support. Your ultimate goal is to facilitate a deeper understanding of complex scientific material, making it more accessible and comprehensible.""",
        tools=[{"type": "retrieval"}],
        files=[file],
    )

    # Create Thread
    thread = manager.create_thread()

    # Create Message on Thread
    message = "Summarize what Robin D.G Kelley is trying to say and the criticisms he brings up."
    manager.add_message_to_thread(
        role="user",
        content=message,
    )

    # Run Assistant
    manager.run_assistant("Please address the user as Chris")

    # Wait for Run completion
    manager.wait_for_run_completion()
    # manager.log_run_steps()


if __name__ == "__main__":
    main()
