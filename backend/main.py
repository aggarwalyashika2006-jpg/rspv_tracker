from datetime import datetime, timezone
from typing import Optional
import sqlite3

from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    WebSocket,
    WebSocketDisconnect,
    status,
)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    require_organizer,
)


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="Real-Time Cloud Event RSVP Tracker",
    description="Cloud-based event planning and real-time RSVP system",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# DATABASE
# ============================================================

DATABASE = "event_tracker.db"


def get_db():
    conn = sqlite3.connect(
        DATABASE,
        check_same_thread=False,
        timeout=30,
    )

    conn.row_factory = sqlite3.Row

    # Enable foreign-key protection.
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


def init_database():

    conn = get_db()

    cursor = conn.cursor()

    # ========================================================
    # USERS
    # ========================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT NOT NULL UNIQUE,

            password_hash TEXT NOT NULL,

            role TEXT NOT NULL DEFAULT 'ATTENDEE',

            created_at TEXT NOT NULL
        )
        """
    )

    # ========================================================
    # EVENTS
    # ========================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            organizer_id INTEGER NOT NULL,

            event_name TEXT NOT NULL,

            description TEXT,

            event_type TEXT,

            event_date TEXT NOT NULL,

            start_time TEXT NOT NULL,

            end_time TEXT NOT NULL,

            venue TEXT,

            online_link TEXT,

            maximum_capacity INTEGER NOT NULL,

            registration_deadline TEXT,

            status TEXT NOT NULL DEFAULT 'PUBLISHED',

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL,

            FOREIGN KEY (organizer_id)
            REFERENCES users(id)
        )
        """
    )

    # ========================================================
    # RSVPS
    # ========================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS rsvps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            event_id INTEGER NOT NULL,

            user_id INTEGER NOT NULL,

            status TEXT NOT NULL,

            responded_at TEXT NOT NULL,

            updated_at TEXT NOT NULL,

            UNIQUE(event_id, user_id),

            FOREIGN KEY (event_id)
            REFERENCES events(id),

            FOREIGN KEY (user_id)
            REFERENCES users(id)
        )
        """
    )

    # ========================================================
    # ANNOUNCEMENTS
    # ========================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            event_id INTEGER NOT NULL,

            title TEXT NOT NULL,

            message TEXT NOT NULL,

            created_at TEXT NOT NULL,

            FOREIGN KEY (event_id)
            REFERENCES events(id)
        )
        """
    )

    # ========================================================
    # NOTIFICATIONS
    # ========================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            event_id INTEGER,

            type TEXT NOT NULL,

            message TEXT NOT NULL,

            read INTEGER NOT NULL DEFAULT 0,

            created_at TEXT NOT NULL,

            FOREIGN KEY (user_id)
            REFERENCES users(id)
        )
        """
    )

    # ========================================================
    # INDEXES
    # ========================================================

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_rsvps_event
        ON rsvps(event_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_rsvps_user
        ON rsvps(user_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_notifications_user
        ON notifications(user_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_events_organizer
        ON events(organizer_id)
        """
    )

    conn.commit()
    conn.close()


init_database()


# ============================================================
# REAL-TIME CONNECTION MANAGER
# ============================================================

class ConnectionManager:

    def __init__(self):
        self.connections = {}

    async def connect(
        self,
        event_id: int,
        websocket: WebSocket,
    ):

        await websocket.accept()

        if event_id not in self.connections:
            self.connections[event_id] = []

        self.connections[event_id].append(websocket)

    def disconnect(
        self,
        event_id: int,
        websocket: WebSocket,
    ):

        if event_id not in self.connections:
            return

        if websocket in self.connections[event_id]:
            self.connections[event_id].remove(websocket)

        if not self.connections[event_id]:
            del self.connections[event_id]

    async def broadcast(
        self,
        event_id: int,
        message: dict,
    ):

        if event_id not in self.connections:
            return

        disconnected = []

        for websocket in list(
            self.connections[event_id]
        ):

            try:

                await websocket.send_json(message)

            except Exception:

                disconnected.append(websocket)

        for websocket in disconnected:

            self.disconnect(
                event_id,
                websocket,
            )


manager = ConnectionManager()


# ============================================================
# PYDANTIC REQUEST MODELS
# ============================================================

