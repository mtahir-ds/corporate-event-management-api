"""FastAPI Application and Route Handlers.

This module initializes the FastAPI application instance, configures OpenAPI documentation
metadata, and defines the HTTP route handlers for Acme Corp's Corporate Event Management API.
Following the separation-of-concerns pattern, these route handlers remain thin by delegating
all persistence, querying, and business rule enforcement to the service layer.
"""

from typing import List  # Type hint for returning lists of entities in response models
from fastapi import FastAPI, Depends, status  # Core FastAPI classes for routing, dependency injection, and status codes
from sqlalchemy.orm import Session  # Provides type hints for the database session dependency

from app.db import get_db  # Dependency generator providing isolated database sessions per request
from app.schemas import (
    EventCreate,  # Schema validating incoming event creation payloads
    EventUpdate,  # Schema validating partial or full event update payloads
    EventResponse,  # Schema serializing event entities into JSON responses
    RegistrationCreate,  # Schema validating incoming employee registration payloads
    RegistrationResponse,  # Schema serializing registration entities into JSON responses
)
from app import services  # Business logic and database operations service module

# Initialize the central FastAPI application with OpenAPI metadata
app = FastAPI(
    title="Corporate Event Management API",  # Displayed as title in Swagger UI
    description="Internal REST API for managing corporate events and employee registrations at Acme Corp.",  # API description in Swagger UI
    version="1.0.0",  # Semantic API version
    docs_url="/docs",  # Interactive Swagger UI endpoint path
    redoc_url="/redoc",  # ReDoc alternative documentation endpoint path
)


# ============================================================================
# ROOT / HEALTH CHECK ENDPOINT
# ============================================================================

@app.get(
    "/",
    summary="API Health Check & Welcome",
    description="Returns a welcome message, API status, and a direct link to the interactive Swagger documentation.",
    tags=["System"],
)
def root():
    """Handle root requests to verify API availability and provide documentation links.

    Inputs:
        None

    Outputs:
        dict: Welcome message and docs URL pointer.
    """
    return {
        "message": "Welcome to the Corporate Event Management API",  # Welcome greeting
        "docs": "/docs",  # Convenience URL pointing to interactive Swagger UI
    }


# ============================================================================
# EVENT ENDPOINTS (CRUD OPERATIONS)
# ============================================================================

@app.post(
    "/events",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new event",
    description="Creates a new corporate event with validated title, description, date, location, and capacity.",
    tags=["Events"],
)
def create_event(
    event: EventCreate,
    db: Session = Depends(get_db),
):
    """Create and persist a new corporate event.

    Inputs:
        event (EventCreate): Validated request body with event details.
        db (Session): Database session injected via FastAPI Depends.

    Outputs:
        EventResponse: The newly created Event database record.
    """
    return services.create_event(db=db, event=event)  # Delegates persistence to the service layer


