from sqlalchemy import create_engine
from config import DATABASE_URL

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Test the connection
try:
    with engine.connect() as connection:
        print("✅ Connection to the database was successful!")
except Exception as e:
    print(f"❌ Failed to connect: {e}")
