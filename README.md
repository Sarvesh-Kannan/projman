# AI-Powered Task Management System

A free MVP tech stack implementation for task management and automation.

## Features

- Task Scheduling with Prefect
- NLP-based Communication Handling
- Resource Allocation with ML
- Interactive Dashboard with Streamlit

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
# Start the FastAPI backend
uvicorn app.main:app --reload

# In a separate terminal, start the Streamlit frontend
streamlit run frontend/app.py
```

## Project Structure

```
.
├── app/                    # Backend FastAPI application
│   ├── main.py            # FastAPI app entry point
│   ├── models/            # ML models and transformers
│   ├── api/               # API routes
│   └── core/              # Core business logic
├── frontend/              # Streamlit frontend
│   └── app.py             # Streamlit dashboard
├── prefect/               # Prefect workflows
│   └── flows/             # Task scheduling flows
└── requirements.txt       # Project dependencies
``` 