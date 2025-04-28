# Project Overview

This project consists of a React frontend and a Python FastAPI backend proxy.

## Prerequisites

- Node.js and npm installed
- Python 3.x installed
- pip installed for Python package management

## Installation

1. Install Python dependencies:

```sh
pip install -r requirements.txt
```

2. Install npm dependencies:

```sh
npm install
```

## Running the Project

1. Start the backend server:

```sh
python backend_proxy.py
```

2. Start the frontend development server:

```sh
npm run dev
```

The frontend will be available at http://localhost:8080 (or the port specified in vite.config.ts).

## Project Structure

- `backend_proxy.py`: Python FastAPI backend proxy server
- `src/`: React frontend source code
- `package.json`: npm dependencies and scripts
- `requirements.txt`: Python dependencies

## Additional Information

- The project uses Vite, React, TypeScript, and Tailwind CSS for the frontend.
- The backend uses FastAPI with uvicorn for serving.
- Make sure both backend and frontend servers are running for the application to work correctly.

## Deployment

Refer to your deployment strategy for both frontend and backend components.