class RegisterRequest(BaseModel):

    name: str = Field(
        min_length=2,
        max_length=100,
    )

    email: EmailStr

    password: str = Field(
        min_length=6,
        max_length=128,
    )

    role: str = "ATTENDEE"


class EventCreate(BaseModel):

    event_name: str = Field(
        min_length=2,
        max_length=200,
    )

    description: Optional[str] = None

    event_type: Optional[str] = None

    event_date: str

    start_time: str

    end_time: str

    venue: Optional[str] = None

    online_link: Optional[str] = None

    maximum_capacity: int = Field(
        gt=0,
        le=1000000,
    )

    registration_deadline: Optional[str] = None


class RSVPRequest(BaseModel):

    status: str


class AnnouncementRequest(BaseModel):

    title: str = Field(
        min_length=1,
        max_length=200,
    )

    message: str = Field(
        min_length=1,
        max_length=5000,
    )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def now_iso():
    return datetime.now(
        timezone.utc
    ).isoformat()


def get_event_or_404(
    conn,
    event_id: int,
):

    event = conn.execute(
        """
        SELECT *
        FROM events
        WHERE id = ?
        """,
        (event_id,),
    ).fetchone()

    if not event:

        raise HTTPException(
            status_code=404,
            detail="Event not found.",
        )

    return event


def get_rsvp_counts(
    conn,
    event_id: int,
):

    row = conn.execute(
        """
        SELECT

            SUM(
                CASE
                    WHEN status = 'GOING'
                    THEN 1
                    ELSE 0
                END
            ) AS going,

            SUM(
                CASE
                    WHEN status = 'MAYBE'
                    THEN 1
                    ELSE 0
                END
            ) AS maybe,

            SUM(
                CASE
                    WHEN status = 'NOT_GOING'
                    THEN 1
                    ELSE 0
                END
            ) AS not_going

        FROM rsvps

        WHERE event_id = ?
        """,
        (event_id,),
    ).fetchone()

    return {
        "going": row["going"] or 0,
        "maybe": row["maybe"] or 0,
        "not_going": row["not_going"] or 0,
    }


def update_event_status(
    conn,
    event_id: int,
):

    event = conn.execute(
        """
        SELECT
            maximum_capacity,
            status
        FROM events
        WHERE id = ?
        """,
        (event_id,),
    ).fetchone()

    if not event:
        return

    if event["status"] in [
        "CANCELLED",
        "COMPLETED",
    ]:
        return

    counts = get_rsvp_counts(
        conn,
        event_id,
    )

    if counts["going"] >= event["maximum_capacity"]:

        new_status = "FULL"

    else:

        new_status = "PUBLISHED"

    conn.execute(
        """
        UPDATE events

        SET status = ?,

            updated_at = ?

        WHERE id = ?
        """,
        (
            new_status,
            now_iso(),
            event_id,
        ),
    )


async def broadcast_rsvp_update(
    event_id: int,
    counts: dict,
):

    await manager.broadcast(
        event_id,
        {
            "type": "RSVP_UPDATED",

            "event_id": event_id,

            "data": {
                "going": counts["going"],
                "maybe": counts["maybe"],
                "not_going": counts["not_going"],
            },
        },
    )


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "message": "Real-Time Cloud Event RSVP Tracker API",
        "status": "running",
        "docs": "/docs",
        "websocket": "/ws/events/{event_id}",
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "database": "SQLite",
        "realtime": "WebSocket",
        "authentication": "JWT",
    }


# ============================================================
# REGISTER
# ============================================================

@app.post(
    "/api/register",
    status_code=status.HTTP_201_CREATED,
)
def register(
    request: RegisterRequest,
):

    role = request.role.upper()

    if role not in [
        "ATTENDEE",
        "ORGANIZER",
    ]:

        raise HTTPException(
            status_code=400,
            detail="Role must be ATTENDEE or ORGANIZER.",
        )

    conn = get_db()

    existing_user = conn.execute(
        """
        SELECT id
        FROM users
        WHERE email = ?
        """,
        (
            request.email.lower(),
        ),
    ).fetchone()

    if existing_user:

        conn.close()

        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists.",
        )

    try:

        password_hash = hash_password(
            request.password
        )

    except Exception as error:

        conn.close()

        raise HTTPException(
            status_code=500,
            detail=f"Password hashing failed: {str(error)}",
        )

    created_at = now_iso()

    try:

        cursor = conn.execute(
            """
            INSERT INTO users
            (
                name,
                email,
                password_hash,
                role,
                created_at
            )

            VALUES (?, ?, ?, ?, ?)
            """,
            (
                request.name,
                request.email.lower(),
                password_hash,
                role,
                created_at,
            ),
        )

        user_id = cursor.lastrowid

        conn.commit()

    except sqlite3.IntegrityError:

        conn.rollback()
        conn.close()

        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists.",
        )

    conn.close()

    return {
        "message": "Registration successful.",

        "user": {
            "id": user_id,
            "name": request.name,
            "email": request.email.lower(),
            "role": role,
        },
    }


