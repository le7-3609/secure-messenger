from sqlalchemy.orm import Session
from ..models import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        '''Injects the SQLAlchemy database session.'''
        self.db = db

    def get_by_username(self, username: str) -> User | None:
        '''Returns the User with the given username, or None if not found.'''
        return self.db.query(User).filter(User.username == username).first()

    def save(self, user: User) -> User:
        '''Persists a new User row and returns it with auto-generated fields populated.'''
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
