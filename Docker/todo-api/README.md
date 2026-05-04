# Todo API — Docker Project
https://hub.docker.com/r/ashwiniii/todo-api/tags

## What is this project?

This project is a simple Todo API built using Python and FastAPI. It lets you create, list, and delete todo items through HTTP requests. The entire application runs inside Docker containers, meaning you do not need to install Python or PostgreSQL on your computer manually. Docker handles everything for you in an isolated environment.


## What does each file do?

**app/main.py** — This is the heart of the API. It defines three endpoints: one for creating a todo, one for listing all todos, and one for deleting a todo by its id. When a request comes in, this file handles it and talks to the database.

**app/models.py** — This file describes the shape of the data in the database. It tells SQLAlchemy to create a table called `todos` with three columns: id, title, and completed.

**app/schemas.py** — This file defines what data the API expects to receive and what it sends back. For example, when creating a todo, the API expects a title. When returning a todo, it sends back the id, title, and completed status.

**app/database.py** — This file sets up the connection to the database. It reads the database URL from an environment variable, so the same code works with both SQLite (for simple testing) and PostgreSQL (for production use with Docker Compose).

**Dockerfile** — This file contains instructions for building the API into a Docker image. It starts from a Python base image, installs the dependencies, copies the code, and tells Docker how to start the app.

**docker-compose.yml** — This file runs two containers together: the API and the PostgreSQL database. It also sets up the network between them and the volume for data persistence.

**requirements.txt** — This lists all the Python libraries the project needs, like FastAPI, SQLAlchemy, and the PostgreSQL driver.

**.dockerignore** — This tells Docker to ignore unnecessary files like cache and database files when building the image, keeping the image small and clean.

**.gitignore** — This tells Git to ignore files that should not be committed, like Python cache files and local database files.

## API Endpoints

**POST /todos** — Creates a new todo. You send a title in the request body and the API saves it to the database and returns the created todo with its id.

**GET /todos** — Returns a list of all todos currently stored in the database. No parameters needed.

**DELETE /todos/{id}** — Deletes a specific todo by its id. If the id does not exist, the API returns a 404 error.

---

## How to run the project

### Using Docker Compose (recommended)

This is the best way to run the project because it starts both the API and the PostgreSQL database together with one command.

```bash
docker-compose up --build
```

To stop everything:

```bash
docker-compose down
```

### Using Docker only (with SQLite)

If you want to run just the API without PostgreSQL:

```bash
docker build -t todo-api .
docker run -p 8000:8000 -e DATABASE_URL=sqlite:///./todos.db todo-api
```


## How to test the API

Once the project is running, open your browser and go to:
http://localhost:8000/docs


This opens the Swagger UI where you can test all three endpoints directly from the browser without needing any extra tools.
## Docker Hub — Sharing the image

Docker Hub is like GitHub but for Docker images. You can push your image there so anyone can pull and run it without building it themselves.

--bash
# tagging the image with your Docker Hub username
docker tag todo-api your_username/todo-api:latest

# pushing the image to Docker Hub
docker push your_username/todo-api:latest

# pulling the image from Docker Hub on any machine
docker pull your_username/todo-api:latest
```

## What this project covers about Docker

Containerization — The API and the database each run in their own container. This means they are isolated from the host machine and from each other, just like virtual machines but much lighter and faster.

Docker Images — The Dockerfile builds a custom image for the API. An image is like a blueprint. Every time you run a container from it, you get the same environment.

Docker Containers — A container is a running instance of an image. This project runs two containers: one for the API and one for PostgreSQL.

Communication between containers — The API container talks to the database container using the service name `db` defined in docker-compose.yml. Docker Compose automatically creates a network between services so they can reach each other by name instead of IP address.

Data persistence with volumes — The PostgreSQL data is stored in a named volume called `postgres_data`. This means even if you stop and restart the containers, all your todos are still there. Without a volume, the data would be lost every time the container stops.

Dockerfile — The Dockerfile defines how to build the API image step by step: choosing a base image, installing dependencies, copying code, and setting the startup command.

Docker Hub— The image can be tagged and pushed to Docker Hub so it can be shared and pulled on any machine in the world.

Docker Compose — docker-compose.yml defines and runs the full multi-container application with a single command. It handles service dependencies, environment variables, port mapping, networking, and volumes all in one place.
