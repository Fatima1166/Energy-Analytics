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


def register_user(username: str, password: str, full_name: str = "") -> dict:
    """Register a new user in dim_users with bcrypt hash."""
    from config.database import get_connection, BACKEND

    user_clean = (username or "").strip()
    if not user_clean:
        raise ValueError("Username cannot be empty.")
    if len(user_clean) < 3:
        raise ValueError("Username must be at least 3 characters long.")
    if len(password) < 4:
        raise ValueError("Password must be at least 4 characters long.")

    existing = _fetch_user(user_clean)
    if existing:
        raise ValueError(f"Username '{user_clean}' already exists. Please sign in or choose another.")

    salt = bcrypt.gensalt(rounds=12)
    pw_hash = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    display_name = (full_name or "").strip() or user_clean

    conn = get_connection()
    try:
        conn.ping(reconnect=True, attempts=3, delay=1)
    except Exception:
        get_connection.clear()
        conn = get_connection()

    cur = conn.cursor()
    try:
        if BACKEND == "sqlite":
            cur.execute(
                "INSERT INTO dim_users (user_id, username, password_hash, full_name, role, created_at) "
                "VALUES ((SELECT COALESCE(MAX(user_id), 0) + 1 FROM dim_users), %s, %s, %s, %s, datetime('now'))",
                (user_clean, pw_hash, display_name, "user"),
            )
            if hasattr(conn, "raw"):
                conn.raw.commit()
        else:
            cur.execute(
                "INSERT INTO dim_users (username, password_hash, full_name, role) "
                "VALUES (%s, %s, %s, %s)",
                (user_clean, pw_hash, display_name, "user"),
            )
            if hasattr(conn, "commit"):
                conn.commit()
    except Exception as exc:
        raise AuthBackendError(f"Database error while creating user: {exc}") from exc
    finally:
        cur.close()

    new_user = _fetch_user(user_clean)
    if not new_user:
        raise AuthBackendError("Failed to retrieve created user record.")

    return {
        "user_id": int(new_user["user_id"]),
        "username": new_user["username"],
        "full_name": new_user.get("full_name") or new_user["username"],
        "role": new_user.get("role") or "user",
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


_PAKISTAN_FLAG_SVG = (
    '<svg viewBox="0 0 900 600" width="100%" height="100%" style="display:block;border-radius:6px;overflow:hidden;">'
    '<rect width="900" height="600" fill="#01411C"/>'
    '<rect width="225" height="600" fill="#FFFFFF"/>'
    '<circle cx="535" cy="300" r="180" fill="#FFFFFF"/>'
    '<circle cx="580" cy="275" r="165" fill="#01411C"/>'
    '<polygon points="580,180 595,225 640,225 605,255 620,300 580,270 540,300 555,255 520,225 565,225" fill="#FFFFFF"/>'
    '</svg>'
)

_LOCK_SVG = (
    '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" '
    'stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>'
    '<path d="M7 11V7a5 5 0 0 1 10 0v4"></path>'
    '</svg>'
)

_MAIL_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
    'stroke="rgba(255,255,255,0.40)" stroke-width="2" stroke-linecap="round" '
    'stroke-linejoin="round"><rect width="20" height="16" x="2" y="4" rx="2"></rect>'
    '<path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"></path></svg>'
)

_KEY_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
    'stroke="rgba(255,255,255,0.40)" stroke-width="2" stroke-linecap="round" '
    'stroke-linejoin="round">'
    '<path d="M2.586 17.414A2 2 0 0 0 2 18.828V21a1 1 0 0 0 1 1h3a1 1 0 0 0 '
    '1-1v-1a1 1 0 0 1 1-1h1a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h.172a2 2 0 0 0 '
    '1.414-.586l.814-.814a6.5 6.5 0 1 0-4-4z"></path>'
    '<circle cx="16.5" cy="7.5" r=".5" fill="rgba(255,255,255,0.40)"></circle></svg>'
)

