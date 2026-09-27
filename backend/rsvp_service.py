from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import Event, RSVP, User


VALID_RSVP_STATUSES = {
    "GOING",
    "MAYBE",
    "NOT_GOING",
}


def utc_now():
    return datetime.now(timezone.utc)


def get_rsvp_counts(db: Session, event_id: int):
    """
    Return the current RSVP counts for an event.
    """

    rows = (
        db.query(
            RSVP.status,
            func.count(RSVP.id)
        )
        .filter(RSVP.event_id == event_id)
        .group_by(RSVP.status)
        .all()
    )

    counts = {
        "GOING": 0,
        "MAYBE": 0,
        "NOT_GOING": 0,
    }

    for status, count in rows:
        if status in counts:
            counts[status] = count

    return {
        "going": counts["GOING"],
        "maybe": counts["MAYBE"],
        "not_going": counts["NOT_GOING"],
    }


def get_existing_rsvp(
    db: Session,
    event_id: int,
    user_id: int,
) -> Optional[RSVP]:
    """
    Find the user's existing RSVP for an event.
    """

    return (
        db.query(RSVP)
        .filter(
            RSVP.event_id == event_id,
            RSVP.user_id == user_id,
        )
        .first()
    )


def check_event_exists(
    db: Session,
    event_id: int,
) -> Event:
    """
    Retrieve an event or raise an error.
    """

    event = (
        db.query(Event)
        .filter(Event.id == event_id)
        .first()
    )

    if not event:
        raise ValueError("Event not found.")

    return event


def validate_rsvp_status(status: str):
    """
    Make sure only valid RSVP statuses are accepted.
    """

    status = status.upper()

    if status not in VALID_RSVP_STATUSES:
        raise ValueError(
            "Invalid RSVP status. "
            "Use GOING, MAYBE, or NOT_GOING."
        )

    return status


def create_or_update_rsvp(
    db: Session,
    event_id: int,
    user: User,
    status: str,
):
    """
    Create a new RSVP or update the user's existing RSVP.

    Rules:

    1. One RSVP per user per event.
    2. GOING cannot exceed capacity.
    3. Existing RSVP can be changed.
    4. Database transaction protects the operation.
    """

    status = validate_rsvp_status(status)

    event = check_event_exists(db, event_id)

    now = utc_now()

    # Check whether registration is closed.
    if getattr(event, "registration_deadline", None):

        deadline = event.registration_deadline

        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)

        if now > deadline:
            raise ValueError(
                "The registration deadline has passed."
            )

    # Do not allow RSVP for cancelled/completed events.
    event_status = getattr(event, "status", "PUBLISHED")

    if event_status in {"CANCELLED", "COMPLETED"}:
        raise ValueError(
            f"RSVP is not allowed because the event is {event_status.lower()}."
        )

    existing = get_existing_rsvp(
        db,
        event_id,
        user.id,
    )

    # ---------------------------------------------------------
    # Existing RSVP
    # ---------------------------------------------------------

    if existing:

        old_status = existing.status

        # Nothing actually changes.
        if old_status == status:
            return existing, get_rsvp_counts(db, event_id)

        # If changing TO GOING, check capacity.
        if status == "GOING" and old_status != "GOING":

            counts = get_rsvp_counts(
                db,
                event_id,
            )

            capacity = event.maximum_capacity

            if counts["going"] >= capacity:
                raise ValueError(
                    "This event is full. "
                    "You cannot change your RSVP to GOING."
                )

        existing.status = status
        existing.updated_at = now

        db.commit()
        db.refresh(existing)

        counts = get_rsvp_counts(
            db,
            event_id,
        )

        update_event_status(
            db,
            event,
            counts["going"],
        )

        return existing, counts

    # ---------------------------------------------------------
    # New RSVP
    # ---------------------------------------------------------

    if status == "GOING":

        counts = get_rsvp_counts(
            db,
            event_id,
        )

        capacity = event.maximum_capacity

        if counts["going"] >= capacity:
            raise ValueError(
                "This event is full. "
                "You cannot RSVP GOING."
            )

    new_rsvp = RSVP(
        event_id=event_id,
        user_id=user.id,
        status=status,
        responded_at=now,
        updated_at=now,
    )

    db.add(new_rsvp)

    db.commit()
    db.refresh(new_rsvp)

    counts = get_rsvp_counts(
        db,
        event_id,
    )

    update_event_status(
        db,
        event,
        counts["going"],
    )

    return new_rsvp, counts


def cancel_rsvp(
    db: Session,
    event_id: int,
    user: User,
):
    """
    Cancel the user's RSVP.

    Instead of deleting the record, we change it to
    NOT_GOING. This keeps useful historical data.
    """

    event = check_event_exists(
        db,
        event_id,
    )

    existing = get_existing_rsvp(
        db,
        event_id,
        user.id,
    )

    if not existing:
        raise ValueError(
            "You do not have an RSVP for this event."
        )

    existing.status = "NOT_GOING"
    existing.updated_at = utc_now()

    db.commit()
    db.refresh(existing)

    counts = get_rsvp_counts(
        db,
        event_id,
    )

    update_event_status(
        db,
        event,
        counts["going"],
    )

    return existing, counts


def update_event_status(
    db: Session,
    event: Event,
    going_count: int,
):
    """
    Automatically update event status.

    PUBLISHED
        ↓
    FULL

    when Going reaches maximum capacity.
    """

    if getattr(event, "status", None) in {
        "CANCELLED",
        "COMPLETED",
    }:
        return

    capacity = event.maximum_capacity

    if going_count >= capacity:
        event.status = "FULL"
    else:
        event.status = "PUBLISHED"

    db.commit()