"""
core/unit_slicer.py -- sidebar unit selector and session accessors.

Each dropdown defaults to the base unit the data is stored in
(TOE / GWh / MW / BCF / t / USD).
"""

from __future__ import annotations

import streamlit as st

from core.units import DOMAINS, DOMAIN_ORDER, defaults, normalise

SESSION_KEY = "unit_prefs"


# ---------------------------------------------------------------------------
# Session accessors
# ---------------------------------------------------------------------------
def get_units() -> dict:
    """Current display unit per domain, always complete."""
    prefs = st.session_state.get(SESSION_KEY)
    if not isinstance(prefs, dict):
        prefs = {}
    merged = defaults()
    for dom in DOMAIN_ORDER:
        chosen = prefs.get(dom)
        if chosen:
            merged[dom] = normalise(chosen)
    return merged


def get_unit(domain: str) -> str:
    """Current display unit for a single domain."""
    return get_units().get(domain) or DOMAINS[domain]["default"]


def set_unit(domain: str, unit: str) -> None:
    """Programmatically change one domain (keeps the widget in sync)."""
    prefs = get_units()
    prefs[domain] = normalise(unit)
    st.session_state[SESSION_KEY] = prefs
    st.session_state[f"unit_sel_{domain}"] = prefs[domain]


# ---------------------------------------------------------------------------
# Sidebar UI
# ---------------------------------------------------------------------------
def render_sidebar_unit_slicer(domains: list = None) -> dict:
    """
    Draw the unit selectors for the active dashboard and return the resulting
    preference dict, e.g. ``{"energy": "TOE", "gas": "BCF", ...}``.

    `domains` should list only the unit families the dashboard actually renders
    (each dashboard declares them in ``dashboards.registry``), so a dashboard is
    never offered a unit it does not use.  Order is preserved and unknown names
    are ignored.  When omitted, every known domain is shown.
    """
    if domains:
        wanted = [d for d in domains if d in DOMAINS]
        display_domains = wanted or list(DOMAIN_ORDER)
    else:
        display_domains = list(DOMAIN_ORDER)

    # ── Section title ────────────────────────────────────────────────────────
    # Plain animated heading (styled globally by .dsh-side-title); no card.
    st.sidebar.markdown(
        '<div class="dsh-side-title">Unit Selection</div>',
        unsafe_allow_html=True,
    )

    current = get_units()

    for dom in display_domains:
        cfg    = DOMAINS[dom]
        options = list(cfg["units"])
        cur    = current.get(dom, cfg["default"])
        index  = options.index(cur) if cur in options else 0

        st.sidebar.selectbox(
            cfg["label"],
            options,
            index=index,
            key=f"unit_sel_{dom}",
            help=cfg["note"],
        )

    # Persist this run's selection.  Start from what is already stored and only
    # overwrite the domains drawn for this dashboard, so a preference chosen on
    # one dashboard survives while another is open.
    prefs = get_units()
    for dom in display_domains:
        chosen = st.session_state.get(f"unit_sel_{dom}")
        prefs[dom] = normalise(chosen or DOMAINS[dom]["default"])
    st.session_state[SESSION_KEY] = prefs
    return prefs
