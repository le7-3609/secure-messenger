"""
broadcaster.py — In-memory pub/sub for SSE push notifications.

When a message is saved, messageService calls broadcaster.publish(recipient, data).
Any open SSE connection for that recipient receives the event instantly.

Each connected client gets its own asyncio.Queue.
publish() puts the event into every queue belonging to the recipient.
The SSE generator reads from its queue and yields events to the HTTP response.
"""

import asyncio
from collections import defaultdict
from typing import AsyncGenerator


class Broadcaster:
    def __init__(self) -> None:
        self._listeners: dict[str, list[asyncio.Queue]] = defaultdict(list)

    def subscribe(self, username: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._listeners[username].append(q)
        return q

    def unsubscribe(self, username: str, q: asyncio.Queue) -> None:
        self._listeners[username].remove(q)
        if not self._listeners[username]:
            del self._listeners[username]

    def active_users(self) -> list[str]:
        return list(self._listeners.keys())

    async def publish(self, username: str, data: str) -> None:
        for q in self._listeners[username]:
            await q.put(data)

    async def listen(self, username: str) -> AsyncGenerator[str, None]:
        q = self.subscribe(username)
        try:
            while True:
                yield await q.get()
        finally:
            self.unsubscribe(username, q)


# One shared instance for the entire process lifetime.
broadcaster = Broadcaster()
