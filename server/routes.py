import logging
from fastapi import APIRouter, Depends, HTTPException, status
from .schemas import RegisterRequest, LoginRequest, TokenResponse, SendMessageRequest, MessageResponse
from .services import UserService, MessageService
from .dependencies import get_user_service, get_message_service, require_auth
from .exceptions import ConflictError, AuthenticationError

log = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, svc: UserService = Depends(get_user_service)) -> dict[str, str]:
    '''Registers a new user. Returns 400 if username is already taken.'''
    try:
        svc.register(body.username, body.password)
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    return {"message": "User created successfully"}


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, svc: UserService = Depends(get_user_service)) -> dict[str, str]:
    '''Validates credentials and returns a JWT token. Returns 401 if invalid.'''
    try:
        token = svc.login(body.username, body.password)
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.message)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(
    body: SendMessageRequest,
    svc: MessageService = Depends(get_message_service),
    username: str = Depends(require_auth),
) -> MessageResponse:
    '''Sends an encrypted message. Requires authentication.'''
    return svc.send(body.content, username, body.recipient)


@router.get("/messages", response_model=list[MessageResponse])
def get_messages(
    svc: MessageService = Depends(get_message_service),
    username: str = Depends(require_auth),
) -> list[MessageResponse]:
    '''Fetches all messages for the authenticated user (sent or received), decrypted.'''
    return svc.get_messages(username)
