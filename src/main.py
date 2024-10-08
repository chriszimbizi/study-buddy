# Standard library imports
import os
import streamlit as st

# Third-party imports
from AssistantManager import AssistantManager
from config.logging import configure_loggers
from config.environment import load_environment
import utils
import openai


def main():

    # Load environment and initialize OpenAI API and client
    openai_api_key = load_environment()
    client = openai.OpenAI(api_key=openai_api_key)

    # Initialize AssistantManager
    model = "gpt-4o"
    loggers = configure_loggers()

    manager = AssistantManager(model=model, client=client, loggers=loggers)

    manager.create_assistant(
        name="Study Assistant",
        instructions="""You are a helpful study assistant who knows a lot about understanding research papers. Your role is to summarize papers, clarify terminology within context, and extract key figures and data. Cross-reference information for additional insights and answer related questions comprehensively. Analyze the papers, noting strengths and limitations. Respond to queries effectively, incorporating feedback to enhance your accuracy. Handle data securely and update your knowledge base with the latest research. Adhere to ethical standards, respect intellectual property, and provide users with guidance on any limitations. Maintain a feedback loop for continuous improvement and user support. Your ultimate goal is to facilitate a deeper understanding of complex scientific material, making it more accessible and comprehensible.""",
        tools=[{"type": "file_search"}],
    )

    # === Streamlit sessions === #

    # Assistant ID
    st.session_state.assistant_id = manager.assistant_id

    # Dictionary to store vector store IDs
    if "vector_store_id_list" not in st.session_state:
        st.session_state.vector_store_id_list = []

    # Directory for uploaded files
    if "uploaded_file_paths" not in st.session_state:
        st.session_state.uploaded_file_paths = []

    if "file_uploader_key" not in st.session_state:
        st.session_state["file_uploader_key"] = 0

    # Start chat button
    if "start_chat" not in st.session_state:
        st.session_state.start_chat = False

    # Thread ID
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = None

    # === Streamlit front-end === #

    # Setup
    st.set_page_config(
        page_title="Study Buddy - Chat with your research paper",
        page_icon=":books:",
    )

    # Display uploaded file names
    if manager.vector_store_id in manager.file_metadata:
        st.sidebar.write("Files in Vector Store:")
        for index, file_info in enumerate(
            manager.file_metadata[manager.vector_store_id]
        ):
            file_name = os.path.basename(file_info["file_path"])
            st.sidebar.write(f"{index + 1}. {file_name}")

    # === Sidebar for file uploads === #

    # File uploads directory
    upload_directory = "../files/uploads"
    if not os.path.exists(upload_directory):
        os.makedirs(upload_directory, exist_ok=True)

    files_to_upload = st.sidebar.file_uploader(
        "Upload files",
        key="file_uploader",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
    )

    if st.sidebar.button("Upload files"):
        if not files_to_upload:
            st.sidebar.warning("No files found. Please select a file to upload.")
        else:
            for file_to_upload in files_to_upload:
                file_path = os.path.join(upload_directory, file_to_upload.name)
                with open(file_path, "wb") as f:
                    f.write(file_to_upload.getbuffer())
                    st.session_state.uploaded_file_paths.append(file_path)

            # Create or update vector store and upload files
            manager.create_vector_store(name="Study Buddy Vector Store")
            st.session_state.vector_store_id_list.append(
                manager.vector_store_id
            )  # Add vector store ID to session state
            manager.upload_files_to_vector_store(st.session_state.uploaded_file_paths)

            # Update the assistant with the vector store
            manager.update_assistant_with_vector_store()

            st.sidebar.success("Files uploaded and vector store updated successfully!")

    # Clear uploaded files
    if manager.vector_store_has_files() or utils.has_files(upload_directory):
        if st.sidebar.button("Clear uploaded files"):
            # Delete local uploaded files
            deleted_file_paths = manager.clear_vector_store()
            if deleted_file_paths:
                for file_path in deleted_file_paths:
                    if os.path.isfile(file_path):
                        os.remove(file_path)

            # Clear session state
            st.session_state.uploaded_file_paths = []
            st.session_state.file_uploader_key += 1  # force re-render and reset
            st.rerun()  # force re-run

    # Start chat button
    if st.sidebar.button("Start chatting..."):
        if manager.vector_store_has_files():
            st.session_state.start_chat = True

            # Create a new thread for the assistant to use
            thread = manager.create_thread()
            st.session_state.thread_id = thread.id
        else:
            st.sidebar.warning("No files found. Please upload a file to get started.")

    # === Main interface === #

    st.title("Study Buddy")
    st.write("A new way to engage with your research paper.")

    # Check sessions
    if st.session_state.start_chat:
        if "openai_model" not in st.session_state:
            st.session_state.openai_model = manager.model
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Show existing messages (if any)
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input for the user
        if prompt := st.chat_input("What would you like to know?"):
            # Add message to session state and display in chat
            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": prompt,
                }
            )
            with st.chat_message("user"):
                st.markdown(prompt)

            # Add message to existing thread
            manager.add_message_to_thread(
                role="user",
                content=prompt,
            )

            # Create a run with additional instructions
            manager.run_assistant(
                "Please answer the questions using the knowledge provided in the files. when adding additional information, make sure to distinguish it with bold or underlined text."
            )

            # Show spinner while waiting for run completion
            with st.spinner("Thinking..."):
                manager.wait_for_run_completion()
                # manager.log_run_steps()

                # Retrieve assistant messages at Run completion
                assistant_messages = manager.get_messages()

                # Process and display messages
                if assistant_messages:
                    # Process and display latest message
                    message = manager.format_message(assistant_messages[0])
                    st.session_state.messages.append(
                        {"role": "assistant", "content": message}
                    )
                    with st.chat_message("assistant"):
                        st.markdown(message, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
