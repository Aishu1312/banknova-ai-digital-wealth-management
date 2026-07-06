import streamlit as st
import requests
import re
import time

API_URL = "http://localhost:8000/auth"

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

def render():
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"
    
    mode = st.session_state.auth_mode
    
    st.markdown("""
        <style>
            .auth-container { max-width: 450px; margin: 4rem auto; background: #111111; padding: 3rem; border-radius: 16px; border: 1px solid #222; box-shadow: 0 20px 40px rgba(0,0,0,0.6); }
            .auth-header { text-align: center; margin-bottom: 2rem; }
            .auth-title { color: white; font-size: 28px; font-weight: 700; margin-bottom: 8px; }
            .auth-subtitle { color: #888; font-size: 15px; }
            .stTextInput>div>div>input { background-color: #1a1a1c !important; border: 1px solid #333 !important; color: white !important; border-radius: 8px !important; padding: 0.75rem 1rem !important; }
            .stTextInput>div>div>input:focus { border-color: #f5b03e !important; box-shadow: 0 0 0 1px #f5b03e !important; }
            .stButton>button { width: 100% !important; border-radius: 8px !important; padding: 0.75rem !important; font-weight: 600 !important; }
            .btn-primary>button { background: #f5b03e !important; color: black !important; border: none !important; }
            .btn-social>button { background: transparent !important; color: white !important; border: 1px solid #333 !important; margin-bottom: 10px !important; }
            .btn-social>button:hover { background: #1a1a1c !important; }
            .link-text { color: #f5b03e; cursor: pointer; text-decoration: none; font-size: 14px; }
            .link-text:hover { text-decoration: underline; }
            .meter { height: 4px; border-radius: 2px; margin-top: 8px; transition: 0.3s; }
            .meter-Weak { background: #ef4444; width: 33%; }
            .meter-Medium { background: #f5b03e; width: 66%; }
            .meter-Strong { background: #4ade80; width: 100%; }
            .error-text { color: #ef4444; font-size: 13px; margin-top: 4px; }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="auth-header">', unsafe_allow_html=True)
    st.markdown("""<div style="background: linear-gradient(135deg, #fcd34d, #f59e0b); color: black; font-weight: 800; font-size: 24px; width: 48px; height: 48px; display: flex; justify-content: center; align-items: center; border-radius: 12px; margin: 0 auto 1rem auto;">B</div>""", unsafe_allow_html=True)
    
    if mode == "login":
        st.markdown('<div class="auth-title">Sign in</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-subtitle">to continue to BankNova AI</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        email = st.text_input("Email", placeholder="you@example.com", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        remember = st.checkbox("Remember Me")
        
        col1, col2 = st.columns([1, 1])
        with col2:
            st.markdown('<div style="text-align: right;"><a href="#" class="link-text">Forgot Password?</a></div>', unsafe_allow_html=True)
            
        if st.button("Sign In", type="primary"):
            if not email or not password:
                st.error("Please enter both email and password.")
            else:
                with st.spinner("Signing in..."):
                    try:
                        res = requests.post(f"{API_URL}/login", data={"username": email, "password": password})
                        if res.status_code == 200:
                            data = res.json()
                            st.session_state.access_token = data["access_token"]
                            st.session_state.logged_in = True
                            st.success("Successfully logged in!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(res.json().get("detail", "Login failed"))
                    except Exception as e:
                        st.error("Something went wrong. Please try again.")
                        
        st.markdown("<div style='text-align: center; margin: 1.5rem 0; color: #666;'>OR</div>", unsafe_allow_html=True)
        st.button("Continue with Google", use_container_width=True)
        st.button("Continue with Microsoft", use_container_width=True)
        st.button("Continue with GitHub", use_container_width=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Create an account", type="secondary"):
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
            st.markdown(f"<div style='font-size: 12px; color: {color}; font-weight: 600; text-align: right;'>{strength}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='meter meter-{strength}'></div>", unsafe_allow_html=True)
            
        if password:
            errors = validate_password(password)
            for err in errors:
                st.markdown(f"<div class='error-text'>• {err}</div>", unsafe_allow_html=True)
                
        if st.button("Register", type="primary"):
            if not name or not email or not password:
                st.error("Please fill in all fields.")
            elif validate_password(password):
                st.error("Choose a stronger password.")
            else:
                with st.spinner("Creating account..."):
                    try:
                        res = requests.post(f"{API_URL}/register", json={"name": name, "email": email, "password": password})
                        if res.status_code == 200:
                            st.success("Account created! Please check your email to verify.")
                            time.sleep(2)
                            st.session_state.auth_mode = "login"
                            st.rerun()
                        else:
                            st.error(res.json().get("detail", "Registration failed"))
                    except:
                        st.error("Something went wrong. Please try again.")
                        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Already have an account? Sign In", type="secondary"):
            st.session_state.auth_mode = "login"
            st.rerun()
