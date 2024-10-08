# Study Buddy

Study Buddy is a Streamlit application designed to facilitate interaction with research papers using OpenAI's Assistants API. This project demonstrates proficiency in Python development, Object-Oriented Programming, API integration, logging, and environment management.

## Project Overview

"Study Buddy" is an interactive platform designed to facilitate engagement with research papers through the use of OpenAI's GPT-4 model. The core functionality is powered by OpenAI's Assistants API, which at the time of this project, is currently in beta. This README provides a comprehensive overview of the project, the technologies used, and the key learning experiences gained during its development.

## Technologies Used

- Python: The programming language used to build the application.
- Streamlit: For creating the web-based user interface.
- OpenAI's Assistants API: Leveraged for advanced AI capabilities. The API is in beta and offers cutting-edge features for handling and processing information.

## Project Structure

- `main.py`: Entry point of the application that initializes the Streamlit interface and manages user interactions.
- `AssistantManager.py`: Contains the `AssistantManager` class responsible for managing interactions with the OpenAI API and handling file uploads.
- `config/logging.py`: Configures logging for different components of the application.
- `config/environment.py`: Manages environment variable loading and configuration.

## Setup

### Prerequisites

- Python 3.12 or later
- Virtual environment (`venv`)
- Streamlit
- OpenAI Python client

### Installation

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Create and activate a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file in the root directory of the project:**

   ```env
   OPENAI_API_KEY=<your-openai-api-key>
   ```

5. **Run the application:**

   ```bash
   streamlit run main.py
   ```

## Usage

1. **Upload Files**: Use the file uploader in the sidebar to upload PDF, DOCX, or TXT files.
2. **Start Chatting**: Click "Start chatting..." to initiate a conversation with the assistant.
3. **Interact with Assistant**: Ask questions or request summaries of the uploaded documents.

## Challenges and Learnings

- Beta API Integration: Working with a beta API involved navigating incomplete documentation and adapting to evolving features. This experience highlighted the importance of flexibility and self-reliance when using new and rapidly changing technologies.
- Custom Error Handling: Developing robust error handling and logging mechanisms was essential for dealing with the challenges presented by the beta API.

## Screenshots
![Study Buddy - Chat with your research paper](https://github.com/user-attachments/assets/378c5738-ed41-414b-9eaf-ac10a65a5738)
