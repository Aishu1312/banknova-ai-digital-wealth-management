"""Rule-based AI response engine — ported from lib/chatEngine.ts."""

from typing import List, Dict, Any, Union
from data import (
    category_breakdown,
    goals,
    portfolio_holdings,
    risk_allocations,
    suggestions_by_risk,
    total_wealth,
)


def get_response(user_text: str, risk: str) -> str:
    text = user_text.lower()

    if any(k in text for k in ["spend", "expense"]):
        breakdown = category_breakdown()
        if not breakdown:
            return "You haven't spent anything this month."
        
        top_cat, top_amount = next(iter(breakdown.items()))
        num_categories = len(breakdown)
        avg = sum(breakdown.values()) / num_categories if num_categories > 0 else 0
        
        if avg > 0:
            pct_vs_avg = round((top_amount / avg - 1) * 100)
            return (
                f"Your top spending category this month is **{top_cat}** at ₹{top_amount:,}, "
                f"which is {pct_vs_avg}% above your average category spend. "
                f"Want me to suggest ways to trim it?"
            )
        else:
            return f"Your top spending category this month is **{top_cat}** at ₹{top_amount:,}."

    if any(k in text for k in ["goal", "retire", "home", "education"]):
        if not goals:
            return "You haven't set any goals yet. Head to the Goals tab to create one."
        g = goals[0]
        target = g.get("target", 0)
        saved = g.get("saved", 0)
        
        pct = round(saved / target * 100) if target > 0 else 0
        boosted_sip = g.get("monthly_sip", 0) + 5000
        return (
            f"Your **{g['name']}** goal is {pct}% funded (₹{saved:,} of ₹{target:,}). "
            f"Bumping your SIP from ₹{g.get('monthly_sip', 0):,}/mo to ₹{boosted_sip:,}/mo would get you there sooner."
        )

    if any(k in text for k in ["invest", "sip", "risk"]):
        alloc = risk_allocations.get(risk)
        if not alloc:
            return f"I don't have allocation data for the {risk} profile."
        
        picks = suggestions_by_risk.get(risk, [])[:2]
        picks_text = " and ".join(f"**{p['name']}** ({p['expected_return']})" for p in picks)
        return (
            f"Based on your **{risk}** risk profile, I suggest an allocation of "
            f"{alloc['equity']}% equity / {alloc['debt']}% debt / {alloc['gold']}% gold. "
            f"{alloc['description']} Top picks for you right now: {picks_text}."
        )

    if any(k in text for k in ["portfolio", "net worth", "worth"]):
        if not portfolio_holdings:
            return f"Your total net worth across holdings is **₹{total_wealth:,}**."
        
        best = max(portfolio_holdings, key=lambda h: h["change"])
        return (
            f"Your total net worth across holdings is **₹{total_wealth:,}**. "
            f"Your best performer is **{best['name']}**, up {best['change']}% this year."
        )

    return (
        "I'm NOVA, your AI wealth advisor. Ask me about your spending, goals, investments, "
        "or portfolio — I can break down the numbers and suggest next steps."
    )


suggestion_chips: List[str] = [
    "How's my spending this month?",
    "What should I invest in?",
    "How's my retirement goal doing?",
    "Show me my portfolio",
]
