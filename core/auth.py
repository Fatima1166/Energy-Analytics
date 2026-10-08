"""
core/auth.py -- login gate for the dashboard.

The app shows the login screen first and renders the dashboard only after a
bcrypt check against MySQL `dim_users`:
    http://localhost:8501  ->  login  ->  dashboard
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional

import bcrypt
import streamlit as st

SESSION_USER = "auth_user"
ERROR_KEY = "login_error"

_HERO_IMAGE = Path(__file__).resolve().parents[1] / "assets" / "login_hero.jpg"


class AuthBackendError(Exception):
    """Raised when the users table cannot be reached."""


# ---------------------------------------------------------------------------
# Credential check (same dim_users table and bcrypt algorithm as before)
# ---------------------------------------------------------------------------
def _fetch_user(username: str) -> Optional[dict]:
    from config.database import get_connection

    conn = get_connection()
    try:
        conn.ping(reconnect=True, attempts=3, delay=1)
    except Exception:
        get_connection.clear()
        conn = get_connection()

    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            "SELECT user_id, username, password_hash, full_name, role "
            "FROM dim_users WHERE username = %s LIMIT 1",
            (username,),
        )
        return cur.fetchone()
    finally:
        cur.close()


def verify_credentials(username: str, password: str) -> Optional[dict]:
    """User dict on success, None on bad credentials, AuthBackendError if MySQL is down."""
    try:
        row = _fetch_user(username)
    except Exception as exc:                      # noqa: BLE001
        raise AuthBackendError(
            "Could not reach the MySQL server. Start MySQL (XAMPP), check the "
            ".env credentials, then try again."
        ) from exc

    if not row:
        return None

    stored = str(row.get("password_hash") or "")
    try:
        ok = bcrypt.checkpw(password.encode("utf-8"), stored.encode("utf-8"))
    except (ValueError, TypeError):
        ok = False
    if not ok:
        return None

    return {
        "user_id": int(row["user_id"]),
        "username": row["username"],
        "full_name": row.get("full_name") or row["username"],
        "role": row.get("role") or "user",
    }


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------
def current_user() -> Optional[dict]:
    user = st.session_state.get(SESSION_USER)
    return user if isinstance(user, dict) else None


def is_authenticated() -> bool:
    return current_user() is not None


def login(user: dict) -> None:
    st.session_state[SESSION_USER] = user


def logout() -> None:
    st.session_state.pop(SESSION_USER, None)


# ---------------------------------------------------------------------------
# Login screen
# ---------------------------------------------------------------------------
def _svg_uri(svg: str) -> str:
    """Inline an SVG icon as a CSS background-image."""
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")


@st.cache_data(show_spinner=False)
def _hero_uri() -> str:
    """The hero photo as a data URI (cached, so the file is read only once)."""
    try:
        raw = _HERO_IMAGE.read_bytes()
    except OSError:
        return ""
    return "data:image/jpeg;base64," + base64.b64encode(raw).decode("ascii")


_LOCK_SVG = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' "
             "stroke='%2393c5fd' stroke-width='2' stroke-linecap='round' "
             "stroke-linejoin='round'><rect width='18' height='11' x='3' y='11' rx='2'/>"
             "<path d='M7 11V7a5 5 0 0 1 10 0v4'/></svg>")

_MAIL_SVG = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' "
             "stroke='rgba(255,255,255,0.30)' stroke-width='2' stroke-linecap='round' "
             "stroke-linejoin='round'><rect width='20' height='16' x='2' y='4' rx='2'/>"
             "<path d='m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7'/></svg>")

_KEY_SVG = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' "
            "stroke='rgba(255,255,255,0.30)' stroke-width='2' stroke-linecap='round' "
            "stroke-linejoin='round'>"
            "<path d='M2.586 17.414A2 2 0 0 0 2 18.828V21a1 1 0 0 0 1 1h3a1 1 0 0 0 "
            "1-1v-1a1 1 0 0 1 1-1h1a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h.172a2 2 0 0 0 "
            "1.414-.586l.814-.814a6.5 6.5 0 1 0-4-4z'/>"
            "<circle cx='16.5' cy='7.5' r='.5' fill='rgba(255,255,255,0.30)'/></svg>")


_LOGIN_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap" rel="stylesheet">
<style>
/* ---------- full-bleed login page ---------- */
header[data-testid="stHeader"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }
div[data-testid="stAppViewContainer"] { background: #020617 !important; }
div[data-testid="stAppViewContainer"] > section.main > div.block-container,
.block-container {
    padding: 0 !important; margin: 0 !important; max-width: 100% !important;
}

/* ---------- two-panel row ---------- */
div[data-testid="stHorizontalBlock"]:has(.hero-panel) {
    gap: 0 !important; align-items: stretch !important;
}
div[data-testid="stHorizontalBlock"]:has(.hero-panel) > div[data-testid="column"] {
    padding: 0 !important; min-height: 100vh;
}
div[data-testid="stHorizontalBlock"]:has(.hero-panel) > div[data-testid="column"]:nth-child(2) {
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    padding: 40px 32px !important; position: relative; overflow: hidden;
    background: radial-gradient(ellipse at 30% 20%, rgba(37,99,235,0.08) 0%, #020617 70%);
}

/* ---------- floating particles behind the card ---------- */
.login-particles { position: absolute; inset: 0; overflow: hidden; pointer-events: none; z-index: 0; }
.particle { position: absolute; border-radius: 50%; pointer-events: none; }
.particle-1 { width: 200px; height: 200px; top: 10%; right: 10%;
    background: radial-gradient(circle, rgba(37,99,235,0.12), transparent 70%);
    animation: particle-float-1 12s ease-in-out infinite; }
.particle-2 { width: 150px; height: 150px; bottom: 20%; left: 5%;
    background: radial-gradient(circle, rgba(6,182,212,0.10), transparent 70%);
    animation: particle-float-2 15s ease-in-out infinite; }
.particle-3 { width: 120px; height: 120px; top: 60%; right: 20%;
    background: radial-gradient(circle, rgba(139,92,246,0.08), transparent 70%);
    animation: particle-float-3 10s ease-in-out infinite; }

/* ---------- left hero panel ---------- */
.hero-panel {
    position: relative; width: 100%; min-height: 100vh; overflow: hidden;
    background-size: cover; background-position: center; background-repeat: no-repeat;
    animation: slide-in-left 1s ease-out;
}
.hero-overlay {
    position: absolute; inset: 0; z-index: 1;
    background: linear-gradient(135deg, rgba(10,17,40,0.88) 0%, rgba(15,26,62,0.75) 30%,
                rgba(30,58,95,0.60) 60%, rgba(37,99,235,0.35) 100%);
}
.hero-content {
    position: relative; z-index: 2; min-height: 100vh; box-sizing: border-box;
    padding: 48px 56px; display: flex; flex-direction: column;
    justify-content: space-between; color: #fff;
    font-family: 'Inter', sans-serif;
}
.hero-logo-lockup { display: flex; align-items: center; gap: 14px; }
.hero-logo-wrap {
    width: 84px; height: 36px; border-radius: 8px; overflow: hidden; background: #fff;
    display: flex; align-items: center; justify-content: center; flex-shrink: 0;
    box-shadow: 0 8px 30px rgba(0,0,0,0.3); font-size: 20px;
}
.hero-brand-title {
    font-family: 'Space Grotesk', sans-serif !important; font-weight: 700 !important;
    font-size: 20px !important; color: #fff !important;
    text-shadow: 0 2px 10px rgba(0,0,0,0.4);
}
.hero-main-content { flex: 1; display: flex; flex-direction: column; justify-content: center; max-width: 520px; }
.hero-title {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 44px !important; font-weight: 700 !important; line-height: 1.1 !important;
    margin: 0 0 20px 0 !important; color: transparent !important;
    background: linear-gradient(135deg, #ffffff 0%, #93c5fd 50%, #06b6d4 100%);
    -webkit-background-clip: text !important; background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    animation: slide-up-fade 0.8s ease-out 0.6s both;
}
.hero-subtitle {
    font-size: 16px !important; line-height: 1.6 !important;
    color: rgba(255,255,255,0.75) !important; max-width: 400px; margin: 0 !important;
    animation: slide-up-fade 0.8s ease-out 0.7s both;
}
.feature-list { display: flex; flex-direction: column; gap: 16px; margin-top: 40px; }
.feature-item {
    display: flex; align-items: flex-start; gap: 16px;
    animation: slide-up-fade 0.8s ease-out calc(0.8s + var(--delay)) both;
}
.feature-number {
    width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;
    border-radius: 12px; background: rgba(37,99,235,0.2);
    border: 1px solid rgba(37,99,235,0.3); color: #60a5fa;
    font-size: 13px; font-weight: 700; flex-shrink: 0; backdrop-filter: blur(10px);
    font-family: 'Inter', sans-serif;
}
.feature-text strong { display: block; color: #fff; font-size: 15px; font-weight: 600; margin-bottom: 2px; }
.feature-text small  { display: block; color: rgba(255,255,255,0.55); font-size: 13px; line-height: 1.4; }
.hero-bottom { animation: slide-up-fade 0.8s ease-out 1.3s both; }
.hero-bottom-line {
    width: 60px; height: 2px; border-radius: 2px; margin-bottom: 16px;
    background: linear-gradient(90deg, #2563eb, #06b6d4);
}
.hero-bottom strong { display: block; font-size: 14px; color: #fff; margin-bottom: 4px; }
.hero-bottom span   { font-size: 12px; color: rgba(255,255,255,0.5); }

/* ---------- right panel: glass login card (the Streamlit form) ---------- */
div[data-testid="stForm"] {
    width: 100% !important; max-width: 420px !important;
    position: relative; z-index: 2;
    background: rgba(15,26,62,0.5) !important;
    backdrop-filter: blur(40px); -webkit-backdrop-filter: blur(40px);
    border: 1px solid rgba(255,255,255,0.10) !important;
    border-radius: 24px !important;
    padding: 44px 36px !important;
    box-shadow: 0 25px 80px rgba(0,0,0,0.4),
                0 0 1px rgba(255,255,255,0.10) inset,
                0 1px 0 rgba(255,255,255,0.06) inset;
    animation: card-entrance 1.2s cubic-bezier(0.16,1,0.3,1) 0.2s both;
}
.login-icon-wrap {
    width: 64px; height: 64px; border-radius: 20px; margin-bottom: 28px;
    background: linear-gradient(135deg, rgba(37,99,235,0.25), rgba(6,182,212,0.15));
    border: 1px solid rgba(37,99,235,0.3);
    display: flex; align-items: center; justify-content: center;
    animation: pulse-ring 3s ease-in-out infinite;
}
.login-icon-wrap svg { width: 28px; height: 28px; }
.login-form-title {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 28px !important; font-weight: 700 !important;
    color: #fff !important; margin: 0 0 8px 0 !important; line-height: 1.2 !important;
}
.login-form-subtitle {
    font-size: 14px !important; color: rgba(255,255,255,0.5) !important;
    line-height: 1.5 !important; margin: 0 0 8px 0 !important;
}

/* inputs */
div[data-testid="stForm"] div[data-testid="stWidgetLabel"] p {
    font-size: 12px !important; font-weight: 600 !important;
    color: rgba(255,255,255,0.5) !important;
    text-transform: uppercase !important; letter-spacing: 1.5px !important;
}
div[data-testid="stForm"] div[data-testid="stTextInput"] { margin-bottom: 12px !important; }
div[data-testid="stForm"] div[data-baseweb="input"],
div[data-testid="stForm"] div[data-baseweb="base-input"] {
    background: transparent !important; border: none !important; box-shadow: none !important;
}
div[data-testid="stForm"] div[data-testid="stTextInput"] input {
    width: 100% !important;
    padding: 14px 16px 14px 48px !important;
    background-color: rgba(255,255,255,0.04) !important;
    background-repeat: no-repeat !important;
    background-position: 16px center !important;
    background-size: 18px 18px !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    border-radius: 14px !important;
    color: #fff !important; font-size: 14px !important;
    font-family: 'Inter', sans-serif !important;
    box-shadow: none !important; outline: none !important;
    transition: all 0.3s ease;
}
div[data-testid="stForm"] input[placeholder="Enter your username"] { background-image: url("__MAIL__") !important; }
div[data-testid="stForm"] input[placeholder="Enter your password"] { background-image: url("__KEY__") !important; }
div[data-testid="stForm"] div[data-testid="stTextInput"] input::placeholder { color: rgba(255,255,255,0.25) !important; }
div[data-testid="stForm"] div[data-testid="stTextInput"] input:focus {
    border-color: #2563eb !important;
    background-color: rgba(37,99,235,0.06) !important;
    box-shadow: 0 0 0 4px rgba(37,99,235,0.12), 0 0 20px rgba(37,99,235,0.08) !important;
}

/* submit button */
div[data-testid="stForm"] button {
    width: 100% !important; margin-top: 12px !important;
    padding: 16px !important;
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
    border: 1px solid rgba(59,130,246,0.3) !important;
    border-radius: 14px !important; color: #fff !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important; font-size: 15px !important;
    box-shadow: none !important; transform: none !important;
    transition: all 0.4s cubic-bezier(0.16,1,0.3,1) !important;
}
div[data-testid="stForm"] button:hover {
    transform: translateY(-2px) !important;
    background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
    box-shadow: 0 15px 40px rgba(37,99,235,0.35), 0 0 20px rgba(37,99,235,0.2) !important;
}
div[data-testid="stForm"] button p::after { content: ' \\2192'; }

/* error + badge */
.error-message {
    display: flex; align-items: center; gap: 10px;
    padding: 14px 16px; margin-bottom: 20px;
    background: rgba(239,68,68,0.10); border: 1px solid rgba(239,68,68,0.25);
    border-radius: 12px; color: #fca5a5; font-size: 13px; line-height: 1.4;
    animation: slide-up-fade 0.3s ease-out;
}
.security-badge {
    display: flex; align-items: center; justify-content: center; gap: 8px;
    margin-top: 28px; font-size: 11px; color: rgba(255,255,255,0.3);
    font-family: 'Inter', sans-serif;
}
.security-dot {
    width: 6px; height: 6px; border-radius: 50%; background: #10b981;
    box-shadow: 0 0 8px rgba(16,185,129,0.5);
    animation: pulse-ring 2s ease-in-out infinite;
}

/* ---------- animations (from the original stylesheet) ---------- */
@keyframes slide-up-fade { from { opacity: 0; transform: translateY(40px) scale(0.95); }
                           to   { opacity: 1; transform: translateY(0) scale(1); } }
@keyframes slide-in-left { from { opacity: 0; transform: translateX(-60px); }
                           to   { opacity: 1; transform: translateX(0); } }
@keyframes card-entrance { from { opacity: 0; transform: perspective(1200px) rotateY(15deg) rotateX(10deg) translateZ(-100px) scale(0.8); }
                           to   { opacity: 1; transform: perspective(1200px) rotateY(0deg) rotateX(0deg) translateZ(0) scale(1); } }
@keyframes pulse-ring { 0%   { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(37,99,235,0.5); }
                        70%  { transform: scale(1);    box-shadow: 0 0 0 15px rgba(37,99,235,0); }
                        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(37,99,235,0); } }
@keyframes glow-pulse { 0%,100% { box-shadow: 0 25px 80px rgba(0,0,0,0.4); }
                        50%     { box-shadow: 0 25px 80px rgba(0,0,0,0.4), 0 0 40px rgba(37,99,235,0.15); } }
@keyframes particle-float-1 { 0%,100% { transform: translate(0,0) scale(1); opacity: 0.4; }
                              25% { transform: translate(100px,-80px) scale(1.2); opacity: 0.7; }
                              50% { transform: translate(50px,-150px) scale(0.8); opacity: 0.3; }
                              75% { transform: translate(-30px,-100px) scale(1.1); opacity: 0.6; } }
@keyframes particle-float-2 { 0%,100% { transform: translate(0,0) scale(0.8); opacity: 0.3; }
                              33% { transform: translate(-80px,-120px) scale(1.3); opacity: 0.6; }
                              66% { transform: translate(60px,-60px) scale(0.9); opacity: 0.5; } }
@keyframes particle-float-3 { 0%,100% { transform: translate(0,0) scale(1.1); opacity: 0.5; }
                              50% { transform: translate(120px,-100px) scale(0.7); opacity: 0.3; } }
</style>
"""

