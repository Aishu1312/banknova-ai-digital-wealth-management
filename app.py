import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from data import (
    category_breakdown,
    goals,
    notifications,
    portfolio_holdings,
    risk_allocations,
    suggestions_by_risk,
    total_wealth,
    transactions,
)
from chat_engine import get_response, suggestion_chips

st.set_page_config(
    page_title="BankNova AI — Wealth OS",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="expanded",
)

if "risk" not in st.session_state:
    st.session_state.risk = "Moderate"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "text": "Hi, I'm NOVA — your AI wealth advisor. I've looked at your spending, goals and portfolio. Ask me anything."}
    ]
if "quiz_step" not in st.session_state:
    st.session_state.quiz_step = 0
if "quiz_score" not in st.session_state:
    st.session_state.quiz_score = 0

st.markdown(
    """
    <style>
    .stApp { background-color: #0a0a0a; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.title("💰 BankNova AI")
st.sidebar.caption("NOVA — Wealth OS · IDBI Innovate 2026")
page = st.sidebar.radio(
    "Navigate",
    ["🏠 Home", "💬 NOVA Chat", "📊 Spend Analysis", "📈 Invest", "🎯 Goals", "🔔 Alerts"],
)
st.sidebar.divider()
st.sidebar.caption(f"Risk profile: **{st.session_state.risk}**")

# ---------------- HOME ----------------
if page == "🏠 Home":
    st.header("Good evening, Aishwarya 👋")
    st.caption("Here's your wealth snapshot")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.metric("Total Portfolio", f"₹{total_wealth:,}", "+12.4% YoY")
    with col2:
        st.metric("This Month's Spend", f"₹{sum(t['amount'] for t in transactions):,}")

    fig = go.Figure(go.Scatter(
        x=["Sep", "Oct", "Nov", "Dec", "Jan", "Feb"],
        y=[19.8, 20.5, 21.1, 22.0, 22.9, 24.85],
        mode="lines",
        line=dict(color="#f5b03e", width=3),
        fill="tozeroy",
        fillcolor="rgba(245,176,62,0.15)",
    ))
    fig.update_layout(
        height=220,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#f5f5f5",
        yaxis_title="₹ Lakhs",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Holdings breakdown")
    for h in portfolio_holdings:
        c1, c2, c3 = st.columns([3, 2, 1])
        c1.write(f"**{h['name']}**")
        c2.write(f"₹{h['value']:,}")
        color = "green" if h["change"] >= 0 else "red"
        c3.markdown(f":{color}[{'+' if h['change'] >= 0 else ''}{h['change']}%]")

    st.subheader("AI insight")
    st.info("You're on track for retirement at 58. Bumping SIP by ₹5,000 lands you there at 55.")

# ---------------- CHAT ----------------
elif page == "💬 NOVA Chat":
    st.header("💬 NOVA — AI Wealth Advisor")
    st.caption("Online · Understands your spending, goals & portfolio")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["text"])

    st.write("")
    chip_cols = st.columns(len(suggestion_chips))
    for i, chip in enumerate(suggestion_chips):
        if chip_cols[i].button(chip, key=f"chip_{i}", use_container_width=True):
            st.session_state.chat_history.append({"role": "user", "text": chip})
            st.session_state.chat_history.append(
                {"role": "assistant", "text": get_response(chip, st.session_state.risk)}
            )
            st.rerun()

    user_input = st.chat_input("Ask NOVA about your money...")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "text": user_input})
        st.session_state.chat_history.append(
            {"role": "assistant", "text": get_response(user_input, st.session_state.risk)}
        )
        st.rerun()

# ---------------- SPEND ----------------
elif page == "📊 Spend Analysis":
    st.header("📊 Spending Analysis")
    breakdown = category_breakdown()
    total = sum(breakdown.values())
    st.caption(f"Total this month: ₹{total:,}")

    fig = go.Figure(go.Bar(
        x=list(breakdown.keys()),
        y=list(breakdown.values()),
        marker_color="#f5b03e",
    ))
    fig.update_layout(
        height=280,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#f5f5f5",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("By category")
    for cat, amt in breakdown.items():
        pct = amt / total
        st.write(f"**{cat}** — ₹{amt:,}")
        st.progress(pct)

    st.subheader("Recent transactions")
    df = pd.DataFrame(transactions).sort_values("date", ascending=False)
    df["amount"] = df["amount"].apply(lambda a: f"-₹{a:,}")
    st.dataframe(df.rename(columns={
        "date": "Date", "merchant": "Merchant", "category": "Category", "amount": "Amount",
    }), hide_index=True, use_container_width=True)

# ---------------- INVEST ----------------
elif page == "📈 Invest":
    st.header("📈 Investment Recommendations")

    quiz_questions = [
        {
            "q": "How would you react to a 20% drop in your portfolio's value?",
            "options": [("Sell everything immediately", 0), ("Wait and watch", 1), ("Buy more at the dip", 2)],
        },
        {
            "q": "What's your primary investment goal?",
            "options": [("Preserve capital", 0), ("Steady growth", 1), ("Maximize long-term returns", 2)],
        },
        {
            "q": "What's your investment horizon?",
            "options": [("Less than 3 years", 0), ("3–7 years", 1), ("7+ years", 2)],
        },
    ]

    with st.expander("🧠 Retake risk assessment quiz", expanded=(st.session_state.quiz_step < len(quiz_questions))):
        if st.session_state.quiz_step < len(quiz_questions):
            q = quiz_questions[st.session_state.quiz_step]
            st.write(f"**Q{st.session_state.quiz_step + 1}. {q['q']}**")
            for label, score in q["options"]:
                if st.button(label, key=f"quiz_{st.session_state.quiz_step}_{label}"):
                    st.session_state.quiz_score += score
                    st.session_state.quiz_step += 1
                    if st.session_state.quiz_step == len(quiz_questions):
                        total_score = st.session_state.quiz_score
                        if total_score <= 2:
                            st.session_state.risk = "Conservative"
                        elif total_score <= 4:
                            st.session_state.risk = "Moderate"
                        else:
                            st.session_state.risk = "Aggressive"
                    st.rerun()
        else:
            st.success(f"Your risk profile: **{st.session_state.risk}**")
            if st.button("Retake quiz"):
                st.session_state.quiz_step = 0
                st.session_state.quiz_score = 0
                st.rerun()

    risk = st.session_state.risk
    alloc = risk_allocations[risk]
    st.subheader(f"Suggested allocation — {risk}")
    fig = go.Figure(go.Bar(
        x=[alloc["equity"], alloc["debt"], alloc["gold"]],
        y=["Allocation"],
        orientation="h",
        marker_color=["#f5b03e", "#60a5fa", "#4ade80"],
    ))
    fig.update_layout(
        barmode="stack", height=90, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#f5f5f5", showlegend=False, xaxis=dict(visible=False), yaxis=dict(visible=False),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.write(f"🟡 Equity {alloc['equity']}% · 🔵 Debt {alloc['debt']}% · 🟢 Gold {alloc['gold']}%")
    st.caption(alloc["description"])

    st.subheader("SIP / FD / Mutual Fund picks")
    for pick in suggestions_by_risk[risk]:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            c1.markdown(f"`{pick['type']}` **{pick['name']}**")
            c2.markdown(f":green[{pick['expected_return']}]")
            st.caption(pick["detail"])

# ---------------- GOALS ----------------
elif page == "🎯 Goals":
    st.header("🎯 Goal Planning")

    with st.expander("➕ Add a new goal"):
        name = st.text_input("Goal name")
        target = st.number_input("Target amount (₹)", min_value=0, step=10000)
        years = st.number_input("Years to reach it", min_value=1, step=1, value=5)
        if st.button("Create goal") and name and target:
            monthly_sip = round(target / (years * 12))
            goals.append({
                "id": f"custom-{len(goals)}",
                "name": name,
                "type": "Custom",
                "target": target,
                "saved": 0,
                "target_year": 2026 + years,
                "monthly_sip": monthly_sip,
            })
            st.success(f"Goal created! Suggested SIP: ₹{monthly_sip:,}/mo")

    for g in goals:
        pct = min(100, round(g["saved"] / g["target"] * 100))
        status = "🟢 On track" if pct >= 20 else "🔴 Needs boost"
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            c1.markdown(f"**{g['name']}** · {g['type']}")
            c2.markdown(status)
            st.progress(pct / 100)
            st.caption(
                f"₹{g['saved']:,} saved of ₹{g['target']:,} · Target {g['target_year']} · SIP ₹{g['monthly_sip']:,}/mo · {pct}%"
            )

# ---------------- ALERTS ----------------
elif page == "🔔 Alerts":
    st.header("🔔 Notifications")
    icon_map = {"alert": "🔴", "tip": "🟡", "goal": "🟢", "bill": "🔵"}
    for n in notifications:
        with st.container(border=True):
            c1, c2 = st.columns([5, 1])
            c1.markdown(f"{icon_map.get(n['type'], '⚪')} **{n['title']}**")
            c2.caption(n["time"])
            st.write(n["body"])
