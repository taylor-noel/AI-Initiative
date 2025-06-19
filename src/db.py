import time
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Date, Numeric, BigInteger, DateTime, ForeignKey, UniqueConstraint, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

class StockSymbol(Base):
    __tablename__ = 'stock_symbols'
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), unique=True, nullable=False)
    company_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
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
    symbol = relationship("StockSymbol", back_populates="stock_data")
    __table_args__ = (UniqueConstraint('symbol_id', 'date', name='uq_symbol_date'),)

def wait_for_database(db_url):
    print("Waiting for database to be ready...")
    for i in range(30):
        try:
            engine = create_engine(
                db_url,
                echo=False,
                pool_pre_ping=True,
                pool_recycle=300,
                connect_args={
                    "connect_timeout": 10,
                    "application_name": "stock_analysis"
                }
            )
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            print(f"Database connection successful after {i+1} attempts")
            return engine
        except Exception as e:
            print(f"Database connection attempt {i+1}/30 failed: {e}")
            if i < 29:
                time.sleep(2)
    raise Exception("Could not connect to the database after 30 attempts")

def create_tables(engine):
    try:
        Base.metadata.create_all(engine)
        print("Database schema created/verified!")
    except Exception as e:
        print(f"Error creating tables: {e}")
        raise

def get_session(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)() 