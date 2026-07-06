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
    <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; max-width: 600px; margin: 40px auto; padding: 40px; background-color: #ffffff; border: 1px solid #eaeaea; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
        <div style="text-align: center; margin-bottom: 30px;">
            <div style="display: inline-block; background: linear-gradient(135deg, #fcd34d, #f59e0b); color: #000; font-weight: 800; font-size: 24px; width: 48px; height: 48px; line-height: 48px; border-radius: 12px; margin: 0 auto;">B</div>
        </div>
        <h2 style="color: #111111; font-size: 24px; font-weight: 600; text-align: center; margin-bottom: 10px;">Verify your email</h2>
        <p style="color: #555555; font-size: 16px; line-height: 1.6; text-align: center; margin-bottom: 30px;">
            Welcome to BankNova AI! To get started and secure your account, please verify your email address.
        </p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{link}" style="background-color: #111111; color: #ffffff; padding: 14px 28px; text-decoration: none; font-weight: 600; font-size: 16px; border-radius: 6px; display: inline-block;">Verify Email Address</a>
        </div>
        <hr style="border: none; border-top: 1px solid #eaeaea; margin: 30px 0;" />
        <p style="color: #888888; font-size: 13px; line-height: 1.5; text-align: center;">
            If you did not create an account with BankNova AI, please ignore this email. This link will expire in 24 hours.
        </p>
    </div>
    """
    send_email(email, "Verify Your BankNova AI Account", html)

def send_reset_password_email(email: str, token: str):
    link = f"http://localhost:8501/?reset={token}"
    html = f"""
    <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; max-width: 600px; margin: 40px auto; padding: 40px; background-color: #ffffff; border: 1px solid #eaeaea; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
        <div style="text-align: center; margin-bottom: 30px;">
            <div style="display: inline-block; background: linear-gradient(135deg, #fcd34d, #f59e0b); color: #000; font-weight: 800; font-size: 24px; width: 48px; height: 48px; line-height: 48px; border-radius: 12px; margin: 0 auto;">B</div>
        </div>
        <h2 style="color: #111111; font-size: 24px; font-weight: 600; text-align: center; margin-bottom: 10px;">Reset your password</h2>
        <p style="color: #555555; font-size: 16px; line-height: 1.6; text-align: center; margin-bottom: 30px;">
            We received a request to reset the password for your BankNova AI account associated with this email. This link is valid for <strong>15 minutes</strong>.
        </p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{link}" style="background-color: #111111; color: #ffffff; padding: 14px 28px; text-decoration: none; font-weight: 600; font-size: 16px; border-radius: 6px; display: inline-block;">Reset Password</a>
        </div>
        <div style="background-color: #fef2f2; border: 1px solid #fecaca; padding: 15px; border-radius: 6px; margin: 20px 0;">
            <p style="color: #dc2626; font-size: 14px; font-weight: 600; margin: 0 0 5px 0;">Security Warning</p>
            <p style="color: #991b1b; font-size: 13px; line-height: 1.5; margin: 0;">If you did not request a password reset, someone may be trying to access your account. Do not click the link and consider updating your security settings.</p>
        </div>
    </div>
    """
    send_email(email, "BankNova AI Password Reset", html)
