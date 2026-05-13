import threading

from .api import ApiClient
from .config import settings


def main() -> None:
    print("=== Secure Messenger ===")
    username = input("Username: ").strip()
    password = input("Password: ").strip()

    api = ApiClient(settings.SERVER_URL)
    api.register(username, password)
    api.login(username, password)
    print(f"Logged in as {username}. Listening for messages...")
    print('Send:  to:<recipient>[,<recipient2>] <message>    Broadcast: to:* <message>    Quit: quit\n')

    def on_message(sender: str, content: str) -> None:
        print(f"\n  [{sender}]: {content}\n> ", end="", flush=True)

    stop = threading.Event()
    t = threading.Thread(target=api.listen, args=(stop, on_message), daemon=True)
    t.start()

    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if line.lower() == "quit":
            break

        if line.startswith("to:"):
            parts = line[3:].split(" ", 1)
            if len(parts) < 2 or not parts[1].strip():
                print("Usage: to:<recipient>[,<recipient2>] <message>")
                continue
            recipients = [r.strip() for r in parts[0].split(",") if r.strip()]
            api.send(recipients, parts[1].strip())
        else:
            print("Usage: to:<recipient> <message>")

    stop.set()
    print("Goodbye.")


if __name__ == "__main__":
    main()
