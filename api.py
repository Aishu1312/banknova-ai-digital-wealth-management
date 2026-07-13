from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, EmailStr
import database
import models
import auth_utils
import datetime
import secrets
import os
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from fastapi.responses import JSONResponse, Response
import json
import logging
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
# NOTE: In production (Render/Railway), set these as real environment
# variables in the dashboard. Localhost values are just safe fallbacks for
# local dev.
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:8501")
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module
        }
        if record.exc_info:
            log_record["trace"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


logger = logging.getLogger("banknova_api")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'"
        return response


limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SecurityHeadersMiddleware)

# Initialize database tables
models.Base.metadata.create_all(bind=database.engine)

# ---------------------------------------------------------------------------
# FIX #1: CORS was allow_origins=["*"] with allow_credentials=True.
# Browsers reject wildcard origin + credentials in practice, and it's an
# open door security-wise. Lock it to the actual deployed frontend, but
# still allow localhost for local dev.
# ---------------------------------------------------------------------------
allowed_origins = [FRONTEND_URL, "http://localhost:8501", "http://127.0.0.1:8501"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth needs session middleware
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SESSION_SECRET_KEY", secrets.token_urlsafe(32)))


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception in {request.url.path}", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error"}
    )


# ---------------------------------------------------------------------------
# FIX #2: /status and /ready were each defined TWICE. FastAPI doesn't error
# on this -- it silently keeps only the LAST definition and the first one
# becomes dead code. Below is the de-duplicated, merged version of each.
# ---------------------------------------------------------------------------

