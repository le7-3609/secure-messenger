import json
import sys
import threading
from collections.abc import Callable

import httpx


class ApiClient:
    def __init__(self, base_url: str) -> None:
        self._base = base_url
        self._token: str | None = None

    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self._token}"}

    def register(self, username: str, password: str) -> None:
        r = httpx.post(f"{self._base}/register", json={"username": username, "password": password})
        if r.status_code not in (201, 400):
            print(f"Registration error: {r.text}")
            sys.exit(1)

    def login(self, username: str, password: str) -> None:
        r = httpx.post(f"{self._base}/login", json={"username": username, "password": password})
        if r.status_code != 200:
            print(f"Login failed: {r.json().get('detail')}")
            sys.exit(1)
        self._token = r.json()["access_token"]

    def send(self, recipients: list[str], content: str) -> None:
        r = httpx.post(f"{self._base}/messages",
                       json={"recipients": recipients, "content": content},
                       headers=self._auth_headers())
        if r.status_code != 201:
            print(f"Send failed: {r.json().get('detail')}")

    def listen(self, stop: threading.Event, on_message: Callable[[str, str], None]) -> None:
        """Connects to GET /stream and calls on_message(sender, content) for each event."""
        try:
            with httpx.stream("GET", f"{self._base}/stream",
                              headers=self._auth_headers(), timeout=None) as r:
                for line in r.iter_lines():
                    if stop.is_set():
                        break
                    if not line.startswith("data:"):
                        continue
                    raw = line[len("data:"):].strip()
                    if not raw:
                        continue
                    try:
                        msg = json.loads(raw)
                        on_message(msg["sender"], msg["content"])
                    except (json.JSONDecodeError, KeyError):
                        pass
        except Exception:
            pass  # server closed or user quit