# ============================================================
# LOGIN
# ============================================================

@app.post("/api/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
):

    email = form_data.username.lower()

    password = form_data.password

    conn = get_db()

    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE email = ?
        """,
        (email,),
    ).fetchone()

    conn.close()

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    try:

        valid_password = verify_password(
            password,
            user["password_hash"],
        )

    except Exception:

        valid_password = False

    if not valid_password:

        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    access_token = create_access_token(
        {
            "sub": str(user["id"]),
            "email": user["email"],
            "role": user["role"],
        }
    )

    return {
        "access_token": access_token,

        "token_type": "bearer",

        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
        },
    }


# ============================================================
# CURRENT USER
# ============================================================

@app.get("/api/me")
def get_me(
    current_user: dict = Depends(
        get_current_user
    ),
):

    conn = get_db()

    user = conn.execute(
        """
        SELECT
            id,
            name,
            email,
            role,
            created_at

        FROM users

        WHERE id = ?
        """,
        (
            current_user["user_id"],
        ),
    ).fetchone()

    conn.close()

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    return dict(user)


# ============================================================
# CREATE EVENT
# ============================================================

@app.post("/api/events")
def create_event(
    event: EventCreate,

    current_user: dict = Depends(
        require_organizer
    ),
):

    now = now_iso()

    conn = get_db()

    cursor = conn.execute(
        """
        INSERT INTO events
        (
            organizer_id,
            event_name,
            description,
            event_type,
            event_date,
            start_time,
            end_time,
            venue,
            online_link,
            maximum_capacity,
            registration_deadline,
            status,
            created_at,
            updated_at
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            current_user["user_id"],
            event.event_name,
            event.description,
            event.event_type,
            event.event_date,
            event.start_time,
            event.end_time,
            event.venue,
            event.online_link,
            event.maximum_capacity,
            event.registration_deadline,
            "PUBLISHED",
            now,
            now,
        ),
    )

    event_id = cursor.lastrowid

    conn.commit()

    created_event = conn.execute(
        """
        SELECT *
        FROM events
        WHERE id = ?
        """,
        (event_id,),
    ).fetchone()

    conn.close()

    return dict(created_event)


# ============================================================
# GET ALL EVENTS
# ============================================================

@app.get("/api/events")
def get_events():

    conn = get_db()

    events = conn.execute(
        """
        SELECT *
        FROM events
        ORDER BY event_date, start_time
        """
    ).fetchall()

    conn.close()

    return [
        dict(event)
        for event in events
    ]


# ============================================================
# GET SINGLE EVENT
# ============================================================

@app.get("/api/events/{event_id}")
def get_event(
    event_id: int,
):

    conn = get_db()

    event = get_event_or_404(
        conn,
        event_id,
    )

    conn.close()

    return dict(event)


# ============================================================
# UPDATE EVENT
# ============================================================

