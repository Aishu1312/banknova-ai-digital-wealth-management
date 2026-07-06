import streamlit as st
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re
import time
import streamlit.components.v1 as components

@st.cache_resource
def get_api_session():
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

API_URL = "http://127.0.0.1:8000/auth"

def check_password_strength(password: str):
    if not password:
        return None
    score = 0
    if len(password) >= 8: score += 1
    if re.search(r"[A-Z]", password): score += 1
    if re.search(r"[a-z]", password): score += 1
    if re.search(r"[0-9]", password): score += 1
    if re.search(r"[\W_]", password): score += 1
    if score <= 2: return "Weak"
    elif score <= 4: return "Medium"
    else: return "Strong"

def validate_password(password: str):
    errors = []
    if len(password) < 8: errors.append("Minimum 8 characters")
    if not re.search(r"[A-Z]", password): errors.append("One uppercase letter")
    if not re.search(r"[a-z]", password): errors.append("One lowercase letter")
    if not re.search(r"[0-9]", password): errors.append("One number")
    if not re.search(r"[\W_]", password): errors.append("One special character")
    return errors

def trigger_oauth(provider):
    st.session_state[f'loading_{provider}'] = True
    js = f"""
    <script>
        setTimeout(function() {{
            window.parent.location.href = '{API_URL}/login/{provider}';
        }}, 800);
    </script>
    """
    components.html(js, height=0)

