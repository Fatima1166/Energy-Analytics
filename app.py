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
selected_label = st.sidebar.radio("nav", labels, label_visibility="collapsed")
selected = next(d for d in DASHBOARDS if d["label"] == selected_label)

st.sidebar.divider()

# ---------------- Header (dynamic per dashboard) ----------------
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
render_sidebar_unit_slicer(selected.get("units"))

# ---------------- 3. Dashboard body ----------------
dashboard_module.render()

# ---------------- Footer ----------------
st.divider()
st.caption("Data Sources: World Bank | EIA | Pakistan Energy Yearbook")
