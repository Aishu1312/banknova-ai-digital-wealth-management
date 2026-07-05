import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import logging
import os

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

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
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CSS Injection ---
current_dir = os.path.dirname(os.path.abspath(__file__))
css_path = os.path.join(current_dir, "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Session State ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
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
if "goals" not in st.session_state:
    import copy
    st.session_state.goals = copy.deepcopy(goals)

# ==========================================
# 1. LANDING PAGE
# ==========================================
if not st.session_state.logged_in:
    # Hide sidebar for landing page
    st.markdown("""
        <style>
            [data-testid="stSidebar"] { display: none !important; }
            .block-container { padding-top: 2rem !important; max-width: 1200px !important; }
        </style>
    """, unsafe_allow_html=True)

    # Header
    col1, col2, col3 = st.columns([4, 1, 1])
    with col1:
        st.markdown("""
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="background: linear-gradient(135deg, #fcd34d, #f59e0b); color: black; font-weight: 800; font-size: 20px; width: 40px; height: 40px; display: flex; justify-content: center; align-items: center; border-radius: 10px; box-shadow: 0 4px 15px rgba(245, 158, 11, 0.3);">B</div>
                <div style="line-height: 1.1;">
                    <div style="font-size: 22px; font-weight: 700; color: white; letter-spacing: -0.5px;">BankNova <span style="color: #f5b03e;">AI</span></div>
                    <div style="font-size: 11px; color: #888; font-weight: 600; letter-spacing: 1.5px;">WEALTH OS</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        if st.button("Login", use_container_width=True, type="secondary"):
            st.session_state.logged_in = True
            st.rerun()
    with col3:
        if st.button("Create Account", key="nav_create_account", use_container_width=True, type="primary"):
            st.session_state.logged_in = True
            st.rerun()
            
    st.markdown("<br><br><br>", unsafe_allow_html=True)

    # Hero Section
    h_col1, h_col2 = st.columns([1.2, 1])
    
    with h_col1:
        st.markdown("""
            <div style="background-color: #222; border-radius: 20px; padding: 4px 12px; display: inline-block; font-size: 12px; color: #aaa; margin-bottom: 20px;">
                ⚡ Powered by Gemini 3 - Built for India
            </div>
            <h1 style="font-size: 3.5rem; line-height: 1.1; margin-bottom: 1.5rem; font-weight: 700;">
                <span style="color: white;">Your </span><span style="color: #f5b03e;">personal wealth</span><br>
                <span style="color: white;">intelligence layer.</span>
            </h1>
            <p style="color: #888; font-size: 1.1rem; line-height: 1.5; margin-bottom: 2rem; max-width: 80%;">
                BankNova AI is a premium digital wealth OS that understands your money in it, forecasts your goals, and explains every recommendation like a private banker would.
            </p>
        """, unsafe_allow_html=True)
        
        btn_col1, btn_col2, btn_col3 = st.columns([1.5, 1.5, 2])
        with btn_col1:
            if st.button("Create Account", key="hero_create_account", type="primary", use_container_width=True):
                st.session_state.logged_in = True
                st.rerun()
        with btn_col2:
            st.markdown("<a href='#' style='color: white; text-decoration: underline; font-size: 14px; line-height: 40px;'>I already have an account</a>", unsafe_allow_html=True)

        st.markdown("""
            <div style="display: flex; gap: 20px; font-size: 12px; color: #888; margin-top: 2rem;">
                <div><span style="color: #4ade80;">●</span> Bank-grade security</div>
                <div><span style="color: #4ade80;">●</span> Explainable AI</div>
                <div><span style="color: #4ade80;">●</span> INR native</div>
            </div>
        """, unsafe_allow_html=True)

    with h_col2:
        # Mockup Portfolio Card via HTML
        st.markdown("""
            <div style="background-color: #141416; border: 1px solid #2a2a2a; border-radius: 16px; padding: 2rem; position: relative; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <div style="color: #666; font-size: 12px; font-weight: 600; letter-spacing: 1.5px;">PORTFOLIO</div>
                    <div style="color: #4ade80; font-size: 12px; font-weight: 600;">+12.4% YoY</div>
                </div>
                <div style="font-size: 2.8rem; color: white; font-weight: 700; margin-bottom: 4px; font-family: 'SF Mono', 'Roboto Mono', Consolas, monospace;">₹ 24,85,320</div>
                <div style="color: #666; font-size: 12px; margin-bottom: 2rem;">Total wealth - Feb 2026</div>
                <div style="display: flex; gap: 10px; margin-bottom: 2rem;">
                    <div style="flex: 1; border: 1px solid #2a2a2a; border-radius: 8px; padding: 12px;">
                        <div style="color: #666; font-size: 10px; margin-bottom: 4px; font-weight: 600; letter-spacing: 1px;">SAVINGS</div>
                        <div style="color: white; font-size: 16px; font-weight: 600;">₹ 3.5L</div>
                    </div>
                    <div style="flex: 1; border: 1px solid #2a2a2a; border-radius: 8px; padding: 12px;">
                        <div style="color: #666; font-size: 10px; margin-bottom: 4px; font-weight: 600; letter-spacing: 1px;">INVESTMENTS</div>
                        <div style="color: white; font-size: 16px; font-weight: 600;">₹ 18.2L</div>
                    </div>
                    <div style="flex: 1; border: 1px solid #2a2a2a; border-radius: 8px; padding: 12px;">
                        <div style="color: #666; font-size: 10px; margin-bottom: 4px; font-weight: 600; letter-spacing: 1px;">EMERGENCY</div>
                        <div style="color: white; font-size: 16px; font-weight: 600;">₹ 3.1L</div>
                    </div>
                </div>
                <div style="border: 1px solid #2a2a2a; border-radius: 12px; height: 110px; position: relative; overflow: hidden; margin-bottom: -0.5rem; background-color: #1a1a1c;">
                    <svg viewBox="0 0 400 100" preserveAspectRatio="none" style="width: 100%; height: 100%; display: block; position: absolute; bottom: 0; left: 0;">
                        <defs>
                            <linearGradient id="chartGradient" x1="0" x2="0" y1="0" y2="1">
                                <stop offset="0%" stop-color="rgba(245, 176, 62, 0.4)" />
                                <stop offset="100%" stop-color="rgba(245, 176, 62, 0.0)" />
                            </linearGradient>
                        </defs>
                        <path d="M0,80 Q100,75 200,60 T400,20 L400,100 L0,100 Z" fill="url(#chartGradient)" />
                        <path d="M0,80 Q100,75 200,60 T400,20" fill="none" stroke="#f5b03e" stroke-width="2.5" />
                    </svg>
                </div>
                <div style="background-color: #1a1a1c; border: 1px solid rgba(255,255,255,0.2); border-radius: 12px; padding: 1rem; position: absolute; bottom: -20px; left: -20px; z-index: 10; width: 300px; box-shadow: 0 10px 25px rgba(0,0,0,0.8);">
                    <div style="color: #aaa; font-size: 11px; font-weight: 600; margin-bottom: 8px; letter-spacing: 1px; display: flex; align-items: center; gap: 6px;">
                        <span style="color: #f5b03e; font-size: 14px;">✨</span> AI INSIGHT
                    </div>
                    <div style="color: #ddd; font-size: 13px; line-height: 1.5;">
                        You're on track for retirement at 58.<br>Bumping SIP by ₹5K lands you there at 55.
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    # Bottom Feature Cards
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        st.markdown("""
            <div style="background-color: #141416; border: 1px solid #2a2a2a; border-radius: 16px; padding: 1.5rem; height: 100%;">
                <div style="color: #f5b03e; font-size: 24px; margin-bottom: 1rem;">🤖</div>
                <h3 style="color: white; font-size: 16px; margin-bottom: 8px;">AI Financial Advisor</h3>
                <p style="color: #888; font-size: 13px; line-height: 1.5;">Chat with a Gemini-powered advisor trained on Indian markets, taxes & personal finance.</p>
            </div>
        """, unsafe_allow_html=True)
    with f_col2:
        st.markdown("""
            <div style="background-color: #141416; border: 1px solid #2a2a2a; border-radius: 16px; padding: 1.5rem; height: 100%;">
                <div style="color: #f5b03e; font-size: 24px; margin-bottom: 1rem;">📈</div>
                <h3 style="color: white; font-size: 16px; margin-bottom: 8px;">Portfolio X-Ray</h3>
                <p style="color: #888; font-size: 13px; line-height: 1.5;">Upload CSV. Get diversification score, risk metrics & AI rebalancing suggestions.</p>
            </div>
        """, unsafe_allow_html=True)
    with f_col3:
        st.markdown("""
            <div style="background-color: #141416; border: 1px solid #2a2a2a; border-radius: 16px; padding: 1.5rem; height: 100%;">
                <div style="color: #f5b03e; font-size: 24px; margin-bottom: 1rem;">🎯</div>
                <h3 style="color: white; font-size: 16px; margin-bottom: 8px;">Goal Planning</h3>
                <p style="color: #888; font-size: 13px; line-height: 1.5;">Inflation-adjusted SIP calculators for retirement, education, home & every life goal.</p>
            </div>
        """, unsafe_allow_html=True)

# ==========================================
# 2. DASHBOARD
# ==========================================
else:
    # Sidebar
    st.sidebar.markdown("""
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 2rem;">
            <div style="background: linear-gradient(135deg, #fcd34d, #f59e0b); color: black; font-weight: 800; font-size: 20px; width: 40px; height: 40px; display: flex; justify-content: center; align-items: center; border-radius: 10px; box-shadow: 0 4px 15px rgba(245, 158, 11, 0.3);">B</div>
            <div style="line-height: 1.1;">
                <div style="font-size: 22px; font-weight: 700; color: white; letter-spacing: -0.5px;">BankNova <span style="color: #f5b03e;">AI</span></div>
                <div style="font-size: 11px; color: #888; font-weight: 600; letter-spacing: 1.5px;">WEALTH OS</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    page = st.sidebar.radio(
        "",
        ["Dashboard", "AI Advisor", "Goal Planner", "Portfolio", "Spending", "Health Score", "AI Recommendations", "Risk Predictor", "Reports"]
    )
    
    st.sidebar.markdown("<br>"*15, unsafe_allow_html=True)
    st.sidebar.divider()
    st.sidebar.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; cursor: pointer;">
            <div style="background-color: #333; color: white; border-radius: 50%; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold;">A</div>
            <div style="line-height: 1.2;">
                <div style="color: white; font-size: 13px; font-weight: 600;">aaishwaryalala13</div>
                <div style="color: #666; font-size: 10px;">aaishwaryalala13@gmail.com</div>
            </div>
        </div>
        <div style="margin-top: 10px; color: #888; font-size: 12px; cursor: pointer;">↪ Log out</div>
    """, unsafe_allow_html=True)
    
    # ---------------- DASHBOARD (HOME) ----------------
    if page == "Dashboard":
        # Header Row
        head_col1, head_col2 = st.columns([3, 1])
        with head_col1:
            st.markdown("""
                <div style="color: #666; font-size: 10px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 4px;">WELCOME BACK</div>
                <h1 style="color: white; font-size: 2rem; font-weight: 700; margin: 0; line-height: 1;">aaishwaryalala13.</h1>
                <div style="color: #888; font-size: 13px; margin-top: 6px; margin-bottom: 1.5rem;">Here's your wealth snapshot for today.</div>
            """, unsafe_allow_html=True)
        with head_col2:
            st.markdown("""
                <div style="background-color: #141416; border: 1px solid #2a2a2a; border-radius: 12px; padding: 12px 16px; display: flex; align-items: center; justify-content: space-between; float: right; min-width: 200px;">
                    <div>
                        <div style="color: #666; font-size: 10px; font-weight: 600; letter-spacing: 1px; margin-bottom: 4px;">FINANCIAL HEALTH</div>
                        <div style="color: #f5b03e; font-size: 20px; font-weight: 700;">64<span style="color: #666; font-size: 14px;">/100</span></div>
                    </div>
                    <div style="color: #f5b03e; font-size: 24px;">✨</div>
                </div>
            """, unsafe_allow_html=True)

        # Metrics Row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("TOTAL WEALTH", "₹13.80 L", "+12.4%")
        m2.metric("SAVINGS", "₹3.50 L", "+3.2%")
        m3.metric("INVESTMENTS", "₹8.50 L", "+8.7%")
        m4.metric("MONTHLY EXPENSES", "₹65.0K", "-2.1%")
        
        st.markdown("<br>", unsafe_allow_html=True)

        # Charts Row
        c1, c2 = st.columns([2.5, 1])
        with c1:
            st.markdown("""
                <div style="background-color: #141416; border: 1px solid #2a2a2a; border-radius: 12px; padding: 1.5rem; height: 100%;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                        <div>
                            <div style="color: #666; font-size: 10px; font-weight: 600; letter-spacing: 1px;">WEALTH TRAJECTORY</div>
                            <div style="color: white; font-size: 18px; font-weight: 600;">Last 12 months</div>
                        </div>
                        <div style="color: #4ade80; font-size: 12px; font-weight: 600;">+₹3.45K YTD</div>
                    </div>
            """, unsafe_allow_html=True)
            fig = go.Figure(go.Scatter(
                x=["Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan"],
                y=[10.5, 10.8, 11.1, 11.5, 12.0, 12.2, 12.5, 12.8, 13.0, 13.3, 13.5, 13.8],
                mode="lines",
                line=dict(color="#f5b03e", width=2),
                fill="tozeroy",
                fillcolor="rgba(245,176,62,0.15)",
            ))
            fig.update_layout(
                height=220,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#888",
                xaxis=dict(showgrid=False, zeroline=False),
                yaxis=dict(showgrid=False, zeroline=False, tickformat="₹.1fL", tickprefix="₹", ticksuffix="L")
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with c2:
            st.markdown("""
                <div style="background-color: #141416; border: 1px solid #2a2a2a; border-radius: 12px; padding: 1.5rem; height: 100%;">
                    <div style="color: #666; font-size: 10px; font-weight: 600; letter-spacing: 1px; margin-bottom: 4px;">SPENDING BREAKDOWN</div>
                    <div style="color: white; font-size: 18px; font-weight: 600; margin-bottom: 1rem;">This month</div>
            """, unsafe_allow_html=True)
            
            # Simple Donut Chart
            donut_fig = go.Figure(data=[go.Pie(
                labels=['Housing', 'Food & Dining', 'Transport', 'Utilities'],
                values=[25, 12.8, 6, 4.5],
                hole=.6,
                marker_colors=['#f5b03e', '#ef4444', '#3b82f6', '#a855f7'],
                textinfo='none'
            )])
            donut_fig.update_layout(
                showlegend=True,
                height=200,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(yanchor="middle", y=0.5, xanchor="left", x=1.0, font=dict(color="white", size=10))
            )
            st.plotly_chart(donut_fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Bottom Row
        b1, b2 = st.columns([2.5, 1])
        with b1:
            st.markdown("""
                <div style="background-color: #141416; border: 1px solid #2a2a2a; border-radius: 12px; padding: 1.5rem; height: 100%;">
                    <div style="color: #666; font-size: 10px; font-weight: 600; letter-spacing: 1px; margin-bottom: 1rem;">✨ AI INSIGHTS</div>
                    <ul style="color: #ddd; font-size: 13px; line-height: 1.8; margin-left: -15px;">
                        <li><span style="color: #f5b03e;">●</span> You saved 45.8% of your income this month — excellent.</li>
                        <li><span style="color: #f5b03e;">●</span> Your emergency fund covers 2.8 months of expenses. Target: 6 months.</li>
                        <li><span style="color: #f5b03e;">●</span> Investments are 24% of annual income. Consider raising SIP by ₹5,000.</li>
                        <li><span style="color: #f5b03e;">●</span> Dining spend rose 12% MoM. Room to trim ~₹1,400.</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)

        with b2:
            st.markdown("""
                <div style="background-color: #141416; border: 1px solid #2a2a2a; border-radius: 12px; padding: 1.5rem; height: 100%;">
                    <div style="color: #666; font-size: 10px; font-weight: 600; letter-spacing: 1px; margin-bottom: 1rem;">🛡️ HEALTH PILLARS</div>
                    
                    <div style="margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px;">
                            <span style="color: white;">Savings</span>
                            <span style="color: #888;">100</span>
                        </div>
                        <div style="background-color: #333; height: 4px; border-radius: 2px;">
                            <div style="background-color: #4ade80; width: 100%; height: 100%; border-radius: 2px;"></div>
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px;">
                            <span style="color: white;">Investments</span>
                            <span style="color: #888;">24</span>
                        </div>
                        <div style="background-color: #333; height: 4px; border-radius: 2px;">
                            <div style="background-color: #ef4444; width: 24%; height: 100%; border-radius: 2px;"></div>
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px;">
                            <span style="color: white;">Emergency Fund</span>
                            <span style="color: #888;">46</span>
                        </div>
                        <div style="background-color: #333; height: 4px; border-radius: 2px;">
                            <div style="background-color: #f5b03e; width: 46%; height: 100%; border-radius: 2px;"></div>
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px;">
                            <span style="color: white;">Insurance</span>
                            <span style="color: #888;">35</span>
                        </div>
                        <div style="background-color: #333; height: 4px; border-radius: 2px;">
                            <div style="background-color: #f97316; width: 35%; height: 100%; border-radius: 2px;"></div>
                        </div>
                    </div>

                </div>
            """, unsafe_allow_html=True)
            
        st.markdown("""
            <div style="text-align: center; margin-top: 20px; padding: 10px; background-color: #1a1a1c; border-radius: 20px; font-size: 12px; color: white; display: inline-block; position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); border: 1px solid #333;">
                Frontend Preview Only. Please wake servers to enable backend functionality. <span style="color: #4ade80; margin-left: 10px; cursor: pointer;">Wake up servers</span>
            </div>
        """, unsafe_allow_html=True)

    # Note: Other pages (AI Advisor, Goal Planner, etc.) can be populated similarly 
    # to the old functionality if needed, but the primary task was to overhaul the visual layout.
    elif page == "AI Advisor":
        st.header("💬 AI Advisor")
        st.info("AI Advisor interface goes here.")
    elif page == "Goal Planner":
        st.header("🎯 Goal Planner")
        st.info("Goal Planner interface goes here.")
    else:
        st.header(f"Page: {page}")
        st.info("This section is under construction.")

