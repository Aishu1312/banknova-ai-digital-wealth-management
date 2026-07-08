from typing import List, Dict, Any, Union
from database import SessionLocal
import models
from sqlalchemy.orm import Session

# ---------------------------------------------------------------------------
# FIX: Every function below used to run db.query(Model).all() with ZERO
# filtering -- meaning every logged-in user saw the exact same portfolio,
# transactions, goals, and notifications. Each function now REQUIRES a
# user_id and filters accordingly. Callers (app.py) must pass the current
# logged-in user's id, e.g. get_portfolio_holdings(user_id=current_user_id).
#
# RiskAllocation and Suggestion are left unscoped on purpose -- they are
# shared reference/lookup tables (risk profile definitions and generic
# investment suggestions), not personal data.
# ---------------------------------------------------------------------------


def get_portfolio_holdings(user_id: int) -> List[Dict[str, Union[str, int, float]]]:
    with SessionLocal() as db:
        holdings = (
            db.query(models.PortfolioHolding)
            .filter(models.PortfolioHolding.user_id == user_id)
            .all()
        )
        return [{"name": h.name, "value": h.value, "change": h.change} for h in holdings]


def get_total_wealth(user_id: int) -> int:
    holdings = get_portfolio_holdings(user_id)
    return int(sum(h["value"] for h in holdings))


def get_transactions(user_id: int) -> List[Dict[str, Union[str, int]]]:
    with SessionLocal() as db:
        txs = (
            db.query(models.Transaction)
            .filter(models.Transaction.user_id == user_id)
            .all()
        )
        return [
            {"date": str(t.date), "merchant": t.merchant, "category": t.category, "amount": t.amount}
            for t in txs
        ]


def category_breakdown(user_id: int) -> Dict[str, int]:
    txs = get_transactions(user_id)
    totals: Dict[str, int] = {}
    for t in txs:
        cat = str(t["category"])
        amt = int(t["amount"])
        totals[cat] = totals.get(cat, 0) + amt
    return dict(sorted(totals.items(), key=lambda kv: kv[1], reverse=True))


def get_goals(user_id: int) -> List[Dict[str, Union[str, int]]]:
    with SessionLocal() as db:
        db_goals = (
            db.query(models.Goal)
            .filter(models.Goal.user_id == user_id)
            .all()
        )
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
    # Shared reference data -- not user-scoped by design.
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
    # Shared reference data -- not user-scoped by design.
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


def get_notifications(user_id: int) -> List[Dict[str, str]]:
    with SessionLocal() as db:
        nots = (
            db.query(models.Notification)
            .filter(models.Notification.user_id == user_id)
            .all()
        )
        return [{
            "title": n.title,
            "body": n.body,
            "time": n.time,
            "type": n.type
        } for n in nots]
