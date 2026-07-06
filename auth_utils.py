import os
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from passlib.context import CryptContext
import jwt
from passlib.context import CryptContext
import jwt

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: datetime.timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    expire = datetime.datetime.utcnow() + datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = data.copy()
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_smtp_config():
    return {
        "server": os.environ.get("SMTP_SERVER"),
        "port": int(os.environ.get("SMTP_PORT", 587)),
        "user": os.environ.get("SMTP_USER"),
        "password": os.environ.get("SMTP_PASSWORD")
    }

def send_email(to_email: str, subject: str, html_body: str):
    config = get_smtp_config()
    
    # Fallback for local development if no SMTP config is provided
    if not config["server"] or not config["user"]:
        print("\n" + "="*50)
        print(f"[DEVELOPMENT MODE] Email to: {to_email}")
        print(f"Subject: {subject}")
        print("Body (HTML snippet):")
        # Just print a snippet of the link
        import re
        link = re.search(r'href=[\'"]?([^\'" >]+)', html_body)
        if link:
            print(f"Action Link: {link.group(1)}")
        print("="*50 + "\n")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"BankNova Security <{config['user']}>"
    msg["To"] = to_email

    msg.attach(MIMEText(html_body, "html"))

    try:
        server = smtplib.SMTP(config["server"], config["port"])
        server.starttls()
        server.login(config["user"], config["password"])
        server.sendmail(config["user"], to_email, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")

def send_verification_email(email: str, token: str):
    link = f"http://localhost:8501/?verify={token}"
    html = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
        <h2 style="color: #333;">Welcome to BankNova AI</h2>
        <p>Please verify your email address to complete your registration and secure your account.</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{link}" style="background-color: #f5b03e; color: black; padding: 12px 24px; text-decoration: none; font-weight: bold; border-radius: 5px;">Verify Email</a>
        </div>
        <p style="color: #888; font-size: 12px;">If you didn't create an account with us, please ignore this email.</p>
    </div>
    """
    send_email(email, "Verify Your BankNova AI Account", html)

def send_reset_password_email(email: str, token: str):
    link = f"http://localhost:8501/?reset={token}"
    html = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
        <h2 style="color: #333;">Password Reset Request</h2>
        <p>We received a request to reset your password. This link is valid for 15 minutes.</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{link}" style="background-color: #f5b03e; color: black; padding: 12px 24px; text-decoration: none; font-weight: bold; border-radius: 5px;">Reset Password</a>
        </div>
        <p style="color: #ef4444; font-size: 13px; font-weight: bold;">Security Warning:</p>
        <p style="color: #888; font-size: 12px;">If you did not request a password reset, someone may be trying to access your account. Do not click the link and consider updating your security settings.</p>
    </div>
    """
    send_email(email, "BankNova AI Password Reset", html)