@app.get(
    "/events",
    response_model=List[EventResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve all events",
    description="Fetches a list of all scheduled corporate events.",
    tags=["Events"],
)
def get_events(
    db: Session = Depends(get_db),
):
    """Retrieve all corporate events from the system.

    Inputs:
        db (Session): Database session injected via FastAPI Depends.

    Outputs:
        List[EventResponse]: Collection of all stored events.
    """
    return services.get_events(db=db)  # Delegates retrieval to the service layer


@app.get(
    "/events/{id}",
    response_model=EventResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve an event by ID",
    description="Fetches detailed information for a specific corporate event by its primary key ID.",
    tags=["Events"],
)
def get_event(
    id: int,
    db: Session = Depends(get_db),
):
    """Retrieve a single corporate event by ID.

    Inputs:
        id (int): Primary key identifier of the event.
        db (Session): Database session injected via FastAPI Depends.

    Outputs:
        EventResponse: The matching Event database record.

    Raises:
        HTTPException: 404 Not Found if no event exists with the given ID.
    """
    return services.get_event_by_id(db=db, event_id=id)  # Delegates lookup to the service layer


@app.put(
    "/events/{id}",
    response_model=EventResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an existing event",
    description="Updates one or more fields of an existing corporate event.",
    tags=["Events"],
)
def update_event(
    id: int,
    event_update: EventUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing event by applying modified fields.

    Inputs:
        id (int): Primary key identifier of the event to modify.
        event_update (EventUpdate): Validated update payload with modified fields.
        db (Session): Database session injected via FastAPI Depends.

    Outputs:
        EventResponse: The updated Event database record.

    Raises:
        HTTPException: 404 Not Found if the event does not exist.
    """
    return services.update_event(db=db, event_id=id, event_update=event_update)  # Delegates update to service layer


@app.delete(
    "/events/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an event",
    description="Permanently deletes an event and cascades deletion to all its registrations.",
    tags=["Events"],
)
def delete_event(
    id: int,
    db: Session = Depends(get_db),
):
    """Delete a corporate event and all its associated registrations.

    Inputs:
        id (int): Primary key identifier of the event to delete.
        db (Session): Database session injected via FastAPI Depends.

    Outputs:
        None: Returns HTTP 204 No Content upon successful deletion.

    Raises:
        HTTPException: 404 Not Found if the event does not exist.
    """
    services.delete_event(db=db, event_id=id)  # Delegates deletion and cascade to the service layer
    return None  # HTTP 204 No Content specifies an empty response body


# ============================================================================
# REGISTRATION ENDPOINTS
# ============================================================================

@app.post(
    "/events/{id}/registrations",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register for an event",
    description="Registers an employee for a specific event while enforcing capacity and duplicate prevention rules.",
    tags=["Registrations"],
)
def create_registration(
    id: int,
    registration: RegistrationCreate,
    db: Session = Depends(get_db),
):
    """Register an employee attendee for a corporate event.

    Inputs:
        id (int): Foreign key event ID path parameter.
        registration (RegistrationCreate): Validated registration payload (employee name and email).
        db (Session): Database session injected via FastAPI Depends.

    Outputs:
        RegistrationResponse: The created Registration database record.

    Raises:
        HTTPException: 404 Not Found if the event does not exist.
        HTTPException: 409 Conflict if employee is already registered.
        HTTPException: 409 Conflict if event is at maximum capacity.
    """
    return services.create_registration(db=db, event_id=id, registration=registration)  # Delegates to service layer


@app.get(
    "/events/{id}/registrations",
    response_model=List[RegistrationResponse],
    status_code=status.HTTP_200_OK,
    summary="View event registrations",
    description="Retrieves a list of all registered employee attendees for a specific event.",
    tags=["Registrations"],
)
def get_registrations(
    id: int,
    db: Session = Depends(get_db),
):
    """Retrieve all attendee registrations for a given event.

    Inputs:
        id (int): Foreign key event ID path parameter.
        db (Session): Database session injected via FastAPI Depends.

    Outputs:
        List[RegistrationResponse]: Collection of all registrations for this event.

    Raises:
        HTTPException: 404 Not Found if the parent event does not exist.
    """
    return services.get_registrations_by_event(db=db, event_id=id)  # Delegates retrieval to service layer


@app.delete(
    "/registrations/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel a registration",
    description="Cancels and permanently deletes an employee event registration by its registration ID.",
    tags=["Registrations"],
)
def delete_registration(
    id: int,
    db: Session = Depends(get_db),
):
    """Cancel and delete an attendee registration.

    Inputs:
        id (int): Primary key identifier of the registration to cancel.
        db (Session): Database session injected via FastAPI Depends.

    Outputs:
        None: Returns HTTP 204 No Content upon successful deletion.

    Raises:
        HTTPException: 404 Not Found if the registration does not exist.
    """
    services.delete_registration(db=db, registration_id=id)  # Delegates cancellation to service layer
    return None  # HTTP 204 No Content specifies an empty response body
