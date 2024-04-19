import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env.

# Determine the current running environment
environment = os.getenv("ENVIRONMENT", "dev")

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