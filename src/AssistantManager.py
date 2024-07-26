import time
from typing import Iterable, List, Literal
import openai
from openai.types.beta import AssistantToolParam


class AssistantManager:
    """
    Manages an OpenAI Assistant to have conversations and call functions.

    Creates an assistant and thread, sends messages to the thread, runs the
    assistant, calls functions based on the assistant's requests, waits for
    completion, and retrieves the summary.
    """

    assistant_id = "asst_ICnLjgfneeQFYrRmSckG2MDL"
    thread_id = "thread_IMy8rg00uxj40kuS0L9RApbN"
    vector_store_id = "vs_fhVKvG244ieSCE6NIcjqcyYd"

    def __init__(self, model: str, client: openai.OpenAI, loggers: dict) -> None:
        self.client = client
        self.model = model
        self.assistant = None
        self.thread = None
        self.vector_store = None
        self.run = None
        self.loggers = loggers

        # Check for existing assistant, thread, and vector store
        if AssistantManager.assistant_id:
            self.assistant = self.client.beta.assistants.retrieve(
                assistant_id=AssistantManager.assistant_id
            )
            self.loggers["assistant_logger"].info(
                f"Found existing assistant with ID: {AssistantManager.assistant_id}"
            )
        if AssistantManager.thread_id:
            self.thread = self.client.beta.threads.retrieve(
                thread_id=AssistantManager.thread_id
            )
            self.loggers["thread_logger"].info(
                f"Found existing thread with ID: {AssistantManager.thread_id}"
            )
        if AssistantManager.vector_store_id:
            self.vector_store = self.client.beta.vector_stores.retrieve(
                vector_store_id=AssistantManager.vector_store_id
            )
            self.loggers["file_logger"].info(
                f"Found existing vector store with ID: {AssistantManager.vector_store_id}"
            )

    def create_assistant(
        self, name: str, instructions: str, tools: Iterable[AssistantToolParam]
    ):
        """
        Create an assistant using the given model and tools.
        """
        if not self.assistant:
            self.loggers["assistant_logger"].info("Creating assistant...")
            assistant = self.client.beta.assistants.create(
                model=self.model,
                name=name,
                instructions=instructions,
                tools=tools,
            )
            self.assistant = assistant
            self.assistant_id = assistant.id
            self.loggers["assistant_logger"].info(
                f"Created new Assistant with ID: {self.assistant_id}"
            )

    def create_vector_store(self, name: str):
        """
        Create a vector store.

        Parameters:
        - name (str): The name of the vector store.
        """
        if not self.vector_store_id:
            self.loggers["file_logger"].info("Creating vector store...")
            vector_store = self.client.beta.vector_stores.create(name=name)
            self.vector_store_id = vector_store.id
            self.loggers["file_logger"].info(
                f"Created new Vector Store with ID: {self.vector_store_id}"
            )

    def upload_files_to_vector_store(self, file_paths: List[str]):
        """
        Upload files to the vector store.

        Parameters:
        - file_paths (List[str]): List of file paths to upload.
        """
        if self.vector_store_id:
            self.loggers["file_logger"].info("Uploading files to vector store...")
            file_streams = [open(file_path, "rb") for file_path in file_paths]
            file_batch = self.client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=self.vector_store_id, files=file_streams
            )
            self.loggers["file_logger"].info(f"File batch status: {file_batch.status}")
            self.loggers["file_logger"].info(
                f"File batch counts: {file_batch.file_counts}"
            )

    def update_assistant_with_vector_store(self):
        """
        Update the assistant to use the new vector store.
        """
        if self.vector_store_id:
            self.loggers["file_logger"].info("Updating assistant with vector store...")
            self.client.beta.assistants.update(
                assistant_id=self.assistant_id,
                tool_resources={
                    "file_search": {"vector_store_ids": [self.vector_store_id]}
                },
            )
            self.loggers["file_logger"].info("Assistant updated with vector store.")

    def create_thread(self):
        """
        Create a thread for the Assistant to use.

        Returns:
        - Thread: The created thread.
        """
        if not self.thread:
            self.loggers["thread_logger"].info("Creating thread...")
            thread = self.client.beta.threads.create()
            self.thread = thread
            self.thread_id = thread.id
            self.loggers["thread_logger"].info(
                f"Created new Thread with ID: {self.thread_id}"
            )
        return self.thread

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
            self.loggers["thread_logger"].info("Adding message to Thread...")
            self.client.beta.threads.messages.create(
                thread_id=self.thread_id,
                role=role,
                content=content,
            )
            self.loggers["thread_logger"].info("Message added.")

    def run_assistant(self, instructions: str) -> None:
        """
        Run the Assistant.

        Parameters:
        - instructions (str): Instructions for the Assistant.
        """
        if self.assistant and self.thread:
            self.run = self.client.beta.threads.runs.create_and_poll(
                thread_id=self.thread_id,
                assistant_id=self.assistant_id,
                instructions=instructions,
            )

    def get_messages(self):
        """
        Retrieve the messages from the Assistant.

        Returns:
        - List[Message] | None: The list of messages from the Assistant. None if no messages are found.
        """
        if self.run:
            messages = self.client.beta.threads.messages.list(thread_id=self.thread_id)
            messages = [message for message in messages if message.role == "assistant"]
            logger = self.loggers["run_logger"]
            logger.info(f"Retrieved {len(messages)} messages from the Assistant.")
            return messages

    # FIXME: Citations not working
    def format_message(self, message) -> str:
        """
        Format the message from the Assistant to include footnotes.

        Parameters:
        - message (Message): The message from the Assistant.

        Returns:
        - str: The formatted message.
        """
        # Extract the message content
        message_content = message.content[0].text
        annotations = message_content.annotations
        citations = []

        # Iterate over the annotations and add footnotes
        for index, annotation in enumerate(annotations):
            # Replace the text with a footnote
            message_content.value = message_content.value.replace(
                annotation.text, f" [{index + 1}]"
            )

            # Gather citations based on annotation attributes
            if file_citation := getattr(annotation, "file_citation", None):
                cited_file = self.client.files.retrieve(file_citation.file_id)
                citations.append(
                    f"[{index + 1}] {file_citation} from {cited_file.filename}"
                )

        # Add footnotes to the end of the message before displaying to user
        # message_content.value += "\n" + "\n\n".join(citations)
        message = message_content.value
        logger = self.loggers["run_logger"]
        logger.info(f"Message successfully formatted")
        return message

    def wait_for_run_completion(self, sleep_interval=5):
        """
        Waits for a run to complete by checking its status periodically.

        Parameters:
        - sleep_interval: Time in seconds to wait between checks.
        """
        while True:
            try:
                if self.run:
                    run = self.client.beta.threads.runs.retrieve(
                        thread_id=self.thread_id, run_id=self.run.id
                    )
                    if run.completed_at:
                        elapsed_time = run.completed_at - run.created_at
                        formatted_elapsed_time = time.strftime(
                            "%H:%M:%S", time.gmtime(elapsed_time)
                        )
                        self.loggers["run_logger"].info(
                            f"Run completed in {formatted_elapsed_time}"
                        )
                        # Retrieve messages at Run completion
                        messages = self.client.beta.threads.messages.list(
                            thread_id=self.thread_id
                        )
                        last_message = messages.data[0]
                        response = self.format_message(last_message)
                        break
            except Exception as e:
                self.loggers["run_logger"].error(
                    f"An error occurred while retrieving the run: {e}"
                )
                break
            self.loggers["run_logger"].info("Waiting for run to complete...")
            time.sleep(sleep_interval)

    # FIXME
    # def log_run_steps(self):
    #     """
    #     Log steps of a run.
    #     """

    #     run_steps = client.beta.threads.runs.list(thread_id=self.thread_id)
    #     for step in run_steps["data"]:
    #         step_type = step["step_details"]["type"]
    #         loggers["run_logger"].info(f"Run Step: {step_type}")
