from fastapi import APIRouter, Depends, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenPair
from app.schemas.user import UserRead, UserRole
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])
bearer = HTTPBearer(auto_error=False)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    return auth_service.register(db, payload)


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> TokenPair:
    response.headers["Cache-Control"] = "no-store"
    return auth_service.login(db, payload)


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, response: Response, db: Session = Depends(get_db)) -> TokenPair:
    response.headers["Cache-Control"] = "no-store"
    return auth_service.refresh(db, payload.refresh_token.get_secret_value())


@router.get("/me", response_model=UserRole)
def me(
    response: Response,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> UserRole:
    if credentials is None:
        raise auth_service.invalid_credentials()
    response.headers["Cache-Control"] = "no-store"
    return auth_service.authenticate(db, credentials.credentials)
