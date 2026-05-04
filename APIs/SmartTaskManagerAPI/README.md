# Smart Task Manager API

A RESTful API built with FastAPI and SQLite for managing tasks. It supports full CRUD operations, filtering by status and priority, pagination, timestamps, and token-based authentication. Interactive API documentation is auto-generated and available at `/docs` once the server is running.

---

## What This Project Does

This API lets you create, read, update, and delete tasks. Each task has a title, an optional description, a status (pending or completed), a priority level (low, medium, or high), and an optional due date. Every task also gets a created_at and updated_at timestamp automatically managed by the server. You can filter tasks by status or priority and paginate through large lists using page and limit parameters.

---

## Project Structure

The project is organized into the following files. `main.py` is the entry point that starts the app and registers all routes. `database.py` sets up the SQLite database connection and provides a session for each request. `models.py` defines the database table structure using SQLAlchemy and the request/response shapes using Pydantic. `auth.py` handles token verification for protected routes. The `routes/` folder contains `tasks.py` which defines all the task endpoints.

---

## Installation and Setup

Start by cloning the repository and navigating into the project folder. Then create a virtual environment and activate it.

```bash
python -m venv venv
source venv/bin/activate
```

Install the required dependencies.

```bash
pip install -r requirements.txt
```

---

## Running the Server

Start the development server using uvicorn. The `--reload` flag automatically restarts the server whenever you save a file change.

```bash
uvicorn main:app --reload
```

The server will start at `http://127.0.0.1:8000`. You can open `http://127.0.0.1:8000/docs` in your browser to access the interactive Swagger UI where you can test all endpoints visually.

If you want to run on a different port, pass the `--port` flag.

```bash
uvicorn main:app --reload --port 8080
```

---

## How Authentication Works

Every request to a `/tasks` endpoint must include an `Authorization` header with a Bearer token. The server reads the expected token from an environment variable called `AUTH_TOKEN`. If that variable is not set, it falls back to the default token `777777`.

When a request comes in, the `verify_token` function in `auth.py` checks whether the token in the header matches the expected token. If the token is missing or wrong, the server immediately returns a `401 Unauthorized` response and the request is blocked. If the token is correct, the request proceeds normally.

To authenticate in the Swagger UI at `/docs`, click the **Authorize** button at the top right, type `777777` in the value field, and click Authorize. You only need to do this once per session. If you refresh the page, you will need to authorize again.

To use the API from the terminal or any HTTP client, include the header like this.

```bash
-H "Authorization: Bearer 777777"
```

To change the token without modifying the code, set the environment variable before starting the server.

```bash
AUTH_TOKEN="your-custom-token" uvicorn main:app --reload
```

The `/health` endpoint does not require authentication and is always publicly accessible.

---

## Using the API

### Creating a Task

Send a POST request to `/tasks/` with a JSON body. The `title` field is required and must be between 1 and 255 characters. All other fields are optional. The `status` defaults to `pending` and `priority` defaults to `medium` if not provided. The `id`, `created_at`, and `updated_at` fields are set automatically by the server — you should never include them in the request body.

```bash
curl -X POST http://127.0.0.1:8000/tasks/ \
  -H "Authorization: Bearer 777777" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Fix login bug",
    "description": "Users cannot login with Google OAuth",
    "status": "pending",
    "priority": "high",
    "due_date": "2026-05-10"
  }'
```

The server responds with the created task including its assigned `id` and timestamps. Note that `id` is auto-incremented by the database — the first task gets id 1, the second gets id 2, and so on. Keep track of the `id` in the response because you will need it to fetch, update, or delete that task later.

### Listing All Tasks

Send a GET request to `/tasks/` to retrieve all tasks. By default it returns the first 10 tasks ordered by newest first. You can filter and paginate using query parameters.

To get all pending tasks, add `?status=pending` to the URL. To get only high priority tasks, add `?priority=high`. You can combine both filters at once. To paginate, use `?page=2&limit=5` to get the second page with 5 tasks per page. The response includes a `total` count, the current `page`, the `limit`, the total number of `pages`, and the `items` array with the matching tasks.

```bash
curl "http://127.0.0.1:8000/tasks/?status=pending&priority=high&page=1&limit=10" \
  -H "Authorization: Bearer 777777"
```

### Getting a Single Task

Send a GET request to `/tasks/{id}` replacing `{id}` with the actual task id number. For example, to get the task with id 3, the URL would be `/tasks/3`. If no task exists with that id, the server returns a `404 Not Found` response.

```bash
curl http://127.0.0.1:8000/tasks/3 \
  -H "Authorization: Bearer 777777"
```

### Updating a Task

Send a PUT request to `/tasks/{id}` with only the fields you want to change in the request body. You do not need to send all fields — only the ones being updated. For example, to mark a task as completed and lower its priority, send just those two fields.

```bash
curl -X PUT http://127.0.0.1:8000/tasks/3 \
  -H "Authorization: Bearer 777777" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed", "priority": "low"}'
```

The server responds with the full updated task. The `updated_at` timestamp will reflect the time of the update.

### Deleting a Task

Send a DELETE request to `/tasks/{id}`. The task is permanently removed from the database. The server responds with a confirmation message.

```bash
curl -X DELETE http://127.0.0.1:8000/tasks/3 \
  -H "Authorization: Bearer 777777"
```

---

## How the ID Works

Every task gets a unique integer `id` assigned automatically by the database when it is created. The first task ever created gets id 1, the next gets id 2, and so on. This id never changes and is never reused — if you delete task 5 and create a new task, the new task will get id 6, not id 5.

The `id` is used in the URL path for GET, PUT, and DELETE operations. You always get the id back in the response when creating or listing tasks, so you can store it and use it for later operations.

---

## Data Persistence

All tasks are stored in a SQLite database file called `tasks.db` in the project root. This file is created automatically the first time you start the server. Tasks persist across server restarts — stopping and restarting the server will not delete any data. The only way to remove a task is by calling the DELETE endpoint.

---

## Error Responses

When something goes wrong, the API returns a JSON object with a `detail` field explaining what happened. A `400` means the request body failed validation, such as a missing title or an invalid status value. A `401` means the token is missing or incorrect. A `404` means no task was found with the given id. A `500` means something unexpected went wrong on the server side.

---

## Health Check

The `/health` endpoint returns `{"status": "ok"}` and does not require authentication. It is useful for checking whether the server is running.

```bash
curl http://127.0.0.1:8000/health
```

---

## License

MIT
