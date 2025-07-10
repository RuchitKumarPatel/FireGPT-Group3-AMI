# 🔥 FireGPT - Wildfire Response Assistant

FireGPT is an advanced, conversational AI assistant designed to help firefighters and emergency response coordinators. It provides real-time, data-driven action plans and tactical guidance for battling wildfires.

## 📖 What FireGPT Does

This application uses a **Retrieval-Augmented Generation (RAG)** pipeline to deliver accurate and context-aware information. When a user asks a question or describes a situation, FireGPT:

1.  **Understands the Query:** It interprets the user's request for information (e.g., "What is the best way to handle a flank fire in a dense forest?").
2.  **Retrieves Relevant Knowledge:** It queries a specialized knowledge base of firefighting documents (located in the `wildfire_docs/` directory) using a high-speed FAISS vector index. This ensures the information is based on established doctrine and operational guides.
3.  **Generates Actionable Answers:** The AI synthesizes the retrieved information to generate a clear, concise, and actionable response, helping teams on the ground make informed decisions quickly.

The goal is to bridge the gap between complex firefighting documentation and the immediate, critical needs of personnel in the field.

-----

## 🚀 Getting Started

To run FireGPT on your local machine, you can use Docker (recommended), Conda, or a standard Python virtual environment.

### Prerequisites

  - Git
  - Docker (for Docker method)
  - Conda (for Conda method)
  - Python 3.9+ (for venv method)

### Option 1: Run with Docker (Recommended)

This is the easiest and most reliable way to get FireGPT running.

1.  **Clone the repository:**

    ```bash
    git clone <your-repository-url>
    cd FireGPT
    ```

2.  **Build the Docker image:**

    ```bash
    docker build -t firegpt .
    ```

3.  **Run the Docker container:**

    ```bash
    docker run -p 5000:5000 firegpt
    ```

4.  Open your browser and navigate to `http://127.0.0.1:5000`.

### Option 2: Run with Conda

1.  **Clone the repository and navigate into it.**

    ```bash
    git clone <your-repository-url>
    cd FireGPT
    ```

2.  **Create and activate the Conda environment:**

    ```bash
    conda env create -f environment.yml
    conda activate firegpt
    ```

3.  **Run the application:**

    ```bash
    python app.py
    ```

4.  Open your browser and navigate to `http://127.0.0.1:5000`.

### Option 3: Run with Python venv + pip

1.  **Clone the repository and navigate into it.**
    ```bash
    git clone <your-repository-url>
    cd FireGPT
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```
3.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Run the application:**
    ```bash
    python app.py
    ```
5.  Open your browser and navigate to `http://127.0.0.1:5000`.

-----

## 🌟 Key Features

### 💬 Chat Interface

  - Modern, responsive design with real-time typing indicators.
  - Support for file uploads to supplement queries.
  - Full message history and auto-scrolling.

### 📁 File Upload

  - Drag & drop support for multiple files.
  - Validation for file types and size limits.
  - Progress indicators for a smooth user experience.

### 🗺️ Map Integration

  - Includes a placeholder for a world map.
  - Ready for integration with real-time fire data overlays.

### 🔔 Notifications

  - Toast notifications for success, error, and warning states.
  - Smooth animations and auto-dismiss functionality.

-----

## 📁 Directory Structure

```
.
├── app.py                  # Main Python (Flask/FastAPI) application
├── Dockerfile              # Docker container configuration
├── environment.yml         # Conda environment definition
├── requirements.txt        # Python package requirements
├── faiss_index/            # Stores the FAISS vector index for documents
├── local_models/           # Placeholder for local LLM/embedding models
├── wildfire_docs/          # The knowledge base for the RAG system
│   ├── aerial_firefighting.txt
│   └── firefighting_action_plan.txt
└── static/                 # All frontend assets
    ├── css/
    ├── js/
    └── index.html
```

-----

## 🔧 Development

### Adding New Features

1.  Add component styles to `static/css/components.css`.
2.  Add utility functions to `static/js/utils.js` if needed.
3.  Add configuration options to `static/js/config.js`.
4.  Implement the core feature logic in `static/js/app.js`.

### Adding to the Knowledge Base

  - Simply add new `.txt` files to the `wildfire_docs/` directory.
  - You will need to re-run the indexing script (not detailed here) to update the `faiss_index` for the new documents to be included in responses.

-----

## 📦 Deployment

The static files and server are ready for production deployment:

  - **Containerized:** The `Dockerfile` ensures consistent deployment anywhere.
  - **Cache-Friendly:** Separated CSS and JS files for better browser caching.
  - **Optimized:** Frontend assets are structured for minification and CDN compatibility.

## 🔒 Security

  - **Input Validation:** The backend should validate all inputs.
  - **HTML Sanitization:** User-generated content displayed in the chat is sanitized to prevent XSS attacks.
  - **File Validation:** File uploads are validated by type and size to prevent malicious uploads.