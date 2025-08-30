# Backend Refactoring Plan

## 1. Introduction

The current backend architecture is monolithic, with the `client.py` file handling API communication, business logic, and caching. This lack of separation of concerns makes the codebase difficult to maintain, test, and scale. This plan outlines a phased approach to refactor the backend into a more robust, service-oriented architecture.

## 2. High-Level Goals

*   **Improve Maintainability:** Decouple components to make them easier to understand and modify.
*   **Enhance Testability:** Isolate business logic from external dependencies like the database and the Sleeper API.
*   **Increase Scalability:** Lay the foundation for a more scalable and performant application.
*   **Introduce Data Validation:** Implement Pydantic models to ensure data consistency and catch errors early.

## 3. Proposed Architecture

The refactored architecture will consist of the following layers:

*   **API Layer (`main.py`):** Responsible for handling HTTP requests and responses. It will delegate business logic to the service layer.
*   **Service Layer (`backend/services/`):** Contains the core business logic of the application. It will be split into multiple services based on functionality (e.g., `league_service.py`, `player_service.py`, `transaction_service.py`).
*   **Client Layer (`client.py`):** A pure API client responsible for making requests to the Sleeper API. It will not contain any business logic or caching.
*   **Data/Cache Layer (`database.py`, `cache.py`):** Manages database interactions and caching.
*   **Configuration (`config.py`):** Centralizes application configuration.
*   **Models (`models.py`):** Defines Pydantic models for data validation and structuring.

## 4. Phased Implementation

### Phase 1: Service-Oriented Refactoring

1.  **Create Directories:**
    *   `mkdir -p backend/services`
    *   `mkdir -p backend/models`

2.  **Refactor `client.py`:**
    *   Move all business logic and data transformation functions to a new `backend/services/sleeper_service.py`.
    *   The `client.py` file should only contain functions that make direct calls to the Sleeper API.

3.  **Create `backend/services/sleeper_service.py`:**
    *   This file will initially house the business logic moved from `client.py`.

4.  **Introduce Pydantic Models:**
    *   Create a `backend/models/sleeper.py` file.
    *   Define Pydantic models for the data structures returned by the Sleeper API (e.g., `User`, `League`, `Draft`, `Player`).
    *   Use these models in the service and API layers to validate and type-hint data.

5.  **Update `main.py`:**
    *   Modify the API endpoints to call the new `sleeper_service.py` instead of `client.py`.

### Phase 2: Caching and Database Layer

1.  **Centralize Database Connection:**
    *   Modify `database.py` to use a connection pool (e.g., `aiosqlite.create_pool`) to manage database connections more efficiently.

2.  **Decouple Caching:**
    *   Create a `backend/cache.py` file.
    *   Move the caching logic from `client.py` into this new file.
    *   The caching layer will use the database connection pool.

### Phase 3: Configuration Management

1.  **Create `config.py`:**
    *   Create a `backend/config.py` file.
    *   Move constants like `API_URL` and `CACHE_TTL_SECONDS` into this file.
    *   Use a library like Pydantic's `BaseSettings` to manage environment variables.

### Phase 4: Splitting the `sleeper_service.py` file

1.  **Split `sleeper_service.py`:**
    *   Split the `sleeper_service.py` file into multiple files based on functionality. For example:
        *   `backend/services/league_service.py`
        *   `backend/services/player_service.py`
        *   `backend/services/transaction_service.py`
        *   `backend/services/draft_service.py`
        *   `backend/services/roster_service.py`
        *   `backend/services/analysis_service.py`

## 5. Conclusion

This phased refactoring will transform the backend into a more modular, maintainable, and scalable application. By separating concerns and introducing modern development practices, we will improve the overall quality of the codebase and set it up for future growth.