def render():
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"
    if "reset_token" not in st.session_state:
        st.session_state.reset_token = None
        
    mode = st.session_state.auth_mode
    
    st.markdown("""
        <style>
            .stApp {
                background: radial-gradient(circle at 50% 0%, #1a1a1f 0%, #09090b 100%) !important;
            }
            [data-testid="block-container"] {
                max-width: 480px !important;
                margin: 4rem auto;
                background: rgba(20, 20, 22, 0.65) !important;
                backdrop-filter: blur(16px) !important;
                -webkit-backdrop-filter: blur(16px) !important;
                padding: 3rem !important;
                border-radius: 24px !important;
                border: 1px solid rgba(255, 255, 255, 0.08) !important;
                box-shadow: 0 30px 60px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.1) !important;
                animation: fade-in-up 0.6s cubic-bezier(0.16, 1, 0.3, 1);
            }
            @keyframes fade-in-up {
                0% { opacity: 0; transform: translateY(20px); }
                100% { opacity: 1; transform: translateY(0); }
            }
            .auth-header { text-align: center; margin-bottom: 2.5rem; }
            .auth-title { color: #ffffff; font-size: 28px; font-weight: 700; margin-bottom: 8px; letter-spacing: -0.5px; }
            .auth-subtitle { color: #a1a1aa; font-size: 15px; }
            .stTextInput>div>div>input { 
                background-color: rgba(0, 0, 0, 0.3) !important; 
                border: 1px solid rgba(255, 255, 255, 0.1) !important; 
                color: white !important; 
                border-radius: 10px !important; 
                padding: 0.85rem 1rem !important; 
                transition: all 0.2s ease !important;
            }
            .stTextInput>div>div>input:focus { 
                border-color: #f5b03e !important; 
                box-shadow: 0 0 0 1px #f5b03e, 0 0 15px rgba(245, 176, 62, 0.2) !important; 
                background-color: rgba(0, 0, 0, 0.5) !important;
            }
            .stButton>button { 
                width: 100% !important; 
                border-radius: 10px !important; 
                padding: 0.75rem !important; 
                font-weight: 600 !important; 
                transition: all 0.2s ease !important;
            }
            [data-testid="baseButton-primary"] { 
                background: linear-gradient(135deg, #fcd34d, #f59e0b) !important; 
                color: #000000 !important; 
                border: none !important; 
                box-shadow: 0 4px 15px rgba(245, 158, 11, 0.3) !important;
            }
            [data-testid="baseButton-primary"]:hover {
                transform: translateY(-1px);
                box-shadow: 0 6px 20px rgba(245, 158, 11, 0.4) !important;
            }
            .meter-container { background: rgba(255,255,255,0.1); height: 4px; border-radius: 2px; margin-top: 8px; overflow: hidden; }
            .meter { height: 100%; border-radius: 2px; transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1), background-color 0.4s ease; }
            .meter-Weak { background: #ef4444; width: 33%; box-shadow: 0 0 10px rgba(239, 68, 68, 0.5); }
            .meter-Medium { background: #f5b03e; width: 66%; box-shadow: 0 0 10px rgba(245, 176, 62, 0.5); }
            .meter-Strong { background: #4ade80; width: 100%; box-shadow: 0 0 10px rgba(74, 222, 128, 0.5); }
            .error-text { color: #f87171; font-size: 13px; margin-top: 4px; }
            .separator {
                display: flex;
                align-items: center;
                text-align: center;
                margin: 2rem 0;
                color: #52525b;
                font-size: 12px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            .separator::before, .separator::after {
                content: '';
                flex: 1;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            .separator:not(:empty)::before { margin-right: .5em; }
            .separator:not(:empty)::after { margin-left: .5em; }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="auth-header">', unsafe_allow_html=True)
    st.markdown("""<div style="background: linear-gradient(135deg, #fcd34d, #f59e0b); color: black; font-weight: 800; font-size: 24px; width: 48px; height: 48px; display: flex; justify-content: center; align-items: center; border-radius: 12px; margin: 0 auto 1rem auto; box-shadow: 0 4px 15px rgba(245, 158, 11, 0.3);">B</div>""", unsafe_allow_html=True)
    
    if mode == "login":
        st.markdown('<div class="auth-title">Welcome back</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-subtitle">Sign in to your BankNova AI account</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        email = st.text_input("Email", placeholder="you@example.com", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.checkbox("Remember Me")
        with col2:
            if st.button("Forgot Password?", type="tertiary", use_container_width=True):
                st.session_state.auth_mode = "forgot"
                st.rerun()
            
        if st.button("Sign In", type="primary"):
            if not email or not password:
                st.error("Please enter both email and password.")
            else:
                with st.spinner("Authenticating..."):
                    try:
                        session = get_api_session()
                        res = session.post(f"{API_URL}/login", data={"username": email, "password": password}, timeout=5)
                        if res.status_code == 200:
                            data = res.json()
                            st.session_state.access_token = data["access_token"]
                            st.session_state.logged_in = True
                            st.rerun()
                        else:
                            msg = res.json().get("detail", "Login failed")
                            if "verify your email" in msg.lower():
                                st.session_state.unverified_email = email
                                st.session_state.auth_mode = "resend_verify"
                                st.rerun()
                            else:
                                st.error(msg)
                    except requests.exceptions.Timeout:
                        st.error("The request timed out. Please try again.")
                    except requests.exceptions.ConnectionError:
                        st.error("Backend Offline: Server unavailable. Attempting reconnection...")
                    except Exception as e:
                        st.error("Network Error: Please check your internet connection.")
                        
        st.markdown('<div class="separator">OR CONTINUE WITH</div>', unsafe_allow_html=True)
        
        if st.button("Continue with Google", type="secondary", use_container_width=True):
            trigger_oauth("google")
        if st.session_state.get("loading_google"):
            st.info("Redirecting to Google...")

        if st.button("Continue with Microsoft", type="secondary", use_container_width=True):
            trigger_oauth("microsoft")
        if st.session_state.get("loading_microsoft"):
            st.info("Redirecting to Microsoft...")

        if st.button("Continue with GitHub", type="secondary", use_container_width=True):
            trigger_oauth("github")
        if st.session_state.get("loading_github"):
            st.info("Redirecting to GitHub...")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Don't have an account? Sign up", type="tertiary"):
            st.session_state.auth_mode = "signup"
            st.rerun()
            
    elif mode == "signup":
        st.markdown('<div class="auth-title">Create account</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-subtitle">Join BankNova AI today</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        name = st.text_input("Full Name", placeholder="Aarav Sharma")
        email = st.text_input("Email", placeholder="you@example.com", key="reg_email")
        password = st.text_input("Password", type="password", key="reg_pass")
        
        strength = check_password_strength(password)
        if strength:
            color = "#ef4444" if strength == "Weak" else "#f5b03e" if strength == "Medium" else "#4ade80"
            st.markdown(f"<div style='font-size: 12px; color: {color}; font-weight: 600; text-align: right; margin-bottom: -5px;'>{strength}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='meter-container'><div class='meter meter-{strength}'></div></div>", unsafe_allow_html=True)
            
        if password:
            errors = validate_password(password)
            if errors:
                st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
                for err in errors:
                    st.markdown(f"<div class='error-text'>• {err}</div>", unsafe_allow_html=True)
                
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Register", type="primary"):
            if not name or not email or not password:
                st.error("Please fill in all fields.")
            elif validate_password(password):
                st.error("Please choose a stronger password matching the criteria.")
            else:
                with st.spinner("Creating account..."):
                    try:
                        session = get_api_session()
                        res = session.post(f"{API_URL}/register", json={"name": name, "email": email, "password": password}, timeout=5)
                        if res.status_code == 200:
                            st.success("Account created! Please check your email to verify.")
                            time.sleep(2)
                            st.session_state.auth_mode = "login"
                            st.rerun()
                        else:
                            st.error(res.json().get("detail", "Registration failed"))
                    except requests.exceptions.Timeout:
                        st.error("The request timed out. Please try again.")
                    except requests.exceptions.ConnectionError:
                        st.error("Backend Offline: Server unavailable.")
                    except Exception:
                        st.error("Something went wrong. Please try again later.")
                        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Already have an account? Sign In", type="tertiary"):
            st.session_state.auth_mode = "login"
            st.rerun()
            
    elif mode == "resend_verify":
        st.markdown('<div class="auth-title">Verify Email</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-subtitle">Your email must be verified to login.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        email = st.session_state.get("unverified_email", "")
        st.info(f"We sent a verification link to **{email}** when you registered.")
        
        if st.button("Resend Verification Email", type="primary"):
            with st.spinner("Sending..."):
                try:
                    session = get_api_session()
                    res = session.post(f"{API_URL}/resend-verification", json={"email": email}, timeout=5)
                    st.success("Verification email sent! Please check your inbox.")
                except requests.exceptions.ConnectionError:
                    st.error("Backend Offline: Unable to connect.")
                except Exception:
                    st.error("Unable to connect. Please try again.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Back to Login", type="tertiary"):
            st.session_state.auth_mode = "login"
            st.rerun()

    elif mode == "forgot":
        st.markdown('<div class="auth-title">Reset Password</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-subtitle">Enter your email to receive a reset link</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        email = st.text_input("Email Address", placeholder="you@example.com", key="forgot_email")
        
        if st.button("Send Reset Link", type="primary"):
            if not email:
                st.error("Please enter your email address.")
            else:
                with st.spinner("Sending password reset link..."):
                    try:
                        session = get_api_session()
                        res = session.post(f"{API_URL}/forgot-password", json={"email": email}, timeout=5)
                        if res.status_code == 200:
                            data = res.json()
                            st.success(data.get("message", "Reset link sent."))
                            if "reset_link" in data:
                                st.info(f"**Reset Link (Dev Mode):** [Click here to reset]({data['reset_link']})")
                        else:
                            st.error(res.json().get("detail", "Error sending reset link."))
                    except requests.exceptions.Timeout:
                        st.error("The request timed out. Please try again.")
                    except requests.exceptions.ConnectionError:
                        st.error("Backend Offline: Server unavailable.")
                    except Exception:
                        st.error("An unexpected error occurred while connecting.")
                        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Back to Login", type="tertiary"):
            st.session_state.auth_mode = "login"
            st.rerun()

    elif mode == "reset":
        st.markdown('<div class="auth-title">New Password</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-subtitle">Create a strong new password</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        password = st.text_input("New Password", type="password", key="reset_pass")
        confirm = st.text_input("Confirm Password", type="password", key="reset_pass_conf")
        
        strength = check_password_strength(password)
        if strength:
            color = "#ef4444" if strength == "Weak" else "#f5b03e" if strength == "Medium" else "#4ade80"
            st.markdown(f"<div style='font-size: 12px; color: {color}; font-weight: 600; text-align: right; margin-bottom: -5px;'>{strength}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='meter-container'><div class='meter meter-{strength}'></div></div>", unsafe_allow_html=True)
            
        if password:
            errors = validate_password(password)
            if errors:
                st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
                for err in errors:
                    st.markdown(f"<div class='error-text'>• {err}</div>", unsafe_allow_html=True)
                
        if st.button("Reset Password", type="primary"):
            if not password or not confirm:
                st.error("Please fill in both fields.")
            elif password != confirm:
                st.error("Passwords do not match.")
            elif validate_password(password):
                st.error("Please choose a stronger password.")
            else:
                with st.spinner("Updating password..."):
                    try:
                        session = get_api_session()
                        res = session.post(f"{API_URL}/reset-password", json={
                            "token": st.session_state.reset_token,
                            "new_password": password
                        }, timeout=5)
                        if res.status_code == 200:
                            st.success("Password changed successfully.")
                            time.sleep(2)
                            st.session_state.auth_mode = "login"
                            st.session_state.reset_token = None
                            st.rerun()
                        else:
                            st.error(res.json().get("detail", "Reset failed."))
                    except requests.exceptions.Timeout:
                        st.error("The request timed out. Please try again.")
                    except requests.exceptions.ConnectionError:
                        st.error("Backend Offline: Server unavailable.")
                    except Exception:
                        st.error("Something went wrong. Please try again later.")
                        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Cancel", type="tertiary"):
            st.session_state.auth_mode = "login"
            st.session_state.reset_token = None
            st.rerun()
