"""Rule-based AI response engine — ported from lib/chatEngine.ts."""

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
        top_cat, top_amount = next(iter(breakdown.items()))
        avg = sum(breakdown.values()) / len(breakdown)
        pct_vs_avg = round((top_amount / avg - 1) * 100)
        return (
            f"Your top spending category this month is **{top_cat}** at ₹{top_amount:,}, "
            f"which is {pct_vs_avg}% above your average category spend. "
            f"Want me to suggest ways to trim it?"
        )

    if any(k in text for k in ["goal", "retire", "home", "education"]):
        g = goals[0]
        pct = round(g["saved"] / g["target"] * 100)
        boosted_sip = g["monthly_sip"] + 5000
        return (
            f"Your **{g['name']}** goal is {pct}% funded (₹{g['saved']:,} of ₹{g['target']:,}). "
            f"Bumping your SIP from ₹{g['monthly_sip']:,}/mo to ₹{boosted_sip:,}/mo would get you there sooner."
        )

    if any(k in text for k in ["invest", "sip", "risk"]):
        alloc = risk_allocations[risk]
        picks = suggestions_by_risk[risk][:2]
        picks_text = " and ".join(f"**{p['name']}** ({p['expected_return']})" for p in picks)
        return (
            f"Based on your **{risk}** risk profile, I suggest an allocation of "
            f"{alloc['equity']}% equity / {alloc['debt']}% debt / {alloc['gold']}% gold. "
            f"{alloc['description']} Top picks for you right now: {picks_text}."
        )

    if any(k in text for k in ["portfolio", "net worth", "worth"]):
        best = max(portfolio_holdings, key=lambda h: h["change"])
        return (
            f"Your total net worth across holdings is **₹{total_wealth:,}**. "
            f"Your best performer is **{best['name']}**, up {best['change']}% this year."
        )

    return (
        "I'm NOVA, your AI wealth advisor. Ask me about your spending, goals, investments, "
        "or portfolio — I can break down the numbers and suggest next steps."
    )


suggestion_chips = [
    "How's my spending this month?",
    "What should I invest in?",
    "How's my retirement goal doing?",
    "Show me my portfolio",
]
