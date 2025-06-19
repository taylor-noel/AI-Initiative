import time
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Date, Numeric, BigInteger, DateTime, ForeignKey, UniqueConstraint, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import SQLAlchemyError

# Configurable stock symbols
STOCK_SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']

# Configurable date range (inclusive)
# Format: 'YYYY-MM-DD'
START_DATE = '2024-01-01'
END_DATE = '2024-06-01'

# SQLAlchemy setup
Base = declarative_base()

class StockSymbol(Base):
    __tablename__ = 'stock_symbols'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), unique=True, nullable=False)
    company_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to stock data
    stock_data = relationship("StockData", back_populates="symbol")

class StockData(Base):
    __tablename__ = 'stock_data'
    
    id = Column(Integer, primary_key=True)
    symbol_id = Column(Integer, ForeignKey('stock_symbols.id'), nullable=False)
    date = Column(Date, nullable=False)
    open_price = Column(Numeric(10, 2))
    high_price = Column(Numeric(10, 2))
    low_price = Column(Numeric(10, 2))
    close_price = Column(Numeric(10, 2))
    volume = Column(BigInteger)
    ma_5_day = Column(Numeric(10, 2))
    ma_30_day = Column(Numeric(10, 2))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to stock symbol
    symbol = relationship("StockSymbol", back_populates="stock_data")
    
    # Unique constraint
    __table_args__ = (UniqueConstraint('symbol_id', 'date', name='uq_symbol_date'),)

def wait_for_database():
    """Wait for Postgres to be ready and return SQLAlchemy engine"""
    print("Waiting for database to be ready...")
    for i in range(30):  # Increased timeout to 60 seconds
        try:
            # Create engine with more explicit connection parameters
            engine = create_engine(
                'postgresql://postgres:postgres@db:5432/postgres',
                echo=False,  # Set to True for SQL debugging
                pool_pre_ping=True,  # Test connections before use
                pool_recycle=300,  # Recycle connections every 5 minutes
                connect_args={
                    "connect_timeout": 10,
                    "application_name": "stock_analysis"
                }
            )
            # Test connection with a simple query using text()
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            print(f"Database connection successful after {i+1} attempts")
            return engine
        except Exception as e:
            print(f"Database connection attempt {i+1}/30 failed: {e}")
            if i < 29:  # Don't sleep on the last attempt
                time.sleep(2)
    
    raise Exception("Could not connect to the database after 30 attempts")

def create_tables(engine):
    """Create the database tables"""
    try:
        Base.metadata.create_all(engine)
        print("Database schema created/verified!")
    except Exception as e:
        print(f"Error creating tables: {e}")
        raise

def insert_or_update_symbols(session, symbols):
    """Insert stock symbols into the database"""
    try:
        for symbol in symbols:
            try:
                # Get company name from yfinance
                ticker = yf.Ticker(symbol)
                info = ticker.info
                company_name = info.get('longName', symbol)
                
                # Check if symbol already exists
                existing_symbol = session.query(StockSymbol).filter_by(symbol=symbol).first()
                if not existing_symbol:
                    new_symbol = StockSymbol(symbol=symbol, company_name=company_name)
                    session.add(new_symbol)
                    print(f"  Added new symbol: {symbol} ({company_name})")
                else:
                    print(f"  Symbol already exists: {symbol}")
                
            except Exception as e:
                print(f"Warning: Could not get info for {symbol}: {e}")
                # Insert with just the symbol if we can't get company name
                existing_symbol = session.query(StockSymbol).filter_by(symbol=symbol).first()
                if not existing_symbol:
                    new_symbol = StockSymbol(symbol=symbol, company_name=symbol)
                    session.add(new_symbol)
                    print(f"  Added new symbol: {symbol}")
        
        session.commit()
        print(f"Stock symbols configured: {', '.join(symbols)}")
    except Exception as e:
        session.rollback()
        print(f"Error inserting symbols: {e}")
        raise

