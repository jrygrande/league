# GEMINI.md

## Project Overview

This project is a web application for exploring Sleeper fantasy football leagues. It provides a data-rich experience for tracking player history, transactions, and drafts to analyze manager performance.

The application follows a decoupled architecture:

*   **Backend:** A Python-based RESTful API built with the **FastAPI** framework. It fetches data from the public Sleeper API and exposes it to the frontend.
*   **Frontend:** A **Next.js** application using **TypeScript** and **shadcn/ui** components for a modern user interface.

The project is currently in the backend development phase.

## Building and Running

### 1. Setup the Environment

This project uses a Python virtual environment to manage dependencies.

*   **Create the virtual environment:**
    ```bash
    python3 -m venv .venv
    ```

*   **Activate the virtual environment:**
    ```bash
    source .venv/bin/activate
    ```

### 2. Install Dependencies

Dependencies are listed in `requirements.txt`.

*   **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### 3. Run the Backend Server

The backend is a FastAPI application run with `uvicorn`.

*   **Start the development server:**
    ```bash
    uvicorn backend.main:app --reload
    ```

The API will be available at `http://127.0.0.1:8000`, and the interactive documentation can be found at `http://127.0.0.1:8000/docs`.

## Development Conventions

*   **Dependency Management:** All Python dependencies are managed in the `requirements.txt` file. After installing a new package, update the file with:
    ```bash
    pip freeze > requirements.txt
    ```

*   **API Development:** The plan for API development is outlined in `API_DEVELOPMENT_PLAN.md`. Please consult this file before adding new endpoints.

*   **Code Style:** The backend code follows standard Python conventions. Asynchronous functions are used for I/O-bound operations (i.e., making requests to the Sleeper API).
