from typing import TypedDict
from datetime import datetime
from ..models import Message
from ..repositories import MessageRepository, UserRepository
from ..exceptions import AppError
from ..crypto import encrypt, decrypt


class NotFoundError(AppError):
    '''Raised when a recipient username does not exist.'''


class MessageDict(TypedDict):
    '''Type definition for a decrypted message returned to the client.'''
    id: int
    sender: str
    recipient: str
    content: str
    created_at: datetime


class MessageService:
    def __init__(self, repo: MessageRepository, user_repo: UserRepository) -> None:
        '''Injects the message and user repositories.'''
        self.repo = repo
        self.user_repo = user_repo

    def resolve_recipients(self, recipients: list[str], sender: str) -> list[str]:
        '''Expands ["*"] to all users except sender. Raises NotFoundError for unknown usernames.'''
        if recipients == ["*"]:
            return [u for u in self.user_repo.get_all_usernames() if u != sender]
        unknown = [r for r in recipients if not self.user_repo.get_by_username(r)]
        if unknown:
            raise NotFoundError(f"Unknown recipient(s): {', '.join(unknown)}")
        return recipients

    def send(self, content: str, sender: str, recipients: list[str]) -> list[MessageDict]:
        '''Encrypts and saves one message per recipient. Returns all saved messages.'''
        results = []
        for recipient in recipients:
            message = self.repo.save(Message(sender=sender, recipient=recipient, ciphertext=encrypt(content)))
            results.append(MessageDict(
                id=message.id,
                sender=message.sender,
                recipient=message.recipient,
                content=content,
                created_at=message.created_at
            ))
        return results

    def get_messages(self, username: str) -> list[MessageDict]:
        '''Fetches all messages for a user (sent or received) and decrypts them.'''
        return [
            MessageDict(
                id=m.id,
                sender=m.sender,
                recipient=m.recipient,
                content=decrypt(m.ciphertext),
                created_at=m.created_at
            )
            for m in self.repo.get_for_user(username)
        ]
