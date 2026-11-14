from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.rate_limit import client_key, rate_limiter
from app.db.session import get_db
from app.models import EmailToken, User
from app.models import Session as UserSession
from app.services.google_auth import verify_google_id_token
from app.services.mailer import send_mail
from app.services.security import (
    expiry,
    hash_password,
    random_token,
    token_hash,
    utcnow,
    valid_college_email,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=5, max_length=128)
    consent: bool


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class GoogleIn(BaseModel):
    credential: str = Field(min_length=20, max_length=10000)


class TokenIn(BaseModel):
    token: str = Field(min_length=20, max_length=200)


class PasswordResetIn(BaseModel):
    email: EmailStr


class PasswordSetIn(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    password: str = Field(min_length=5, max_length=128)


class ProfilePatch(BaseModel):
    name: str = Field(min_length=2, max_length=120)


def _set_session(response: Response, db: Session, user: User):
    raw = random_token()
    db.add(
        UserSession(
            user_id=user.id,
            token_hash=token_hash(raw),
            expires_at=expiry(settings.session_hours * 60),
        )
    )
    response.set_cookie(
        "hf_session",
        raw,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.session_hours * 3600,
        path="/",
    )
    response.set_cookie(
        "hf_csrf",
        random_token(),
        httponly=False,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.session_hours * 3600,
        path="/",
    )


def _public_user(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "category_id": user.category_id,
        "is_verified": user.is_verified,
        "created_at": user.created_at,
    }


@router.get("/config")
def auth_config():
    return {"client_id": settings.google_client_id}


@router.post("/register", status_code=201)
def register(
    request: Request, payload: RegisterIn, response: Response, db: Session = Depends(get_db)
):
    rate_limiter.check(
        client_key(request, "register"), 5, 900, "Too many registration attempts. Try again later."
    )
    email = str(payload.email).lower()
    if not valid_college_email(email):
        raise HTTPException(422, "Only exact iitdh.ac.in email addresses are allowed")
    if not payload.consent:
        raise HTTPException(422, "Consent is required to create an account")
    if db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first():
        raise HTTPException(409, "An account with this email already exists")
    user = User(
        name=payload.name.strip(),
        email=email,
        role="student",
        password_hash=hash_password(payload.password),
        is_verified=False,
    )
    db.add(user)
    db.flush()
    raw = random_token()
    db.add(
        EmailToken(
            user_id=user.id,
            token_hash=token_hash(raw),
            purpose="verify",
            expires_at=expiry(24 * 60),
        )
    )
    db.commit()
    link = f"{settings.cors_origin_list[0]}/?verify={raw}"
    send_mail(
        email,
        "Verify your HostelFix account",
        f"Open this link to verify your account:\n{link}\n\nThis link expires in 24 hours.",
    )
    return {
        "message": "Registration successful. Check your college email for the verification link.",
        "development_verification_url": link if settings.mail_mode == "log" else None,
    }


@router.post("/verify")
def verify_email(request: Request, payload: TokenIn, db: Session = Depends(get_db)):
    rate_limiter.check(
        client_key(request, "verify"), 10, 900, "Too many verification attempts. Try again later."
    )
    row = (
        db.query(EmailToken)
        .filter_by(token_hash=token_hash(payload.token), purpose="verify")
        .first()
    )
    if not row or row.expires_at < utcnow():
        raise HTTPException(400, "Verification link is invalid or expired")
    user = db.get(User, row.user_id)
    if not user or user.deleted_at:
        raise HTTPException(400, "Verification link is invalid")
    user.is_verified = True
    db.delete(row)
    db.commit()
    return {"message": "Email verified. You can now sign in."}


@router.post("/login")
def login(request: Request, payload: LoginIn, response: Response, db: Session = Depends(get_db)):
    rate_limiter.check(
        client_key(request, "login"),
        10,
        300,
        "Too many login attempts. Try again in a few minutes.",
    )
    email = str(payload.email).lower()
    if not valid_college_email(email):
        raise HTTPException(422, "Only exact iitdh.ac.in email addresses are allowed")
    user = db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first()
    if user and user.role == "student":
        raise HTTPException(403, "Student accounts must sign in with Google.")
    if (
        not user
        or not user.password_hash
        or not verify_password(payload.password, user.password_hash)
    ):
        raise HTTPException(401, "Invalid staff or administrator email or password")
    if not user.is_verified:
        raise HTTPException(403, "Email is not verified. Check your verification link.")
    _set_session(response, db, user)
    db.commit()
    return _public_user(user)


@router.post("/google")
def google_login(
    request: Request, payload: GoogleIn, response: Response, db: Session = Depends(get_db)
):
    rate_limiter.check(
        client_key(request, "google"), 10, 300, "Too many Google sign-in attempts. Try again later."
    )
    claims = verify_google_id_token(payload.credential)
    email = str(claims["email"]).lower()
    sub = str(claims["sub"])
    user = db.query(User).filter(User.google_sub == sub, User.deleted_at.is_(None)).first()
    if not user:
        user = db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first()
        if user and not user.is_verified:
            raise HTTPException(403, "Verify your college email before linking Google sign-in")
        if not user:
            user = User(
                name=str(claims.get("name") or email.split("@")[0]),
                email=email,
                role="student",
                google_sub=sub,
                is_verified=True,
            )
            db.add(user)
        else:
            user.google_sub = sub
    user.is_verified = True
    db.flush()
    _set_session(response, db, user)
    db.commit()
    return _public_user(user)


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    raw = request.cookies.get("hf_session")
    if raw:
        row = db.query(UserSession).filter_by(token_hash=token_hash(raw)).first()
        if row:
            db.delete(row)
            db.commit()
    response.delete_cookie("hf_session", path="/")
    response.delete_cookie("hf_csrf", path="/")


@router.post("/forgot-password")
def forgot_password(request: Request, payload: PasswordResetIn, db: Session = Depends(get_db)):
<<<<<<< HEAD
    rate_limiter.check(client_key(request, "forgot"), 5, 900, "Too many password-reset requests. Try again later.")
    email = str(payload.email).lower()
    if not valid_college_email(email): raise HTTPException(422, "Only exact iitdh.ac.in email addresses are allowed")
=======
    rate_limiter.check(
        client_key(request, "forgot"), 5, 900, "Too many password-reset requests. Try again later."
    )
    email = str(payload.email).lower()
    if not valid_college_email(email):
        raise HTTPException(422, "Only exact iitdh.ac.in email addresses are allowed")
>>>>>>> 674014b3680ed9758c12e5cb16302fa9b00d513d
    user = db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first()
    if user and user.password_hash:
        raw = random_token()
        db.add(
            EmailToken(
                user_id=user.id, token_hash=token_hash(raw), purpose="reset", expires_at=expiry(30)
            )
        )
        db.commit()
        link = f"{settings.cors_origin_list[0]}/?reset={raw}"
        send_mail(
            email,
            "Reset your HostelFix password",
            f"Open this link:\n{link}\n\nThis link expires in 30 minutes.",
        )
    return {"message": "If that account exists, a password reset link has been sent."}


@router.post("/reset-password")
def reset_password(
    request: Request, payload: PasswordSetIn, response: Response, db: Session = Depends(get_db)
):
    rate_limiter.check(
        client_key(request, "reset"), 10, 900, "Too many password-reset attempts. Try again later."
    )
    row = (
        db.query(EmailToken)
        .filter(
            EmailToken.token_hash == token_hash(payload.token),
            EmailToken.purpose.in_(["reset", "set_password"]),
        )
        .first()
    )
    if not row or row.expires_at < utcnow():
        raise HTTPException(400, "Reset link is invalid or expired")
    user = db.get(User, row.user_id)
    if not user or user.deleted_at:
        raise HTTPException(400, "Reset link is invalid")
    user.password_hash = hash_password(payload.password)
    if row.purpose == "set_password":
        user.is_verified = True
    db.query(UserSession).filter_by(user_id=user.id).delete(synchronize_session=False)
    db.delete(row)
    db.commit()
    return {"message": "Password reset successfully. Sign in again."}


@router.get("/csrf")
def csrf(request: Request, response: Response):
    token = request.cookies.get("hf_csrf") or random_token()
    response.set_cookie(
        "hf_csrf",
        token,
        httponly=False,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.session_hours * 3600,
        path="/",
    )
    return {"csrf_token": token}
