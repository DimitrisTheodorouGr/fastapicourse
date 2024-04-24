from .database import SessionLocal, engine
from .models import Ranches
from .routers import auth
from fastapi import FastAPI, Depends,APIRouter
from typing import Union, Annotated
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session



# Define the list of origins allowed to make cross-origin requests
origins = [
    "http://localhost",
    "http://localhost:8000",
    "https://project-wellness.ece.uowm.gr",
]

app = FastAPI(root_path="/wellness-api")

app.include_router(auth.router)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

#Function for opening and closing connection with the database after each query.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#Dependancy connection
db_dependancy = Annotated[Session, Depends(get_db)]


# Example API endpoint
@app.get("/read-all-ranches")
def read_all_ranches(db: db_dependancy):
    return db.query(Ranches).all()
