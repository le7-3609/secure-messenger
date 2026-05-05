from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .models import get_db
from .repositories import UserRepository, MessageRepository
from .services import AuthService, UserService, MessageService

_bearer = HTTPBearer()


def get_auth_service() -> AuthService:
    '''Creates a fresh AuthService instance.'''
    return AuthService()


def get_user_repo(db: Session = Depends(get_db)) -> UserRepository:
    '''Creates a UserRepository bound to the current request's DB session.'''
    return UserRepository(db)


def get_message_repo(db: Session = Depends(get_db)) -> MessageRepository:
    '''Creates a MessageRepository bound to the current request's DB session.'''
    return MessageRepository(db)


def get_user_service(
    repo: UserRepository = Depends(get_user_repo),
    auth: AuthService = Depends(get_auth_service),
) -> UserService:
    '''Wires UserService with its repository and auth dependencies.'''
    return UserService(repo, auth)


def get_message_service(
    repo: MessageRepository = Depends(get_message_repo),
) -> MessageService:
    '''Wires MessageService with its repository dependency.'''
    return MessageService(repo)


def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    auth: AuthService = Depends(get_auth_service),
) -> str:
    '''Extracts and validates the Bearer token. Returns the username or raises HTTP 401.'''
    username = auth.decode_token(credentials.credentials)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username
