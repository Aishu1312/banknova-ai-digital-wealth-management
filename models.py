from sqlalchemy import Column, Integer, String, Float, Date, JSON, Text
from database import Base

class PortfolioHolding(Base):
    __tablename__ = "portfolio_holdings"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    value = Column(Float)
    change = Column(Float)

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date)
    merchant = Column(String, index=True)
    category = Column(String, index=True)
    amount = Column(Float)

class Goal(Base):
    __tablename__ = "goals"
    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    type = Column(String)
    target = Column(Float)
    saved = Column(Float)
    target_year = Column(Integer)
    monthly_sip = Column(Float)

class RiskAllocation(Base):
    __tablename__ = "risk_allocations"
    profile = Column(String, primary_key=True, index=True)
    equity = Column(Integer)
    debt = Column(Integer)
    gold = Column(Integer)
    description = Column(Text)

class Suggestion(Base):
    __tablename__ = "suggestions"
    id = Column(Integer, primary_key=True, index=True)
    risk_profile = Column(String, index=True)
    type = Column(String)
    name = Column(String)
    detail = Column(String)
    expected_return = Column(String)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    body = Column(String)
    time = Column(String)
    type = Column(String)
