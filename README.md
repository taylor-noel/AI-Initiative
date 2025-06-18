# Python + Postgres with Docker Compose

This project demonstrates a minimal Python app that writes dummy data to a Postgres database, with both services running in Docker containers using Docker Compose. It also includes instructions for debugging the Python app using Cursor IDE.

## Prerequisites

- Windows machine with [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [WSL2](https://learn.microsoft.com/en-us/windows/wsl/) enabled
- [Cursor IDE](https://www.cursor.so/) installed
- Python extension for Cursor (for debugging)

## Project Structure

- `hello.py` — Python script that connects to Postgres and writes dummy data
- `Dockerfile` — Builds the Python app container
- `docker-compose.yml` — Defines and runs the Python and Postgres containers together
- `requirements.txt` — Python dependencies

## Running the App

1. Open a WSL terminal (e.g., Ubuntu).
2. Navigate to the project directory:
   ```sh
   cd "/mnt/c/Users/TaylorNoel/OneDrive - Arcurve/Documents/Projects/AI Initiative"
   ```
3. Build and start both containers:
   ```sh
   docker compose up --build
   ```
   The Python app will connect to the Postgres database, create a table, insert dummy data, and print the table contents.

## Debugging with Cursor IDE (Attach to Python)

1. Open the project folder in Cursor IDE.
2. Make sure you have the Python extension enabled.
3. Set a breakpoint in `hello.py` (e.g., on the `print` line).
4. Start the containers with Docker Compose (as above):
   ```sh
   docker compose up --build
   ```
5. In Cursor, use the "Attach to Python" debug configuration:
   - Host: `localhost`
   - Port: `5678`
6. Start debugging. Cursor will connect to the running Python container and stop at your breakpoint.

## Stopping the App

To stop and remove the containers, press `Ctrl+C` in your terminal and run:
```sh
docker compose down
```

## Notes
- The Python app will wait and retry if the Postgres database is not immediately available.
- You can edit and debug the code in Cursor IDE as usual.
- For more advanced setups (e.g., Flask, FastAPI), update the Dockerfile, requirements, and Compose file as needed. 