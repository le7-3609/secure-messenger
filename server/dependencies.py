from fastapi import Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .models import get_db
from .repositories import UserRepository, MessageRepository
from .services import AuthService, UserService, MessageService
from .broadcaster import broadcaster, Broadcaster

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


def get_broadcaster() -> Broadcaster:
    '''Returns the shared broadcaster singleton.'''
    return broadcaster


def get_message_service(
    repo: MessageRepository = Depends(get_message_repo),
    user_repo: UserRepository = Depends(get_user_repo),
) -> MessageService:
    '''Wires MessageService with its repository dependencies.'''
    return MessageService(repo, user_repo)


def require_auth(
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    token: str | None = Query(default=None),
) -> str:
    '''Accepts Bearer token from Authorization header or ?token= query param (for EventSource).'''
    raw = token
    if raw is None:
        authorization = request.headers.get("Authorization", "")
        scheme, _, raw = authorization.partition(" ")
        if scheme.lower() != "bearer" or not raw:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authenticated",
            )
    username = auth.decode_token(raw)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username
