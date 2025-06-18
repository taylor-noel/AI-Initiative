import psycopg2
import time
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Configurable stock symbols
STOCK_SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']

def wait_for_database():
    """Wait for Postgres to be ready"""
    for i in range(10):
        try:
            conn = psycopg2.connect(
                dbname="postgres",
                user="postgres",
                password="postgres",
                host="db",
                port=5432
            )
            return conn
        except Exception as e:
            print(f"Waiting for database... ({i+1}/10)")
            time.sleep(2)
    raise Exception("Could not connect to the database.")

def create_tables(conn):
    """Create the database schema for stock data"""
    cur = conn.cursor()
    try:
        # Table for stock symbols
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stock_symbols (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(10) UNIQUE NOT NULL,
                company_name VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Table for stock data with moving averages
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stock_data (
                id SERIAL PRIMARY KEY,
                symbol_id INTEGER REFERENCES stock_symbols(id),
                date DATE NOT NULL,
                open_price DECIMAL(10,2),
                high_price DECIMAL(10,2),
                low_price DECIMAL(10,2),
                close_price DECIMAL(10,2),
                volume BIGINT,
                ma_5_day DECIMAL(10,2),
                ma_30_day DECIMAL(10,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol_id, date)
            );
        """)
        
        conn.commit()
        print("Database schema created/verified!")
    except Exception as e:
        conn.rollback()
        print(f"Error creating tables: {e}")
        raise
    finally:
        cur.close()

def insert_or_update_symbols(conn, symbols):
    """Insert stock symbols into the database"""
    cur = conn.cursor()
    try:
        for symbol in symbols:
            try:
                # Get company name from yfinance
                ticker = yf.Ticker(symbol)
                info = ticker.info
                company_name = info.get('longName', symbol)
                
                cur.execute("""
                    INSERT INTO stock_symbols (symbol, company_name)
                    VALUES (%s, %s)
                    ON CONFLICT (symbol) DO NOTHING
                """, (symbol, company_name))
                
            except Exception as e:
                print(f"Warning: Could not get info for {symbol}: {e}")
                # Insert with just the symbol if we can't get company name
                cur.execute("""
                    INSERT INTO stock_symbols (symbol, company_name)
                    VALUES (%s, %s)
                    ON CONFLICT (symbol) DO NOTHING
                """, (symbol, symbol))
        
        conn.commit()
        print(f"Stock symbols configured: {', '.join(symbols)}")
    except Exception as e:
        conn.rollback()
        print(f"Error inserting symbols: {e}")
        raise
    finally:
        cur.close()

def get_stock_data(symbol, days=60):
    """Fetch stock data for a symbol"""
    try:
        ticker = yf.Ticker(symbol)
        # Get data for more days to calculate 30-day moving average
        data = ticker.history(period=f"{days}d")
        
        if data.empty:
            print(f"No data found for {symbol}")
            return None
            
        # Calculate moving averages
        data['ma_5_day'] = data['Close'].rolling(window=5).mean()
        data['ma_30_day'] = data['Close'].rolling(window=30).mean()
        
        return data
        
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

def store_stock_data(conn, symbol, data):
    """Store stock data in the database"""
    if data is None or data.empty:
        return
    
    cur = conn.cursor()
    try:
        print(f"  Getting symbol_id for {symbol}...")
        # Get symbol_id
        cur.execute("SELECT id FROM stock_symbols WHERE symbol = %s", (symbol,))
        result = cur.fetchone()
        if not result:
            print(f"Symbol {symbol} not found in database")
            return
        
        symbol_id = result[0]
        print(f"  Found symbol_id: {symbol_id}")
        
        # Insert data
        inserted_count = 0
        for date, row in data.iterrows():
            try:
                # Handle NaN values
                open_price = float(row['Open']) if pd.notna(row['Open']) else None
                high_price = float(row['High']) if pd.notna(row['High']) else None
                low_price = float(row['Low']) if pd.notna(row['Low']) else None
                close_price = float(row['Close']) if pd.notna(row['Close']) else None
                volume = int(row['Volume']) if pd.notna(row['Volume']) else None
                ma_5 = float(row['ma_5_day']) if pd.notna(row['ma_5_day']) else None
                ma_30 = float(row['ma_30_day']) if pd.notna(row['ma_30_day']) else None
                
                # Debug print for first few rows
                if inserted_count < 3:
                    print(f"    Inserting {date.date()}: Close={close_price}, MA5={ma_5}, MA30={ma_30}")
                
                cur.execute("""
                    INSERT INTO stock_data 
                    (symbol_id, date, open_price, high_price, low_price, close_price, volume, ma_5_day, ma_30_day)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (symbol_id, date) DO UPDATE SET
                        open_price = EXCLUDED.open_price,
                        high_price = EXCLUDED.high_price,
                        low_price = EXCLUDED.low_price,
                        close_price = EXCLUDED.close_price,
                        volume = EXCLUDED.volume,
                        ma_5_day = EXCLUDED.ma_5_day,
                        ma_30_day = EXCLUDED.ma_30_day
                """, (
                    symbol_id,
                    date.date(),
                    open_price,
                    high_price,
                    low_price,
                    close_price,
                    volume,
                    ma_5,
                    ma_30
                ))
                inserted_count += 1
                
            except Exception as e:
                print(f"Error inserting data for {symbol} on {date}: {e}")
                import traceback
                traceback.print_exc()
                conn.rollback()
                return
        
        conn.commit()
        print(f"  Successfully stored {inserted_count} data points for {symbol}")
    except Exception as e:
        conn.rollback()
        print(f"Error storing data for {symbol}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()

def display_latest_data(conn):
    """Display the latest stock data"""
    cur = conn.cursor()
    try:
        # Very simple query to get all data
        cur.execute("""
            SELECT 
                s.symbol,
                s.company_name,
                sd.date,
                sd.close_price,
                sd.ma_5_day,
                sd.ma_30_day
            FROM stock_data sd
            JOIN stock_symbols s ON sd.symbol_id = s.id
            ORDER BY s.symbol, sd.date DESC
        """)
        
        rows = cur.fetchall()
        
        if not rows:
            print("\nNo stock data found in database.")
            return
            
        # Group by symbol and get the latest for each
        latest_data = {}
        for row in rows:
            symbol, company, date, close_price, ma_5, ma_30 = row
            if symbol not in latest_data:
                latest_data[symbol] = (company, date, close_price, ma_5, ma_30)
        
        print("\nLatest Stock Data:")
        print("Symbol | Company | Date | Close | 5-Day MA | 30-Day MA")
        print("-" * 60)
        
        for symbol in sorted(latest_data.keys()):
            company, date, close_price, ma_5, ma_30 = latest_data[symbol]
            print(f"{symbol:6} | {company[:20]:20} | {date} | {close_price:6.2f} | {ma_5:8.2f} | {ma_30:9.2f}")
            
    except Exception as e:
        print(f"Error displaying data: {e}")
        # Print the full error for debugging
        import traceback
        traceback.print_exc()
    finally:
        cur.close()

def main():
    """Main function to run the stock analysis"""
    print("Starting stock data analysis...")
    
    # Connect to database
    print("Step 1: Connecting to database...")
    conn = wait_for_database()
    print("Connected to database successfully!")
    
    try:
        # Create tables
        print("Step 2: Creating database tables...")
        create_tables(conn)
        
        # Insert stock symbols
        print("Step 3: Inserting stock symbols...")
        insert_or_update_symbols(conn, STOCK_SYMBOLS)
        
        # Fetch and store data for each symbol
        print("Step 4: Processing stock data...")
        for symbol in STOCK_SYMBOLS:
            print(f"\nProcessing {symbol}...")
            data = get_stock_data(symbol)
            if data is not None:
                print(f"  Got {len(data)} data points for {symbol}")
                store_stock_data(conn, symbol, data)
            else:
                print(f"Failed to process {symbol}")
        
        # Display results
        print("Step 5: Displaying results...")
        display_latest_data(conn)
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close connection
        conn.close()
        print("\nStock analysis complete!")

if __name__ == "__main__":
    main() 