# Federal Registry Document Search System

A modern, AI-powered search system for Federal Registry documents that combines FastAPI, MySQL, and Ollama for efficient document processing and semantic search capabilities.

## Architecture Overview

The system is built with a modular architecture consisting of several key components:

### Core Components

1. **Data Pipeline** (`data_pipeline/`)
   - Handles document ingestion from the Federal Registry API
   - Processes and stores documents in the database
   - Implements efficient data processing workflows

2. **Database Layer** (`database/`)
   - MySQL-based storage system
   - Manages document metadata and content
   - Handles database connections and queries

3. **API Layer** (`api/`)
   - FastAPI-based REST API
   - Provides endpoints for document search and retrieval
   - Implements authentication and rate limiting

4. **Agent System** (`agent/`)
   - Manages document processing workflows
   - Coordinates between different system components
   - Handles asynchronous operations

5. **Web Interface** (`templates/` and `static/`)
   - User-friendly web interface for document search

### Key Design Choices

1. **Asynchronous Architecture**
   - Uses `aiohttp` and `aiomysql` for non-blocking I/O operations
   - Enables high concurrency and better performance
   - Efficient handling of multiple simultaneous requests

2. **Local LLM Integration**
   - Utilizes Ollama for local language model processing
   - Enables semantic search capabilities without external API dependencies
   - Configurable model selection through environment variables

3. **Modular Design**
   - Clear separation of concerns between components
   - Easy to extend and maintain
   - Independent testing and deployment of components

## Prerequisites

- Python 3.8+
- MySQL Server
- Ollama (with desired model pulled)
- Virtual environment (recommended)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd federal-registry-search
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file with the following variables:
   ```
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=your_username
   DB_PASSWORD=your_password
   DB_NAME=federal_registry
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama3
   API_HOST=localhost
   API_PORT=8000
   ```

## Running the Application

1. Start the MySQL server:
2. Start Ollama:
   ```bash
   ollama serve
   ```
3. Run the FastAPI application:
   ```bash
   uvicorn main:app --host localhost --port 8000 --reload
   ```
4. Access the web interface:
   Open your browser and navigate to `http://localhost:8000`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

