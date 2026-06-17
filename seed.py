"""
seed.py — Populate the database with test users and messages.

Usage:
    python seed.py

Safe to run multiple times — existing users are skipped, not duplicated.
"""

import httpx

BASE_URL = "http://127.0.0.1:8000"

USERS = [
    {"username": "alice",   "password": "alice1234"},
    {"username": "bob",     "password": "bob12345"},
    {"username": "charlie", "password": "charlie1"},
]

MESSAGES = [
    ("alice",   ["bob"],              "Hey everyone, the server is up!"),
    ("bob",     ["alice"],            "Nice, I can see this message."),
    ("charlie", ["alice", "bob"],     "Encryption is working — messages are safe at rest."),
    ("alice",   ["bob", "charlie"],   "This is a seed message to pre-populate the history."),
    ("bob",     ["alice"],            "Let's test the broadcast too."),
]


def main() -> None:
    print("=== Seeding database ===\n")
    tokens: dict[str, str] = {}

    print("Registering users...")
    for user in USERS:
        r = httpx.post(f"{BASE_URL}/register", json=user)
        if r.status_code == 201:
            print(f"  [+] Registered:  {user['username']}")
        elif r.status_code == 400:
            print(f"  [~] Already exists: {user['username']}")
        else:
            print(f"  [!] Unexpected {r.status_code} for {user['username']}: {r.text}")

    print("\nLogging in...")
    for user in USERS:
        r = httpx.post(f"{BASE_URL}/login", json=user)
        if r.status_code == 200:
            tokens[user["username"]] = r.json()["access_token"]
            print(f"  [+] Logged in:   {user['username']}")
        else:
            print(f"  [!] Login failed for {user['username']}: {r.text}")

    print("\nSending seed messages...")
    for sender, recipients, content in MESSAGES:
        if sender not in tokens:
            print(f"  [!] No token for {sender}, skipping.")
            continue
        r = httpx.post(
            f"{BASE_URL}/messages",
            json={"recipients": recipients, "content": content},
            headers={"Authorization": f"Bearer {tokens[sender]}"},
        )
        if r.status_code == 201:
            print(f"  [+] Message sent by {sender}: '{content}'")
        else:
            print(f"  [!] Failed ({r.status_code}): {r.text}")

    print("\nDone!  Database is seeded.")


if __name__ == "__main__":
    main()
