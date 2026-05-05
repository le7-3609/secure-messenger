from sqlalchemy.orm import Session
from ..models import Message


class MessageRepository:
    def __init__(self, db: Session) -> None:
        '''Injects the SQLAlchemy database session.'''
        self.db = db

    def save(self, message: Message) -> Message:
        '''Persists a new Message row and returns it with auto-generated fields populated.'''
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_for_user(self, username: str) -> list[Message]:
        '''Returns all messages where the user is either sender or recipient, ordered by time.'''
        return (
            self.db.query(Message)
            .filter((Message.sender == username) | (Message.recipient == username))
            .order_by(Message.created_at)
            .all()
        )