_USER_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
    'stroke="rgba(255,255,255,0.40)" stroke-width="2" stroke-linecap="round" '
    'stroke-linejoin="round">'
    '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path>'
    '<circle cx="12" cy="7" r="4"></circle></svg>'
)


_LOGIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap');

/* ---------- Hide Streamlit chrome on login screen ---------- */
header[data-testid="stHeader"],
div[data-testid="stHeader"] { display: none !important; }
section[data-testid="stSidebar"],
div[data-testid="stSidebar"],
button[data-testid="stSidebarCollapsedControl"],
div[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] { display: none !important; }
footer[data-testid="stDecoration"],
footer,
#MainMenu,
[data-testid="stToolbar"] { display: none !important; }

/* ---------- Full-bleed container reset ---------- */
html, body {
    background: #020617 !important;
    margin: 0 !important;
    padding: 0 !important;
    height: 100vh !important;
    overflow: hidden !important;
    font-family: 'Inter', sans-serif !important;
}

div[data-testid="stAppViewContainer"],
section[data-testid="stMain"],
div[data-testid="stMainBlockContainer"],
.block-container {
    padding: 0 !important;
    margin: 0 !important;
    max-width: 100% !important;
    width: 100% !important;
    height: 100vh !important;
    max-height: 100vh !important;
    overflow: hidden !important;
    background: #020617 !important;
}

div[data-testid="stAppViewContainer"] > .main {
    padding: 0 !important;
}

div[data-testid="stVerticalBlock"]:has(div[data-testid="stHorizontalBlock"]) {
    gap: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    height: 100vh !important;
}

/* ---------- Two-panel layout row ---------- */
div[data-testid="stHorizontalBlock"] {
    gap: 0 !important;
    align-items: stretch !important;
    height: 100vh !important;
    min-height: 100vh !important;
    max-height: 100vh !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    width: 100% !important;
}

div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"],
div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
    padding: 0 !important;
    height: 100vh !important;
    min-height: 100vh !important;
    max-height: 100vh !important;
    overflow: hidden !important;
}

/* Left Hero Column */
div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:first-child,
div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child {
    flex: 1.18 1 0% !important;
    min-width: 0 !important;
    height: 100vh !important;
}

/* Right Login Column */
div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:last-child,
div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:last-child {
    flex: 1 1 0% !important;
    min-width: 0 !important;
    height: 100vh !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    position: relative !important;
    background: radial-gradient(ellipse at 40% 30%, rgba(16, 185, 129, 0.12) 0%, rgba(2, 6, 23, 0.98) 75%) !important;
    padding: 32px 28px !important;
    box-sizing: border-box !important;
    overflow-y: auto !important;
}

/* Override core/styles.py vertical block stretch for login right column */
div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:last-child [data-testid="stVerticalBlock"],
div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:last-child [data-testid="stVerticalBlock"] {
    height: 100% !important;
    width: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    margin: auto 0 !important;
    gap: 0 !important;
}

div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:last-child [data-testid="stElementContainer"],
div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:last-child [data-testid="stElementContainer"] {
    height: auto !important;
    flex: 0 1 auto !important;
    width: 100% !important;
    max-width: 440px !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 0 auto !important;
}

/* ---------- floating ambient particles ---------- */
.login-particles {
    position: absolute;
    inset: 0;
    overflow: hidden;
    pointer-events: none;
    z-index: 0;
}
.particle {
    position: absolute;
    border-radius: 50%;
    pointer-events: none;
}
.particle-1 {
    width: 220px; height: 220px; top: 8%; right: 10%;
    background: radial-gradient(circle, rgba(16, 185, 129, 0.15), transparent 70%);
    animation: particle-float-1 12s ease-in-out infinite;
}
.particle-2 {
    width: 180px; height: 180px; bottom: 15%; left: 8%;
    background: radial-gradient(circle, rgba(0, 166, 251, 0.12), transparent 70%);
    animation: particle-float-2 15s ease-in-out infinite;
}
.particle-3 {
    width: 140px; height: 140px; top: 58%; right: 18%;
    background: radial-gradient(circle, rgba(52, 211, 153, 0.10), transparent 70%);
    animation: particle-float-3 10s ease-in-out infinite;
}

