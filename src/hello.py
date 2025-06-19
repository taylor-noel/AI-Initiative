from db import wait_for_database, create_tables, get_session
from logic import insert_or_update_symbols, get_stock_data, store_stock_data, display_latest_data

# Configurable stock symbols
STOCK_SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']

# Configurable date range (inclusive)
# Format: 'YYYY-MM-DD'
START_DATE = '2024-01-01'
END_DATE = '2024-06-01'

DB_URL = 'postgresql://postgres:postgres@db:5432/postgres'

def main():
    """Main function to run the stock analysis"""
    print("Starting stock data analysis...")
    print(f"Configured date range: {START_DATE} to {END_DATE}")
    
    # Connect to database
    print("Step 1: Connecting to database...")
    try:
        engine = wait_for_database(DB_URL)
        print("Connected to database successfully!")
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        print("Please check that:")
        print("1. Docker Compose is running")
        print("2. The Postgres container is healthy")
        print("3. The database service is accessible")
        return
    
    try:
        # Create tables
        print("Step 2: Creating database tables...")
        create_tables(engine)
        
        # Create session
        session = get_session(engine)
        
        # Insert stock symbols
        print("Step 3: Inserting stock symbols...")
        insert_or_update_symbols(session, STOCK_SYMBOLS)
        
        # Fetch and store data for each symbol
        print("Step 4: Processing stock data...")
        for symbol in STOCK_SYMBOLS:
            print(f"\nProcessing {symbol}...")
            data = get_stock_data(symbol, START_DATE, END_DATE)
            if data is not None:
                print(f"  Got {len(data)} data points for {symbol}")
                store_stock_data(session, symbol, data)
            else:
                print(f"Failed to process {symbol}")
        
        # Display results
        print("Step 5: Displaying results...")
        display_latest_data(session)
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close session and engine
        if 'session' in locals():
            session.close()
        engine.dispose()
        print("\nStock analysis complete!")

if __name__ == "__main__":
    main() 