@app.put("/api/events/{event_id}")
def update_event(
    event_id: int,

    event: EventCreate,

    current_user: dict = Depends(
        require_organizer
    ),
):

    conn = get_db()

    existing = get_event_or_404(
        conn,
        event_id,
    )

    if existing["organizer_id"] != current_user["user_id"]:

        conn.close()

        raise HTTPException(
            status_code=403,
            detail="You can only modify your own events.",
        )

    # Prevent organizer from lowering capacity below
    # the number of existing GOING attendees.

    counts = get_rsvp_counts(
        conn,
        event_id,
    )

    if event.maximum_capacity < counts["going"]:

        conn.close()

        raise HTTPException(
            status_code=400,
            detail=(
                "Maximum capacity cannot be lower "
                "than the current number of GOING attendees."
            ),
        )

    now = now_iso()

    conn.execute(
        """
        UPDATE events

        SET
            event_name = ?,
            description = ?,
            event_type = ?,
            event_date = ?,
            start_time = ?,
            end_time = ?,
            venue = ?,
            online_link = ?,
            maximum_capacity = ?,
            registration_deadline = ?,
            updated_at = ?

        WHERE id = ?
        """,
        (
            event.event_name,
            event.description,
            event.event_type,
            event.event_date,
            event.start_time,
            event.end_time,
            event.venue,
            event.online_link,
            event.maximum_capacity,
            event.registration_deadline,
            now,
            event_id,
        ),
    )

    update_event_status(
        conn,
        event_id,
    )

    conn.commit()

    updated = conn.execute(
        """
        SELECT *
        FROM events
        WHERE id = ?
        """,
        (event_id,),
    ).fetchone()

    conn.close()

    return dict(updated)


# ============================================================
# DELETE EVENT
# ============================================================

@app.delete("/api/events/{event_id}")
def delete_event(
    event_id: int,

    current_user: dict = Depends(
        require_organizer
    ),
):

    conn = get_db()

    event = get_event_or_404(
        conn,
        event_id,
    )

    if event["organizer_id"] != current_user["user_id"]:

        conn.close()

        raise HTTPException(
            status_code=403,
            detail="You can only delete your own events.",
        )

    conn.execute(
        """
        DELETE FROM notifications
        WHERE event_id = ?
        """,
        (event_id,),
    )

    conn.execute(
        """
        DELETE FROM announcements
        WHERE event_id = ?
        """,
        (event_id,),
    )

    conn.execute(
        """
        DELETE FROM rsvps
        WHERE event_id = ?
        """,
        (event_id,),
    )

    conn.execute(
        """
        DELETE FROM events
        WHERE id = ?
        """,
        (event_id,),
    )

    conn.commit()

    conn.close()

    return {
        "message": "Event deleted successfully."
    }


# ============================================================
# RSVP CREATE / UPDATE
# ============================================================

