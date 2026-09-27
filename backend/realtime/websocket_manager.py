from typing import Dict, List
from fastapi import WebSocket


class ConnectionManager:
    """
    Manages active WebSocket connections.

    Each event can have multiple connected users.
    Example:

    Event 1
        ├── Organizer browser
        ├── Attendee A browser
        └── Attendee B browser
    """

    def __init__(self):
        self.connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, event_id: int, websocket: WebSocket):
        """
        Accept a WebSocket connection and associate it
        with a particular event.
        """

        await websocket.accept()

        if event_id not in self.connections:
            self.connections[event_id] = []

        self.connections[event_id].append(websocket)

    def disconnect(self, event_id: int, websocket: WebSocket):
        """
        Remove a disconnected WebSocket.
        """

        if event_id not in self.connections:
            return

        if websocket in self.connections[event_id]:
            self.connections[event_id].remove(websocket)

        if len(self.connections[event_id]) == 0:
            del self.connections[event_id]

    async def broadcast(self, event_id: int, message: dict):
        """
        Send a message to every connected client
        watching this event.
        """

        if event_id not in self.connections:
            return

        disconnected = []

        for websocket in self.connections[event_id]:

            try:
                await websocket.send_json(message)

            except Exception:
                disconnected.append(websocket)

        for websocket in disconnected:
            self.disconnect(event_id, websocket)


manager = ConnectionManager()