/* ---------- Left hero panel ---------- */
.hero-panel {
    position: relative;
    width: 100%;
    height: 100vh;
    min-height: 100vh;
    max-height: 100vh;
    overflow: hidden;
    background-color: #030b06;
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    animation: slide-in-left 0.9s ease-out;
}
.hero-overlay {
    position: absolute;
    inset: 0;
    z-index: 1;
    background: linear-gradient(
        135deg,
        rgba(2, 12, 6, 0.90) 0%,
        rgba(5, 24, 13, 0.80) 30%,
        rgba(10, 48, 28, 0.65) 60%,
        rgba(16, 185, 129, 0.35) 100%
    );
}
.hero-content {
    position: relative;
    z-index: 2;
    height: 100vh;
    max-height: 100vh;
    box-sizing: border-box;
    padding: clamp(28px, 4.5vh, 48px) clamp(32px, 4vw, 56px);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    color: #ffffff;
    overflow-y: auto;
}
.hero-logo-lockup {
    display: flex;
    align-items: center;
    gap: 14px;
}
.hero-logo-wrap {
    width: 52px;
    height: 35px;
    border-radius: 7px;
    overflow: hidden;
    background: #01411C;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.2);
}
.hero-brand-title {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    font-size: 21px !important;
    letter-spacing: -0.3px !important;
    color: #ffffff !important;
    text-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
}
.hero-main-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    max-width: 540px;
    margin: 20px 0;
}
.hero-title {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: clamp(32px, 3.2vw, 44px) !important;
    font-weight: 700 !important;
    line-height: 1.12 !important;
    margin: 0 0 16px 0 !important;
    color: transparent !important;
    background: linear-gradient(135deg, #ffffff 0%, #a7f3d0 45%, #38bdf8 100%);
    -webkit-background-clip: text !important;
    background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    animation: slide-up-fade 0.8s ease-out 0.4s both;
}
.hero-subtitle {
    font-size: 15.5px !important;
    line-height: 1.6 !important;
    color: rgba(255, 255, 255, 0.78) !important;
    max-width: 440px;
    margin: 0 !important;
    animation: slide-up-fade 0.8s ease-out 0.5s both;
}
.feature-list {
    display: flex;
    flex-direction: column;
    gap: 14px;
    margin-top: 32px;
}
.feature-item {
    display: flex;
    align-items: flex-start;
    gap: 15px;
    animation: slide-up-fade 0.8s ease-out calc(0.6s + var(--delay)) both;
}
.feature-number {
    width: 38px;
    height: 38px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 11px;
    background: rgba(16, 185, 129, 0.16);
    border: 1px solid rgba(16, 185, 129, 0.35);
    color: #34d399;
    font-size: 13px;
    font-weight: 700;
    flex-shrink: 0;
    backdrop-filter: blur(10px);
    font-family: 'Space Grotesk', sans-serif;
}
.feature-text strong {
    display: block;
    color: #ffffff;
    font-size: 14.5px;
    font-weight: 600;
    margin-bottom: 2px;
}
.feature-text small {
    display: block;
    color: rgba(255, 255, 255, 0.60);
    font-size: 12.5px;
    line-height: 1.4;
}
.hero-bottom {
    animation: slide-up-fade 0.8s ease-out 1s both;
}
.hero-bottom-line {
    width: 56px;
    height: 3px;
    border-radius: 3px;
    margin-bottom: 14px;
    background: linear-gradient(90deg, #10b981, #00A6FB);
}
.hero-bottom strong {
    display: block;
    font-size: 13.5px;
    color: #ffffff;
    margin-bottom: 3px;
}
.hero-bottom span {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.52);
}

/* ---------- Glass Login Card (Streamlit Form) ---------- */
div[data-testid="stForm"] {
    width: 100% !important;
    max-width: 440px !important;
    margin: 0 auto !important;
    position: relative !important;
    z-index: 2 !important;
    background: rgba(10, 20, 24, 0.72) !important;
    backdrop-filter: blur(40px) !important;
    -webkit-backdrop-filter: blur(40px) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 24px !important;
    padding: 38px 34px !important;
    box-shadow: 0 25px 80px rgba(0, 0, 0, 0.55),
                0 0 1px rgba(255, 255, 255, 0.15) inset,
                0 1px 0 rgba(255, 255, 255, 0.08) inset !important;
    animation: card-entrance 1.1s cubic-bezier(0.16, 1, 0.3, 1) 0.15s both !important;
}

div[data-testid="stForm"]:hover {
    border-color: rgba(16, 185, 129, 0.3) !important;
    box-shadow: 0 30px 90px rgba(0, 0, 0, 0.6),
                0 0 35px rgba(16, 185, 129, 0.12),
                0 0 1px rgba(255, 255, 255, 0.15) inset !important;
}

.login-icon-wrap {
    width: 60px;
    height: 60px;
    border-radius: 18px;
    margin-bottom: 22px;
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.22), rgba(0, 166, 251, 0.14));
    border: 1px solid rgba(52, 211, 153, 0.35);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 8px 24px rgba(16, 185, 129, 0.2);
    animation: pulse-ring 3s ease-in-out infinite;
}
.login-icon-wrap svg {
    display: block;
    width: 28px;
    height: 28px;
}

