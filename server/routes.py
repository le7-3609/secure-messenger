import asyncio
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sse_starlette.sse import EventSourceResponse
from .schemas import RegisterRequest, LoginRequest, TokenResponse, SendMessageRequest, MessageResponse
from .services import UserService, MessageService, NotFoundError
from .dependencies import get_user_service, get_message_service, get_broadcaster, require_auth
from .broadcaster import Broadcaster
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


@router.post("/messages", response_model=list[MessageResponse], status_code=status.HTTP_201_CREATED)
async def send_message(
    body: SendMessageRequest,
    svc: MessageService = Depends(get_message_service),
    bc: Broadcaster = Depends(get_broadcaster),
    username: str = Depends(require_auth),
) -> list[MessageResponse]:
    '''Sends an encrypted message to one or more recipients. Use ["*"] to broadcast to everyone.'''
    try:
        resolved = svc.resolve_recipients(body.recipients, sender=username)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    results = svc.send(body.content, username, resolved)
    payload = json.dumps({"sender": username, "content": body.content,
                          "created_at": results[0]["created_at"].isoformat()})
    for recipient in resolved:
        await bc.publish(recipient, payload)
    return results


@router.get("/messages", response_model=list[MessageResponse])
def get_messages(
    svc: MessageService = Depends(get_message_service),
    username: str = Depends(require_auth),
) -> list[MessageResponse]:
    '''Fetches all messages for the authenticated user (sent or received), decrypted.'''
    return svc.get_messages(username)


@router.get("/stream")
async def stream(
    request: Request,
    bc: Broadcaster = Depends(get_broadcaster),
    username: str = Depends(require_auth),
):
    '''SSE endpoint. Pushes new incoming messages to the authenticated user in real time.'''
    async def event_generator():
        async for payload in bc.listen(username):
            if await request.is_disconnected():
                break
            yield {"data": payload}
    return EventSourceResponse(event_generator())
