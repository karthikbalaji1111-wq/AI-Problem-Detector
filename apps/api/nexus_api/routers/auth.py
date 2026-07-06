from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_api.audit import record_audit
from nexus_api.config import get_settings
from nexus_api.database import get_db
from nexus_api.dependencies import current_user
from nexus_api.models import User
from nexus_api.schemas import GoogleAuthStart, TokenResponse, UserCreate, UserLogin, UserRead
from nexus_api.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> TokenResponse:
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(
        email=payload.email.lower(),
        name=payload.name.strip(),
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    record_audit(
        db,
        organization_id=None,
        actor_type="user",
        actor_id=user.id,
        action="user.registered",
        target_type="user",
        target_id=user.id,
    )
    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserRead.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(user.id)
    record_audit(
        db,
        organization_id=None,
        actor_type="user",
        actor_id=user.id,
        action="user.login",
        target_type="user",
        target_id=user.id,
    )
    return TokenResponse(access_token=token, user=UserRead.model_validate(user))


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(current_user)) -> User:
    return user


@router.get("/google/start", response_model=GoogleAuthStart)
def google_start() -> GoogleAuthStart:
    settings = get_settings()
    if not settings.google_client_id or not settings.google_redirect_uri:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")
    query = urlencode(
        {
            "client_id": settings.google_client_id,
            "redirect_uri": str(settings.google_redirect_uri),
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
        }
    )
    return GoogleAuthStart(authorization_url=f"https://accounts.google.com/o/oauth2/v2/auth?{query}")


@router.get("/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)) -> RedirectResponse:
    settings = get_settings()
    if not all([settings.google_client_id, settings.google_client_secret, settings.google_redirect_uri]):
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")
    async with httpx.AsyncClient(timeout=15) as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": str(settings.google_redirect_uri),
                "grant_type": "authorization_code",
            },
        )
        token_response.raise_for_status()
        access_token = token_response.json()["access_token"]
        profile_response = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        profile_response.raise_for_status()
        profile = profile_response.json()
    email = profile["email"].lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(
            email=email,
            name=profile.get("name") or email.split("@")[0],
            oauth_provider="google",
            oauth_subject=profile["sub"],
        )
        db.add(user)
    else:
        user.oauth_provider = "google"
        user.oauth_subject = profile["sub"]
    db.commit()
    db.refresh(user)
    jwt_token = create_access_token(user.id)
    record_audit(
        db,
        organization_id=None,
        actor_type="user",
        actor_id=user.id,
        action="user.google_login",
        target_type="user",
        target_id=user.id,
    )
    return RedirectResponse(url=f"{settings.frontend_url.rstrip('/')}/login?token={jwt_token}")
