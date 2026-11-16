"""SQLAlchemy Database Models.

This module defines the SQLAlchemy ORM models representing the core database tables
for the Corporate Event Management API: Event and Registration. It establishes table
schemas, column types, relationships, cascade behaviors, and database constraints.
"""

from datetime import datetime  # Provides datetime objects for timestamp defaults
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint, func  # Core column and schema constructs
from sqlalchemy.orm import relationship  # Establishes bidirectional ORM relationships between tables

try:
    from app.db import Base  # Imports declarative Base when running as a package from the project root
except ImportError:
    from db import Base  # Fallback import for running directly inside the app folder


class Event(Base):
    """Event ORM Model.

    Represents a corporate event organized by Acme Corp, including its title,
    schedule, location venue, and maximum attendee capacity.

    Attributes:
        id (int): Primary key unique identifier.
        title (str): Name or title of the event.
        description (str): Detailed overview or agenda.
        date (datetime): Scheduled date and time for the event.
        location (str): Physical venue or virtual meeting link.
        max_capacity (int): Maximum number of allowed registrations.
        registrations (list[Registration]): Related registrations for this event.
    """

    __tablename__ = "events"  # Explicitly names the PostgreSQL table in the database

    id = Column(Integer, primary_key=True, index=True)  # Unique primary key ID, indexed for fast lookups
    title = Column(String, nullable=False, index=True)  # Event title, required and indexed for title searches
    description = Column(Text, nullable=True)  # Detailed event description, optional
    date = Column(DateTime, nullable=False)  # Scheduled date and time of the event, required
    location = Column(String, nullable=False)  # Physical room or online meeting URL, required
    max_capacity = Column(Integer, nullable=False)  # Maximum attendee capacity limit, required

    # Defines one-to-many relationship with Registration; cascades delete if event is removed
    registrations = relationship(
        "Registration",
        back_populates="event",
        cascade="all, delete-orphan",  # Deleting an event automatically removes its attendee registrations
    )


class Registration(Base):
    """Registration ORM Model.

    Represents an employee attendee registration for a specific corporate event.
    Enforces a unique constraint to prevent duplicate registrations by the same employee.

    Attributes:
        id (int): Primary key unique identifier for the registration record.
        event_id (int): Foreign key referencing the associated event ID.
        employee_name (str): Full name of the registering employee.
        employee_email (str): Corporate email address of the employee.
        registered_at (datetime): Timestamp when the registration was created.
        event (Event): Parent event instance associated with this registration.
    """

    __tablename__ = "registrations"  # Explicitly names the PostgreSQL table in the database

    id = Column(Integer, primary_key=True, index=True)  # Unique primary key ID, indexed for fast lookups
    event_id = Column(
        Integer,
        ForeignKey("events.id", ondelete="CASCADE"),  # References events table primary key; cascades delete on foreign key
        nullable=False,  # Ensures a registration is always linked to an existing event
    )
    employee_name = Column(String, nullable=False)  # Full name of the registering employee, required
    employee_email = Column(String, nullable=False, index=True)  # Employee email address, required and indexed
    registered_at = Column(
        DateTime,
        default=func.now(),  # Sets default to server timestamp when record is inserted
        nullable=False,  # Timestamp is required and automatically populated
    )

    # Defines many-to-one relationship back to the parent Event model
    event = relationship("Event", back_populates="registrations")

    # Enforces database-level constraint: an employee cannot register for the same event twice
    __table_args__ = (
        UniqueConstraint("event_id", "employee_email", name="uq_event_employee"),
    )
