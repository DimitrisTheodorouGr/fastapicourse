import os

from fastapi import FastAPI
from typing import Union
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env.

# Determine the current running environment
environment = os.getenv("ENVIRONMENT", "dev")


# Define the list of origins allowed to make cross-origin requests
origins = [
    "http://localhost",
    "http://localhost:8000",
    "https://project-wellness.ece.uowm.gr",
]

app = FastAPI(root_path="/wellness-api")

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Choose the database URL based on the environment
if environment.lower() == "prod":
    SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL_PROD")
else:
    SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL_DEV")

# Create the SQLAlchemy engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)

# Session factory bound to the engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative class definitions
Base = declarative_base()

# Test database connection
def test_db_connection():
    try:
        # Create a new connection to the database
        with engine.connect() as connection:
            # Execute a simple query (get the current time from the database server)
            result = connection.execute(text("SELECT now()"))
            current_time = result.scalar()
            return f"Database connection successful, current server time is: {current_time}"
    except Exception as e:
        return f"Database connection failed: {str(e)}"

# API endpoint to test database connectivity
@app.get("/test-db")
def test_database():
    return test_db_connection()

# Example API endpoint
@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}
