from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="ATTENDEE")
    created_at = Column(DateTime, default=datetime.utcnow)

    events = relationship(
        "Event",
        back_populates="organizer",
        cascade="all, delete-orphan",
    )

    rsvps = relationship(
        "RSVP",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    notifications = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)

    organizer_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    event_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    event_type = Column(String(100), nullable=False)

    event_date = Column(String(20), nullable=False)
    start_time = Column(String(20), nullable=False)
    end_time = Column(String(20), nullable=False)

    venue = Column(String(255), nullable=True)
    online_link = Column(String(500), nullable=True)

    maximum_capacity = Column(Integer, nullable=False)

    registration_deadline = Column(String(30), nullable=True)

    status = Column(
        String(30),
        nullable=False,
        default="DRAFT",
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    organizer = relationship(
        "User",
        back_populates="events",
    )

    rsvps = relationship(
        "RSVP",
        back_populates="event",
        cascade="all, delete-orphan",
    )

    announcements = relationship(
        "Announcement",
        back_populates="event",
        cascade="all, delete-orphan",
    )


class RSVP(Base):
    __tablename__ = "rsvps"

    id = Column(Integer, primary_key=True, index=True)

    event_id = Column(
        Integer,
        ForeignKey("events.id"),
        nullable=False,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    status = Column(
        String(20),
        nullable=False,
    )

    responded_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    __table_args__ = (
        UniqueConstraint(
            "event_id",
            "user_id",
            name="unique_event_user_rsvp",
        ),
    )

    event = relationship(
        "Event",
        back_populates="rsvps",
    )

    user = relationship(
        "User",
        back_populates="rsvps",
    )


class Waitlist(Base):
    __tablename__ = "waitlist"

    id = Column(Integer, primary_key=True, index=True)

    event_id = Column(
        Integer,
        ForeignKey("events.id"),
        nullable=False,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    position = Column(Integer, nullable=False)

    status = Column(
        String(30),
        nullable=False,
        default="WAITLISTED",
    )

    joined_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    __table_args__ = (
        UniqueConstraint(
            "event_id",
            "user_id",
            name="unique_event_user_waitlist",
        ),
    )


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)

    event_id = Column(
        Integer,
        ForeignKey("events.id"),
        nullable=False,
        index=True,
    )

    title = Column(
        String(200),
        nullable=False,
    )

    message = Column(
        Text,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    event = relationship(
        "Event",
        back_populates="announcements",
    )


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    event_id = Column(
        Integer,
        ForeignKey("events.id"),
        nullable=True,
        index=True,
    )

    notification_type = Column(
        String(50),
        nullable=False,
    )

    message = Column(
        Text,
        nullable=False,
    )

    read = Column(
        Boolean,
        default=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    user = relationship(
        "User",
        back_populates="notifications",
    )