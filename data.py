from typing import List, Dict, Any, Union
from database import SessionLocal
import models
from sqlalchemy.orm import Session

def get_portfolio_holdings() -> List[Dict[str, Union[str, int, float]]]:
    with SessionLocal() as db:
        holdings = db.query(models.PortfolioHolding).all()
        return [{"name": h.name, "value": h.value, "change": h.change} for h in holdings]

def get_total_wealth() -> int:
    holdings = get_portfolio_holdings()
    return int(sum(h["value"] for h in holdings))

def get_transactions() -> List[Dict[str, Union[str, int]]]:
    with SessionLocal() as db:
        txs = db.query(models.Transaction).all()
        return [{"date": str(t.date), "merchant": t.merchant, "category": t.category, "amount": t.amount} for t in txs]

def category_breakdown() -> Dict[str, int]:
    txs = get_transactions()
    totals: Dict[str, int] = {}
    for t in txs:
        cat = str(t["category"])
        amt = int(t["amount"])
        totals[cat] = totals.get(cat, 0) + amt
    return dict(sorted(totals.items(), key=lambda kv: kv[1], reverse=True))

def get_goals() -> List[Dict[str, Union[str, int]]]:
    with SessionLocal() as db:
        db_goals = db.query(models.Goal).all()
        return [{
            "id": g.id,
            "name": g.name,
            "type": g.type,
            "target": g.target,
            "saved": g.saved,
            "target_year": g.target_year,
            "monthly_sip": g.monthly_sip
        } for g in db_goals]

def get_risk_allocations() -> Dict[str, Dict[str, Union[int, str]]]:
    with SessionLocal() as db:
        allocs = db.query(models.RiskAllocation).all()
        return {
            a.profile: {
                "equity": a.equity,
                "debt": a.debt,
                "gold": a.gold,
                "description": a.description
            } for a in allocs
        }

def get_suggestions_by_risk() -> Dict[str, List[Dict[str, str]]]:
    with SessionLocal() as db:
        suggs = db.query(models.Suggestion).all()
        res = {}
        for s in suggs:
            if s.risk_profile not in res:
                res[s.risk_profile] = []
            res[s.risk_profile].append({
                "type": s.type,
                "name": s.name,
                "detail": s.detail,
                "expected_return": s.expected_return
            })
        return res

def get_notifications() -> List[Dict[str, str]]:
    with SessionLocal() as db:
        nots = db.query(models.Notification).all()
        return [{
            "title": n.title,
            "body": n.body,
            "time": n.time,
            "type": n.type
        } for n in nots]
