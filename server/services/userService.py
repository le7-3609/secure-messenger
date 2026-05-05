from ..models import User
from ..repositories import UserRepository
from ..exceptions import ConflictError, AuthenticationError
from .authService import AuthService


class UserService:
    def __init__(self, repo: UserRepository, auth: AuthService) -> None:
        '''Injects the user repository and auth service.'''
        self.repo = repo
        self.auth = auth

    def register(self, username: str, password: str) -> User:
        '''Registers a new user. Raises ConflictError if the username is already taken.'''
        if self.repo.get_by_username(username):
            raise ConflictError(f"Username '{username}' is already taken")
        return self.repo.save(User(username=username, password_hash=self.auth.hash_password(password)))

    def login(self, username: str, password: str) -> str:
        '''Validates credentials and returns a JWT token. Raises AuthenticationError if invalid.'''
        user = self.repo.get_by_username(username)
        if not user or not self.auth.verify_password(password, user.password_hash):
            raise AuthenticationError(f"Invalid credentials for user '{username}'")
        return self.auth.create_token(username)
