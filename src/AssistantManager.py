import json
import time
from typing import Iterable, List, Literal
import openai
from openai.types.beta import AssistantToolParam
import os


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

    def __init__(
        self,
        model: str,
        client: openai.OpenAI,
        loggers: dict,
        metadata_file="../files/metadata.json",
    ) -> None:
        self.client = client
        self.model = model
        self.assistant = None
        self.thread = None
        self.vector_store = None
        self.run = None
        self.loggers = loggers
        self.metadata_file = metadata_file
        self.file_metadata = self.load_file_metadata()

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

    def load_file_metadata(self) -> dict:
        """
        Load the file metadata from the metadata file.

        Returns:
        - dict: The file metadata dictionary.
        """
        if (
            os.path.exists(self.metadata_file)
            and os.path.getsize(self.metadata_file) > 0
        ):
            try:
                with open(self.metadata_file, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                self.loggers["file_logger"].error(
                    "Invalid JSON in metadata file. Returning empty metadata."
                )
                return {}
        else:
            return {}

    def save_file_metadata(self):
        with open(self.metadata_file, "w") as f:
            json.dump(self.file_metadata, f)

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

            # Store metadata for each file
            file_ids = self.get_file_ids_from_vector_store(self.vector_store_id)

            if file_ids:
                for file_path, file_id in zip(file_paths, file_ids):
                    # Add to the file metadata dictionary
                    if self.vector_store_id not in self.file_metadata:
                        self.file_metadata[self.vector_store_id] = []

                    self.file_metadata[self.vector_store_id].append(
                        {
                            "file_path": file_path,
                            "file_id": file_id,
                        }
                    )

            # Save metadata to persistent storage
            self.save_file_metadata()

    def get_file_ids_from_vector_store(self, vector_store_id: str) -> List[str] | None:
        """
        Retrieve the file IDs from the vector store.

        Parameters:
        - vector_store_id (str): The ID of the vector store.

        Returns:
        - List[str] | None: The list of file IDs from the vector store. None if no files are found.
        """
        if self.vector_store_id:
            self.loggers["file_logger"].info("Retrieving files from vector store...")
            response = self.client.beta.vector_stores.files.list(
                vector_store_id=vector_store_id
            )
            file_ids = [file.id for file in response.data]
            self.loggers["file_logger"].info(
                f"Retrieved {len(file_ids)} file IDs from the vector store."
            )
            return file_ids

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

    def clear_vector_store(self) -> List[str] | None:
        """
        Clear the vector store and return the list of deleted files.

        Returns:
        - List[str] | None: The list of deleted files. None if no files are found.
        """
        deleted_file_paths = []

        try:
            # Load metadata
            with open(self.metadata_file, "r") as f:
                data = json.load(f)

            # Delete files from vector store
            for file_metadata in data.get(self.vector_store_id, []):
                file_path = file_metadata.get("file_path")
                file_id = file_metadata.get("file_id")
                file_name = os.path.basename(file_path)
                try:
                    self.client.beta.vector_stores.files.delete(
                        file_id=file_id, vector_store_id=self.vector_store_id
                    )
                    logger = self.loggers["file_logger"]
                    logger.info(f"Deleted '{file_name}' from vector store.")
                    deleted_file_paths.append(file_path)  # Track deleted file paths
                except Exception as e:
                    logger.error(
                        f"Failed to delete '{file_name}' from vector store: {e}"
                    )

            # Clear metadata file
            with open(self.metadata_file, "w") as f:
                json.dump({}, f)
            logger.info("Cleared all metadata from the file.")

            return deleted_file_paths

        except Exception as e:
            logger = self.loggers["file_logger"]
            logger.error(f"An error occurred while clearing vector store: {e}")

    def vector_store_has_files(self) -> bool:
        """
        Check if the vector store has files.

        Returns:
        - bool: True if the vector store has files, False otherwise.
        """
        vector_store_list = self.client.beta.vector_stores.files.list(
            vector_store_id=self.vector_store_id
        )
        if vector_store_list.data:
            return True
        return False

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