.login-form-title {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 28px !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    margin: 0 0 8px 0 !important;
    line-height: 1.2 !important;
    letter-spacing: -0.4px !important;
}
.login-form-subtitle {
    font-size: 13.5px !important;
    color: rgba(255, 255, 255, 0.55) !important;
    line-height: 1.5 !important;
    margin: 0 0 24px 0 !important;
}

/* Inputs styling & Label typography -- equal spacing & exact alignment */
div[data-testid="stForm"] [data-testid="stElementContainer"] {
    width: 100% !important;
    max-width: 100% !important;
    align-items: stretch !important;
}

div[data-testid="stForm"] div[data-testid="stTextInput"] {
    width: 100% !important;
    margin-bottom: 16px !important;
}

div[data-testid="stForm"] label,
div[data-testid="stForm"] [data-testid="stWidgetLabel"] {
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    text-align: left !important;
    margin: 0 0 6px 0 !important;
    padding: 0 !important;
    min-height: auto !important;
}

div[data-testid="stForm"] label div,
div[data-testid="stForm"] [data-testid="stWidgetLabel"] div,
div[data-testid="stForm"] [data-testid="stWidgetLabel"] [data-testid="stMarkdownContainer"] {
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    text-align: left !important;
}

div[data-testid="stForm"] label p,
div[data-testid="stForm"] [data-testid="stWidgetLabel"] p {
    font-size: 11px !important;
    font-weight: 600 !important;
    color: #94a3b8 !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.4 !important;
    font-family: 'Inter', sans-serif !important;
    text-align: left !important;
}

/* Hide Streamlit form enter instructions */
div[data-testid="InputInstructions"],
span[data-testid="InputInstructions"],
[data-testid="InputInstructions"],
div[data-testid="stTextInput"] [data-testid="InputInstructions"],
div[data-testid="stTextInput"] div:has(> span:empty) {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    height: 0 !important;
    width: 0 !important;
    pointer-events: none !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* Outer input container - identical 48px height, rounded border & dark backdrop for both inputs */
div[data-testid="stForm"] div[data-baseweb="input"] {
    background-color: rgba(255, 255, 255, 0.04) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 14px !important;
    display: flex !important;
    align-items: center !important;
    box-shadow: none !important;
    transition: all 0.3s ease !important;
    overflow: hidden !important;
    height: 48px !important;
    min-height: 48px !important;
    max-height: 48px !important;
    width: 100% !important;
    box-sizing: border-box !important;
    padding: 0 !important;
    margin: 0 !important;
}

div[data-testid="stForm"] div[data-baseweb="input"]:focus-within {
    border-color: #10b981 !important;
    background-color: rgba(16, 185, 129, 0.06) !important;
    box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.15), 0 0 20px rgba(16, 185, 129, 0.1) !important;
}

