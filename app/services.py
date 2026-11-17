"""Business Logic and Database Operations Service Layer.

This module encapsulates all database transactions, CRUD operations, and core business
rules for Events and Registrations in the Corporate Event Management API. It keeps API
routes thin by centralizing entity queries, updates, cascades, and validation checks.
"""

from typing import List  # Provides type hints for list return values
from fastapi import HTTPException, status  # Used to raise standard HTTP status exceptions for business rule violations
from sqlalchemy.orm import Session  # Provides transactional database session type hints
from app.models import Event, Registration  # SQLAlchemy ORM models representing database tables
from app.schemas import EventCreate, EventUpdate, RegistrationCreate  # Pydantic validation schemas for incoming request data


# ============================================================================
# EVENT CRUD SERVICES
# ============================================================================

def create_event(db: Session, event: EventCreate) -> Event:
    """Create and persist a new corporate event in the database.

    Instantiates an Event ORM model from validated schema data, commits it to
    PostgreSQL, and refreshes the instance to obtain its database-generated ID.

    Inputs:
        db (Session): Active SQLAlchemy database session.
        event (EventCreate): Validated event creation schema payload.

    Outputs:
        Event: The newly created Event database record.
    """
    event_instance = Event(**event.model_dump())  # Unpacks validated schema fields into the SQLAlchemy model
    db.add(event_instance)  # Stages the new event entity in the current database session
    db.commit()  # Commits the transaction to persist the event in PostgreSQL
    db.refresh(event_instance)  # Refreshes the instance from the database to populate the generated primary key ID
    return event_instance


def get_events(db: Session) -> List[Event]:
    """Retrieve all corporate events from the database.

    Inputs:
        db (Session): Active SQLAlchemy database session.

    Outputs:
        List[Event]: List of all event records stored in the database.
    """
    return db.query(Event).all()  # Executes SELECT * query across the events table


def get_event_by_id(db: Session, event_id: int) -> Event:
    """Retrieve a single corporate event by its unique primary key ID.

    Inputs:
        db (Session): Active SQLAlchemy database session.
        event_id (int): Primary key identifier of the event to locate.

    Outputs:
        Event: The located Event database record.

    Raises:
        HTTPException: 404 Not Found if no event exists with the provided ID.
    """
    event = db.query(Event).filter(Event.id == event_id).first()  # Queries the first matching event by ID
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with id {event_id} not found."
        )  # Rejects request when event does not exist
    return event


def update_event(db: Session, event_id: int, event_update: EventUpdate) -> Event:
    """Update an existing corporate event with partial or full field updates.

    Fetches the existing event record, applies any fields explicitly set in the
    update schema, commits the changes, and returns the refreshed model.

    Inputs:
        db (Session): Active SQLAlchemy database session.
        event_id (int): Primary key identifier of the event to update.
        event_update (EventUpdate): Validated update schema containing modified fields.

    Outputs:
        Event: The updated Event database record.

    Raises:
        HTTPException: 404 Not Found if the event to update does not exist.
    """
    event = db.query(Event).filter(Event.id == event_id).first()  # Finds the existing event record
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with id {event_id} not found."
        )  # Enforces 404 if event is missing

    update_data = event_update.model_dump(exclude_unset=True)  # Extracts only fields explicitly sent by client
    for key, value in update_data.items():
        setattr(event, key, value)  # Dynamically updates each modified attribute on the ORM model

    db.commit()  # Commits the update transaction to PostgreSQL
    db.refresh(event)  # Refreshes model to ensure all attributes match the committed database state
    return event


def delete_event(db: Session, event_id: int) -> bool:
    """Delete a corporate event and cascade delete its associated registrations.

    Inputs:
        db (Session): Active SQLAlchemy database session.
        event_id (int): Primary key identifier of the event to delete.

    Outputs:
        bool: True if deletion was successful.

    Raises:
        HTTPException: 404 Not Found if the event to delete does not exist.
    """
    event = db.query(Event).filter(Event.id == event_id).first()  # Finds the target event record
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with id {event_id} not found."
        )  # Enforces 404 if event is missing

    db.delete(event)  # Stages the event for deletion; SQLAlchemy cascades removal to registrations
    db.commit()  # Commits deletion transaction to permanently remove records
    return True


# ============================================================================
# REGISTRATION SERVICES & BUSINESS RULES
# ============================================================================

def create_registration(db: Session, event_id: int, registration: RegistrationCreate) -> Registration:
    """Register an employee for a corporate event while strictly enforcing business rules.

    Enforces 3 mandatory business rules:
        1. Reject registration if target event does not exist (404 Not Found).
        2. Prevent duplicate registrations by the same employee for the same event (409 Conflict).
        3. Prevent registrations if the event has reached its maximum capacity (409 Conflict).

    Inputs:
        db (Session): Active SQLAlchemy database session.
        event_id (int): Foreign key identifier of the event to attend.
        registration (RegistrationCreate): Validated employee registration schema payload.

    Outputs:
        Registration: The newly created and committed Registration database record.

    Raises:
        HTTPException: 404 Not Found if the target event does not exist.
        HTTPException: 409 Conflict if the employee is already registered.
        HTTPException: 409 Conflict if the event capacity is already full.
    """
    # Rule 1: Check if the target event exists
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with id {event_id} not found."
        )

    # Rule 2: Prevent duplicate employee registration for this specific event
    existing_registration = db.query(Registration).filter(
        Registration.event_id == event_id,
        Registration.employee_email == registration.employee_email
    ).first()
    if existing_registration:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Employee '{registration.employee_email}' is already registered for this event."
        )

    # Rule 3: Enforce maximum attendee capacity limit
    current_attendee_count = db.query(Registration).filter(Registration.event_id == event_id).count()
    if current_attendee_count >= event.max_capacity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Event has reached maximum attendee capacity."
        )

    # Instantiate the Registration record linking the foreign key event_id with employee data
    registration_instance = Registration(
        event_id=event_id,
        **registration.model_dump()
    )
    db.add(registration_instance)  # Stages new registration in the session
    db.commit()  # Commits record to PostgreSQL
    db.refresh(registration_instance)  # Refreshes instance to populate generated ID and timestamp
    return registration_instance


def get_registrations_by_event(db: Session, event_id: int) -> List[Registration]:
    """Retrieve all attendee registrations for a specific corporate event.

    Verifies the event exists first before querying its registrations.

    Inputs:
        db (Session): Active SQLAlchemy database session.
        event_id (int): Primary key identifier of the parent event.

    Outputs:
        List[Registration]: All registration records associated with the specified event.

    Raises:
        HTTPException: 404 Not Found if the parent event does not exist.
    """
    event = db.query(Event).filter(Event.id == event_id).first()  # Validates that the event exists
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with id {event_id} not found."
        )  # Returns 404 if querying registrations of a non-existent event

    return db.query(Registration).filter(Registration.event_id == event_id).all()  # Retrieves registrations filtered by event_id


def delete_registration(db: Session, registration_id: int) -> bool:
    """Cancel and delete an employee's event registration.

    Inputs:
        db (Session): Active SQLAlchemy database session.
        registration_id (int): Primary key identifier of the registration to cancel.

    Outputs:
        bool: True if cancellation was successful.

    Raises:
        HTTPException: 404 Not Found if the registration does not exist.
    """
    registration = db.query(Registration).filter(Registration.id == registration_id).first()  # Finds target registration
    if not registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registration with id {registration_id} not found."
        )  # Returns 404 if registration not found

    db.delete(registration)  # Stages deletion of the registration record
    db.commit()  # Commits deletion transaction
    return True
