from .base import Base, engine, get_db
from .user import User
from .message import Message


def create_tables():
    Base.metadata.create_all(bind=engine)
