# Stock Data Analysis with Python + Postgres

This project demonstrates a Python app that fetches stock data using the yfinance library, computes 5-day and 30-day moving averages, and stores the results in a Postgres database using SQLAlchemy ORM. Both services run in Docker containers using Docker Compose. It also includes instructions for debugging the Python app using Cursor IDE.

## Prerequisites

- Windows machine with [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [WSL2](https://learn.microsoft.com/en-us/windows/wsl/) enabled
- [Cursor IDE](https://www.cursor.so/) installed
- Python extension for Cursor (for debugging)

## Project Structure

- `hello.py` — Python script that fetches stock data, calculates moving averages, and stores results in Postgres using SQLAlchemy ORM
- `Dockerfile` — Builds the Python app container
- `docker-compose.yml` — Defines and runs the Python and Postgres containers together
- `requirements.txt` — Python dependencies (psycopg2-binary, yfinance, pandas, sqlalchemy)

## Features

- **Configurable Stock Symbols**: Edit the `STOCK_SYMBOLS` list in `hello.py` to analyze different stocks
- **Moving Averages**: Calculates 5-day and 30-day moving averages for each stock
- **SQLAlchemy ORM**: Uses SQLAlchemy for database operations instead of raw SQL
- **Flexible Database Schema**: Stores stock symbols and historical data without hardcoding specific symbols
- **Data Persistence**: Stores open, high, low, close prices, volume, and moving averages
- **Error Handling**: Gracefully handles connection issues and missing data
- **Object-Relational Mapping**: Clean separation between database schema and Python code

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
   The Python app will:
   - Connect to the Postgres database using SQLAlchemy
   - Create the necessary tables using ORM models
   - Fetch stock data for configured symbols (AAPL, GOOGL, MSFT, TSLA, AMZN)
   - Calculate 5-day and 30-day moving averages
   - Store all data in the database using SQLAlchemy sessions
   - Display a summary of the latest data

## Debugging with Cursor IDE (Attach to Python)

1. Open the project folder in Cursor IDE.
2. Make sure you have the Python extension enabled.
3. Set a breakpoint in `hello.py` (e.g., in the `main()` function or `get_stock_data()` function).
4. Start the containers with Docker Compose (as above):
   ```sh
   docker compose up --build
   ```
5. In Cursor, use the "Attach to Python" debug configuration:
   - Host: `localhost`
   - Port: `5678`
6. Start debugging. Cursor will connect to the running Python container and stop at your breakpoint.

## Customizing Stock Symbols and Date Range

To analyze different stocks, edit the `STOCK_SYMBOLS` list in `hello.py`:

```python
STOCK_SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'NVDA', 'META']
```

To change the date range for analysis, edit the `START_DATE` and `END_DATE` variables in `hello.py`:

```python
START_DATE = '2024-01-01'
END_DATE = '2024-06-01'
```

The app will fetch and store all available data for the specified symbols and date range, and compute moving averages for each day in that range.

## Database Models

The application uses two SQLAlchemy models:

- **StockSymbol**: Represents stock symbols with company names
- **StockData**: Represents historical stock data with moving averages

Both models include proper relationships and constraints for data integrity.

## Stopping the App

To stop and remove the containers, press `Ctrl+C` in your terminal and run:
```sh
docker compose down
```

## Notes
- The Python app will wait and retry if the Postgres database is not immediately available.
- Stock data is fetched from Yahoo Finance via the yfinance library.
- SQLAlchemy ORM provides clean, maintainable database operations.
- The database schema supports any number of stock symbols without modification.
- You can edit and debug the code in Cursor IDE as usual.
- For more advanced setups (e.g., real-time data, web interface), update the Dockerfile, requirements, and Compose file as needed.

## Running Unit Tests

Unit tests are located in the `tests/` directory and use `pytest`.

To run all tests:

```sh
pip install -r requirements.txt
pytest
```

The tests use an in-memory SQLite database and mock yfinance, so they do not require a running Postgres instance or network access. 