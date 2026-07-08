"""Rule-based AI response engine — ported from lib/chatEngine.ts."""
from typing import List, Dict, Any, Union
from data import (
    category_breakdown,
    get_goals,
    get_portfolio_holdings,
    get_risk_allocations,
    get_suggestions_by_risk,
    get_total_wealth,
)


# ---------------------------------------------------------------------------
# FIX: data.py functions now REQUIRE a user_id (per-user data scoping).
# get_response() previously called them with zero arguments, which would
# now raise a TypeError on every single message. Added a required user_id
# parameter and threaded it through to every data.py call below.
# ---------------------------------------------------------------------------
def get_response(user_text: str, risk: str, user_id: int) -> str:
    text = user_text.lower()

    if any(k in text for k in ["spend", "expense"]):
        breakdown = category_breakdown(user_id)
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
        goals = get_goals(user_id)
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
        risk_allocs = get_risk_allocations()
        alloc = risk_allocs.get(risk)
        if not alloc:
            return f"I don't have allocation data for the {risk} profile."

        suggs = get_suggestions_by_risk()
        picks = suggs.get(risk, [])[:2]
        picks_text = " and ".join(f"**{p['name']}** ({p['expected_return']})" for p in picks)

        return (
            f"Based on your **{risk}** risk profile, I suggest an allocation of "
            f"{alloc['equity']}% equity / {alloc['debt']}% debt / {alloc['gold']}% gold. "
            f"{alloc['description']} Top picks for you right now: {picks_text}."
        )

    if any(k in text for k in ["portfolio", "net worth", "worth"]):
        holdings = get_portfolio_holdings(user_id)
        wealth = get_total_wealth(user_id)

        if not holdings:
            return f"Your total net worth across holdings is **₹{wealth:,}**."

        best = max(holdings, key=lambda h: h["change"])
        return (
            f"Your total net worth across holdings is **₹{wealth:,}**. "
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
