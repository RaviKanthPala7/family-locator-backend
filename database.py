from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

# Create SQLAlchemy Engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Session Local (Database Session)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base Class for ORM Models
Base = declarative_base()
