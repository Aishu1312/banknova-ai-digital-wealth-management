import datetime
from database import engine, Base, SessionLocal
import models
import static_data as data

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Clear existing data if any
    db.query(models.PortfolioHolding).delete()
    db.query(models.Transaction).delete()
    db.query(models.Goal).delete()
    db.query(models.RiskAllocation).delete()
    db.query(models.Suggestion).delete()
    db.query(models.Notification).delete()

    # Seed Portfolio Holdings
    for h in data.portfolio_holdings:
        db.add(models.PortfolioHolding(
            name=h["name"],
            value=h["value"],
            change=h["change"]
        ))

    # Seed Transactions
    for t in data.transactions:
        # Convert string date to date object
        dt = datetime.datetime.strptime(t["date"], "%Y-%m-%d").date()
        db.add(models.Transaction(
            date=dt,
            merchant=t["merchant"],
            category=t["category"],
            amount=t["amount"]
        ))

    # Seed Goals
    for g in data.goals:
        db.add(models.Goal(
            id=g["id"],
            name=g["name"],
            type=g["type"],
            target=g["target"],
            saved=g["saved"],
            target_year=g["target_year"],
            monthly_sip=g["monthly_sip"]
        ))

    # Seed Risk Profiles
    for profile, alloc in data.risk_allocations.items():
        db.add(models.RiskAllocation(
            profile=profile,
            equity=alloc["equity"],
            debt=alloc["debt"],
            gold=alloc["gold"],
            description=alloc["description"]
        ))

    # Seed Suggestions
    for profile, sugg_list in data.suggestions_by_risk.items():
        for sugg in sugg_list:
            db.add(models.Suggestion(
                risk_profile=profile,
                type=sugg["type"],
                name=sugg["name"],
                detail=sugg["detail"],
                expected_return=sugg["expected_return"]
            ))

    # Seed Notifications
    for n in data.notifications:
        db.add(models.Notification(
            title=n["title"],
            body=n["body"],
            time=n["time"],
            type=n["type"]
        ))

    db.commit()
    db.close()
    print("Database seeded successfully!")

if __name__ == "__main__":
    seed()
