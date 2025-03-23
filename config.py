import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# Database Credentials
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

# Construct the SQLAlchemy connection string
DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"

if not all([USER, PASSWORD, HOST, PORT, DBNAME]):
    print("⚠️ WARNING: Missing database credentials in .env!")

# print("🔍 DATABASE_URL:", DATABASE_URL)  # Debugging step