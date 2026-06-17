import threading
from getpass import getpass

from .api import ApiClient
from .config import settings


def prompt_auth(api: ApiClient) -> str:
    print("=== Secure Messenger ===")
    print("1) Register")
    print("2) Login")

    while True:
        choice = input("Choose (1/2): ").strip()
        if choice in {"1", "2"}:
            break
        print("Please enter 1 or 2.")

    username = input("Username: ").strip()
    password = getpass("Password: ").strip()

    if choice == "1":
        api.register(username, password)

    api.login(username, password)
    return username


def main() -> None:
    api = ApiClient(settings.SERVER_URL)
    username = prompt_auth(api)
    print(f"\nWelcome, {username}!  (type your message and press Enter, or 'quit' to exit)\n")

    print("--- message history ---")
    for message in api.get_messages():
        print(f"  [{message['sender']}]: {message['content']}")
    print("-----------------------\n")

    print("Send:  to:<recipient>[,<recipient2>] <message>    Broadcast: to:* <message>    Quit: quit\n")

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