_HERO_HTML = """
<div class="hero-overlay"></div>
<div class="hero-content">
  <div class="hero-logo-lockup">
    <div class="hero-logo-wrap">&#127477;&#127472;</div>
    <span class="hero-brand-title">Pakistan Energy</span>
  </div>

  <div class="hero-main-content">
    <h1 class="hero-title">Outlook &amp; Renewable<br>Impact Dashboard</h1>
    <p class="hero-subtitle">Data-driven insights for a sustainable energy future.
      Monitor, analyze, and transform Pakistan&rsquo;s energy landscape.</p>

    <div class="feature-list">
      <div class="feature-item" style="--delay:0s">
        <div class="feature-number">01</div>
        <div class="feature-text"><strong>Energy Supply</strong>
          <small>Track primary and secondary energy sources</small></div>
      </div>
      <div class="feature-item" style="--delay:0.15s">
        <div class="feature-number">02</div>
        <div class="feature-text"><strong>Renewable Impact</strong>
          <small>Monitor clean energy growth and share</small></div>
      </div>
      <div class="feature-item" style="--delay:0.3s">
        <div class="feature-number">03</div>
        <div class="feature-text"><strong>Sustainability</strong>
          <small>Build a cleaner, greener Pakistan</small></div>
      </div>
    </div>
  </div>

  <div class="hero-bottom">
    <div class="hero-bottom-line"></div>
    <strong>Powering a cleaner, greener Pakistan</strong>
    <span>Insight today. Impact tomorrow.</span>
  </div>
</div>
"""

