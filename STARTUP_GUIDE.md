# Project Startup Guide

This guide outlines the steps to set up and run this project.

## 1. Environment Setup

### Create Conda Environment

First, create a Conda environment with Python 3.9.6. We recommend creating it within the project directory for better organization:

```bash
conda create -p ./py396_env python=3.9.6 -y
```

### Activate Environment

Activate the newly created environment:

```bash
conda activate ./py396_env
```

_(Note: If you created the environment with a different name or path, adjust the activation command accordingly.)_

## 2. Install Dependencies

### Modify requirements.txt (Important)

Before installing, you need to modify `requirements.txt`. The specified versions for `ipython` and `scipy` might be incompatible with Python 3.9. Remove the specific version numbers for these two packages.

Change:

```
ipython==9.2.0
...
scipy==1.15.2
```

To:

```
ipython
...
scipy
```

### Install Packages

Once the environment is active and `requirements.txt` is modified, install the Python packages:

```bash
pip install -r requirements.txt
```

## 3. Running the Backend

The backend is a FastAPI application. To run it:

1.  **Navigate to the project root directory** (if you're not already there).
2.  Ensure your Conda environment (`py396_env` or your chosen name) is **active**.
3.  Run the Uvicorn server:
    ```bash
    uvicorn backend.app:app --host 0.0.0.0 --port 5001 --reload
    ```
    This will start the backend server, typically accessible at `http://localhost:5001`. The `--reload` flag enables auto-reloading when code changes are detected.

## 4. Running the Frontend

The frontend application requires Node.js and npm.

1.  **Navigate to the frontend directory** (`autoui`):
    ```bash
    cd autoui
    ```
2.  Install frontend dependencies:
    ```bash
    npm install
    ```
3.  Start the frontend development server:
    ```bash
    npm run dev
    ```
    This will typically start the frontend application, and the access URL (often `http://localhost:3000` or similar) will be displayed in the terminal.

## 6. Frontend to Backend Connection (Important)

For the frontend to communicate with the backend, it needs to know the backend's address and port. This is configured in the frontend code.

- **File:** `autoui/src/services/api.ts`
- **Constant:** `API_BASE`

Initially, this constant might be set to a relative path like `'/api'`. When the frontend runs on a specific port (e.g., `http://localhost:5173`), a relative path `'/api'` would resolve to `http://localhost:5173/api`.

**Impact of Modification:**

You **must** change this constant to the full URL of your running backend. If your backend is running on `http://localhost:5001`, then `API_BASE` should be changed to:

```typescript
const API_BASE = "http://localhost:5001/api";
```

**Why this is important:**
If `API_BASE` is not correctly set to the backend's address:

- The frontend will try to send API requests to the wrong URL (e.g., its own address or a non-existent one).
- This will result in network errors, typically HTTP 404 (Not Found), as seen when the frontend tries to call an API endpoint that doesn't exist on its own server.
- The application will not function correctly as it won't be able to fetch or send data to the backend.

Ensure this path is correct if you change the port or host of your backend server.
