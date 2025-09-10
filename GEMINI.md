## Project Overview

This is a billing system for an FTTH (Fiber to the Home) internet provider. It is built with a Python FastAPI backend and a Vue.js frontend. The system is designed to automate billing, manage customers, and handle payments.

**Backend:**

*   **Framework:** FastAPI
*   **Database:** SQLAlchemy with an async engine (likely PostgreSQL or MySQL)
*   **Authentication:** Token-based (likely JWT)
*   **Scheduled Jobs:** `apscheduler` is used for tasks like generating invoices, suspending services, and verifying payments.
*   **Real-time Features:** WebSockets are used for real-time notifications.

**Frontend:**

*   **Framework:** Vue.js
*   **Build Tool:** Vite
*   **UI Library:** Vuetify
*   **State Management:** Pinia
*   **Routing:** Vue Router
*   **Desktop App:** The project is configured to be packaged as a desktop application using Electron and Tauri.

## Building and Running

### Backend

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Set up environment variables:**
    *   Copy `.env.example` to `.env` and fill in the required values, especially the `DATABASE_URL`.
3.  **Run database migrations:**
    ```bash
    alembic upgrade head
    ```
4.  **Run the development server:**
    ```bash
    uvicorn app.main:app --reload
    ```

### Frontend

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```
2.  **Install dependencies:**
    ```bash
    npm install
    ```
3.  **Run the development server:**
    ```bash
    npm run dev
    ```

## Development Conventions

*   The backend is structured using FastAPI's router system, with each module in the `app/routers` directory corresponding to a specific feature.
*   The frontend uses a standard Vue.js project structure.
*   The project uses environment variables for configuration, which is a good practice for separating configuration from code.
*   Database migrations are managed with Alembic.
