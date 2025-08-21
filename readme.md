# Local RAG Chatbot with Semantic Search Powered by Qdrant

[![Python Version](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

English | <a href="https://github.com/Talen-520/Qdrant-Local-RAG/blob/main/readme_CN.md">中文</a>

This is a fully-featured, local RAG (Retrieval-Augmented Generation) chat application. It uses [Ollama](https://ollama.com/) to run open-source Large Language Models (like Gemma) locally and leverages the [Qdrant](https://qdrant.tech/) vector database for efficient semantic search. The entire experience is delivered through a modern web UI.

The entire application runs completely on your local machine, ensuring data privacy and security.

---

## 🏛️ Architecture

This project is composed of four core components:

1.  **🧠 Local Large Language Model (LLM)**: Uses **Ollama** to serve and manage local open-source models (e.g., Google's `gemma`).
2.  **📦 Vector Database (Vector DB)**: Uses **Qdrant**, running via Docker, to store vector embeddings of text.
3.  **⚙️ Backend Service**: A **Python** server that handles business logic, connecting Ollama and Qdrant. It uses `uv` for package management.
4.  **🎨 Frontend UI**: A **Node.js** web application located in the `qdrant-web/` directory that provides the user chat interface.

## 📋 Prerequisites

Before you begin, please ensure you have all the following tools installed on your system:

* **Git**: For cloning the repository.
* **Python 3.13+**: [Official Download](https://www.python.org/downloads/).
* **[uv](https://github.com/astral-sh/uv)**: An extremely fast Python package installer and resolver.
    ```bash
    # macOS / Linux
    curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh
    # Windows
    powershell -c "irm [https://astral.sh/uv/install.ps1](https://astral.sh/uv/install.ps1) | iex"
    ```
* **Node.js**: v18 or later. [Official Download](https://nodejs.org/).
* **Docker**: For running the Qdrant vector database. [Official Download](https://www.docker.com/products/docker-desktop/).
* **[Ollama](https://ollama.com/)**: For running the LLM locally. Please download and install it from the official website.

## 🚀 Setup and Running Guide

Follow these steps carefully to set up and launch the application.

### Step 1: Clone Repository & Install AI Model

1.  **Clone this repository**
    ```bash
    git clone https://github.com/Talen-520/Qdrant-Local-RAG.git
    cd Qdrant-Local-RAG
    ```

2.  **Download and run the Ollama model**
    After installing Ollama, run the following command in your terminal to download and run the `gemma` model for the first time. This may take a while, depending on your internet connection and hardware.
    ```bash
    ollama run gemma
    ```
    > You can replace `gemma` with any other model supported by Ollama, such as `llama3`, `mistral`, etc.

### Step 2: Launch the Qdrant Vector Database

We will use Docker to run the Qdrant service in a clean, isolated environment.

1.  **Pull the Qdrant image from Docker Hub**
    ```bash
    docker pull qdrant/qdrant
    ```

2.  **Create and run the container**
    This command creates a container named `local-qdrant-container` and configures it to persist data in a `qdrant_storage` folder within your project directory.
    ```bash
    # For macOS / Linux
    docker run -d --name local-qdrant-container -p 6333:6333 -p 6334:6334 -v "$(pwd)/qdrant_storage:/qdrant/storage" qdrant/qdrant

    # For Windows (PowerShell)
    docker run -d --name local-qdrant-container -p 6333:6333 -p 6334:6334 -v "${PWD}/qdrant_storage:/qdrant/storage" qdrant/qdrant
    ```

### Step 3: Install Project Dependencies

1.  **Install Python backend dependencies**
    From the project's root directory, run `uv sync`. This will automatically create a virtual environment and install all dependencies defined in `pyproject.toml`.
    ```bash
    uv sync
    ```

2.  **Install Node.js frontend dependencies**
    ```bash
    cd qdrant-web
    npm install
    cd ..
    ```

### Step 4: Launch All Services

With all components ready, it's time to start the application. **It's recommended to open three separate terminal windows** to run each service.

1.  **Terminal 1: Ensure Qdrant is running**
    If the container was stopped previously, start it with this command.
    ```bash
    docker start local-qdrant-container
    ```
    > You can check if the container is running with the `docker ps` command.

2.  **Terminal 2: Start the Backend Server**
    From the project's **root directory**, run:
    ```bash
    uv run backend/server.py
    ```

3.  **Terminal 3: Start the Frontend Web UI**
    From the project's **root directory**, run:
    ```bash
    cd qdrant-web
    npm run dev
    ```

### Step 5: Start Chatting!

Once all services are running successfully, open your web browser and navigate to:

➡️ **http://localhost:5173/**

You can now begin interacting with your local RAG chatbot!

## ⚙️ Service Management

#### Stopping the Qdrant Container
When you are finished, you can stop the database container to free up system resources.
```bash
docker stop local-qdrant-container