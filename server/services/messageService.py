from typing import TypedDict
from datetime import datetime
from ..models import Message
from ..repositories import MessageRepository
from ..crypto import encrypt, decrypt


class MessageDict(TypedDict):
    '''Type definition for a decrypted message returned to the client.'''
    id: int
    sender: str
    recipient: str
    content: str
    created_at: datetime


class MessageService:
    def __init__(self, repo: MessageRepository) -> None:
        '''Injects the message repository.'''
        self.repo = repo

    def send(self, content: str, sender: str, recipient: str) -> MessageDict:
        '''Encrypts and saves a new message. Returns the message with decrypted content.'''
        message = self.repo.save(Message(sender=sender, recipient=recipient, ciphertext=encrypt(content)))
        return MessageDict(
            id=message.id,
            sender=message.sender,
            recipient=message.recipient,
            content=content,
            created_at=message.created_at
        )

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
