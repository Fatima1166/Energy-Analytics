ICONS = {
    # Navigation
    "overview":   "fa-solid fa-gauge-high",
    "supply":     "fa-solid fa-bolt",
    "demand":     "fa-solid fa-fire-flame-simple",
    "renewables": "fa-solid fa-leaf",
    "scenario":   "fa-solid fa-chart-line",
    "emissions":  "fa-solid fa-smog",
    "cost":       "fa-solid fa-dollar-sign",
    "data":       "fa-solid fa-magnifying-glass-chart",
    "insights":   "fa-solid fa-lightbulb",

    # KPI icons
    "primary_energy": "fa-solid fa-oil-well",
    "generation":     "fa-solid fa-plug-circle-bolt",
    "re_share":       "fa-solid fa-leaf",
    "imports":        "fa-solid fa-ship",
    "co2":            "fa-solid fa-cloud",
    "intensity":      "fa-solid fa-gauge",
    "gas":            "fa-solid fa-fire",
    "warning":        "fa-solid fa-triangle-exclamation",
    "insights":       "fa-solid fa-lightbulb",

    # Impact icons
    "impact_gen":     "fa-solid fa-bolt",
    "impact_gas":     "fa-solid fa-fire",
    "impact_co2":     "fa-solid fa-cloud-arrow-down",
    "impact_bill":    "fa-solid fa-money-bill-trend-up",

    # Units / conversion
    "units":          "fa-solid fa-ruler-combined",
    "convert":        "fa-solid fa-right-left",

    # Arrows / actions
    "up":             "fa-solid fa-arrow-trend-up",
    "down":           "fa-solid fa-arrow-trend-down",
    "run":            "fa-solid fa-play",
    "reset":          "fa-solid fa-rotate-left",
    "filter":         "fa-solid fa-sliders",
    "chart":          "fa-solid fa-chart-column",
}


def icon(name: str, extra_class: str = "") -> str:
    cls = ICONS.get(name, "fa-solid fa-circle")
    return f'<i class="{cls} {extra_class}"></i>'
