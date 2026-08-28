"""
Auth router — login endpoint.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.auth import create_token, get_user_context

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str


class LoginResponse(BaseModel):
    token: str
    user_id: str
    email: str
    department: str
    roles: list[str]


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest):
    """
    Login with an email address. Returns a JWT token.

    For the PoC, any registered demo user email works (no password needed).
    """
    # Find user by email
    from backend.database import SessionLocal
    from backend.models import User

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == req.email).first()
        if not user:
            raise HTTPException(status_code=401, detail=f"Unknown user: {req.email}")

        token = create_token(user.user_id)
        ctx = get_user_context(user.user_id)

        return LoginResponse(
            token=token,
            user_id=ctx.user_id,
            email=ctx.email,
            department=ctx.department,
            roles=ctx.roles,
        )
    finally:
        db.close()
