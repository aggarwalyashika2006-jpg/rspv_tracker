from fastapi import WebSocket


class ConnectionManager:

    def __init__(self):
        self.connections = {}

    async def connect(
        self,
        event_id: int,
        websocket: WebSocket
    ):
        await websocket.accept()

        if event_id not in self.connections:
            self.connections[event_id] = []

        self.connections[event_id].append(websocket)

    def disconnect(
        self,
        event_id: int,
        websocket: WebSocket
    ):
        if event_id in self.connections:

            if websocket in self.connections[event_id]:
                self.connections[event_id].remove(websocket)

            if not self.connections[event_id]:
                del self.connections[event_id]

    async def broadcast(
        self,
        event_id: int,
        message: dict
    ):
        if event_id not in self.connections:
            return

        disconnected = []

        for websocket in self.connections[event_id]:

            try:
                await websocket.send_json(message)

            except Exception:
                disconnected.append(websocket)

        for websocket in disconnected:
            self.disconnect(
                event_id,
                websocket
            )


manager = ConnectionManager()