# BillingFtthV2

This project provides a billing system API for FTTH (Fiber To The Home) internet service providers, incorporating features for customer management, subscription handling, invoice generation, Mikrotik integration, and more.

## Features and Functionality

*   **Customer Management:** Create, read, update, and delete customer records, including contact information and service details.
*   **Subscription Management:** Manage customer subscriptions, including package assignments, billing cycles, and payment methods.
*   **Invoice Generation:** Automatically generate invoices based on customer subscriptions and billing cycles. Supports both 'Otomatis' (automatic) and 'Prorate' billing. Integrates with Xendit for payment processing and link generation.
*   **Mikrotik Integration:** Manage PPPoE secrets on Mikrotik routers, enabling service suspension and re-activation based on payment status. Includes retry mechanisms for failed syncs.
*   **Role-Based Access Control (RBAC):** Secure the application with granular permissions, controlling access to different features based on user roles (Admin, NOC, Finance, etc.).
*   **Inventory Management:** Track inventory items, types, and statuses, managing serial numbers, MAC addresses, and deployment locations.
*   **Reporting and Analytics:** Generate revenue reports, track customer growth, and monitor key performance indicators (KPIs) via interactive dashboards.
*   **System Settings:** Configure system-wide settings, such as maintenance mode and callback tokens.
*   **Activity Logging:** Track user actions (create, update, delete) for auditing and monitoring.
*   **Real-time Notifications:** Utilizes WebSockets for sending real-time notifications to relevant users (e.g., new payments received, new technical data, new customers)

## Technology Stack

*   **Backend:**
    *   Python 3.x
    *   FastAPI (for API development)
    *   SQLAlchemy (for database interaction)
    *   AsyncIO (for asynchronous operations)
    *   Alembic (for database migrations)
    *   Pydantic (for data validation and serialization)
    *   Passlib (for password hashing)
    *   jose (for JWT token management)
    *   python-dotenv (for managing environment variables)
    *   routeros-api (for Mikrotik router integration)
    *   httpx (for making HTTP requests, e.g., to Xendit)
    *   APScheduler (for scheduled jobs)
    *   dateutil (for date calculations)
    *   pytz (for timezone handling)
*   **Frontend:**
    *   Vue 3
    *   Vuetify 3
    *   Pinia (for state management)
    *   Axios (for API requests)
    *   ECharts (for charting)
    *   html2canvas (for exporting charts to PNG)
    *   mapbox-gl (for interactive maps)

## Prerequisites

*   Python 3.x
*   PostgreSQL database
*   Xendit account and API keys
*   Mikrotik router(s) with API access enabled
*   Node.js and npm (for frontend development)