/* Inner containers - transparent so outer container styling rules */
div[data-testid="stForm"] div[data-baseweb="input"] > div,
div[data-testid="stForm"] div[data-baseweb="base-input"] {
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    height: 100% !important;
    display: flex !important;
    align-items: center !important;
    box-sizing: border-box !important;
}

div[data-testid="stForm"] div[data-baseweb="base-input"] {
    flex: 1 1 auto !important;
    width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
}

div[data-testid="stForm"] div[data-testid="stTextInput"] input {
    width: 100% !important;
    flex: 1 1 auto !important;
    height: 100% !important;
    min-height: 46px !important;
    padding: 0 16px 0 44px !important;
    background-color: transparent !important;
    border: none !important;
    color: #ffffff !important;
    font-size: 14px !important;
    font-family: 'Inter', sans-serif !important;
    box-shadow: none !important;
    outline: none !important;
    box-sizing: border-box !important;
    background-repeat: no-repeat !important;
    background-position: 14px center !important;
    background-size: 18px 18px !important;
}

/* Browser autofill override so password / username autofill doesn't discolor */
div[data-testid="stForm"] input:-webkit-autofill,
div[data-testid="stForm"] input:-webkit-autofill:hover,
div[data-testid="stForm"] input:-webkit-autofill:focus,
div[data-testid="stForm"] input:-webkit-autofill:active {
    -webkit-box-shadow: 0 0 0 1000px #0b1a13 inset !important;
    -webkit-text-fill-color: #ffffff !important;
    transition: background-color 5000s ease-in-out 0s !important;
    caret-color: #ffffff !important;
}

div[data-testid="stForm"] input[placeholder="Enter your full name"] {
    background-image: url("__USER__") !important;
}

div[data-testid="stForm"] input:not([type="password"]):not([placeholder="Enter your full name"]) {
    background-image: url("__MAIL__") !important;
}

div[data-testid="stForm"] input[type="password"] {
    background-image: url("__KEY__") !important;
}

div[data-testid="stForm"] div[data-testid="stTextInput"] input::placeholder {
    color: rgba(255, 255, 255, 0.28) !important;
}

/* Password eye button -- seamlessly integrated inside the outer container */
div[data-testid="stForm"] div[data-testid="stTextInput"] button,
div[data-testid="stForm"] div[data-baseweb="input"] button,
div[data-testid="stForm"] div[data-baseweb="base-input"] button {
    width: 36px !important;
    height: 36px !important;
    min-width: 36px !important;
    max-width: 36px !important;
    padding: 0 !important;
    margin: 0 6px 0 0 !important;
    background: transparent !important;
    border: none !important;
    border-radius: 8px !important;
    box-shadow: none !important;
    transform: none !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    color: rgba(255, 255, 255, 0.45) !important;
    cursor: pointer !important;
    transition: color 0.2s ease, background 0.2s ease !important;
    flex-shrink: 0 !important;
}

div[data-testid="stForm"] div[data-testid="stTextInput"] button:hover,
div[data-testid="stForm"] div[data-baseweb="input"] button:hover,
div[data-testid="stForm"] div[data-baseweb="base-input"] button:hover {
    background: rgba(255, 255, 255, 0.08) !important;
    color: #10b981 !important;
    transform: none !important;
    box-shadow: none !important;
}

div[data-testid="stForm"] div[data-testid="stTextInput"] button svg,
div[data-testid="stForm"] div[data-baseweb="input"] button svg,
div[data-testid="stForm"] div[data-baseweb="base-input"] button svg {
    width: 18px !important;
    height: 18px !important;
    color: inherit !important;
    stroke: currentColor !important;
}

