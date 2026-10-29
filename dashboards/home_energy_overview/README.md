# Home — Energy Overview (Landing Dashboard)

The platform's website-style front page: hero banner, headline national
energy stats, three signature charts and clickable tiles that jump into any
analytical question dashboard.  Registered as the **first** entry in
`dashboards/registry.py`, so it is the default view on load.

## Architecture

| Layer | File | Role |
|-------|------|------|
| Engine | `core/energy_overview.py` | Supply/demand history, latest fuel mix, CO2 record, headline snapshot with 10-year deltas |
| Charts | `dashboards/home_energy_overview/charts.py` | Three dumb visuals |
| Page | `dashboards/home_energy_overview/page.py` | Hero CSS, stat cards, chart rows, dashboard tile grid |
| Config | `dashboards/home_energy_overview/config.py` | Hero copy + fuel palette |

## Visuals

- **H1** Supply vs demand — twin filled area lines (national energy balance)
- **H2** Fuel-mix donut — latest-year primary supply share by source
- **H3** CO2 bars — annual emissions, latest year highlighted

## Tile navigation

Each tile is an `st.button` that sets `st.session_state["nav_pending"]` and
reruns; `app.py` applies it to the sidebar selectbox (key `nav_selector`)
**before** the widget is instantiated — widget state cannot be written after
instantiation within the same run.  Hovering a tile shows the full question
text.

## Units

Headline stats and H1/H3 honour the global unit slicer
(`energy`, `electricity`, `emission` families); the donut is share-based and
unitless.

## Data gaps

The four headline cards take each metric from its **own** year: a card names the
latest year that metric reported, or prints *no reading* when it has none at
all. Nothing is carried over from another year and no missing year is drawn as
zero; the H1/H3 charts break their line where the record is silent. The fuel
mix and the carbon-intensity note only appear when they belong to the same year
as the numbers they describe.

## Data sources

`Q_ENERGY_OVERVIEW`, `Q_ELEC_GEN`, `Q_RENEWABLE_ENERGY`, `Q_PRIMARY_SUPPLY`,
`Q_ECONOMIC`.
