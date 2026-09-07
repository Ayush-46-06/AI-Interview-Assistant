# AI Interview Assistant - Backend

This is the FastAPI backend for the AI Interview Assistant. 
Currently, it establishes the foundation for:
- FastAPI Application setup
- PostgreSQL Database with SQLAlchemy (Async)
- Alembic for database migrations
- Configuration management using Pydantic Settings

## Project Setup

### 1. Create a Virtual Environment

It is recommended to use a Python virtual environment:
```bash
python -m venv venv
```

Activate the virtual environment:
- On Windows:
  ```bash
  .\venv\Scripts\activate
  ```
- On macOS/Linux:
  ```bash
  source venv/bin/activate
  ```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Variables

Copy `.env.example` to `.env` and fill in your actual credentials (DO NOT commit `.env` to version control).

```bash
cp .env.example .env
```
Ensure you provide a valid `DATABASE_URL` to connect to PostgreSQL.

### 4. Running the Application

To start the FastAPI development server:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

### 5. Health Check

You can verify the backend is running by accessing the health endpoint:

```bash
curl http://localhost:8000/health
```
Response:
```json
{"status": "ok", "message": "Backend is running!"}
```

### 6. Database Migrations (Alembic)

To create a new migration after modifying models:
```bash
alembic revision --autogenerate -m "describe_your_changes"
```

To apply migrations to the database:
```bash
alembic upgrade head
```
