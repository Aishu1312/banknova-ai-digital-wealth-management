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

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

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
    
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

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

@app.post("/auth/refresh")
def refresh_token(payload: RefreshTokenReq, db: Session = Depends(database.get_db)):
    db_token = db.query(models.RefreshToken).filter(models.RefreshToken.token == payload.refresh_token).first()
    if not db_token or db_token.expires_at < datetime.datetime.utcnow():
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
        
    user = db.query(models.User).filter(models.User.id == db_token.user_id).first()
    access_token = auth_utils.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}