_CARD_HEAD = (
    '<div class="login-icon-wrap">' + _LOCK_SVG.replace("%2393c5fd", "#93c5fd") + '</div>'
    '<h2 class="login-form-title">Welcome Back</h2>'
    '<p class="login-form-subtitle">Sign in to access the Pakistan Energy<br>'
    'Outlook &amp; Renewable Impact Dashboard</p>'
)


def render_login_page() -> None:
    """Full-screen login screen -- the single entry point of the app."""
    css = (_LOGIN_CSS
           .replace("__MAIL__", _svg_uri(_MAIL_SVG))
           .replace("__KEY__", _svg_uri(_KEY_SVG)))
    st.markdown(css, unsafe_allow_html=True)

    hero_uri = _hero_uri()
    style = f' style="background-image:url(\'{hero_uri}\')"' if hero_uri else ""

    left, right = st.columns([1.22, 1])

    with left:
        st.markdown(f'<div class="hero-panel"{style}>{_HERO_HTML}</div>',
                    unsafe_allow_html=True)

    with right:
        st.markdown(
            '<div class="login-particles">'
            '<span class="particle particle-1"></span>'
            '<span class="particle particle-2"></span>'
            '<span class="particle particle-3"></span>'
            '</div>',
            unsafe_allow_html=True,
        )

        error = st.session_state.pop(ERROR_KEY, None)

        with st.form("login_form", clear_on_submit=False):
            st.markdown(_CARD_HEAD, unsafe_allow_html=True)
            if error:
                st.markdown(
                    '<div class="error-message"><span>&#9888;</span>'
                    f'<span>{error}</span></div>',
                    unsafe_allow_html=True,
                )

            username = st.text_input(
                "Username", placeholder="Enter your username",
                autocomplete="username",
            )
            password = st.text_input(
                "Password", type="password", placeholder="Enter your password",
                autocomplete="current-password",
            )
            submitted = st.form_submit_button("Sign In", use_container_width=True)

            if submitted:
                user_in = (username or "").strip()
                if not user_in or not password:
                    st.session_state[ERROR_KEY] = "Please enter both username and password."
                    st.rerun()
                else:
                    try:
                        user = verify_credentials(user_in, password)
                    except AuthBackendError as exc:
                        st.session_state[ERROR_KEY] = str(exc)
                        st.rerun()
                    else:
                        if user:
                            login(user)
                            st.rerun()
                        st.session_state[ERROR_KEY] = "Invalid credentials. Please try again."
                        st.rerun()

        st.markdown(
            '<div class="security-badge"><span class="security-dot"></span>'
            'Protected access &middot; bcrypt encrypted credentials</div>',
            unsafe_allow_html=True,
        )


