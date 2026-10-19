import streamlit as st


def inject_css():
    # Font Awesome 6 CDN & Google Fonts
    st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
    /* ---------- Global Typography & Theme ---------- */
    html, body, [class*="css"], .stMarkdown, h1, h2, h3, p, span, div {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    .main {
        background: radial-gradient(circle at 15% 15%, #141822 0%, #0D1017 100%);
    }
    .block-container {
        padding-top: 0.8rem; padding-bottom: 1.2rem;
        padding-left: 1.5rem; padding-right: 1.5rem;
        max-width: 100%;
    }

    /* ---------- Animations ---------- */
    @keyframes pulseGlow {
        0% { box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.4); }
        70% { box-shadow: 0 0 0 8px rgba(46, 204, 113, 0); }
        100% { box-shadow: 0 0 0 0 rgba(46, 204, 113, 0); }
    }
    @keyframes pulseBlue {
        0% { box-shadow: 0 0 0 0 rgba(0, 166, 251, 0.45); }
        70% { box-shadow: 0 0 0 8px rgba(0, 166, 251, 0); }
        100% { box-shadow: 0 0 0 0 rgba(0, 166, 251, 0); }
    }
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes titleShimmer {
        0%   { background-position: 0% 50%; }
        100% { background-position: 200% 50%; }
    }

    /* ---------- Sidebar section titles (shared) ---------- */
    /* One simple animated heading per sidebar block, no surrounding card. */
    .dsh-side-title {
        font-size: 17px;
        font-weight: 800;
        letter-spacing: -0.3px;
        line-height: 1.25;
        padding: 2px 2px 9px 2px;
        margin-bottom: 12px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.10);
        background: linear-gradient(90deg, #FFFFFF 0%, #7DE2A8 25%,
                                    #FFFFFF 50%, #7DE2A8 75%, #FFFFFF 100%);
        background-size: 200% 100%;
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        color: #FFFFFF;
        animation: titleShimmer 6s linear infinite;
    }
    @media (prefers-reduced-motion: reduce) {
        .dsh-side-title {
            animation: none;
            -webkit-text-fill-color: #FFFFFF;
            color: #FFFFFF;
        }
    }

    /* ---------- Dashboard footer ---------- */
    .dsh-footer {
        margin-top: 18px;
        padding: 12px 16px;
        border-radius: 10px;
        background: rgba(255, 255, 255, 0.025);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-left: 3px solid #2E8B57;
    }
    .dsh-footer-head {
        color: #E2E8F0;
        font-size: 11.5px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 7px;
        margin-bottom: 7px;
    }
    .dsh-footer-icon { color: #2ECC71; font-size: 12px; }
    .dsh-footer-body {
        color: #8B95A7;
        font-size: 10.5px;
        line-height: 1.75;
    }
    .dsh-footer-key {
        display: inline-block;
        min-width: 54px;
        color: #64748B;
        font-weight: 700;
        text-transform: uppercase;
        font-size: 9px;
        letter-spacing: 0.5px;
    }

    /* ---------- Top Header ---------- */
    .top-header {
        background: linear-gradient(135deg, rgba(26, 32, 44, 0.95) 0%, rgba(14, 17, 23, 0.98) 100%);
        padding: 16px 24px;
        border-radius: 12px;
        border: 1px solid rgba(46, 139, 87, 0.35);
        box-shadow: 0 8px 24px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.06);
        margin-bottom: 16px;
        display: flex; align-items: center; gap: 16px;
        position: relative; overflow: hidden;
    }
    .top-header::after {
        content: ''; position: absolute;
        bottom: 0; left: 0; right: 0; height: 2.5px;
        background: linear-gradient(90deg, #2E8B57, #00A6FB, #2ECC71, #F4A300);
        background-size: 300% 100%;
        animation: gradientShift 6s ease infinite;
    }
    .top-header .header-icon {
        color: #2ECC71; font-size: 26px; flex-shrink: 0;
        background: rgba(46, 204, 113, 0.12);
        width: 48px; height: 48px; border-radius: 12px;
        display: flex; align-items: center; justify-content: center;
        border: 1px solid rgba(46, 204, 113, 0.25);
    }
    .top-header h1 {
        color: #FFFFFF; font-size: 20px; margin: 0;
        font-weight: 700; letter-spacing: -0.2px; line-height: 1.35;
    }
    .top-header p {
        color: #94A3B8; font-size: 11.5px; margin: 5px 0 0 0;
        letter-spacing: 0.2px; font-weight: 500;
    }

    /* ---------- Sidebar: only stSidebarContent may scroll ---------- */
    section[data-testid="stSidebar"] {
        background: #0B0E14 !important;
        border-right: 1px solid rgba(255,255,255,0.07);
        overflow: hidden !important;
    }
    section[data-testid="stSidebar"] > div:first-child,
    div[data-testid="stSidebarContent"] {
        background: #0B0E14 !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        height: 100% !important;
        max-height: 100vh !important;
    }
    div[data-testid="stSidebarUserContent"] {
        background: #0B0E14 !important;
        overflow: visible !important;
        height: auto !important;
        max-height: none !important;
    }
    /* Slim, themed scrollbar for the one real container */
    div[data-testid="stSidebarContent"]::-webkit-scrollbar {
        width: 8px;
    }
    div[data-testid="stSidebarContent"]::-webkit-scrollbar-thumb {
        background: rgba(255,255,255,0.16);
        border-radius: 8px;
    }
    div[data-testid="stSidebarContent"]::-webkit-scrollbar-thumb:hover {
        background: rgba(46, 204, 113, 0.55);
    }
    div[data-testid="stSidebarContent"]::-webkit-scrollbar-track {
        background: transparent;
    }
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 0.4rem !important;
        padding-bottom: 0.4rem !important;
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
    }
    section[data-testid="stSidebar"] hr {
        margin: 6px 0 !important;
    }
    section[data-testid="stSidebar"] .stRadio label {
        color: #CBD5E1 !important;
        padding: 5px 10px; border-radius: 6px; font-size: 12.5px; font-weight: 500;
        transition: all 0.2s ease;
    }
    section[data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(255,255,255,0.05); color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] .stSelectbox {
        margin-bottom: 4px !important;
    }
    section[data-testid="stSidebar"] .stSlider {
        padding-top: 0 !important;
        padding-bottom: 2px !important;
    }

    /* ---------- Equal Column Heights across all Streamlit versions ---------- */
    [data-testid="column"],
    [data-testid="stColumn"],
    .stColumn {
        display: flex !important;
        flex-direction: column !important;
        flex: 1 1 0 !important;
        height: 100% !important;
    }
    [data-testid="column"] > div,
    [data-testid="stColumn"] > div,
    .stColumn > div,
    [data-testid="column"] [data-testid="stVerticalBlock"],
    [data-testid="stColumn"] [data-testid="stVerticalBlock"],
    [data-testid="column"] [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stColumn"] [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="column"] [data-testid="stElementContainer"],
    [data-testid="stColumn"] [data-testid="stElementContainer"],
    [data-testid="column"] .stMarkdown,
    [data-testid="stColumn"] .stMarkdown,
    [data-testid="column"] [data-testid="stMarkdownContainer"],
    [data-testid="stColumn"] [data-testid="stMarkdownContainer"] {
        display: flex !important;
        flex-direction: column !important;
        flex: 1 1 auto !important;
        height: 100% !important;
        width: 100% !important;
    }

    /* ---------- KPI Card with Equal Height & Bottom Balance (Q2) ---------- */
    .kpi-card {
        background: linear-gradient(145deg, rgba(28, 33, 44, 0.95) 0%, rgba(18, 22, 30, 0.98) 100%);
        border-radius: 12px;
        padding: 14px 16px;
        border: 1px solid rgba(255, 255, 255, 0.07);
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35);
        height: 142px !important;
        min-height: 142px !important;
        max-height: 142px !important;
        box-sizing: border-box !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
        position: relative; overflow: hidden;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        width: 100% !important;
    }
    .kpi-card::before {
        content: ''; position: absolute;
        top: 0; left: 0; width: 4px; height: 100%;
        background: linear-gradient(180deg, #2ECC71 0%, #2E8B57 100%);
        border-radius: 4px 0 0 4px;
    }
    .kpi-card:hover {
        transform: translateY(-4px);
        border-color: rgba(46, 204, 113, 0.45);
        box-shadow: 0 10px 24px rgba(0, 0, 0, 0.5), 0 0 16px rgba(46, 204, 113, 0.18);
    }
    /* Inline KPI row cards (Q3–Q7) share one fixed balanced height so every
       card in a Streamlit columns row stays strictly bottom-aligned. */
    .kpi-balance {
        background: linear-gradient(135deg, rgba(22, 27, 38, 0.95) 0%, rgba(14, 18, 26, 0.98) 100%) !important;
        border-radius: 14px !important;
        padding: 14px 15px 12px !important;
        height: 225px !important;
        min-height: 225px !important;
        max-height: 225px !important;
        box-sizing: border-box !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
        position: relative !important;
        overflow: hidden !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35) !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
        width: 100% !important;
    }
    .kpi-balance:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 10px 24px rgba(0, 0, 0, 0.5) !important;
    }
    .kpi-balance-details {
        margin-top: auto !important;
        border-top: 1px solid rgba(255, 255, 255, 0.06) !important;
        padding-top: 6px !important;
    }
    .kpi-icon-wrap { margin-bottom: 8px; }
    .kpi-icon {
        color: #2ECC71; font-size: 16px;
        background: rgba(46,204,113,0.12);
        padding: 7px; border-radius: 8px;
        width: 32px; height: 32px;
        display: flex; align-items: center; justify-content: center;
        border: 1px solid rgba(46,204,113,0.2);
    }
    .kpi-icon.blue   { color: #00A6FB; background: rgba(0,166,251,0.12); border-color: rgba(0,166,251,0.22); }
    .kpi-icon.orange { color: #F59E0B; background: rgba(245,158,11,0.12); border-color: rgba(245,158,11,0.22); }
    .kpi-icon.purple { color: #A855F7; background: rgba(168,85,247,0.12); border-color: rgba(168,85,247,0.22); }
    .kpi-icon.red    { color: #EF4444; background: rgba(239,68,68,0.12); border-color: rgba(239,68,68,0.22); }
    .kpi-icon.teal   { color: #14B8A6; background: rgba(20,184,166,0.12); border-color: rgba(20,184,166,0.22); }
    .kpi-icon.green  { color: #10B981; background: rgba(16,185,129,0.12); border-color: rgba(16,185,129,0.22); }

    .kpi-title {
        color: #94A3B8; font-size: 10.5px; font-weight: 600;
        text-transform: uppercase; letter-spacing: 0.5px;
        margin-bottom: 4px;
        min-height: 28px;
        line-height: 1.35;
    }
    .kpi-value {
        color: #F8FAFC; font-size: 23px; font-weight: 800;
        margin: 0; line-height: 1.15; letter-spacing: -0.5px;
    }
    .kpi-unit { color: #64748B; font-size: 11.5px; font-weight: 500; margin-left: 3px; }
    .kpi-delta-up   { color: #10B981; font-size: 11px; font-weight: 600; margin-top: auto; display: flex; align-items: center; gap: 4px; }
    .kpi-delta-down { color: #EF4444; font-size: 11px; font-weight: 600; margin-top: auto; display: flex; align-items: center; gap: 4px; }

    /* ---------- Section Card ---------- */
    .section-card {
        background: linear-gradient(145deg, rgba(24, 28, 38, 0.9) 0%, rgba(16, 20, 28, 0.95) 100%);
        border-radius: 12px;
        padding: 14px 18px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 4px 16px rgba(0,0,0,0.3);
        margin-bottom: 12px;
        position: relative;
    }
    .section-title {
        color: #FFFFFF; font-size: 13px; font-weight: 700;
        margin-bottom: 8px; padding-bottom: 6px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.07);
        display: flex; align-items: center; justify-content: space-between;
    }
    .section-title i { color: #10B981; font-size: 14px; }

    /* ---------- Section Badges & Pulse Badge ---------- */
    .section-badge {
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid rgba(16, 185, 129, 0.35);
        color: #10B981;
        font-size: 10px;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 20px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .pulse-badge {
        animation: pulseBlue 2s infinite ease-in-out;
    }

    /* ---------- Impact Metric Cards (Strict 4-in-1-Row) ---------- */
    .impact-summary-container {
        display: grid;
        grid-template-columns: repeat(4, 1fr) !important;
        gap: 12px;
        margin-bottom: 4px;
        width: 100%;
        box-sizing: border-box;
    }
    .impact-metric-card {
        background: linear-gradient(135deg, rgba(30, 36, 48, 0.9) 0%, rgba(20, 24, 34, 0.95) 100%);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 10px;
        padding: 10px 14px;
        display: flex;
        align-items: center;
        gap: 12px;
        min-width: 0;
        height: 100%;
        box-sizing: border-box;
        transition: all 0.3s ease;
    }
    .impact-metric-card:hover {
        transform: translateY(-3px);
        border-color: rgba(0, 166, 251, 0.45);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
    }
    .impact-icon {
        width: 36px; height: 36px; border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        font-size: 15px; flex-shrink: 0;
    }
    .impact-icon.green  { background: rgba(16,185,129,0.15); color: #10B981; border: 1px solid rgba(16,185,129,0.25); }
    .impact-icon.orange { background: rgba(245,158,11,0.15);  color: #F59E0B; border: 1px solid rgba(245,158,11,0.25); }
    .impact-icon.red    { background: rgba(239,68,68,0.15);   color: #EF4444; border: 1px solid rgba(239,68,68,0.25); }
    .impact-icon.blue   { background: rgba(0,166,251,0.15);   color: #00A6FB; border: 1px solid rgba(0,166,251,0.25); }
    .impact-details {
        display: flex; flex-direction: column;
        min-width: 0;
        overflow: hidden;
    }
    .impact-label {
        font-size: 10px; color: #94A3B8; font-weight: 600;
        text-transform: uppercase; letter-spacing: 0.5px;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    .impact-val {
        font-size: 16px; font-weight: 800; color: #F8FAFC;
        line-height: 1.25; margin-top: 2px;
        white-space: nowrap;
    }
    .impact-sub {
        font-size: 10px; color: #10B981; margin-top: 2px; font-weight: 500;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }

    /* ---------- Plotly Container Styling ---------- */
    .js-plotly-plot {
        background: #141822 !important;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 4px 18px rgba(0,0,0,0.35);
        transition: border-color 0.3s ease, box-shadow 0.3s ease;
    }
    .js-plotly-plot:hover {
        border-color: rgba(46, 139, 87, 0.45);
        box-shadow: 0 8px 24px rgba(0,0,0,0.45);
    }

    /* ---------- Buttons ---------- */
    .stButton > button {
        background: linear-gradient(90deg, #10B981 0%, #059669 100%);
        color: white; border: none; border-radius: 8px;
        padding: 8px 18px; font-weight: 700;
        width: 100%; font-size: 13px;
        transition: all 0.25s ease;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }
    .stButton > button:hover {
        background: linear-gradient(90deg, #059669 0%, #047857 100%);
        box-shadow: 0 6px 16px rgba(16, 185, 129, 0.45);
        transform: translateY(-1px);
    }

    /* ---------- Sliders Styling ---------- */
    .stSlider [data-baseweb="slider"] {
        padding: 8px 0;
    }

    /* ---------- Hide Streamlit branding ---------- */
    #MainMenu, footer, header { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)