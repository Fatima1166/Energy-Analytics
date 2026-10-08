from core.icons import icon


def kpi_card(title, value, unit, delta=None, delta_type="up",
             icon_name="primary_energy", color="green"):
    delta_html = ""
    if delta is not None:
        delta_class = "kpi-delta-up" if delta_type == "up" else "kpi-delta-down"
        delta_icon = icon("up") if delta_type == "up" else icon("down")
        delta_html = f'<div class="{delta_class}">{delta_icon} {delta}</div>'

    unit_html = f' <span class="kpi-unit">{unit}</span>' if unit else ""
    return (
        f'<div class="kpi-card">'
        f'<div class="kpi-icon-wrap"><div class="kpi-icon {color}">{icon(icon_name)}</div></div>'
        f'<div class="kpi-title">{title}</div>'
        f'<div class="kpi-value">{value}{unit_html}</div>'
        f'{delta_html}'
        f'</div>'
    )


def section_title(text, icon_name, badge=None):
    badge_html = f'<span class="section-badge">{badge}</span>' if badge else ""
    return (
        f'<div class="section-title">'
        f'<div style="display:flex;align-items:center;gap:8px;">'
        f'{icon(icon_name)} <span>{text}</span>'
        f'</div>'
        f'{badge_html}'
        f'</div>'
    )


def impact_metric(icon_name, color, label, value, subtext):
    return (
        f'<div class="impact-metric-card">'
        f'<div class="impact-icon {color}">{icon(icon_name)}</div>'
        f'<div class="impact-details">'
        f'<span class="impact-label">{label}</span>'
        f'<span class="impact-val">{value}</span>'
        f'<span class="impact-sub">{subtext}</span>'
        f'</div>'
        f'</div>'
    )


def dashboard_footer(scope_line, method_line, source_line, note=None, icon_name="data"):
    """
    Compact, data-driven footnote for the bottom of a dashboard.

    `scope_line`   -- what the current view is showing (updates with the slicers)
    `method_line`  -- how the figures are produced, in one line
    `source_line`  -- where the underlying data comes from
    `note`         -- optional short caveat, rendered in amber

    Three short lines, no prose.  Everything is passed in so the text always
    describes the live filter state rather than a static blurb.
    """
    note_html = (
        f'<div style="color:#F59E0B;font-size:10.5px;margin-top:5px;">{note}</div>'
        if note else ""
    )
    return (
        f'<div class="dsh-footer">'
        f'<div class="dsh-footer-head">'
        f'<span class="dsh-footer-icon">{icon(icon_name)}</span>'
        f'{scope_line}'
        f'</div>'
        f'<div class="dsh-footer-body">'
        f'<div><span class="dsh-footer-key">Method</span> {method_line}</div>'
        f'<div><span class="dsh-footer-key">Source</span> {source_line}</div>'
        f'{note_html}'
        f'</div>'
        f'</div>'
    )