@app.get("/health")
def health_check(db: Session = Depends(database.get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "error"
    return {"status": "ok" if db_status == "ok" else "degraded", "database": db_status}


@app.get("/ready")
def ready_check(db: Session = Depends(database.get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="Service Unavailable")

    if not os.environ.get("JWT_SECRET_KEY"):
        logger.warning("JWT_SECRET_KEY is missing, using default.")

    return {"status": "ready"}


@app.get("/status")
def full_status(db: Session = Depends(database.get_db)):
    db_status = "offline"
    try:
        db.execute(text("SELECT 1"))
        db_status = "online"
    except Exception:
        pass

    return {
        "status": "online",
        "service": "BankNova API",
        "version": "1.0.0",
        "services": {
            "database": db_status,
            "authentication": "online",
            "email_service": "online"
        },
        "environment": {
            "jwt_configured": bool(os.environ.get("JWT_SECRET_KEY")),
            "google_oauth_configured": bool(os.environ.get("GOOGLE_CLIENT_ID")),
            "frontend_url": FRONTEND_URL,
            "api_base_url": API_BASE_URL
        }
    }


@app.get("/version")
def version_check():
    return {"version": "1.0.0"}


oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# ---------------------------------------------------------------------------
# NEW: /auth/me endpoint. The frontend only ever received an access_token
# after login -- there was no way to find out WHICH user that token
# belongs to (no user_id in the response anywhere). Since data.py now
# requires user_id for every query, the frontend needs this endpoint to
# resolve "who am I" right after login / on page load.
# ---------------------------------------------------------------------------
import jwt as pyjwt
from auth_utils import SECRET_KEY, ALGORITHM


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except pyjwt.PyJWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user


@app.get("/auth/me")
def read_current_user(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "avatar_url": current_user.avatar_url,
    }


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class ResendVerification(BaseModel):
    email: EmailStr


class ForgotPassword(BaseModel):
    email: EmailStr


class ResetPassword(BaseModel):
    token: str
    new_password: str


class RefreshTokenReq(BaseModel):
    refresh_token: str


@app.post("/auth/register")
@limiter.limit("5/minute")
def register(request: Request, user: UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = auth_utils.get_password_hash(user.password)

    new_user = models.User(
        name=user.name,
        email=user.email,
        hashed_password=hashed_password,
        is_verified=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully. You can now log in."}


@app.post("/auth/login")
@limiter.limit("10/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user:
        raise HTTPException(status_code=400, detail="No account found with this email.")

    if user.locked_until and user.locked_until > datetime.datetime.utcnow():
        raise HTTPException(status_code=400, detail="Too many failed login attempts. Please try again later.")

    if not auth_utils.verify_password(form_data.password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
        db.commit()
        raise HTTPException(status_code=400, detail="Incorrect password. Please try again.")

    # Successful login
    user.failed_login_attempts = 0
    user.locked_until = None

    access_token = auth_utils.create_access_token(data={"sub": user.email})
    refresh_token = auth_utils.create_refresh_token(data={"sub": user.email})

    # Clear existing refresh tokens for the user to avoid duplication/bloat
    db.query(models.RefreshToken).filter(models.RefreshToken.user_id == user.id).delete()

    # Store refresh token
    db_refresh = models.RefreshToken(user_id=user.id, token=refresh_token, expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=7))
    db.add(db_refresh)
    db.commit()

    response = JSONResponse(content={"access_token": access_token, "token_type": "bearer"})
    is_prod = os.environ.get("ENVIRONMENT", "development") == "production"
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        max_age=7 * 24 * 60 * 60
    )
    return response


@app.post("/auth/forgot-password")
@limiter.limit("3/minute")
def forgot_password(request: Request, payload: ForgotPassword, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if user:
        reset_token = secrets.token_urlsafe(32)
        db_token = models.PasswordResetToken(
            user_id=user.id,
            token=reset_token,
            expires_at=datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
        )
        db.add(db_token)
        db.commit()
        background_tasks.add_task(auth_utils.send_reset_password_email, user.email, reset_token)
        reset_link = f"{FRONTEND_URL}/?reset={reset_token}"
        return {"message": "If an account exists for this email, a reset link has been sent.", "reset_link": reset_link}
    return {"message": "If an account exists for this email, a reset link has been sent."}


@app.post("/auth/reset-password")
@limiter.limit("5/minute")
def reset_password(request: Request, payload: ResetPassword, db: Session = Depends(database.get_db)):
    token_record = db.query(models.PasswordResetToken).filter(models.PasswordResetToken.token == payload.token).first()
    if not token_record or token_record.expires_at < datetime.datetime.utcnow():
        raise HTTPException(status_code=400, detail="This reset link has expired.")

    user = db.query(models.User).filter(models.User.id == token_record.user_id).first()
    user.hashed_password = auth_utils.get_password_hash(payload.new_password)
    db.query(models.PasswordResetToken).filter(models.PasswordResetToken.user_id == user.id).delete()
    db.query(models.RefreshToken).filter(models.RefreshToken.user_id == user.id).delete()
    db.commit()
    return {"message": "Password changed successfully."}


@app.post("/auth/verify-email")
def verify_email(token: str, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.verification_token == token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid verification token")

    user.is_verified = True
    user.verification_token = None
    db.commit()
    return {"message": "Email verified successfully"}


@app.post("/auth/resend-verification")
@limiter.limit("3/minute")
def resend_verification(request: Request, payload: ResendVerification, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user:
        return {"message": "If an account exists, a verification email has been sent."}

    if user.is_verified:
        raise HTTPException(status_code=400, detail="Account is already verified.")

    verification_token = secrets.token_urlsafe(32)
    user.verification_token = verification_token
    db.commit()

    background_tasks.add_task(auth_utils.send_verification_email, user.email, verification_token)
    return {"message": "If an account exists, a verification email has been sent."}


@app.post("/auth/refresh")
def refresh_token(request: Request, db: Session = Depends(database.get_db)):
    token = request.cookies.get("refresh_token")
    if not token:
        # Fallback to payload for testing/streamlit
        data = request.json() if request.method == "POST" else {}
        token = data.get("refresh_token") if isinstance(data, dict) else None

    if not token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    db_token = db.query(models.RefreshToken).filter(models.RefreshToken.token == token).first()
    if not db_token or db_token.expires_at < datetime.datetime.utcnow():
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = db.query(models.User).filter(models.User.id == db_token.user_id).first()
    access_token = auth_utils.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/auth/logout")
def logout(request: Request, response: Response, db: Session = Depends(database.get_db)):
    token = request.cookies.get("refresh_token")
    if token:
        db.query(models.RefreshToken).filter(models.RefreshToken.token == token).delete()
        db.commit()

    response = JSONResponse(content={"message": "Logged out successfully."})
    response.delete_cookie("refresh_token")
    return response


@app.post("/auth/logout-all")
def logout_all(request: Request, response: Response, email: str, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if user:
        db.query(models.RefreshToken).filter(models.RefreshToken.user_id == user.id).delete()
        db.commit()

    response = JSONResponse(content={"message": "Logged out of all devices."})
    response.delete_cookie("refresh_token")
    return response


@app.get("/auth/login/{provider}")
async def login_via_oauth(provider: str, request: Request):
    if provider not in ["google"]:
        raise HTTPException(status_code=400, detail="Unsupported provider")

    redirect_uri = f"{API_BASE_URL}/auth/callback/{provider}"
    client = oauth.create_client(provider)
    return await client.authorize_redirect(request, redirect_uri)


@app.get("/auth/callback/{provider}")
async def auth_callback(provider: str, request: Request, db: Session = Depends(database.get_db)):
    try:
        if provider != "google":
            raise HTTPException(status_code=400, detail="Unsupported provider")

        client = oauth.create_client(provider)
        token = await client.authorize_access_token(request)
        user_info = token.get('userinfo')
        if not user_info:
            user_info = await client.parse_id_token(request, token)

        email = user_info.get("email")
        name = user_info.get("name", "User")

        if not email:
            return RedirectResponse(url=f"{FRONTEND_URL}/?error=NoEmailFound")

        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            # Create user for OAuth automatically verified
            user = models.User(
                name=name,
                email=email,
                hashed_password=auth_utils.get_password_hash(secrets.token_urlsafe(16)),
                is_verified=True,
                auth_provider=provider,
                avatar_url=user_info.get('picture')
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # Generate our own JWT
        access_token = auth_utils.create_access_token(data={"sub": user.email})
        refresh_token = auth_utils.create_refresh_token(data={"sub": user.email})
        db_refresh = models.RefreshToken(user_id=user.id, token=refresh_token, expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=7))
        db.add(db_refresh)
        db.commit()

        response = RedirectResponse(url=f"{FRONTEND_URL}/?token={access_token}")
        is_prod = os.environ.get("ENVIRONMENT", "development") == "production"
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=is_prod,
            samesite="lax",
            max_age=7 * 24 * 60 * 60
        )
        return response
    except Exception as e:
        logger.error(f"OAuth error: {str(e)}", exc_info=e)
        return RedirectResponse(url=f"{FRONTEND_URL}/?error=OAuthFailed")



        
