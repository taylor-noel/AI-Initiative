# Python Hello World in Docker

This project demonstrates a minimal Python Hello World app running in a Docker container, with instructions for debugging using Cursor IDE on Windows with WSL and Docker Desktop.

## Prerequisites

- Windows machine with [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [WSL2](https://learn.microsoft.com/en-us/windows/wsl/) enabled
- [Cursor IDE](https://www.cursor.so/) installed
- Python extension for Cursor (for debugging)

## Running the App

1. Open a WSL terminal (e.g., Ubuntu).
2. Navigate to the project directory:
   ```sh
   cd "/mnt/c/Users/TaylorNoel/OneDrive - Arcurve/Documents/Projects/AI Initiative"
   ```
3. Build the Docker image:
   ```sh
   docker build -t hello-python .
   ```
4. Run the container:
   ```sh
   docker run --rm hello-python
   ```
   You should see:
   ```
   Hello, world!
   ```

## Debugging with Cursor IDE

1. Open the project folder in Cursor IDE.
2. Make sure you have the Python extension enabled.
3. Set a breakpoint in `hello.py` (e.g., on the `print` line).
4. To debug inside Docker:
   - Install `debugpy` in your Docker image (add `RUN pip install debugpy` to your Dockerfile and rebuild).
   - Update your `Dockerfile` to start Python with debugpy:
     ```dockerfile
     CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "--wait-for-client", "hello.py"]
     ```
   - Expose port 5678 in your Dockerfile:
     ```dockerfile
     EXPOSE 5678
     ```
   - Run the container with port mapping:
     ```sh
     docker run -p 5678:5678 hello-python
     ```
   - In Cursor, use the "Attach to Python" debug configuration, connecting to `localhost:5678`.

## Notes
- You can edit and debug the code in Cursor IDE as usual.
- For more advanced setups (e.g., Flask, FastAPI), update the Dockerfile and requirements as needed. 