@app.post(
    "/api/events/{event_id}/rsvp"
)
async def create_or_update_rsvp(
    event_id: int,

    request: RSVPRequest,

    current_user: dict = Depends(
        get_current_user
    ),
):

    requested_status = request.status.upper()

    allowed_statuses = {
        "GOING",
        "MAYBE",
        "NOT_GOING",
    }

    if requested_status not in allowed_statuses:

        raise HTTPException(
            status_code=400,
            detail=(
                "RSVP status must be "
                "GOING, MAYBE or NOT_GOING."
            ),
        )

    conn = get_db()

    try:

        # ====================================================
        # BEGIN IMMEDIATE
        #
        # This locks the SQLite database for writes while
        # this critical operation is running.
        #
        # This is important for capacity management.
        # ====================================================

        conn.execute(
            "BEGIN IMMEDIATE"
        )

        event = conn.execute(
            """
            SELECT *
            FROM events
            WHERE id = ?
            """,
            (event_id,),
        ).fetchone()

        if not event:

            raise HTTPException(
                status_code=404,
                detail="Event not found.",
            )

        if event["status"] == "CANCELLED":

            raise HTTPException(
                status_code=400,
                detail="This event has been cancelled.",
            )

        if event["status"] == "COMPLETED":

            raise HTTPException(
                status_code=400,
                detail="This event has already completed.",
            )

        # ====================================================
        # REGISTRATION DEADLINE
        # ====================================================

        if event["registration_deadline"]:

            try:

                deadline = datetime.fromisoformat(
                    event["registration_deadline"]
                )

                if deadline.tzinfo is None:

                    deadline = deadline.replace(
                        tzinfo=timezone.utc
                    )

                if datetime.now(
                    timezone.utc
                ) > deadline:

                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "The registration deadline "
                            "has passed."
                        ),
                    )

            except ValueError:

                pass

        # ====================================================
        # EXISTING RSVP
        # ====================================================

        existing_rsvp = conn.execute(
            """
            SELECT *
            FROM rsvps

            WHERE event_id = ?

            AND user_id = ?
            """,
            (
                event_id,
                current_user["user_id"],
            ),
        ).fetchone()

        # ====================================================
        # CURRENT GOING COUNT
        # ====================================================

        going_count = conn.execute(
            """
            SELECT COUNT(*)

            FROM rsvps

            WHERE event_id = ?

            AND status = 'GOING'
            """,
            (event_id,),
        ).fetchone()[0]

        already_going = (
            existing_rsvp is not None
            and existing_rsvp["status"] == "GOING"
        )

        # ====================================================
        # CAPACITY CHECK
        # ====================================================

        if (
            requested_status == "GOING"
            and not already_going
            and going_count >= event["maximum_capacity"]
        ):

            raise HTTPException(
                status_code=409,
                detail=(
                    "Event is full. "
                    "GOING RSVP cannot be accepted."
                ),
            )

        now = now_iso()

        # ====================================================
        # UPDATE EXISTING RSVP
        # ====================================================

        if existing_rsvp:

            conn.execute(
                """
                UPDATE rsvps

                SET
                    status = ?,
                    updated_at = ?

                WHERE event_id = ?

                AND user_id = ?
                """,
                (
                    requested_status,
                    now,
                    event_id,
                    current_user["user_id"],
                ),
            )

        # ====================================================
        # CREATE NEW RSVP
        # ====================================================

        else:

            conn.execute(
                """
                INSERT INTO rsvps
                (
                    event_id,
                    user_id,
                    status,
                    responded_at,
                    updated_at
                )

                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    current_user["user_id"],
                    requested_status,
                    now,
                    now,
                ),
            )

        # ====================================================
        # NOTIFICATION
        # ====================================================

        conn.execute(
            """
            INSERT INTO notifications
            (
                user_id,
                event_id,
                type,
                message,
                read,
                created_at
            )

            VALUES (?, ?, ?, ?, 0, ?)
            """,
            (
                current_user["user_id"],
                event_id,
                "RSVP",
                (
                    "Your RSVP has been updated to "
                    f"{requested_status}."
                ),
                now,
            ),
        )

        # ====================================================
        # UPDATE EVENT STATUS
        # ====================================================

        update_event_status(
            conn,
            event_id,
        )

        # ====================================================
        # COMMIT
        # ====================================================

        conn.commit()

        # ====================================================
        # GET NEW COUNTS
        # ====================================================

        counts = get_rsvp_counts(
            conn,
            event_id,
        )

    except HTTPException:

        conn.rollback()
        conn.close()

        raise

    except sqlite3.IntegrityError:

        conn.rollback()
        conn.close()

        raise HTTPException(
            status_code=409,
            detail=(
                "This RSVP could not be created "
                "because a duplicate RSVP was detected."
            ),
        )

    except sqlite3.OperationalError as error:

        conn.rollback()
        conn.close()

        raise HTTPException(
            status_code=503,
            detail=(
                "The database is temporarily busy. "
                f"Please try again. {str(error)}"
            ),
        )

    except Exception as error:

        conn.rollback()
        conn.close()

        raise HTTPException(
            status_code=500,
            detail=f"RSVP operation failed: {str(error)}",
        )

    conn.close()

    # ========================================================
    # REAL-TIME BROADCAST
    # ========================================================

    await broadcast_rsvp_update(
        event_id,
        counts,
    )

    return {
        "message": "RSVP recorded successfully.",

        "event_id": event_id,

        "status": requested_status,

        "going": counts["going"],

        "maybe": counts["maybe"],

        "not_going": counts["not_going"],
    }


# ============================================================
# CANCEL RSVP
# ============================================================

@app.delete(
    "/api/events/{event_id}/rsvp"
)
async def cancel_rsvp(
    event_id: int,

    current_user: dict = Depends(
        get_current_user
    ),
):

    conn = get_db()

    try:

        conn.execute(
            "BEGIN IMMEDIATE"
        )

        event = get_event_or_404(
            conn,
            event_id,
        )

        existing = conn.execute(
            """
            SELECT *
            FROM rsvps

            WHERE event_id = ?

            AND user_id = ?
            """,
            (
                event_id,
                current_user["user_id"],
            ),
        ).fetchone()

        if not existing:

            raise HTTPException(
                status_code=404,
                detail=(
                    "You do not have an RSVP "
                    "for this event."
                ),
            )

        now = now_iso()

        conn.execute(
            """
            UPDATE rsvps

            SET
                status = 'NOT_GOING',
                updated_at = ?

            WHERE event_id = ?

            AND user_id = ?
            """,
            (
                now,
                event_id,
                current_user["user_id"],
            ),
        )

        conn.execute(
            """
            INSERT INTO notifications
            (
                user_id,
                event_id,
                type,
                message,
                read,
                created_at
            )

            VALUES (?, ?, ?, ?, 0, ?)
            """,
            (
                current_user["user_id"],
                event_id,
                "RSVP_CANCELLED",
                "Your RSVP has been cancelled.",
                now,
            ),
        )

        update_event_status(
            conn,
            event_id,
        )

        conn.commit()

        counts = get_rsvp_counts(
            conn,
            event_id,
        )

    except HTTPException:

        conn.rollback()
        conn.close()

        raise

    except Exception as error:

        conn.rollback()
        conn.close()

        raise HTTPException(
            status_code=500,
            detail=f"Unable to cancel RSVP: {str(error)}",
        )

    conn.close()

    await broadcast_rsvp_update(
        event_id,
        counts,
    )

    return {
        "message": "RSVP cancelled successfully.",

        "event_id": event_id,

        "going": counts["going"],

        "maybe": counts["maybe"],

        "not_going": counts["not_going"],
    }


# ============================================================
# GET MY RSVPS
# ============================================================

@app.get("/api/rsvps/me")
def get_my_rsvps(
    current_user: dict = Depends(
        get_current_user
    ),
):

    conn = get_db()

    rows = conn.execute(
        """
        SELECT

            r.id,

            r.event_id,

            r.status,

            r.responded_at,

            r.updated_at,

            e.event_name,

            e.event_date,

            e.start_time,

            e.end_time,

            e.venue,

            e.status AS event_status

        FROM rsvps r

        JOIN events e

        ON r.event_id = e.id

        WHERE r.user_id = ?

        ORDER BY
            e.event_date,
            e.start_time
        """,
        (
            current_user["user_id"],
        ),
    ).fetchall()

    conn.close()

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# GET EVENT RSVPS
# ============================================================

@app.get(
    "/api/events/{event_id}/rsvps"
)
def get_event_rsvps(
    event_id: int,

    current_user: dict = Depends(
        require_organizer
    ),
):

    conn = get_db()

    event = get_event_or_404(
        conn,
        event_id,
    )

    if event["organizer_id"] != current_user["user_id"]:

        conn.close()

        raise HTTPException(
            status_code=403,
            detail="You do not own this event.",
        )

    rows = conn.execute(
        """
        SELECT

            r.id,

            r.user_id,

            u.name,

            u.email,

            r.status,

            r.responded_at,

            r.updated_at

        FROM rsvps r

        JOIN users u

        ON r.user_id = u.id

        WHERE r.event_id = ?

        ORDER BY
            r.updated_at DESC
        """,
        (event_id,),
    ).fetchall()

    conn.close()

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# ANALYTICS
# ============================================================

@app.get(
    "/api/events/{event_id}/analytics"
)
def get_analytics(
    event_id: int,

    current_user: dict = Depends(
        require_organizer
    ),
):

    conn = get_db()

    event = get_event_or_404(
        conn,
        event_id,
    )

    if event["organizer_id"] != current_user["user_id"]:

        conn.close()

        raise HTTPException(
            status_code=403,
            detail="You do not own this event.",
        )

    counts = get_rsvp_counts(
        conn,
        event_id,
    )

    conn.close()

    total = (
        counts["going"]
        + counts["maybe"]
        + counts["not_going"]
    )

    capacity = event["maximum_capacity"]

    available_seats = max(
        capacity - counts["going"],
        0,
    )

    capacity_utilization = (
        counts["going"] / capacity * 100
        if capacity > 0
        else 0
    )

    response_rate = (
        total / capacity * 100
        if capacity > 0
        else 0
    )

    return {
        "event_id": event_id,

        "event_name": event["event_name"],

        "maximum_capacity": capacity,

        "total_rsvps": total,

        "going": counts["going"],

        "maybe": counts["maybe"],

        "not_going": counts["not_going"],

        "available_seats": available_seats,

        "response_rate": round(
            response_rate,
            2,
        ),

        "capacity_utilization": round(
            capacity_utilization,
            2,
        ),
    }


# ============================================================
# CREATE ANNOUNCEMENT
# ============================================================

@app.post(
    "/api/events/{event_id}/announcements"
)
def create_announcement(
    event_id: int,

    request: AnnouncementRequest,

    current_user: dict = Depends(
        require_organizer
    ),
):

    conn = get_db()

    event = get_event_or_404(
        conn,
        event_id,
    )

    if event["organizer_id"] != current_user["user_id"]:

        conn.close()

        raise HTTPException(
            status_code=403,
            detail="You do not own this event.",
        )

    now = now_iso()

    cursor = conn.execute(
        """
        INSERT INTO announcements
        (
            event_id,
            title,
            message,
            created_at
        )

        VALUES (?, ?, ?, ?)
        """,
        (
            event_id,
            request.title,
            request.message,
            now,
        ),
    )

    announcement_id = cursor.lastrowid

    # Notify users who have an RSVP.
    attendees = conn.execute(
        """
        SELECT DISTINCT user_id

        FROM rsvps

        WHERE event_id = ?
        """,
        (event_id,),
    ).fetchall()

    for attendee in attendees:

        conn.execute(
            """
            INSERT INTO notifications
            (
                user_id,
                event_id,
                type,
                message,
                read,
                created_at
            )

            VALUES (?, ?, ?, ?, 0, ?)
            """,
            (
                attendee["user_id"],
                event_id,
                "ANNOUNCEMENT",
                request.message,
                now,
            ),
        )

    conn.commit()

    announcement = conn.execute(
        """
        SELECT *
        FROM announcements
        WHERE id = ?
        """,
        (announcement_id,),
    ).fetchone()

    conn.close()

    return dict(announcement)


# ============================================================
# GET ANNOUNCEMENTS
# ============================================================

@app.get(
    "/api/events/{event_id}/announcements"
)
def get_announcements(
    event_id: int,

    current_user: dict = Depends(
        get_current_user
    ),
):

    conn = get_db()

    # Make sure event exists.
    get_event_or_404(
        conn,
        event_id,
    )

    announcements = conn.execute(
        """
        SELECT *

        FROM announcements

        WHERE event_id = ?

        ORDER BY created_at DESC
        """,
        (event_id,),
    ).fetchall()

    conn.close()

    return [
        dict(item)
        for item in announcements
    ]


# ============================================================
# GET NOTIFICATIONS
# ============================================================

@app.get("/api/notifications")
def get_notifications(
    current_user: dict = Depends(
        get_current_user
    ),
):

    conn = get_db()

    notifications = conn.execute(
        """
        SELECT *

        FROM notifications

        WHERE user_id = ?

        ORDER BY created_at DESC
        """,
        (
            current_user["user_id"],
        ),
    ).fetchall()

    conn.close()

    return [
        dict(notification)
        for notification in notifications
    ]


# ============================================================
# MARK NOTIFICATION AS READ
# ============================================================

@app.put(
    "/api/notifications/{notification_id}/read"
)
def mark_notification_read(
    notification_id: int,

    current_user: dict = Depends(
        get_current_user
    ),
):

    conn = get_db()

    notification = conn.execute(
        """
        SELECT *

        FROM notifications

        WHERE id = ?

        AND user_id = ?
        """,
        (
            notification_id,
            current_user["user_id"],
        ),
    ).fetchone()

    if not notification:

        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Notification not found.",
        )

    conn.execute(
        """
        UPDATE notifications

        SET read = 1

        WHERE id = ?
        """,
        (notification_id,),
    )

    conn.commit()

    conn.close()

    return {
        "message": "Notification marked as read."
    }


# ============================================================
# WEBSOCKET
# ============================================================

@app.websocket(
    "/ws/events/{event_id}"
)
async def websocket_endpoint(
    websocket: WebSocket,
    event_id: int,
):

    await manager.connect(
        event_id,
        websocket,
    )

    try:

        while True:

            # The frontend can send "ping" messages
            # to keep the connection alive.

            await websocket.receive_text()

    except WebSocketDisconnect:

        manager.disconnect(
            event_id,
            websocket,
        )

    except Exception:

        manager.disconnect(
            event_id,
            websocket,
        )