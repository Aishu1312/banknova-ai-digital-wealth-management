from fastapi import FastAPI, Depends, HTTPException, status, Request
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

# OAuth needs session middleware
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SESSION_SECRET_KEY", secrets.token_urlsafe(32)))

oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

oauth.register(
    name='github',
    client_id=os.environ.get('GITHUB_CLIENT_ID'),
    client_secret=os.environ.get('GITHUB_CLIENT_SECRET'),
    access_token_url='https://github.com/login/oauth/access_token',
    access_token_params=None,
    authorize_url='https://github.com/login/oauth/authorize',
    authorize_params=None,
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'}
)

oauth.register(
    name='microsoft',
    client_id=os.environ.get('MICROSOFT_CLIENT_ID'),
    client_secret=os.environ.get('MICROSOFT_CLIENT_SECRET'),
    server_metadata_url='https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

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
    verification_token = secrets.token_urlsafe(32)
    
    new_user = models.User(
        name=user.name,
        email=user.email,
        hashed_password=hashed_password,
        verification_token=verification_token
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    auth_utils.send_verification_email(user.email, verification_token)
    return {"message": "User created successfully. Please verify your email."}

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
        
    if not user.is_verified:
        raise HTTPException(status_code=400, detail="Please verify your email before logging in.")
        
    # Successful login
    user.failed_login_attempts = 0
    user.locked_until = None
    
    access_token = auth_utils.create_access_token(data={"sub": user.email})
    refresh_token = auth_utils.create_refresh_token(data={"sub": user.email})
    
    # Store refresh token
    db_refresh = models.RefreshToken(user_id=user.id, token=refresh_token, expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=7))
    db.add(db_refresh)
    db.commit()
    
    response = JSONResponse(content={"access_token": access_token, "token_type": "bearer"})
    response.set_cookie(
        key="refresh_token", 
        value=refresh_token, 
        httponly=True, 
        secure=True, 
        samesite="lax", 
        max_age=7*24*60*60
    )
    return response

@app.post("/auth/forgot-password")
@limiter.limit("3/minute")
def forgot_password(request: Request, payload: ForgotPassword, db: Session = Depends(database.get_db)):
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
        auth_utils.send_reset_password_email(user.email, reset_token)
        reset_link = f"http://localhost:8501/?reset={reset_token}"
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
def resend_verification(request: Request, payload: ResendVerification, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user:
        return {"message": "If an account exists, a verification email has been sent."}
    
    if user.is_verified:
        raise HTTPException(status_code=400, detail="Account is already verified.")
        
    verification_token = secrets.token_urlsafe(32)
    user.verification_token = verification_token
    db.commit()
    auth_utils.send_verification_email(user.email, verification_token)
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
    if provider not in ["google", "github", "microsoft"]:
        raise HTTPException(status_code=400, detail="Unsupported provider")
    redirect_uri = f"http://localhost:8000/auth/callback/{provider}"
    client = oauth.create_client(provider)
    return await client.authorize_redirect(request, redirect_uri)

@app.get("/auth/callback/{provider}")
async def auth_callback(provider: str, request: Request, db: Session = Depends(database.get_db)):
    try:
        client = oauth.create_client(provider)
        token = await client.authorize_access_token(request)
        
        if provider == "google" or provider == "microsoft":
            user_info = token.get('userinfo')
            if not user_info:
                user_info = await client.parse_id_token(request, token)
            email = user_info.get("email")
            name = user_info.get("name", "User")
        elif provider == "github":
            resp = await client.get('user/emails', token=token)
            emails = resp.json()
            email = next((e['email'] for e in emails if e.get('primary')), emails[0]['email'])
            resp_prof = await client.get('user', token=token)
            prof_data = resp_prof.json()
            name = prof_data.get('name') or "User"
            avatar = prof_data.get('avatar_url')
            
        if not email:
            return RedirectResponse(url="http://localhost:8501/?error=NoEmailFound")
            
        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            # Create user for OAuth automatically verified
            user = models.User(
                name=name,
                email=email,
                hashed_password=auth_utils.get_password_hash(secrets.token_urlsafe(16)),
                is_verified=True,
                auth_provider=provider,
                avatar_url=avatar if provider == 'github' else user_info.get('picture')
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
        
        response = RedirectResponse(url=f"http://localhost:8501/?token={access_token}")
        response.set_cookie(
            key="refresh_token", 
            value=refresh_token, 
            httponly=True, 
            secure=True, 
            samesite="lax", 
            max_age=7*24*60*60
        )
        return response
        
    except Exception as e:
        return RedirectResponse(url="http://localhost:8501/?error=OAuthFailed")