## Installation Instructions

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/Ahmad-Rizki21/BillingFtthV2
    cd BillingFtthV2
    ```

2.  **Backend Setup:**

    a.  **Create a virtual environment (recommended):**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Linux/macOS
    # venv\Scripts\activate  # On Windows
    ```

    b.  **Install backend dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

    c.  **Configure environment variables:**

    *   Create a `.env` file in the root directory.
    *   Add the following variables, replacing the values with your actual configuration:

        ```
        DATABASE_URL="postgresql+asyncpg://user:password@host:port/database"
        XENDIT_CALLBACK_TOKEN_ARTACOMINDO="your_artacomindo_callback_token"
        XENDIT_CALLBACK_TOKEN_JELANTIK="your_jelantik_callback_token"
        SECRET_KEY="your_secret_key"
        ALGORITHM="HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES=30
        XENDIT_API_KEY_JAKINET="your_jakinet_api_key"
        XENDIT_API_KEY_JELANTIK="your_jelantik_api_key"
        ENCRYPTION_KEY="your_encryption_key"
        ```

        *   **DATABASE\_URL:** PostgreSQL database connection string.  Example: `postgresql+asyncpg://billing_user:secure_password@localhost:5432/billing_db`
        *   **XENDIT\_CALLBACK\_TOKEN\_\***: Xendit callback tokens for different brands (e.g., ARTACOM, JELANTIK).  Obtain these from your Xendit dashboard.
        *   **SECRET\_KEY:** A strong, randomly generated secret key used for JWT encryption.
        *   **ALGORITHM:** The JWT algorithm (e.g., HS256).
        *   **ACCESS\_TOKEN\_EXPIRE\_MINUTES:** The access token expiration time in minutes.
        *   **XENDIT\_API\_KEY\_\***:  Xendit API keys for different brands.  Obtain these from your Xendit dashboard.
        *   **ENCRYPTION\_KEY:**  A 32-character encryption key for encrypting sensitive data (e.g. passwords) This needs to be a valid key, generated by something like `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

    d.  **Run database migrations:**

    ```bash
    alembic upgrade head
    ```

        *   This command uses Alembic (configured in `alembic/env.py`) to create the database tables based on the models defined in the `app/models` directory.  Make sure your `DATABASE_URL` in `.env` is configured correctly first.

    e.  **Start the FastAPI application:**

    ```bash
    uvicorn app.main:app --reload
    ```

        *   This command starts the FastAPI server using Uvicorn, enabling automatic reloading on code changes.

3.  **Frontend Setup:**

    a.  **Navigate to the `frontend` directory:**

    ```bash
    cd frontend
    ```

    b.  **Install frontend dependencies:**

    ```bash
    npm install
    ```

    c.  **Configure frontend environment variables:**

    *   While the frontend code does not explicitly show the usage of `.env` files for environment configuration, you might need to adjust API base URLs or other settings directly within the code or through the build process (e.g., using Vite's environment variable features). For example, to configure the API base URL in development:

        *   Inspect `frontend/src/services/api.ts` to configure your `baseURL`.
        *   Update `frontend/src/services/api.ts` to point to your backend:
           ```typescript
           // baseURL: import.meta.env.VITE_API_BASE_URL,
           // baseURL: '/api', // Jika ingin build lalu Upload ke Server
           baseURL: 'http://127.0.0.1:8000', // Local
           ```

        If you plan to build a production version, consult Vite's documentation on how to properly inject environment variables during the build process.

    d.  **Run the frontend development server:**

    ```bash
    npm run dev
    ```

        *   This command starts the Vue.js development server, typically on port 3000.

## Usage Guide

1.  **Access the API:**

    *   The backend API will be accessible at `http://127.0.0.1:8000` (or your configured host and port).
    *   Access the interactive API documentation (Swagger UI) at `http://127.0.0.1:8000/docs`.

2.  **Access the Frontend:**

    *   The frontend application will be accessible at `http://localhost:3000` (or your configured port).

3.  **Authentication:**

    *   Use the `/users/token` endpoint with `username` and `password` to obtain an access token. Example:

        ```bash
        curl -X POST -d "username=test@example.com&password=securepassword" http://127.0.0.1:8000/users/token
        ```

    *   Include the access token in the `Authorization` header of subsequent requests: `Authorization: Bearer <access_token>`.

4.  **Key Endpoints:**
    *   `/pelanggan`: Customer management.
    *   `/langganan`: Subscription management.
    *   `/invoices`: Invoice management.
    *   `/mikrotik_servers`: Mikrotik server management.
    *   `/olt`: OLT Management
    *   `/odp`: ODP Management
    *   `/permissions`: Permission management.
    *   `/reports/revenue`: Revenue reports.
    *   `/ws/notifications`: WebSocket endpoint for real-time notifications.

5.  **Importing Data:** The system supports importing data from CSV files for customers and technical data. Use the provided templates to ensure correct formatting.
        * CSV Template Download :  `[API_BASE_URL]/data_teknis/template/csv` 
        * CSV Import :  `/data_teknis/import/csv` and `/pelanggan/import`

## API Documentation

Detailed API documentation is available through Swagger UI at `http://127.0.0.1:8000/docs`.  or `https://artacomindo.portal.swaggerhub.com/api/docs/billing-system-api-v-1-0-0` This provides interactive exploration of all available endpoints, request parameters, and response schemas.

## Contributing Guidelines

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Implement your changes, adhering to the project's coding style and conventions.
4.  Write unit tests to ensure the functionality of your changes.
5.  Submit a pull request with a clear description of your changes.

## License Information

License not specified.

## Contact/Support Information

For support or questions regarding this project, please contact:

*   Ahmad Rizki:  (GitHub username: Ahmad-Rizki21)