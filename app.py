import streamlit as st

from config.settings import APP_TITLE, APP_SUBTITLE, APP_ICON, LOGIN_MODE
from core.auth import (
    current_user,
    is_authenticated,
    logout,
    render_login_page,
    render_user_chip,
)
from core.styles import inject_css
from core.icons import icon
from core.unit_slicer import render_sidebar_unit_slicer
from dashboards.registry import DASHBOARDS, load_dashboard_module

# ---------------- Page Config ----------------
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",

    initial_sidebar_state="expanded",
    
)
inject_css()

# ---------------- Login gate ----------------
# LOGIN_MODE = "react"     -> the React portal (:5173) logs the user in, this app
#                             is embedded in it, so no second login is asked.
# LOGIN_MODE = "streamlit" -> the built-in login screen below protects :8501.
if LOGIN_MODE == "streamlit" and not is_authenticated():
    render_login_page()
    st.stop()

# ---------------- Sidebar: signed-in user + dashboard selector ----------------
if current_user() is not None:
    if render_user_chip():
        logout()
        st.rerun()
    st.sidebar.divider()

st.sidebar.markdown(
    '<div style="color:#8B95A7;font-size:11px;text-transform:uppercase;'
    'letter-spacing:1px;padding:4px 12px 8px;">Dashboards</div>',
    unsafe_allow_html=True
)

labels = [d["label"] for d in DASHBOARDS]

# Check query parameters (e.g. from home card arrow clicks ?nav=q1)
if "nav" in st.query_params:
    target_q = st.query_params.get("nav")
    matched_dash = next((d for d in DASHBOARDS if d["key"].lower() == str(target_q).lower() or d["label"] == target_q), None)
    if matched_dash:
        st.session_state["nav_pending"] = matched_dash["label"]
    try:
        st.query_params.clear()
    except Exception:
        pass

# The Energy Overview home tiles ask for a dashboard by st.session_state
# ["nav_pending"]; we must apply it BEFORE the selectbox is instantiated
# (widget-state writes are rejected after the widget exists in a run).
_pending_nav = st.session_state.pop("nav_pending", None)
if _pending_nav and _pending_nav in labels:
    st.session_state["nav_selector"] = _pending_nav
selected_label = st.sidebar.selectbox("nav", labels, label_visibility="collapsed",
                                      key="nav_selector")
selected = next(d for d in DASHBOARDS if d["label"] == selected_label)

st.sidebar.divider()

# ---------------- Header (dynamic per dashboard) ----------------
# The landing Home dashboard renders its own full-width executive command header.
if selected.get("key") != "home":
    dash_title    = selected.get("title",    APP_TITLE)
    dash_subtitle = selected.get("subtitle", APP_SUBTITLE)
    dash_icon     = selected.get("icon",     "overview")

    st.markdown(
        f'<div class="top-header">'
        f'<div class="header-icon">{icon(dash_icon)}</div>'
        f'<div>'
        f'<h1>{dash_title}</h1>'
        f'<p>{dash_subtitle}</p>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )

dashboard_module = load_dashboard_module(selected["module"])

# ---------------- 1. Dashboard's own slicers (Scenario, Growth Rate, Year Range) ---
sidebar_fn = getattr(dashboard_module, "sidebar", None)
if callable(sidebar_fn):
    sidebar_fn()

# ---------------- 2. Global unit selection ----------------
# Only the unit families this dashboard actually renders are offered.
# On the landing page, the Home sidebar handles unit controls directly.
if selected.get("key") != "home":
    render_sidebar_unit_slicer(selected.get("units"))

# ---------------- 3. Dashboard body ----------------
dashboard_module.render()

# ---------------- Footer ----------------
st.divider()
st.caption("Data Sources: World Bank | EIA | Pakistan Energy Yearbook")