def render_user_chip() -> bool:
    """Sidebar identity block + Logout. Returns True when Logout was clicked."""
    user = current_user() or {}
    name = user.get("full_name") or user.get("username") or "User"
    uname = user.get("username") or ""
    role = (user.get("role") or "").upper()

    st.sidebar.markdown(
        f'<div style="display:flex;align-items:center;gap:10px;'
        f'padding:6px 4px 8px;">'
        f'<div style="width:34px;height:34px;border-radius:10px;flex-shrink:0;'
        f'display:flex;align-items:center;justify-content:center;font-size:14px;'
        f'background:linear-gradient(135deg,rgba(46,204,113,0.20),rgba(0,166,251,0.14));'
        f'border:1px solid rgba(46,204,113,0.30);color:#2ECC71;">&#128100;</div>'
        f'<div style="min-width:0;">'
        f'<div style="color:#E2E8F0;font-size:12.5px;font-weight:600;'
        f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{name}</div>'
        f'<div style="color:#5C677D;font-size:10px;">{uname} &middot; {role}</div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        "<style>"
        "section[data-testid='stSidebar'] .stButton > button {"
        "background:rgba(255,255,255,0.06) !important;"
        "box-shadow:none !important; color:#C8CDD6 !important;"
        "border:1px solid rgba(255,255,255,0.10) !important;"
        "font-weight:600 !important; font-size:12px !important;"
        "padding:6px 12px !important;}"
        "section[data-testid='stSidebar'] .stButton > button:hover {"
        "background:rgba(239,68,68,0.16) !important; color:#FCA5A5 !important;"
        "border-color:rgba(239,68,68,0.35) !important; transform:none !important;}"
        "</style>",
        unsafe_allow_html=True,
    )
    return st.sidebar.button("Logout", key="logout_btn", use_container_width=True)
