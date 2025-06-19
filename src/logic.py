import yfinance as yf
import pandas as pd
from db import StockSymbol, StockData

def insert_or_update_symbols(session, symbols):
    try:
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                company_name = info.get('longName', symbol)
                existing_symbol = session.query(StockSymbol).filter_by(symbol=symbol).first()
                if not existing_symbol:
                    new_symbol = StockSymbol(symbol=symbol, company_name=company_name)
                    session.add(new_symbol)
                    print(f"  Added new symbol: {symbol} ({company_name})")
                else:
                    print(f"  Symbol already exists: {symbol}")
            except Exception as e:
                print(f"Warning: Could not get info for {symbol}: {e}")
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

def get_stock_data(symbol, start_date, end_date):
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(start=start_date, end=end_date)
        if data.empty:
            print(f"No data found for {symbol} in range {start_date} to {end_date}")
            return None
        data['ma_5_day'] = data['Close'].rolling(window=5).mean()
        data['ma_30_day'] = data['Close'].rolling(window=30).mean()
        return data
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

def store_stock_data(session, symbol, data):
    if data is None or data.empty:
        return
    try:
        print(f"  Getting symbol_id for {symbol}...")
        stock_symbol = session.query(StockSymbol).filter_by(symbol=symbol).first()
        if not stock_symbol:
            print(f"Symbol {symbol} not found in database")
            return
        print(f"  Found symbol_id: {stock_symbol.id}")
        inserted_count = 0
        for date, row in data.iterrows():
            try:
                open_price = float(row['Open']) if pd.notna(row['Open']) else None
                high_price = float(row['High']) if pd.notna(row['High']) else None
                low_price = float(row['Low']) if pd.notna(row['Low']) else None
                close_price = float(row['Close']) if pd.notna(row['Close']) else None
                volume = int(row['Volume']) if pd.notna(row['Volume']) else None
                ma_5 = float(row['ma_5_day']) if pd.notna(row['ma_5_day']) else None
                ma_30 = float(row['ma_30_day']) if pd.notna(row['ma_30_day']) else None
                if inserted_count < 3:
                    print(f"    Inserting {date.date()}: Close={close_price}, MA5={ma_5}, MA30={ma_30}")
                existing_data = session.query(StockData).filter_by(
                    symbol_id=stock_symbol.id, 
                    date=date.date()
                ).first()
                if existing_data:
                    existing_data.open_price = open_price
                    existing_data.high_price = high_price
                    existing_data.low_price = low_price
                    existing_data.close_price = close_price
                    existing_data.volume = volume
                    existing_data.ma_5_day = ma_5
                    existing_data.ma_30_day = ma_30
                else:
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
    try:
        from collections import defaultdict
        from datetime import date as dtdate
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