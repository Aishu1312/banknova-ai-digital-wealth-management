import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import logging
import os
import requests
import time
import subprocess

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")

def ensure_backend_running():
    if st.session_state.get("backend_checked"):
        return
        
    import sys
    import os
    import shutil
    import subprocess
    import time
    
    # Do not auto-start in explicitly configured Production environments
    if os.environ.get("ENVIRONMENT") == "production":
        st.session_state.backend_checked = True
        return
        
    if "127.0.0.1" not in API_BASE_URL and "localhost" not in API_BASE_URL:
        st.session_state.backend_checked = True
        return
    try:
        if requests.get(f"{API_BASE_URL}/health", timeout=1).status_code == 200:
            st.session_state.backend_checked = True
            return
    except:
        pass
        
    st.session_state.backend_checked = True
    
    st.toast("Starting local backend server... This may take 15 seconds.", icon="⏳")
    
    # Method 1: Try uv (if the user is using uv instead of standard pip)
    if shutil.which("uv"):
        process = subprocess.Popen(
            ["uv", "run", "--with-requirements", "requirements.txt", "uvicorn", "api:app", "--host", "127.0.0.1", "--port", "8000"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    # Method 2: Try standard python
    elif shutil.which("python"):
        subprocess.run(["python", "-m", "pip", "install", "-r", "requirements.txt"], capture_output=True)
        process = subprocess.Popen(
            ["python", "-m", "uvicorn", "api:app", "--host", "127.0.0.1", "--port", "8000"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    # Method 3: Fallback to sys.executable
    else:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], capture_output=True)
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "api:app", "--host", "127.0.0.1", "--port", "8000"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
    for _ in range(20):
        time.sleep(1)
        try:
            if requests.get(f"{API_BASE_URL}/health", timeout=1).status_code == 200:
                st.toast("Backend server online!", icon="✅")
                return True
        except:
            pass
            
    st.toast("Failed to start backend server. Please run 'uvicorn api:app' manually.", icon="❌")
    return False

# Ensure backend is running before rendering UI
ensure_backend_running()

# Auto-seed the database if it doesn't exist and we're using SQLite
if os.environ.get("DATABASE_URL", "sqlite").startswith("sqlite") and not os.path.exists("./banknova.db"):
    try:
        import seed_db
        seed_db.seed()
        logger.info("Auto-seeded SQLite database successfully.")
    except Exception as e:
        logger.error(f"Error auto-seeding database: {e}")

from data import (
    category_breakdown,
    get_goals,
    get_notifications,
    get_portfolio_holdings,
    get_risk_allocations,
    get_suggestions_by_risk,
    get_total_wealth,
    get_transactions,
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

if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = None

import auth_ui
import requests

# --- Handle OAuth / Email Callbacks ---
if "token" in st.query_params:
    st.session_state.access_token = st.query_params["token"]
    st.session_state.logged_in = True
    st.query_params.clear()

if "reset" in st.query_params:
    st.session_state.auth_mode = "reset"
    st.session_state.reset_token = st.query_params["reset"]
    st.query_params.clear()

if "verify" in st.query_params:
    try:
        session = auth_ui.get_api_session()
        res = session.post(f"{API_BASE_URL}/auth/verify-email?token={st.query_params['verify']}", timeout=5)
        if res.status_code == 200:
            st.toast("Email verified successfully! You can now log in.", icon="✅")
        else:
            st.toast("Verification failed or link expired.", icon="❌")
    except:
        pass
    st.query_params.clear()

if "error" in st.query_params:
    st.toast(f"Error: {st.query_params['error']}", icon="⚠️")
    st.query_params.clear()

# ==========================================
# 1. LANDING PAGE
# ==========================================
if not st.session_state.logged_in:
    if st.session_state.auth_mode:
        auth_ui.render()
        st.stop()

    # Set layout for landing page
    st.markdown("""
        <style>
            .block-container { max-width: 1200px !important; padding-top: 2rem !important; }
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
            st.session_state.auth_mode = "login"
            st.rerun()
    with col3:
        if st.button("Create Account", key="nav_create_account", use_container_width=True, type="primary"):
            st.session_state.auth_mode = "signup"
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
                st.session_state.auth_mode = "signup"
                st.rerun()
        with btn_col2:
            if st.button("I already have an account", key="hero_login", type="tertiary", use_container_width=True):
                st.session_state.auth_mode = "login"
                st.rerun()

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
    # -----------------------------------------------------------------
    # FIX: data.py functions (get_goals, get_portfolio_holdings, etc.)
    # now REQUIRE a user_id -- they used to run unfiltered and leak every
    # user's data to every session. app.py used to call get_goals() with
    # no arguments at all, which now raises a TypeError and crashes the
    # app on load. Resolve the logged-in user's id via /auth/me (using
    # the same authenticated session auth_ui already sets up for us) and
    # cache it in session_state, then use it for any user-scoped data.py
    # calls instead of calling those functions unscoped.
    # -----------------------------------------------------------------
    if "user_id" not in st.session_state:
        try:
            session = auth_ui.get_api_session()
            me_res = session.get(f"{API_BASE_URL}/auth/me", timeout=5)
            if me_res.status_code == 200:
                st.session_state.user_id = me_res.json()["id"]
            else:
                # Access token invalid/expired -- send back to login instead
                # of crashing on a missing user_id.
                st.session_state.logged_in = False
                st.session_state.access_token = None
                st.toast("Your session expired. Please log in again.", icon="⚠️")
                st.rerun()
        except Exception as e:
            logger.error(f"Failed to resolve current user: {e}")
            st.session_state.logged_in = False
            st.session_state.access_token = None
            st.toast("Could not verify your session. Please log in again.", icon="⚠️")
            st.rerun()

    if "goals" not in st.session_state:
        st.session_state.goals = get_goals(st.session_state.user_id)

    # Reset layout CSS that might have leaked from the Auth/Landing page
    st.markdown("""
        <style>
            .block-container { max-width: 95% !important; padding-top: 1rem !important; }
        </style>
    """, unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.markdown("""
        <style>
            /* Custom Sidebar Radio Tabs */
            [data-testid="stSidebar"] div[role="radiogroup"] > label {
                padding: 12px 16px !important;
                border-radius: 8px !important;
                margin-bottom: 4px !important;
                background-color: transparent !important;
                color: #888 !important;
                font-size: 14px !important;
                font-weight: 500 !important;
                cursor: pointer !important;
                transition: all 0.2s !important;
            }
            [data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
                background-color: rgba(255,255,255,0.05) !important;
                color: white !important;
            }
            [data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"] {
                background-color: #1a1a1c !important;
                color: white !important;
                border-left: 3px solid #f5b03e !important;
                border-top-left-radius: 0 !important;
                border-bottom-left-radius: 0 !important;
            }
            /* KPI Card Hover styling */
            .kpi-card {
                background-color: #141416;
                border: 1px solid #2a2a2a;
                border-radius: 12px;
                padding: 1.2rem;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            .kpi-card:hover {
                border-color: #f5b03e;
                transform: translateY(-2px);
                box-shadow: 0 8px 24px rgba(245,176,62,0.1);
            }
        </style>
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
        ["📊 Dashboard", "💬 AI Advisor ᴬᴵ", "🎯 Goal Planner", "💼 Portfolio", "💸 Spending", "❤️ Health Score", "✨ AI Recommendations ᴬᴵ", "⚠️ Risk Predictor", "📄 Reports"]
    )
    
    st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
    st.sidebar.divider()
    
    # Use real Streamlit buttons for logout
    st.sidebar.markdown("""
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="background-color: #333; color: white; border-radius: 50%; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold;">U</div>
            <div style="line-height: 1.2;">
                <div style="color: white; font-size: 13px; font-weight: 600;">My Account</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    if st.sidebar.button("↪ Log out", type="tertiary", use_container_width=True):
        try:
            session = auth_ui.get_api_session()
            session.post(f"{API_BASE_URL}/auth/logout", timeout=5)
        except:
            pass
        st.session_state.logged_in = False
        st.session_state.access_token = None
        st.rerun()
    
    # ---------------- DASHBOARD (HOME) ----------------
    if page == "📊 Dashboard":
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
        
        with m1:
            st.markdown("""
                <div class="kpi-card">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
                        <div style="color: #f5b03e; font-size: 16px;">💼</div>
                        <div style="color: #4ade80; font-size: 12px; font-weight: 600;">↗ +12.4%</div>
                    </div>
                    <div style="color: #666; font-size: 10px; font-weight: 600; letter-spacing: 1px; margin-bottom: 4px; text-transform: uppercase;">TOTAL WEALTH</div>
                    <div style="color: white; font-size: 24px; font-weight: 700;">₹13.80 L</div>
                </div>
            """, unsafe_allow_html=True)
            
        with m2:
            st.markdown("""
                <div class="kpi-card">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
                        <div style="color: #f5b03e; font-size: 16px;">🐷</div>
                        <div style="color: #4ade80; font-size: 12px; font-weight: 600;">↗ +3.2%</div>
                    </div>
                    <div style="color: #666; font-size: 10px; font-weight: 600; letter-spacing: 1px; margin-bottom: 4px; text-transform: uppercase;">SAVINGS</div>
                    <div style="color: white; font-size: 24px; font-weight: 700;">₹3.50 L</div>
                </div>
            """, unsafe_allow_html=True)
            
        with m3:
            st.markdown("""
                <div class="kpi-card">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
                        <div style="color: #f5b03e; font-size: 16px;">📈</div>
                        <div style="color: #4ade80; font-size: 12px; font-weight: 600;">↗ +8.7%</div>
                    </div>
                    <div style="color: #666; font-size: 10px; font-weight: 600; letter-spacing: 1px; margin-bottom: 4px; text-transform: uppercase;">INVESTMENTS</div>
                    <div style="color: white; font-size: 24px; font-weight: 700;">₹8.50 L</div>
                </div>
            """, unsafe_allow_html=True)
            
        with m4:
            st.markdown("""
                <div class="kpi-card">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
                        <div style="color: #f5b03e; font-size: 16px;">📉</div>
                        <div style="color: #ef4444; font-size: 12px; font-weight: 600;">↘ -2.1%</div>
                    </div>
                    <div style="color: #666; font-size: 10px; font-weight: 600; letter-spacing: 1px; margin-bottom: 4px; text-transform: uppercase;">MONTHLY EXPENSES</div>
                    <div style="color: white; font-size: 24px; font-weight: 700;">₹65.0K</div>
                </div>
            """, unsafe_allow_html=True)
        
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
                            <span style="color: #4ade80; font-weight: 600;">100</span>
                        </div>
                        <div style="background-color: #333; height: 4px; border-radius: 2px;">
                            <div style="background-color: #4ade80; width: 100%; height: 4px; border-radius: 2px;"></div>
                        </div>
                    </div>
                    <div style="margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px;">
                            <span style="color: white;">Investments</span>
                            <span style="color: #ef4444; font-weight: 600;">24</span>
                        </div>
                        <div style="background-color: #333; height: 4px; border-radius: 2px;">
                            <div style="background-color: #ef4444; width: 24%; height: 4px; border-radius: 2px;"></div>
                        </div>
                    </div>
                    <div style="margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px;">
                            <span style="color: white;">Emergency Fund</span>
                            <span style="color: #f5b03e; font-weight: 600;">46</span>
                        </div>
                        <div style="background-color: #333; height: 4px; border-radius: 2px;">
                            <div style="background-color: #f5b03e; width: 46%; height: 4px; border-radius: 2px;"></div>
                        </div>
                    </div>
                    <div style="margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px;">
                            <span style="color: white;">Insurance</span>
                            <span style="color: #ef4444; font-weight: 600;">35</span>
                        </div>
                        <div style="background-color: #333; height: 4px; border-radius: 2px;">
                            <div style="background-color: #ef4444; width: 35%; height: 4px; border-radius: 2px;"></div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown("""
            <div style="text-align: center; margin-top: 20px; padding: 10px; background-color: #1a1a1c; border-radius: 20px; font-size: 12px; color: white; display: inline-block; position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); border: 1px solid #333; z-index: 9999; box-shadow: 0 5px 20px rgba(0,0,0,0.5);">
                Frontend Preview Only. Please wake servers to enable backend functionality. <span style="color: #4ade80; margin-left: 10px; cursor: pointer; text-decoration: underline;" onclick="alert('Waking up BankNova AI backend servers... (Simulation)')">Wake up servers</span>
            </div>
        """, unsafe_allow_html=True)

    elif page == "💬 AI Advisor ᴬᴵ":
        st.markdown("""
            <div style="margin-bottom: 2rem;">
                <div style="color: #f5b03e; font-size: 10px; font-weight: 600; letter-spacing: 1.5px; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
                    <span style="font-size: 14px;">🤖</span> CONVERSATIONAL AI
                </div>
                <h1 style="color: white; font-size: 32px; font-weight: 700; margin: 0 0 8px 0; padding: 0;">AI Advisor</h1>
                <div style="color: #888; font-size: 14px;">Chat with your INR-native, explainable AI banker.</div>
            </div>
        """, unsafe_allow_html=True)
        
        components.html("""
            <style>
                body { margin: 0; padding: 0; font-family: sans-serif; background-color: #0e1117; }
                .suggestion-box {
                    border: 1px solid #333; padding: 12px; border-radius: 8px; margin-bottom: 10px; 
                    color: #ccc; font-size: 12px; cursor: pointer; transition: all 0.2s;
                }
                .suggestion-box:hover {
                    border-color: #f5b03e; color: white;
                }
                
                /* Custom Scrollbar for chat history */
                #chat-history::-webkit-scrollbar { width: 6px; }
                #chat-history::-webkit-scrollbar-track { background: transparent; }
                #chat-history::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }
            </style>
            
            <script>
                function sendMessage() {
                    var input = document.getElementById('chat-input-box');
                    var text = input.value.trim();
                    if (!text) return;
                    
                    var history = document.getElementById('chat-history');
                    
                    // Create User Message
                    var userMsgContainer = document.createElement('div');
                    userMsgContainer.style.display = 'flex';
                    userMsgContainer.style.justifyContent = 'flex-end';
                    userMsgContainer.style.marginBottom = '10px';
                    
                    var userMsg = document.createElement('div');
                    userMsg.style.backgroundColor = '#f5b03e';
                    userMsg.style.color = 'black';
                    userMsg.style.padding = '12px 16px';
                    userMsg.style.borderRadius = '12px';
                    userMsg.style.borderTopRightRadius = '4px';
                    userMsg.style.fontSize = '13px';
                    userMsg.style.display = 'inline-block';
                    userMsg.style.maxWidth = '80%';
                    userMsg.innerText = text;
                    
                    userMsgContainer.appendChild(userMsg);
                    history.appendChild(userMsgContainer);
                    
                    // Clear input
                    input.value = '';
                    
                    // Scroll to bottom
                    history.scrollTop = history.scrollHeight;
                    
                    // Create AI loading message
                    var aiMsgContainer = document.createElement('div');
                    aiMsgContainer.style.display = 'flex';
                    aiMsgContainer.style.justifyContent = 'flex-start';
                    aiMsgContainer.style.marginBottom = '10px';
                    
                    var aiMsg = document.createElement('div');
                    aiMsg.style.backgroundColor = '#1e1e1e';
                    aiMsg.style.border = '1px solid #333';
                    aiMsg.style.padding = '12px 16px';
                    aiMsg.style.borderRadius = '12px';
                    aiMsg.style.borderTopLeftRadius = '4px';
                    aiMsg.style.color = '#eee';
                    aiMsg.style.fontSize = '13px';
                    aiMsg.style.display = 'inline-block';
                    aiMsg.style.maxWidth = '80%';
                    aiMsg.style.lineHeight = '1.5';
                    aiMsg.innerHTML = '<span style="color:#f5b03e; font-weight:bold; margin-right:5px;">AI:</span> <i>Thinking...</i>';
                    
                    aiMsgContainer.appendChild(aiMsg);
                    history.appendChild(aiMsgContainer);
                    history.scrollTop = history.scrollHeight;
                    
                    // Fetch real AI response from public endpoint (No API key needed)
                    var sysPrompt = "You are BankNova AI, a smart, polite, and concise financial advisor for Indian users. Keep answers under 3 short paragraphs. User asks: ";
                    fetch('https://text.pollinations.ai/' + encodeURIComponent(sysPrompt + text))
                        .then(response => response.text())
                        .then(aiText => {
                            // Format markdown-like text to HTML
                            var formattedText = aiText
                                .replace(/\\*\\*(.*?)\\*\\*/g, '<b>$1</b>') // Bold
                                .replace(/\\n/g, '<br>'); // Newlines
                            
                            aiMsg.innerHTML = '<span style="color:#f5b03e; font-weight:bold; margin-right:5px;">AI:</span> ' + formattedText;
                            history.scrollTop = history.scrollHeight;
                        })
                        .catch(err => {
                            aiMsg.innerHTML = '<span style="color:#ef4444; font-weight:bold; margin-right:5px;">Error:</span> Failed to connect to AI brain.';
                        });
                }
            </script>
            
            <div style="display: flex; gap: 1.5rem; width: 100%;">
                <div style="flex: 2.5; background-color: #141416; border: 1px solid #2a2a2a; border-radius: 12px; height: 500px; display: flex; flex-direction: column; justify-content: space-between; padding: 1.5rem; box-sizing: border-box;">
                    
                    <div id="chat-history" style="flex: 1; overflow-y: auto; display: flex; flex-direction: column; margin-bottom: 15px; padding-right: 5px;">
                        <div style="display: flex; justify-content: flex-start; margin-bottom: 10px;">
                            <div style="background-color: #1e1e1e; border: 1px solid #333; padding: 12px 16px; border-radius: 12px; border-top-left-radius: 4px; color: #eee; font-size: 13px; display: inline-block; max-width: 80%;">
                                Namaste! I am your BankNova AI advisor. Ask me anything about your money in ₹.
                            </div>
                        </div>
                    </div>
                    
                    <div style="display: flex; gap: 10px; align-items: center; border: 1px solid #333; padding: 4px; border-radius: 8px; background-color: #0a0a0a; flex-shrink: 0;">
                        <input id="chat-input-box" onkeypress="if(event.key === 'Enter') sendMessage();" type="text" placeholder="Ask about SIPs, taxes, retirement..." style="flex: 1; background: transparent; border: none; color: white; padding: 8px 12px; outline: none; font-size: 13px;">
                        <button onclick="sendMessage()" style="background-color: #f5b03e; color: black; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: bold; display: flex; align-items: center; justify-content: center;">
                            ➤
                        </button>
                    </div>
                </div>
                
                <div style="flex: 1; background-color: #141416; border: 1px solid #2a2a2a; border-radius: 12px; height: 500px; padding: 1.5rem; box-sizing: border-box;">
                    <div style="color: #666; font-size: 10px; font-weight: 600; letter-spacing: 1px; margin-bottom: 1.5rem;">✨ SUGGESTIONS</div>
                    <div class="suggestion-box" onclick="document.getElementById('chat-input-box').value = 'How can I retire at 55?'; document.getElementById('chat-input-box').focus();">
                        How can I retire at 55?
                    </div>
                    <div class="suggestion-box" onclick="document.getElementById('chat-input-box').value = 'Is my portfolio too risky?'; document.getElementById('chat-input-box').focus();">
                        Is my portfolio too risky?
                    </div>
                    <div class="suggestion-box" onclick="document.getElementById('chat-input-box').value = 'How much term insurance do I need?'; document.getElementById('chat-input-box').focus();">
                        How much term insurance do I need?
                    </div>
                    <div class="suggestion-box" onclick="document.getElementById('chat-input-box').value = 'Best tax-saving instruments for me?'; document.getElementById('chat-input-box').focus();">
                        Best tax-saving instruments for me?
                    </div>
                </div>
            </div>
        """, height=520)
            
    elif page == "🎯 Goal Planner":
        st.markdown("""
            <div style="margin-bottom: 2rem;">
                <div style="color: #f5b03e; font-size: 10px; font-weight: 600; letter-spacing: 1.5px; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
                    <span style="font-size: 14px;">🧭</span> LIFE GOALS
                </div>
                <h1 style="color: white; font-size: 32px; font-weight: 700; margin: 0 0 8px 0; padding: 0;">Goal Planner</h1>
                <div style="color: #888; font-size: 14px;">Inflation-adjusted plans for every life milestone.</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Grid of Goals
        g1, g2 = st.columns(2)
        with g1:
            st.markdown("""
                <div style="background-color: #141416; border: 1px solid #2a2a2a; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; cursor: pointer; transition: 0.2s;" onmouseover="this.style.borderColor='#f5b03e'" onmouseout="this.style.borderColor='#2a2a2a'">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="color: #666; font-size: 10px; font-weight: 600; letter-spacing: 1px;">GOAL</span>
                        <span style="color: #666; font-size: 10px; font-weight: 600; letter-spacing: 1px;">IN</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 1.5rem;">
                        <span style="color: white; font-size: 16px; font-weight: 600;">Retirement</span>
                        <span style="color: white; font-size: 14px; font-weight: 500;">25 yrs</span>
                    </div>
                    <div style="margin-bottom: 1rem;">
                        <span style="color: white; font-size: 24px; font-weight: 600;">Rs 42.00L</span>
                        <span style="color: #666; font-size: 12px; margin-left: 6px;">of Rs 3.00Cr</span>
                    </div>
                    <div style="background-color: #222; height: 4px; border-radius: 2px; margin-bottom: 8px;">
                        <div style="background-color: #f5b03e; width: 14%; height: 100%; border-radius: 2px;"></div>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #666; font-size: 11px;">14% complete</span>
                        <span style="color: #888; font-size: 11px;">Suggested SIP: <span style="color: white; font-weight: 600;">Rs 1,00,000</span></span>
                    </div>
                </div>
                
                <div style="background-color: #141416; border: 1px solid #2a2a2a; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; cursor: pointer; transition: 0.2s;" onmouseover="this.style.borderColor='#3b82f6'" onmouseout="this.style.borderColor='#2a2a2a'">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="color: #666; font-size: 10px; font-weight: 600; letter-spacing: 1px;">GOAL</span>
                        <span style="color: #666; font-size: 10px; font-weight: 600; letter-spacing: 1px;">IN</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 1.5rem;">
                        <span style="color: white; font-size: 16px; font-weight: 600;">Child Education</span>
                        <span style="color: white; font-size: 14px; font-weight: 500;">12 yrs</span>
                    </div>
                    <div style="margin-bottom: 1rem;">
                        <span style="color: white; font-size: 24px; font-weight: 600;">Rs 9.00L</span>
                        <span style="color: #666; font-size: 12px; margin-left: 6px;">of Rs 80.00L</span>
                    </div>
                    <div style="background-color: #222; height: 4px; border-radius: 2px; margin-bottom: 8px;">
                        <div style="background-color: #3b82f6; width: 11%; height: 100%; border-radius: 2px;"></div>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #666; font-size: 11px;">11% complete</span>
                        <span style="color: #888; font-size: 11px;">Suggested SIP: <span style="color: white; font-weight: 600;">Rs 55,600</span></span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        with g2:
            st.markdown("""
                <div style="background-color: #141416; border: 1px solid #2a2a2a; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; cursor: pointer; transition: 0.2s;" onmouseover="this.style.borderColor='#4ade80'" onmouseout="this.style.borderColor='#2a2a2a'">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="color: #666; font-size: 10px; font-weight: 600; letter-spacing: 1px;">GOAL</span>
                        <span style="color: #666; font-size: 10px; font-weight: 600; letter-spacing: 1px;">IN</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 1.5rem;">
                        <span style="color: white; font-size: 16px; font-weight: 600;">Home Down Payment</span>
                        <span style="color: white; font-size: 14px; font-weight: 500;">5 yrs</span>
                    </div>
                    <div style="margin-bottom: 1rem;">
                        <span style="color: white; font-size: 24px; font-weight: 600;">Rs 16.50L</span>
                        <span style="color: #666; font-size: 12px; margin-left: 6px;">of Rs 45.00L</span>
                    </div>
                    <div style="background-color: #222; height: 4px; border-radius: 2px; margin-bottom: 8px;">
                        <div style="background-color: #4ade80; width: 37%; height: 100%; border-radius: 2px;"></div>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #666; font-size: 11px;">37% complete</span>
                        <span style="color: #888; font-size: 11px;">Suggested SIP: <span style="color: white; font-weight: 600;">Rs 75,000</span></span>
                    </div>
                </div>
                
                <div style="background-color: #141416; border: 1px solid #2a2a2a; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; cursor: pointer; transition: 0.2s;" onmouseover="this.style.borderColor='#a855f7'" onmouseout="this.style.borderColor='#2a2a2a'">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="color: #666; font-size: 10px; font-weight: 600; letter-spacing: 1px;">GOAL</span>
                        <span style="color: #666; font-size: 10px; font-weight: 600; letter-spacing: 1px;">IN</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 1.5rem;">
                        <span style="color: white; font-size: 16px; font-weight: 600;">World Trip</span>
                        <span style="color: white; font-size: 14px; font-weight: 500;">3 yrs</span>
                    </div>
                    <div style="margin-bottom: 1rem;">
                        <span style="color: white; font-size: 24px; font-weight: 600;">Rs 2.20L</span>
                        <span style="color: #666; font-size: 12px; margin-left: 6px;">of Rs 8.00L</span>
                    </div>
                    <div style="background-color: #222; height: 4px; border-radius: 2px; margin-bottom: 8px;">
                        <div style="background-color: #a855f7; width: 28%; height: 100%; border-radius: 2px;"></div>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #666; font-size: 11px;">28% complete</span>
                        <span style="color: #888; font-size: 11px;">Suggested SIP: <span style="color: white; font-weight: 600;">Rs 22,200</span></span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    elif page == "💸 Spending":
        st.markdown("""
            <div style="margin-bottom: 2rem;">
                <div style="display: flex; justify-content: space-between; align-items: flex-end;">
                    <div>
                        <div style="color: #f5b03e; font-size: 10px; font-weight: 600; letter-spacing: 1.5px; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
                            <span style="font-size: 14px;">📄</span> BEHAVIOUR INTELLIGENCE
                        </div>
                        <h1 style="color: white; font-size: 32px; font-weight: 700; margin: 0 0 8px 0; padding: 0;">Spending Analyzer</h1>
                        <div style="color: #888; font-size: 14px;">Upload bank statement CSV. We categorize, chart & find leaks.</div>
                    </div>
                    <div>
                        <a href="#" style="color: #f5b03e; font-size: 12px; text-decoration: none; font-weight: 500;">Download sample CSV</a>
                    </div>
                </div>
            </div>
            <div style="background-color: #141416; border: 1px solid #2a2a2a; border-radius: 12px; height: 350px; display: flex; flex-direction: column; justify-content: center; align-items: center; cursor: pointer; transition: 0.2s;" onmouseover="this.style.borderColor='#f5b03e'" onmouseout="this.style.borderColor='#2a2a2a'">
                <div style="color: #f5b03e; font-size: 32px; margin-bottom: 12px;">☁️↑</div>
                <div style="color: white; font-size: 18px; font-weight: 700; margin-bottom: 8px;">Drop bank statement CSV here</div>
                <div style="color: #666; font-size: 12px;">Columns: <span style="font-family: monospace; color: #888;">date, description, amount</span></div>
            </div>
        """, unsafe_allow_html=True)
        
    elif page == "❤️ Health Score":
        st.markdown("""
            <div style="margin-bottom: 2rem;">
                <div style="color: #f5b03e; font-size: 10px; font-weight: 600; letter-spacing: 1.5px; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
                    <span style="font-size: 14px;">❤️</span> 7-PILLAR MODEL
                </div>
                <h1 style="color: white; font-size: 32px; font-weight: 700; margin: 0 0 8px 0; padding: 0;">Financial Health Score</h1>
                <div style="color: #888; font-size: 14px;">Your composite wellness rating across the pillars of personal finance.</div>
            </div>
            <div style="display: flex; gap: 1rem; margin-bottom: 1rem;">
                <div style="flex: 1; background-color: #141416; border: 1px solid #2a2a2a; border-radius: 12px; padding: 2rem; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px;">
                    <div style="position: relative; width: 180px; height: 180px; border-radius: 50%; background: conic-gradient(#f5b03e 0% 64%, #333 64% 100%); display: flex; align-items: center; justify-content: center; margin-bottom: 1.5rem;">
                        <div style="width: 150px; height: 150px; background-color: #141416; border-radius: 50%; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                            <div style="color: #f5b03e; font-size: 14px; margin-bottom: 4px;">❤️</div>
                            <div style="color: white; font-size: 42px; font-weight: 700; line-height: 1;">64</div>
                            <div style="color: #666; font-size: 12px;">out of 100</div>
                        </div>
                    </div>
                    <div style="color: white; font-size: 18px; font-weight: 500;">Good</div>
                </div>
                <div style="flex: 2.2; background-color: #141416; border: 1px solid #2a2a2a; border-radius: 12px; padding: 2rem;">
                    <div style="color: white; font-size: 16px; font-weight: 600; margin-bottom: 1.5rem;">Pillar breakdown</div>
                    <div style="display: flex; gap: 2rem; margin-bottom: 1.5rem;">
                        <div style="flex: 1;">
                            <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 4px;">
                                <div>
                                    <div style="color: white; font-size: 14px; font-weight: 500;">Savings</div>
                                    <div style="color: #666; font-size: 10px;">Target benchmarks for Indian households.</div>
                                </div>
                                <div style="color: #4ade80; font-size: 14px; font-weight: 600;">100</div>
                            </div>
                            <div style="background-color: #222; height: 4px; border-radius: 2px;">
                                <div style="background-color: #4ade80; width: 100%; height: 4px; border-radius: 2px;"></div>
                            </div>
                        </div>
                        <div style="flex: 1;">
                            <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 4px;">
                                <div>
                                    <div style="color: white; font-size: 14px; font-weight: 500;">Investments</div>
                                    <div style="color: #666; font-size: 10px;">Target benchmarks for Indian households.</div>
                                </div>
                                <div style="color: #ef4444; font-size: 14px; font-weight: 600;">24</div>
                            </div>
                            <div style="background-color: #222; height: 4px; border-radius: 2px;">
                                <div style="background-color: #ef4444; width: 24%; height: 4px; border-radius: 2px;"></div>
                            </div>
                        </div>
                    </div>
                    <div style="display: flex; gap: 2rem; margin-bottom: 1.5rem;">
                        <div style="flex: 1;">
                            <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 4px;">
                                <div>
                                    <div style="color: white; font-size: 14px; font-weight: 500;">Emergency Fund</div>
                                    <div style="color: #666; font-size: 10px;">Target benchmarks for Indian households.</div>
                                </div>
                                <div style="color: #f5b03e; font-size: 14px; font-weight: 600;">46</div>
                            </div>
                            <div style="background-color: #222; height: 4px; border-radius: 2px;">
                                <div style="background-color: #f5b03e; width: 46%; height: 4px; border-radius: 2px;"></div>
                            </div>
                        </div>
                        <div style="flex: 1;">
                            <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 4px;">
                                <div>
                                    <div style="color: white; font-size: 14px; font-weight: 500;">Insurance</div>
                                    <div style="color: #666; font-size: 10px;">Target benchmarks for Indian households.</div>
                                </div>
                                <div style="color: #ef4444; font-size: 14px; font-weight: 600;">35</div>
                            </div>
                            <div style="background-color: #222; height: 4px; border-radius: 2px;">
                                <div style="background-color: #ef4444; width: 35%; height: 4px; border-radius: 2px;"></div>
                            </div>
                        </div>
                    </div>
                    <div style="display: flex; gap: 2rem;">
                        <div style="flex: 1;">
                            <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 4px;">
                                <div>
                                    <div style="color: white; font-size: 14px; font-weight: 500;">Debt</div>
                                    <div style="color: #666; font-size: 10px;">Target benchmarks for Indian households.</div>
                                </div>
                                <div style="color: #f5b03e; font-size: 14px; font-weight: 600;">65</div>
                            </div>
                            <div style="background-color: #222; height: 4px; border-radius: 2px;">
                                <div style="background-color: #f5b03e; width: 65%; height: 4px; border-radius: 2px;"></div>
                            </div>
                        </div>
                        <div style="flex: 1;">
                            <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 4px;">
                                <div>
                                    <div style="color: white; font-size: 14px; font-weight: 500;">Credit Behaviour</div>
                                    <div style="color: #666; font-size: 10px;">Target benchmarks for Indian households.</div>
                                </div>
                                <div style="color: #4ade80; font-size: 14px; font-weight: 600;">80</div>
                            </div>
                            <div style="background-color: #222; height: 4px; border-radius: 2px;">
                                <div style="background-color: #4ade80; width: 80%; height: 4px; border-radius: 2px;"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div style="background-color: #141416; border: 1px solid #2a2a2a; border-radius: 12px; padding: 1.5rem;">
                <div style="color: white; font-size: 16px; font-weight: 600; margin-bottom: 1rem;">What this means</div>
                <div style="color: #888; font-size: 13px; line-height: 1.6; margin-bottom: 0.5rem;">
                    Your financial health score is a weighted composite across 7 pillars, each measured against ideal benchmarks for the Indian household.<br>
                    Scores above <span style="color: #4ade80; font-weight: 600;">70</span> indicate excellent financial resilience. Scores between <span style="color: #f5b03e; font-weight: 600;">40-70</span> suggest room to strengthen specific pillars. Below <span style="color: #ef4444; font-weight: 600;">40</span> warrants immediate action.
                </div>
                <div style="color: #aaa; font-size: 13px; display: flex; align-items: center; gap: 6px;">
                    <span style="color: #f5b03e;">💡</span> Head to <a href="#" style="color: #f5b03e; text-decoration: underline;">AI Advisor</a> to ask personalized questions about improving any pillar.
                </div>
            </div>
        """, unsafe_allow_html=True)
        
    elif page == "✨ AI Recommendations ᴬᴵ":
        st.markdown("""
            <div style="margin-bottom: 2rem;">
                <div style="color: #f5b03e; font-size: 10px; font-weight: 600; letter-spacing: 1.5px; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
                    <span style="font-size: 14px;">✨</span> AI RECOMMENDATIONS
                </div>
                <h1 style="color: white; font-size: 32px; font-weight: 700; margin: 0 0 8px 0; padding: 0;">Actions you can take today</h1>
                <div style="color: #888; font-size: 14px;">Prioritized, explainable moves that improve your wealth outcome.</div>
            </div>
            <div style="display: flex; gap: 1rem; margin-bottom: 1rem;">
                <div style="flex: 1; background-color: #141416; border: 1px solid #2a2a2a; border-radius: 12px; padding: 1.5rem; transition: 0.2s;" onmouseover="this.style.borderColor='#f5b03e'" onmouseout="this.style.borderColor='#2a2a2a'">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div style="color: #666; font-size: 10px; font-weight: 600; letter-spacing: 1px;">RECOMMENDATION</div>
                        <div style="color: #ef4444; font-size: 10px; font-weight: 600; letter-spacing: 1px;">HIGH</div>
                    </div>
                    <div style="color: white; font-size: 18px; font-weight: 600; margin-bottom: 12px;">Increase SIP by ₹5,000</div>
                    <div style="color: #888; font-size: 13px; margin-bottom: 2rem;">Would push retirement age from 58 to 55 and add ~₹1.4Cr by 60.</div>
                    <div><a href="#" style="color: #f5b03e; font-size: 13px; font-weight: 500; text-decoration: none;">Apply this</a></div>
                </div>
                <div style="flex: 1; background-color: #141416; border: 1px solid #2a2a2a; border-radius: 12px; padding: 1.5rem; transition: 0.2s;" onmouseover="this.style.borderColor='#f5b03e'" onmouseout="this.style.borderColor='#2a2a2a'">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div style="color: #666; font-size: 10px; font-weight: 600; letter-spacing: 1px;">RECOMMENDATION</div>
                        <div style="color: #f5b03e; font-size: 10px; font-weight: 600; letter-spacing: 1px;">MEDIUM</div>
                    </div>
                    <div style="color: white; font-size: 18px; font-weight: 600; margin-bottom: 12px;">Move idle savings to liquid fund</div>
                    <div style="color: #888; font-size: 13px; margin-bottom: 2rem;">₹1.2L parked at 3% could earn ~6.8% in a liquid fund.</div>
                    <div><a href="#" style="color: #f5b03e; font-size: 13px; font-weight: 500; text-decoration: none;">Apply this</a></div>
                </div>
            </div>
            <div style="display: flex; gap: 1rem;">
                <div style="flex: 1; background-color: #141416; border: 1px solid #2a2a2a; border-radius: 12px; padding: 1.5rem; transition: 0.2s;" onmouseover="this.style.borderColor='#f5b03e'" onmouseout="this.style.borderColor='#2a2a2a'">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div style="color: #666; font-size: 10px; font-weight: 600; letter-spacing: 1px;">RECOMMENDATION</div>
                        <div style="color: #ef4444; font-size: 10px; font-weight: 600; letter-spacing: 1px;">HIGH</div>
                    </div>
                    <div style="color: white; font-size: 18px; font-weight: 600; margin-bottom: 12px;">Term insurance top-up</div>
                    <div style="color: #888; font-size: 13px; margin-bottom: 2rem;">Cover is 3.5x income. Recommended: 10x for dependents.</div>
                    <div><a href="#" style="color: #f5b03e; font-size: 13px; font-weight: 500; text-decoration: none;">Apply this</a></div>
                </div>
                <div style="flex: 1; background-color: #141416; border: 1px solid #2a2a2a; border-radius: 12px; padding: 1.5rem; transition: 0.2s;" onmouseover="this.style.borderColor='#f5b03e'" onmouseout="this.style.borderColor='#2a2a2a'">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div style="color: #666; font-size: 10px; font-weight: 600; letter-spacing: 1px;">RECOMMENDATION</div>
                        <div style="color: #4ade80; font-size: 10px; font-weight: 600; letter-spacing: 1px;">LOW</div>
                    </div>
                    <div style="color: white; font-size: 18px; font-weight: 600; margin-bottom: 12px;">Refinance vehicle loan</div>
                    <div style="color: #888; font-size: 13px; margin-bottom: 2rem;">Current rate 11.2% vs market 9.4% — save ~₹18k over tenure.</div>
                    <div><a href="#" style="color: #f5b03e; font-size: 13px; font-weight: 500; text-decoration: none;">Apply this</a></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    elif page == "💼 Portfolio":
        st.markdown("""
            <div style="margin-bottom: 2rem;">
                <div style="display: flex; justify-content: space-between; align-items: flex-end;">
                    <div>
                        <div style="color: #f5b03e; font-size: 10px; font-weight: 600; letter-spacing: 1.5px; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;"><span style="font-size: 14px;">📄</span> PORTFOLIO X-RAY</div>
                        <h1 style="color: white; font-size: 32px; font-weight: 700; margin: 0 0 8px 0; padding: 0;">Portfolio Analyzer</h1>
                        <div style="color: #888; font-size: 14px;">Upload your holdings CSV and get an instant diagnostic.</div>
                    </div>
                    <div><a href="#" style="color: #f5b03e; font-size: 12px; text-decoration: none; font-weight: 500;">Download sample CSV</a></div>
                </div>
            </div>
            <div style="background-color: #141416; border: 1px solid #2a2a2a; border-radius: 12px; height: 350px; display: flex; flex-direction: column; justify-content: center; align-items: center; cursor: pointer; transition: 0.2s;" onmouseover="this.style.borderColor='#f5b03e'" onmouseout="this.style.borderColor='#2a2a2a'">
                <div style="color: #f5b03e; font-size: 32px; margin-bottom: 12px;">☁️↑</div>
                <div style="color: white; font-size: 18px; font-weight: 700; margin-bottom: 8px;">Drop your portfolio CSV here</div>
                <div style="color: #666; font-size: 12px;">or click to browse. Columns: <span style="font-family: monospace; color: white;">asset, category, quantity, price</span></div>
            </div>
        """, unsafe_allow_html=True)
    elif page == "⚠️ Risk Predictor":
        st.markdown("""
            <div style="margin-bottom: 2rem;">
                <div style="color: #f5b03e; font-size: 10px; font-weight: 600; letter-spacing: 1.5px; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;"><span style="font-size: 14px;">🛡️</span> PREDICTIVE</div>
                <h1 style="color: white; font-size: 32px; font-weight: 700; margin: 0 0 8px 0; padding: 0;">Risk Predictor</h1>
                <div style="color: #888; font-size: 14px;">Forward-looking indicators of your financial risks.</div>
            </div>
            <div style="display: flex; gap: 1rem; margin-bottom: 1rem;">
                <div style="flex: 1; background-color: #141416; border: 1px solid #2a2a2a; border-radius: 12px; padding: 1.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div style="color: #666; font-size: 10px; font-weight: 600; letter-spacing: 1px;">RISK</div>
                        <div style="color: #ef4444; font-size: 10px; font-weight: 600; letter-spacing: 1px;">HIGH</div>
                    </div>
                    <div style="color: white; font-size: 18px; font-weight: 600; margin-bottom: 2rem;">Overspending Risk</div>
                    <div style="background-color: #222; height: 4px; border-radius: 2px; margin-bottom: 8px;"><div style="background-color: #ef4444; width: 54%; height: 4px; border-radius: 2px;"></div></div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                        <div style="color: #666; font-size: 10px;">Risk score</div>
                        <div style="color: #ef4444; font-size: 12px; font-weight: 600;">54<span style="color: #666;">/100</span></div>
                    </div>
                    <div style="color: #aaa; font-size: 12px;">⚠️ You spend 54% of your income. Aim below 70%.</div>
                </div>
                <div style="flex: 1; background-color: #141416; border: 1px solid #2a2a2a; border-radius: 12px; padding: 1.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div style="color: #666; font-size: 10px; font-weight: 600; letter-spacing: 1px;">RISK</div>
                        <div style="color: #4ade80; font-size: 10px; font-weight: 600; letter-spacing: 1px;">LOW</div>
                    </div>
                    <div style="color: white; font-size: 18px; font-weight: 600; margin-bottom: 2rem;">Debt Risk</div>
                    <div style="background-color: #222; height: 4px; border-radius: 2px; margin-bottom: 8px;"><div style="background-color: #4ade80; width: 17%; height: 4px; border-radius: 2px;"></div></div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                        <div style="color: #666; font-size: 10px;">Risk score</div>
                        <div style="color: #4ade80; font-size: 12px; font-weight: 600;">17<span style="color: #666;">/100</span></div>
                    </div>
                    <div style="color: #aaa; font-size: 12px;">⚠️ Debt is 17% of annual income. Below 35% is healthy.</div>
                </div>
            </div>
            <div style="display: flex; gap: 1rem; margin-bottom: 1rem;">
                <div style="flex: 1; background-color: #141416; border: 1px solid #2a2a2a; border-radius: 12px; padding: 1.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div style="color: #666; font-size: 10px; font-weight: 600; letter-spacing: 1px;">RISK</div>
                        <div style="color: #f5b03e; font-size: 10px; font-weight: 600; letter-spacing: 1px;">MEDIUM</div>
                    </div>
                    <div style="color: white; font-size: 18px; font-weight: 600; margin-bottom: 2rem;">Emergency Fund Gap</div>
                    <div style="background-color: #222; height: 4px; border-radius: 2px; margin-bottom: 8px;"><div style="background-color: #f5b03e; width: 54%; height: 4px; border-radius: 2px;"></div></div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                        <div style="color: #666; font-size: 10px;">Risk score</div>
                        <div style="color: #f5b03e; font-size: 12px; font-weight: 600;">54<span style="color: #666;">/100</span></div>
                    </div>
                    <div style="color: #aaa; font-size: 12px;">⚠️ Emergency fund covers 2.8 months of expenses. Target 6 months.</div>
                </div>
                <div style="flex: 1; background-color: #141416; border: 1px solid #2a2a2a; border-radius: 12px; padding: 1.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div style="color: #666; font-size: 10px; font-weight: 600; letter-spacing: 1px;">RISK</div>
                        <div style="color: #4ade80; font-size: 10px; font-weight: 600; letter-spacing: 1px;">LOW</div>
                    </div>
                    <div style="color: white; font-size: 18px; font-weight: 600; margin-bottom: 2rem;">Goal Failure Risk</div>
                    <div style="background-color: #222; height: 4px; border-radius: 2px; margin-bottom: 8px;"><div style="background-color: #4ade80; width: 35%; height: 4px; border-radius: 2px;"></div></div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                        <div style="color: #666; font-size: 10px;">Risk score</div>
                        <div style="color: #4ade80; font-size: 12px; font-weight: 600;">35<span style="color: #666;">/100</span></div>
                    </div>
                    <div style="color: #aaa; font-size: 12px;">⚠️ Current savings pace supports your goals with 65% confidence.</div>
                </div>
            </div>
            <div style="display: flex; gap: 1rem;">
                <div style="flex: 1; background-color: #141416; border: 1px solid #2a2a2a; border-radius: 12px; padding: 1.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div style="color: #666; font-size: 10px; font-weight: 600; letter-spacing: 1px;">RISK</div>
                        <div style="color: #f5b03e; font-size: 10px; font-weight: 600; letter-spacing: 1px;">MEDIUM</div>
                    </div>
                    <div style="color: white; font-size: 18px; font-weight: 600; margin-bottom: 2rem;">Investment Risk</div>
                    <div style="background-color: #222; height: 4px; border-radius: 2px; margin-bottom: 8px;"><div style="background-color: #f5b03e; width: 50%; height: 4px; border-radius: 2px;"></div></div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                        <div style="color: #666; font-size: 10px;">Risk score</div>
                        <div style="color: #f5b03e; font-size: 12px; font-weight: 600;">50<span style="color: #666;">/100</span></div>
                    </div>
                    <div style="color: #aaa; font-size: 12px;">⚠️ Portfolio risk is moderate. Consider diversification review.</div>
                </div>
                <div style="flex: 1;"></div>
            </div>
        """, unsafe_allow_html=True)
    elif page == "📄 Reports":
        st.markdown("""
            <div style="margin-bottom: 2rem;">
                <div style="display: flex; justify-content: space-between; align-items: flex-end;">
                    <div>
                        <div style="color: #f5b03e; font-size: 10px; font-weight: 600; letter-spacing: 1.5px; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;"><span style="font-size: 14px;">📄</span> PORTABLE PORTFOLIO</div>
                        <h1 style="color: white; font-size: 32px; font-weight: 700; margin: 0 0 8px 0; padding: 0;">Financial Report</h1>
                        <div style="color: #888; font-size: 14px;">One-page snapshot of everything BankNova knows about your wealth.</div>
                    </div>
                    <div style="display: flex; gap: 12px;">
                        <button style="background-color: #f5b03e; color: black; border: none; border-radius: 6px; padding: 8px 16px; font-size: 12px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px;">🖨️ Print / Save PDF</button>
                        <button style="background-color: transparent; color: white; border: 1px solid #333; border-radius: 6px; padding: 8px 16px; font-size: 12px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px;">📥 JSON</button>
                    </div>
                </div>
            </div>
            <div style="background-color: #141416; border: 1px solid #2a2a2a; border-radius: 12px; padding: 2rem; margin-bottom: 2rem;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 3rem; border-bottom: 1px solid #2a2a2a; padding-bottom: 2rem;">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <div style="background: linear-gradient(135deg, #fcd34d, #f59e0b); color: black; font-weight: 800; font-size: 18px; width: 36px; height: 36px; display: flex; justify-content: center; align-items: center; border-radius: 8px;">B</div>
                        <div style="line-height: 1.2;">
                            <div style="color: white; font-size: 16px; font-weight: 700;">BankNova AI</div>
                            <div style="color: #666; font-size: 12px;">Wealth Intelligence Report</div>
                        </div>
                    </div>
                    <div style="text-align: right; line-height: 1.5;">
                        <div style="color: #666; font-size: 10px;">Generated for</div>
                        <div style="color: white; font-size: 12px; font-weight: 600;">aaishwaryalala13</div>
                        <div style="color: #888; font-size: 12px;">aaishwaryalala13@gmail.com</div>
                        <div style="color: #888; font-size: 12px;">5/7/2026, 7:47:36 pm</div>
                    </div>
                </div>
                <div style="color: #f5b03e; font-size: 10px; font-weight: 600; letter-spacing: 1px; margin-bottom: 1.5rem;">WEALTH SUMMARY</div>
                <div style="display: flex; gap: 1rem; margin-bottom: 1rem;">
                    <div style="flex: 1; border-bottom: 1px solid #2a2a2a; padding-bottom: 1rem;">
                        <div style="color: #666; font-size: 11px; margin-bottom: 4px;">Total Wealth</div>
                        <div style="color: white; font-size: 18px; font-weight: 600;">Rs 13.80 L</div>
                    </div>
                    <div style="flex: 1; border-bottom: 1px solid #2a2a2a; padding-bottom: 1rem;">
                        <div style="color: #666; font-size: 11px; margin-bottom: 4px;">Savings</div>
                        <div style="color: white; font-size: 18px; font-weight: 600;">Rs 3.50 L</div>
                    </div>
                    <div style="flex: 1; border-bottom: 1px solid #2a2a2a; padding-bottom: 1rem;">
                        <div style="color: #666; font-size: 11px; margin-bottom: 4px;">Investments</div>
                        <div style="color: white; font-size: 18px; font-weight: 600;">Rs 8.50 L</div>
                    </div>
                    <div style="flex: 1; border-bottom: 1px solid #2a2a2a; padding-bottom: 1rem;">
                        <div style="color: #666; font-size: 11px; margin-bottom: 4px;">Emergency Fund</div>
                        <div style="color: white; font-size: 18px; font-weight: 600;">Rs 1.80 L</div>
                    </div>
                </div>
                <div style="display: flex; gap: 1rem; margin-bottom: 3rem;">
                    <div style="flex: 1;">
                        <div style="color: #666; font-size: 11px; margin-bottom: 4px;">Monthly Income</div>
                        <div style="color: white; font-size: 18px; font-weight: 600;">Rs 1.20 L</div>
                    </div>
                    <div style="flex: 1;">
                        <div style="color: #666; font-size: 11px; margin-bottom: 4px;">Monthly Expenses</div>
                        <div style="color: white; font-size: 18px; font-weight: 600;">Rs 65.0K</div>
                    </div>
                    <div style="flex: 1;">
                        <div style="color: #666; font-size: 11px; margin-bottom: 4px;">Monthly Savings</div>
                        <div style="color: white; font-size: 18px; font-weight: 600;">Rs 55.0K</div>
                    </div>
                    <div style="flex: 1;">
                        <div style="color: #666; font-size: 11px; margin-bottom: 4px;">Savings Rate</div>
                        <div style="color: white; font-size: 18px; font-weight: 600;">45.8%</div>
                    </div>
                </div>
                <div style="color: #f5b03e; font-size: 10px; font-weight: 600; letter-spacing: 1px; margin-bottom: 1rem;">FINANCIAL HEALTH SCORE</div>
                <div style="color: #f5b03e; font-size: 42px; font-weight: 700; line-height: 1; margin-bottom: 2rem;">64<span style="color: #666; font-size: 16px;"> /100</span></div>
                <div style="display: flex; gap: 1rem; margin-bottom: 1rem;">
                    <div style="flex: 1; border-bottom: 1px solid #2a2a2a; padding-bottom: 1rem;">
                        <div style="color: #666; font-size: 11px; margin-bottom: 4px;">Savings</div>
                        <div style="color: #4ade80; font-size: 14px; font-weight: 600;">100/100</div>
                    </div>
                    <div style="flex: 1; border-bottom: 1px solid #2a2a2a; padding-bottom: 1rem;">
                        <div style="color: #666; font-size: 11px; margin-bottom: 4px;">Investments</div>
                        <div style="color: #ef4444; font-size: 14px; font-weight: 600;">24/100</div>
                    </div>
                    <div style="flex: 1; border-bottom: 1px solid #2a2a2a; padding-bottom: 1rem;">
                        <div style="color: #666; font-size: 11px; margin-bottom: 4px;">Emergency Fund</div>
                        <div style="color: #f5b03e; font-size: 14px; font-weight: 600;">46/100</div>
                    </div>
                    <div style="flex: 1; border-bottom: 1px solid #2a2a2a; padding-bottom: 1rem;">
                        <div style="color: #666; font-size: 11px; margin-bottom: 4px;">Insurance</div>
                        <div style="color: #ef4444; font-size: 14px; font-weight: 600;">35/100</div>
                    </div>
                </div>
                <div style="display: flex; gap: 1rem; margin-bottom: 3rem;">
                    <div style="flex: 1;">
                        <div style="color: #666; font-size: 11px; margin-bottom: 4px;">Debt</div>
                        <div style="color: #f5b03e; font-size: 14px; font-weight: 600;">65/100</div>
                    </div>
                    <div style="flex: 1;">
                        <div style="color: #666; font-size: 11px; margin-bottom: 4px;">Budgeting</div>
                        <div style="color: #4ade80; font-size: 14px; font-weight: 600;">100/100</div>
                    </div>
                    <div style="flex: 1;">
                        <div style="color: #666; font-size: 11px; margin-bottom: 4px;">Credit Behaviour</div>
                        <div style="color: #4ade80; font-size: 14px; font-weight: 600;">80/100</div>
                    </div>
                    <div style="flex: 1;"></div>
                </div>
                <div style="color: #666; font-size: 10px; line-height: 1.5; font-style: italic;">Disclaimer: This report is generated for educational purposes only and does not constitute licensed investment advice. All computations use user-provided data and standard financial models. Consult a SEBI-registered advisor for personalized recommendations.</div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.header(f"Page: {page}")
        st.info("This section is under construction.")
