"""Keeps track of open WebSocket connections and sends messages to them."""

from fastapi import WebSocket


class Connection:
    def __init__(self, socket: WebSocket, user_id: int, class_id: int | None):
        self.socket = socket
        self.user_id = user_id
        self.class_id = class_id


class ConnectionManager:
    def __init__(self):
        self.connections: list[Connection] = []

    async def connect(self, socket: WebSocket, user_id: int, class_id: int | None):
        await socket.accept()
        self.connections.append(Connection(socket, user_id, class_id))

    def disconnect(self, socket: WebSocket):
        self.connections = [c for c in self.connections if c.socket is not socket]

    async def _send(self, connection: Connection, data: dict):
        try:
            await connection.socket.send_json(data)
        except Exception:
            self.disconnect(connection.socket)  # the browser went away

    async def send_market(self, data: dict):
        """Prices go to everyone who is not inside a class room page."""
        for connection in list(self.connections):
            if connection.class_id is None:
                await self._send(connection, data)

    async def send_class(self, class_id: int, data: dict):
        """Class events (notes, questions) go to people inside that class."""
        for connection in list(self.connections):
            if connection.class_id == class_id:
                await self._send(connection, data)

    async def send_user(self, user_id: int, data: dict):
        """Personal messages (order filled, alert) go to one user."""
        for connection in list(self.connections):
            if connection.user_id == user_id and connection.class_id is None:
                await self._send(connection, data)


manager = ConnectionManager()
