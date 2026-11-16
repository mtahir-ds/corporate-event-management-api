"""Pydantic Request Validation and Response Schemas.

This module defines Pydantic schemas for the Corporate Event Management API.
Schemas enforce strict data validation rules on incoming HTTP requests (create, update)
and define serialization contracts for HTTP responses using Pydantic v2 from_attributes.
"""

from datetime import datetime  # Provides date and time handling for event scheduling
from typing import Optional  # Allows fields to be optional in update operations
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator  # Core Pydantic tools for validation and serialization


class EventBase(BaseModel):
    """Base schema for corporate event data.

    Defines shared event fields and fundamental data validation constraints
    enforced across both creation and response serialization.
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Non-empty title of the corporate event.",
        examples=["Annual Tech Symposium 2026"],
    )  # Enforces that event title cannot be an empty string
    description: Optional[str] = Field(
        default=None,
        description="Optional detailed overview or agenda of the event.",
        examples=["A full-day conference exploring cloud architectures and AI agents."],
    )  # Optional descriptive text for the event
    date: datetime = Field(
        ...,
        description="Scheduled date and time of the event in ISO 8601 format.",
        examples=["2026-11-20T09:00:00"],
    )  # Validates that the input is a valid ISO datetime format
    location: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Physical venue or virtual meeting URL.",
        examples=["Main Auditorium / https://meet.acme.com/tech-symposium"],
    )  # Enforces a valid venue or meeting link
    max_capacity: int = Field(
        ...,
        gt=0,
        description="Maximum number of attendees allowed. Must be greater than zero.",
        examples=[100],
    )  # Enforces assignment rule: capacity must be strictly greater than 0

    @field_validator("title")
    @classmethod
    def validate_title_not_blank(cls, value: str) -> str:
        """Validate that the title is not empty or composed solely of whitespace.

        Inputs:
            value (str): The incoming event title string.

        Outputs:
            str: Cleaned, whitespace-stripped title string.

        Raises:
            ValueError: If the title is empty or contains only spaces.
        """
        stripped_value = value.strip()  # Removes leading and trailing whitespace
        if not stripped_value:
            raise ValueError("Event title cannot be empty or consist solely of whitespace.")  # Rejects whitespace-only titles
        return stripped_value


class EventCreate(EventBase):
    """Schema for creating a new corporate event.

    Inherits all required fields and validation rules from EventBase.
    Used as the request body schema for POST /events.
    """

    pass  # All necessary validation logic and required fields are inherited from EventBase


class EventUpdate(BaseModel):
    """Schema for updating an existing corporate event.

    All fields are optional to allow partial updates via PUT /events/{id}.
    Any provided field is validated against the required constraints.
    """

    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Updated non-empty event title.",
    )  # Optional new title
    description: Optional[str] = Field(
        default=None,
        description="Updated event description.",
    )  # Optional new description
    date: Optional[datetime] = Field(
        default=None,
        description="Updated scheduled date and time.",
    )  # Optional new date
    location: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Updated venue or meeting URL.",
    )  # Optional new location
    max_capacity: Optional[int] = Field(
        default=None,
        gt=0,
        description="Updated capacity, must be greater than zero.",
    )  # Optional new capacity (must still be > 0 if provided)

    @field_validator("title")
    @classmethod
    def validate_update_title(cls, value: Optional[str]) -> Optional[str]:
        """Validate that if a title is provided, it is not blank whitespace.

        Inputs:
            value (Optional[str]): The incoming optional title.

        Outputs:
            Optional[str]: Cleaned title or None.
        """
        if value is not None:
            stripped_value = value.strip()
            if not stripped_value:
                raise ValueError("Updated event title cannot be empty or blank.")
            return stripped_value
        return value


class EventResponse(EventBase):
    """Schema for serializing corporate event data in API responses.

    Extends EventBase with the database-generated primary key ID and
    enables ORM mode for compatibility with SQLAlchemy models.
    """

    id: int = Field(
        ...,
        description="Unique database identifier for the event.",
        examples=[1],
    )  # Database primary key ID

    # Pydantic v2 configuration to read data directly from SQLAlchemy ORM attributes
    model_config = ConfigDict(from_attributes=True)


class RegistrationBase(BaseModel):
    """Base schema for attendee registrations.

    Defines the employee's name and corporate email with strict format validation.
    """

    employee_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Full name of the registering employee.",
        examples=["Sarah Connor"],
    )  # Required employee name
    employee_email: EmailStr = Field(
        ...,
        description="Valid corporate email address of the attendee.",
        examples=["sarah.connor@acme.com"],
    )  # Enforces valid email syntax (user@domain.com)

    @field_validator("employee_name")
    @classmethod
    def validate_name_not_blank(cls, value: str) -> str:
        """Validate that employee name is not blank whitespace.

        Inputs:
            value (str): The incoming employee name string.

        Outputs:
            str: Cleaned employee name.
        """
        stripped_value = value.strip()
        if not stripped_value:
            raise ValueError("Employee name cannot be empty or consist solely of whitespace.")
        return stripped_value


class RegistrationCreate(RegistrationBase):
    """Schema for registering an employee for an event.

    Used as the request body schema for POST /events/{id}/registrations.
    Inherits all validation constraints from RegistrationBase.
    """

    pass  # The event_id is supplied via URL path parameter in the route


class RegistrationResponse(RegistrationBase):
    """Schema for returning registration details in API responses.

    Includes database-assigned fields such as registration ID, event ID,
    and registration timestamp.
    """

    id: int = Field(
        ...,
        description="Unique database identifier for this registration.",
        examples=[1],
    )  # Registration primary key ID
    event_id: int = Field(
        ...,
        description="Foreign key ID of the event the employee registered for.",
        examples=[1],
    )  # Associated event ID
    registered_at: datetime = Field(
        ...,
        description="Timestamp when the registration was recorded in the database.",
        examples=["2026-11-17T02:15:00"],
    )  # Creation timestamp

    # Pydantic v2 configuration to read data directly from SQLAlchemy ORM attributes
    model_config = ConfigDict(from_attributes=True)
