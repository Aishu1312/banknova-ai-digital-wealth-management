from sqlalchemy import Column, Integer, String, Float, Date, JSON, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import datetime
from database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_verified = Column(Boolean, default=True)
    verification_token = Column(String, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    auth_provider = Column(String, default="local")
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token = Column(String, unique=True, index=True)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token = Column(String, unique=True, index=True)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


# ---------------------------------------------------------------------------
# FIX: The 4 tables below previously had NO user_id column at all, meaning
# every logged-in user shared the exact same portfolio/transactions/
# goals/notifications. Added user_id FK + index to each so data.py can
# properly scope queries per-user.
# ---------------------------------------------------------------------------

class PortfolioHolding(Base):
    __tablename__ = "portfolio_holdings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name = Column(String, index=True)
    value = Column(Float)
    change = Column(Float)


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    date = Column(Date)
    merchant = Column(String, index=True)
    category = Column(String, index=True)
    amount = Column(Float)


class Goal(Base):
    __tablename__ = "goals"
    # NOTE: id was a String primary key before (e.g. "goal_1"). Kept as-is
    # for backwards compatibility with any existing seed data / frontend
    # references, just added user_id alongside it.
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name = Column(String)
    type = Column(String)
    target = Column(Float)
    saved = Column(Float)
    target_year = Column(Integer)
    monthly_sip = Column(Float)


class RiskAllocation(Base):
    __tablename__ = "risk_allocations"
    # Intentionally NOT user-scoped: this is reference/lookup data
    # (Conservative/Moderate/Aggressive profiles), same for every user.
    profile = Column(String, primary_key=True, index=True)
    equity = Column(Integer)
    debt = Column(Integer)
    gold = Column(Integer)
    description = Column(Text)


class Suggestion(Base):
    __tablename__ = "suggestions"
    # Intentionally NOT user-scoped: these are generic recommendations
    # keyed off risk_profile, not tied to an individual user's data.
    id = Column(Integer, primary_key=True, index=True)
    risk_profile = Column(String, index=True)
    type = Column(String)
    name = Column(String)
    detail = Column(String)
    expected_return = Column(String)


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title = Column(String)
    body = Column(String)
    time = Column(String)
    type = Column(String)