/* Form Submit Button -- Centered Sign In Action */
div[data-testid="stFormSubmitButton"] {
    margin-top: 6px !important;
    margin-bottom: 0 !important;
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

div[data-testid="stFormSubmitButton"] > button {
    width: 100% !important;
    padding: 0 24px !important;
    height: 48px !important;
    min-height: 48px !important;
    max-height: 48px !important;
    box-sizing: border-box !important;
    background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
    border: 1px solid rgba(52, 211, 153, 0.35) !important;
    border-radius: 14px !important;
    color: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    box-shadow: 0 8px 24px rgba(16, 185, 129, 0.3) !important;
    transform: none !important;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    cursor: pointer !important;
}

div[data-testid="stFormSubmitButton"] > button:hover {
    background: linear-gradient(135deg, #34d399 0%, #10b981 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 14px 32px rgba(16, 185, 129, 0.45), 0 0 25px rgba(16, 185, 129, 0.25) !important;
}

div[data-testid="stFormSubmitButton"] > button:active {
    transform: translateY(0) !important;
}

div[data-testid="stFormSubmitButton"] > button div[data-testid="stMarkdownContainer"],
div[data-testid="stFormSubmitButton"] > button div {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    width: 100% !important;
    margin: 0 auto !important;
    padding: 0 !important;
}

div[data-testid="stFormSubmitButton"] > button p {
    color: #ffffff !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    margin: 0 auto !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    width: auto !important;
    line-height: 1 !important;
}

div[data-testid="stFormSubmitButton"] > button p::after {
    content: ' \\2192' !important;
    display: inline-block !important;
    margin-left: 8px !important;
    transition: transform 0.2s ease !important;
}

div[data-testid="stFormSubmitButton"] > button:hover p::after {
    transform: translateX(4px) !important;
}

/* Error message */
.error-message {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 14px;
    margin-bottom: 16px;
    background: rgba(239, 68, 68, 0.12);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 12px;
    color: #fca5a5;
    font-size: 13px;
    line-height: 1.4;
    animation: slide-up-fade 0.3s ease-out;
}

/* Security badge */
.security-badge {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    margin-top: 22px;
    font-size: 11.5px;
    color: rgba(255, 255, 255, 0.45);
    font-family: 'Inter', sans-serif;
}

.security-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #10b981;
    box-shadow: 0 0 8px rgba(16, 185, 129, 0.7);
    animation: pulse-ring 2s ease-in-out infinite;
}

/* ---------- Keyframe animations ---------- */
@keyframes slide-up-fade {
    from { opacity: 0; transform: translateY(30px) scale(0.97); }
    to   { opacity: 1; transform: translateY(0) scale(1); }
}
@keyframes slide-in-left {
    from { opacity: 0; transform: translateX(-40px); }
    to   { opacity: 1; transform: translateX(0); }
}
@keyframes card-entrance {
    from { opacity: 0; transform: translateY(20px) scale(0.95); }
    to   { opacity: 1; transform: translateY(0) scale(1); }
}
@keyframes pulse-ring {
    0%   { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.5); }
    70%  { transform: scale(1);    box-shadow: 0 0 0 12px rgba(16, 185, 129, 0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}
@keyframes particle-float-1 {
    0%, 100% { transform: translate(0, 0) scale(1); opacity: 0.4; }
    25% { transform: translate(80px, -60px) scale(1.15); opacity: 0.65; }
    50% { transform: translate(40px, -120px) scale(0.85); opacity: 0.3; }
    75% { transform: translate(-20px, -70px) scale(1.05); opacity: 0.55; }
}
@keyframes particle-float-2 {
    0%, 100% { transform: translate(0, 0) scale(0.85); opacity: 0.3; }
    33% { transform: translate(-60px, -90px) scale(1.2); opacity: 0.55; }
    66% { transform: translate(50px, -45px) scale(0.9); opacity: 0.45; }
}
@keyframes particle-float-3 {
    0%, 100% { transform: translate(0, 0) scale(1.05); opacity: 0.45; }
    50% { transform: translate(90px, -75px) scale(0.75); opacity: 0.25; }
}
</style>
"""

_HERO_HTML = (
    '<div class="hero-overlay"></div>'
    '<div class="hero-content">'
    '<div class="hero-logo-lockup">'
    f'<div class="hero-logo-wrap">{_PAKISTAN_FLAG_SVG}</div>'
    '<span class="hero-brand-title">Pakistan Energy</span>'
    '</div>'
    '<div class="hero-main-content">'
    '<h1 class="hero-title">Outlook &amp; Renewable<br>Impact Dashboard</h1>'
    '<p class="hero-subtitle">Data-driven insights for a sustainable energy future. '
    'Monitor, analyze, and transform Pakistan&rsquo;s energy landscape.</p>'
    '<div class="feature-list">'
    '<div class="feature-item" style="--delay:0s">'
    '<div class="feature-number">01</div>'
    '<div class="feature-text"><strong>Energy Supply</strong><small>Track primary and secondary energy sources</small></div>'
    '</div>'
    '<div class="feature-item" style="--delay:0.15s">'
    '<div class="feature-number">02</div>'
    '<div class="feature-text"><strong>Renewable Impact</strong><small>Monitor clean energy growth and share</small></div>'
    '</div>'
    '<div class="feature-item" style="--delay:0.3s">'
    '<div class="feature-number">03</div>'
    '<div class="feature-text"><strong>Sustainability</strong><small>Build a cleaner, greener Pakistan</small></div>'
    '</div>'
    '</div>'
    '</div>'
    '<div class="hero-bottom">'
    '<div class="hero-bottom-line"></div>'
    '<strong>Powering a cleaner, greener Pakistan</strong>'
    '<span>Insight today. Impact tomorrow.</span>'
    '</div>'
    '</div>'
)

_SIGNIN_CARD_HEAD = (
    '<div class="login-icon-wrap">' + _LOCK_SVG + '</div>'
    '<h2 class="login-form-title">Welcome Back</h2>'
    '<p class="login-form-subtitle">Sign in to access the Pakistan Energy<br>'
    'Outlook &amp; Renewable Impact Dashboard</p>'
)

_SECURITY_BADGE_HTML = (
    '<div class="security-badge"><span class="security-dot"></span>'
    'Protected access &middot; bcrypt encrypted credentials</div>'
)


def render_login_page() -> None:
    """Full-screen login screen -- the single entry point of the app."""
    css = (_LOGIN_CSS
           .replace("__MAIL__", _svg_uri(_MAIL_SVG))
           .replace("__KEY__", _svg_uri(_KEY_SVG))
           .replace("__USER__", _svg_uri(_USER_SVG)))
    st.markdown(css, unsafe_allow_html=True)

    hero_uri = _hero_uri()
    style = f' style="background-image:url(\'{hero_uri}\')"' if hero_uri else ""

    left, right = st.columns([1.18, 1], gap="small")

    with left:
        st.markdown(f'<div class="hero-panel"{style}>{_HERO_HTML}</div>', unsafe_allow_html=True)

    with right:
        st.markdown(
            '<div class="login-particles">'
            '<span class="particle particle-1"></span>'
            '<span class="particle particle-2"></span>'
            '<span class="particle particle-3"></span>'
            '</div>',
            unsafe_allow_html=True
        )

        error = st.session_state.pop(ERROR_KEY, None)

        with st.form("login_form", clear_on_submit=False):
            st.markdown(_SIGNIN_CARD_HEAD, unsafe_allow_html=True)

            if error:
                st.markdown(
                    '<div class="error-message"><span>&#9888;</span>'
                    f'<span>{error}</span></div>',
                    unsafe_allow_html=True
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

            st.markdown(_SECURITY_BADGE_HTML, unsafe_allow_html=True)

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
