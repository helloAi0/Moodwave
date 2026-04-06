"""
socket_manager.py — Simplified socket management without python-socketio.

For now, we'll use a simple in-memory event system.
In production, replace with proper Socket.IO or WebSocket library.
"""

class SocketManager:
    """Simple in-memory socket manager for broadcasting events."""

    def __init__(self):
        self.clients = set()

    async def emit(self, event: str, data: dict, to: str = None):
        """Emit an event to clients (stub for now)."""
        print(f"[Socket] Event '{event}' would be emitted to clients: {data}")

    async def on(self, event: str, handler):
        """Register event handler (stub for now)."""
        print(f"[Socket] Handler registered for event '{event}'")

    async def connect(self, client_id: str):
        """Handle client connection."""
        self.clients.add(client_id)
        print(f"[Socket] Client {client_id} connected")

    async def disconnect(self, client_id: str):
        """Handle client disconnection."""
        self.clients.discard(client_id)
        print(f"[Socket] Client {client_id} disconnected")


# Global instance
sio = SocketManager()


# ASGI app stub (will be handled by FastAPI's built-in capabilities)
class ASGIApp:
    def __init__(self, manager):
        self.manager = manager

    async def __call__(self, scope, receive, send):
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [[b"content-type", b"application/json"]],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": b'{"status":"socket_manager_active"}',
            }
        )


socket_app = ASGIApp(sio)