def get_stock_data(symbol, start_date=START_DATE, end_date=END_DATE):
    """Fetch stock data for a symbol in a configurable date range"""
    try:
        ticker = yf.Ticker(symbol)
        # Fetch data for the given date range
        data = ticker.history(start=start_date, end=end_date)
        
        if data.empty:
            print(f"No data found for {symbol} in range {start_date} to {end_date}")
            return None
            
        # Calculate moving averages
        data['ma_5_day'] = data['Close'].rolling(window=5).mean()
        data['ma_30_day'] = data['Close'].rolling(window=30).mean()
        
        return data
        
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

def store_stock_data(session, symbol, data):
    """Store stock data in the database"""
    if data is None or data.empty:
        return
    
    try:
        print(f"  Getting symbol_id for {symbol}...")
        # Get symbol from database
        stock_symbol = session.query(StockSymbol).filter_by(symbol=symbol).first()
        if not stock_symbol:
            print(f"Symbol {symbol} not found in database")
            return
        
        print(f"  Found symbol_id: {stock_symbol.id}")
        
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
                
                # Check if data already exists for this date
                existing_data = session.query(StockData).filter_by(
                    symbol_id=stock_symbol.id, 
                    date=date.date()
                ).first()
                
                if existing_data:
                    # Update existing record
                    existing_data.open_price = open_price
                    existing_data.high_price = high_price
                    existing_data.low_price = low_price
                    existing_data.close_price = close_price
                    existing_data.volume = volume
                    existing_data.ma_5_day = ma_5
                    existing_data.ma_30_day = ma_30
                else:
                    # Create new record
                    new_data = StockData(
                        symbol_id=stock_symbol.id,
                        date=date.date(),
                        open_price=open_price,
                        high_price=high_price,
                        low_price=low_price,
                        close_price=close_price,
                        volume=volume,
                        ma_5_day=ma_5,
                        ma_30_day=ma_30
                    )
                    session.add(new_data)
                
                inserted_count += 1
                
            except Exception as e:
                print(f"Error inserting data for {symbol} on {date}: {e}")
                import traceback
                traceback.print_exc()
                session.rollback()
                return
        
        session.commit()
        print(f"  Successfully stored {inserted_count} data points for {symbol}")
    except Exception as e:
        session.rollback()
        print(f"Error storing data for {symbol}: {e}")
        import traceback
        traceback.print_exc()

def display_latest_data(session):
    """Display the latest stock data"""
    try:
        # Get all stock data with symbol information
        latest_data = session.query(
            StockSymbol.symbol,
            StockSymbol.company_name,
            StockData.date,
            StockData.close_price,
            StockData.ma_5_day,
            StockData.ma_30_day
        ).join(StockData).order_by(
            StockSymbol.symbol, 
            StockData.date.desc()
        ).all()
        
        if not latest_data:
            print("\nNo stock data found in database.")
            return
            
        # Group by symbol and get the latest for each
        latest_by_symbol = {}
        for row in latest_data:
            symbol, company, date, close_price, ma_5, ma_30 = row
            if symbol not in latest_by_symbol:
                latest_by_symbol[symbol] = (company, date, close_price, ma_5, ma_30)
        
        print("\nLatest Stock Data:")
        print("Symbol | Company | Date | Close | 5-Day MA | 30-Day MA")
        print("-" * 60)
        
        for symbol in sorted(latest_by_symbol.keys()):
            company, date, close_price, ma_5, ma_30 = latest_by_symbol[symbol]
            print(f"{symbol:6} | {company[:20]:20} | {date} | {close_price:6.2f} | {ma_5:8.2f} | {ma_30:9.2f}")
            
    except Exception as e:
        print(f"Error displaying data: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to run the stock analysis"""
    print("Starting stock data analysis...")
    print(f"Configured date range: {START_DATE} to {END_DATE}")
    
    # Connect to database
    print("Step 1: Connecting to database...")
    try:
        engine = wait_for_database()
        print("Connected to database successfully!")
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        print("Please check that:")
        print("1. Docker Compose is running")
        print("2. The Postgres container is healthy")
        print("3. The database service is accessible")
        return
    
    # Create session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    try:
        # Create tables
        print("Step 2: Creating database tables...")
        create_tables(engine)
        
        # Create session
        session = SessionLocal()
        
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