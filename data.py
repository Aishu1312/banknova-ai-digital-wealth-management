"""Mock data for BankNova AI — ported from the React prototype's data/mockData.ts."""

from datetime import date

# ---- Portfolio holdings ----
portfolio_holdings = [
    {"name": "Equity Mutual Funds", "value": 1120000, "change": 14.2},
    {"name": "Fixed Deposits", "value": 550000, "change": 6.8},
    {"name": "Direct Equity", "value": 380000, "change": 21.4},
    {"name": "Gold ETF", "value": 210000, "change": 9.1},
    {"name": "Emergency Fund (Savings)", "value": 225320, "change": 3.5},
]

total_wealth = sum(h["value"] for h in portfolio_holdings)

# ---- Transactions ----
transactions = [
    {"date": "2026-02-27", "merchant": "Zomato", "category": "Food & Dining", "amount": 640},
    {"date": "2026-02-26", "merchant": "Big Bazaar", "category": "Groceries", "amount": 2150},
    {"date": "2026-02-25", "merchant": "Uber", "category": "Transport", "amount": 320},
    {"date": "2026-02-24", "merchant": "Netflix", "category": "Entertainment", "amount": 649},
    {"date": "2026-02-23", "merchant": "Myntra", "category": "Shopping", "amount": 3200},
    {"date": "2026-02-22", "merchant": "Apollo Pharmacy", "category": "Health", "amount": 890},
    {"date": "2026-02-20", "merchant": "Airtel", "category": "Bills & Utilities", "amount": 799},
    {"date": "2026-02-18", "merchant": "Amazon", "category": "Shopping", "amount": 6550},
    {"date": "2026-02-15", "merchant": "BigBasket", "category": "Groceries", "amount": 4320},
    {"date": "2026-02-12", "merchant": "IRCTC", "category": "Transport", "amount": 1450},
    {"date": "2026-02-10", "merchant": "Swiggy", "category": "Food & Dining", "amount": 760},
    {"date": "2026-02-05", "merchant": "Electricity Board", "category": "Bills & Utilities", "amount": 1640},
]


def category_breakdown():
    totals = {}
    for t in transactions:
        totals[t["category"]] = totals.get(t["category"], 0) + t["amount"]
    return dict(sorted(totals.items(), key=lambda kv: kv[1], reverse=True))


# ---- Goals ----
goals = [
    {
        "id": "g1",
        "name": "Retirement Corpus",
        "type": "Retirement",
        "target": 25000000,
        "saved": 4850000,
        "target_year": 2054,
        "monthly_sip": 25000,
    },
    {
        "id": "g2",
        "name": "Dream Home Down Payment",
        "type": "Home",
        "target": 3000000,
        "saved": 950000,
        "target_year": 2029,
        "monthly_sip": 18000,
    },
    {
        "id": "g3",
        "name": "Child's Education",
        "type": "Education",
        "target": 5000000,
        "saved": 620000,
        "target_year": 2038,
        "monthly_sip": 12000,
    },
]

# ---- Risk profiles ----
risk_allocations = {
    "Conservative": {
        "equity": 25,
        "debt": 60,
        "gold": 15,
        "description": "Capital protection first. Mostly debt & gold with a small equity sleeve for inflation-beating growth.",
    },
    "Moderate": {
        "equity": 55,
        "debt": 35,
        "gold": 10,
        "description": "Balanced growth. Diversified equity + debt mix aiming for steady long-term compounding.",
    },
    "Aggressive": {
        "equity": 80,
        "debt": 12,
        "gold": 8,
        "description": "Growth-focused. Heavily tilted to equity to maximize long-term wealth creation.",
    },
}

suggestions_by_risk = {
    "Conservative": [
        {"type": "FD", "name": "IDBI Max FD", "detail": "7.1% p.a., 3-year lock-in", "expected_return": "7.1% p.a."},
        {"type": "SIP", "name": "IDBI Conservative Hybrid SIP", "detail": "₹5,000/mo, debt-heavy", "expected_return": "8% p.a."},
        {"type": "Mutual Fund", "name": "IDBI Liquid Fund", "detail": "Low volatility, high liquidity", "expected_return": "6.5% p.a."},
    ],
    "Moderate": [
        {"type": "SIP", "name": "IDBI Flexicap Fund SIP", "detail": "₹10,000/mo, diversified equity", "expected_return": "12% p.a."},
        {"type": "Mutual Fund", "name": "IDBI Hybrid Equity Fund", "detail": "65% equity / 35% debt", "expected_return": "11% p.a."},
        {"type": "FD", "name": "IDBI Year FD", "detail": "6.8% p.a., 1-year lock-in", "expected_return": "6.8% p.a."},
    ],
    "Aggressive": [
        {"type": "SIP", "name": "IDBI Smallcap Momentum SIP", "detail": "₹15,000/mo, high growth", "expected_return": "16% p.a."},
        {"type": "Mutual Fund", "name": "IDBI Midcap Opportunities Fund", "detail": "Growth-focused equity", "expected_return": "15% p.a."},
        {"type": "Mutual Fund", "name": "IDBI Global Equity Fund", "detail": "International diversification", "expected_return": "13% p.a."},
    ],
}

# ---- Notifications ----
notifications = [
    {"title": "Unusual spending detected", "body": "Your Shopping spend is 38% higher than last month's average.", "time": "2h ago", "type": "alert"},
    {"title": "SIP opportunity", "body": "Bumping your retirement SIP by ₹5,000 gets you there 3 years sooner.", "time": "5h ago", "type": "tip"},
    {"title": "Goal milestone reached", "body": "You're 19% funded toward your Dream Home goal. Keep going!", "time": "1d ago", "type": "goal"},
    {"title": "Bill due soon", "body": "Airtel postpaid bill of ₹799 is due in 3 days.", "time": "1d ago", "type": "bill"},
    {"title": "Portfolio rebalance suggested", "body": "Your equity allocation has drifted 8% above target. Consider rebalancing.", "time": "3d ago", "type": "tip"},
]
