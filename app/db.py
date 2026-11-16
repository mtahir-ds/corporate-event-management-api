"""Database Configuration and Connection Setup.

This module initializes the database connection engine, session management,
declarative base class, and utility functions for session lifecycle management
and table creation in PostgreSQL using SQLAlchemy.
"""

import os  # Provides access to environment variables to securely read configuration
from dotenv import load_dotenv  # Loads environment variables from a .env file to keep secrets out of source code
from sqlalchemy import create_engine  # Creates the database engine to establish and manage connections to the database
from sqlalchemy.orm import sessionmaker, declarative_base  # sessionmaker manages DB sessions/transactions; declarative_base provides a base class for ORM models

load_dotenv()  # Reads the .env file and loads variables into the environment so they are accessible to the app

# Retrieves the DB connection URL from the environment (supports either DATABASE_URL or SQLALCHEMY_DATABASE_URL)
# Retrieves the DB connection URL from the environment (supports either DATABASE_URL or SQLALCHEMY_DATABASE_URL)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("SQLALCHEMY_DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("Database connection URL is not set in the .env file")  # Ensures application fails fast if configuration is missing

# Ensure SQLAlchemy explicitly uses the psycopg2 driver for PostgreSQL connections
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif SQLALCHEMY_DATABASE_URL.startswith("postgresql://") and not SQLALCHEMY_DATABASE_URL.startswith("postgresql+"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

engine = create_engine(SQLALCHEMY_DATABASE_URL)  # Initializes the connection pool and dialect to communicate with the database
SessionLocal = sessionmaker(
    autocommit=False,  # Prevents automatic commits so transactions remain explicit and atomic
    autoflush=False,  # Prevents premature flushing of queries before committing or explicitly flushing
    bind=engine,  # Associates the session factory with our configured database engine
)

Base = declarative_base()  # Base class for all ORM models to inherit from and register their schema metadata


def get_db():
    """Create and yield a database session per request.

    Acts as a FastAPI dependency to provide an isolated database session and
    guarantees session cleanup upon completion to avoid connection leaks.

    Inputs:
        None

    Outputs:
        Generator: Yields an active SQLAlchemy Session instance.
    """
    db = SessionLocal()  # Instantiates a new database session for the request

    try:
        yield db  # Provides the session to the calling endpoint/context
    except Exception as e:
        print(f"Exception: {e}")  # Logs any error encountered during session usage
        raise  # Re-raises the exception so FastAPI can manage the HTTP error response cycle
    finally:
        db.close()  # Ensures the session is closed when the request lifecycle ends


def create_table():
    """Create all database tables defined in the ORM models.

    Emits DDL statements to create any missing tables bound to the declarative Base metadata.

    Inputs:
        None

    Outputs:
        None
    """
    try:
        from app import models  # Imports ORM models as a package to register mapped tables with Base.metadata before creation
    except ImportError:
        import models  # Fallback import if running directly inside the app folder
    Base.metadata.create_all(
        bind=engine
    )  # Generates and executes CREATE TABLE SQL statements for all registered models


if __name__ == "__main__":
    create_table()
    print("Tables created")