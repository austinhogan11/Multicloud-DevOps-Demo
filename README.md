# Multicloud DevOps Demo

Portfolio project to showcase:

- API development (FastAPI). We created a simple FastAPI application with a root, health check, and a Tasks API to demonstrate API concepts.
- Monitoring (Splunk)
- Analytics (Adobe Analytics)
- Cloud deployment (AWS)

## Local Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

3. Test the endpoints:
   - `/` for root
   - `/health` for health check
   - `/tasks` for Tasks API

## Features

- `/health`: Returns a simple status check to confirm the API is running.
- `/tasks`: Supports GET to list all tasks, POST to create a new task, PUT to update tasks, and DELETE to remove tasks.
- `/tasks/{id}`: Supports GET to fetch a single task by id, PUT to update a specific task, and DELETE to remove a specific task.

The Task data model includes:
- `id` (int): Unique identifier for the task.
- `title` (str): The title or description of the task.
- `completed` (bool, default False): Status indicating if the task is completed.

## Status

Work in progress. The application details will be added as development continues.