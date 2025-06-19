import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db import Base, StockSymbol, StockData
from logic import insert_or_update_symbols, get_stock_data, store_stock_data
import pandas as pd
from unittest.mock import patch, MagicMock

@pytest.fixture(scope="function")
def session():
    # Use in-memory SQLite for fast tests
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@patch('logic.yf.Ticker')
def test_insert_or_update_symbols(mock_ticker, session):
    mock_ticker.return_value.info = MagicMock()
    mock_ticker.return_value.info.get.return_value = 'Test Company'
    insert_or_update_symbols(session, ['TEST'])
    symbol = session.query(StockSymbol).filter_by(symbol='TEST').first()
    assert symbol is not None
    assert symbol.company_name == 'Test Company'

@patch('logic.yf.Ticker')
def test_get_stock_data_and_store(mock_ticker, session):
    # Prepare mock data
    dates = pd.date_range('2024-01-01', '2024-01-10')
    data = pd.DataFrame({
        'Open': [1,2,3,4,5,6,7,8,9,10],
        'High': [2,3,4,5,6,7,8,9,10,11],
        'Low': [0,1,2,3,4,5,6,7,8,9],
        'Close': [1,2,3,4,5,6,7,8,9,10],
        'Volume': [100]*10
    }, index=dates)
    mock_ticker.return_value.history.return_value = data
    mock_ticker.return_value.info = MagicMock()
    mock_ticker.return_value.info.get.return_value = 'Test Company'
    # Insert symbol
    insert_or_update_symbols(session, ['TEST'])
    # Fetch and store data
    fetched = get_stock_data('TEST', '2024-01-01', '2024-01-10')
    assert fetched is not None
    store_stock_data(session, 'TEST', fetched)
    # Check DB
    symbol = session.query(StockSymbol).filter_by(symbol='TEST').first()
    assert symbol is not None
    stock_rows = session.query(StockData).filter_by(symbol_id=symbol.id).all()
    assert len(stock_rows) == 10
    # Check moving averages
    for row in stock_rows:
        assert row.close_price is not None
        # 5-day MA is None for first 4 days, then should be a float
        if row.date >= pd.Timestamp('2024-01-05').date():
            assert row.ma_5_day is not None
        else:
            assert row.ma_5_day is None 