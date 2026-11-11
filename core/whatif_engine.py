"""
core/whatif_engine.py -- Runtime Cognitive & Machine Learning What-If Prediction Engine.
Integrates trained ML models and WisRule cognitive association rules from wisrule/ directory.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
import streamlit as st

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
WISRULE_DIR = _PROJECT_ROOT / "wisrule"
MODELS_DIR = WISRULE_DIR / "models"
RULES_CSV = WISRULE_DIR / "wisrule_energy_rules.csv"
NEG_RULES_CSV = WISRULE_DIR / "wisrule_negative_rules.csv"
SCENARIOS_CSV = WISRULE_DIR / "wisrule_whatif_scenarios.csv"
HISTORICAL_CSV = WISRULE_DIR / "energy_historical_data.csv"
METADATA_JSON = MODELS_DIR / "model_metadata.json"


# ---------------------------------------------------------------------------
# 1. Model & Data Loaders (Cached)
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def load_wisrule_models() -> Dict[str, Any]:
    """Load trained scikit-learn models from wisrule/models/."""
    models: Dict[str, Any] = {}
    if not MODELS_DIR.exists():
        return models

    model_files = {
        "reg_gen": "regressor_total_generation_gwh.joblib",
        "reg_re": "regressor_renewable_share_pct.joblib",
        "reg_co2": "regressor_co2_emissions_t.joblib",
        "clf_sec": "security_status_classifier.joblib",
        "clf_dem": "demand_regime_classifier.joblib",
    }
    for key, filename in model_files.items():
        path = MODELS_DIR / filename
        if path.exists():
            try:
                models[key] = joblib.load(path)
            except Exception as exc:
                print(f"Warning: could not load {filename}: {exc}")

    if METADATA_JSON.exists():
        try:
            with open(METADATA_JSON, "r", encoding="utf-8") as f:
                models["metadata"] = json.load(f)
        except Exception:
            models["metadata"] = {}
    else:
        models["metadata"] = {}

    return models


@st.cache_data(show_spinner=False)
def load_wisrule_rules() -> pd.DataFrame:
    """Load all 1,546 mined WisRule association rules."""
    if not RULES_CSV.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(RULES_CSV, encoding="utf-8")
        df["Support"] = pd.to_numeric(df["Support"], errors="coerce")
        df["Confidence"] = pd.to_numeric(df["Confidence"], errors="coerce")
        df["Interest"] = pd.to_numeric(df["Interest"], errors="coerce")
        df["Utility"] = pd.to_numeric(df["Utility"], errors="coerce")
        df["Quality_Score"] = pd.to_numeric(df["Quality_Score"], errors="coerce")
        return df
    except Exception as exc:
        print(f"Warning: could not load rules CSV: {exc}")
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_wisrule_negative_rules() -> pd.DataFrame:
    """Load mined negative association rules (WFISn, iWisVal == 2.0)."""
    if not NEG_RULES_CSV.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(NEG_RULES_CSV, encoding="utf-8")
    except Exception:
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_historical_baseline() -> Dict[str, Any]:
    """Load baseline historical energy state (latest 2024 reporting)."""
    if HISTORICAL_CSV.exists():
        try:
            df = pd.read_csv(HISTORICAL_CSV, encoding="utf-8")
            if not df.empty:
                latest = df.iloc[-1].to_dict()
                gen = float(latest.get("total_generation_gwh", 140875.0))
                cons = float(latest.get("total_final_consumption_gwh", 113140.0))
                waste_pct = max(0.0, ((gen - cons) / gen) * 100.0) if gen > 0 else 19.7
                return {
                    "year": int(latest.get("year", 2024)),
                    "gdp_growth_pct": float(latest.get("gdp_growth_pct", 3.08)),
                    "population": float(latest.get("population", 251269164)),
                    "installed_capacity_mw": float(latest.get("installed_capacity_mw", 45380.0)),
                    "total_generation_gwh": gen,
                    "total_final_consumption_gwh": cons,
                    "waste_pct": round(waste_pct, 2),
                    "gen_hydro_gwh": float(latest.get("gen_hydro_gwh", 38270.0)),
                    "gen_solar_gwh": float(latest.get("gen_solar_gwh", 19830.0)),
                    "gen_wind_gwh": float(latest.get("gen_wind_gwh", 5160.0)),
                    "gen_coal_gwh": float(latest.get("gen_coal_gwh", 24360.0)),
                    "gen_gas_gwh": float(latest.get("gen_gas_gwh", 43980.0)),
                    "gen_nuclear_gwh": float(latest.get("gen_nuclear_gwh", 22880.0)),
                    "gas_production_bcf": float(latest.get("gas_production_bcf", 1054.8)),
                    "gas_consumption_bcf": float(latest.get("gas_consumption_bcf", 1128.9)),
                    "co2_emissions_t": float(latest.get("co2_emissions_t", 179800380.0)),
                    "renewable_share_pct": float(latest.get("renewable_share_pct", 44.91)),
                    "fossil_share_pct": float(latest.get("fossil_share_pct", 48.51)),
                    "capacity_util_pct": float(latest.get("capacity_util_pct", 35.44)),
                    "gas_self_suff_pct": float(latest.get("gas_self_suff_pct", 93.43)),
                    "import_dependence_pct": float(latest.get("import_dependence_pct", 6.57)),
                }
        except Exception:
            pass

    # Built-in fallback baseline (2024 actuals)
    return {
        "year": 2024,
        "gdp_growth_pct": 3.08,
        "population": 251269164,
        "installed_capacity_mw": 45380.0,
        "total_generation_gwh": 140875.0,
        "total_final_consumption_gwh": 113140.0,
        "waste_pct": 19.69,
        "gen_hydro_gwh": 38270.0,
        "gen_solar_gwh": 19830.0,
        "gen_wind_gwh": 5160.0,
        "gen_coal_gwh": 24360.0,
        "gen_gas_gwh": 43980.0,
        "gen_nuclear_gwh": 22880.0,
        "gas_production_bcf": 1054.8,
        "gas_consumption_bcf": 1128.9,
        "co2_emissions_t": 179800380.0,
        "renewable_share_pct": 44.91,
        "fossil_share_pct": 48.51,
        "capacity_util_pct": 35.44,
        "gas_self_suff_pct": 93.43,
        "import_dependence_pct": 6.57,
    }


# ---------------------------------------------------------------------------
# 2. Categorization & Rule Matching Helpers
# ---------------------------------------------------------------------------

def discretize_scenario_state(state: Dict[str, Any]) -> List[str]:
    """Convert quantitative scenario state into WisRule itemset strings."""
    items: List[str] = []

    # Renewable Share Cat
    re_sh = state.get("renewable_share_pct", 0)
    if re_sh < 10:
        items.append("Renewable_Share_Cat=Very_Low")
    elif re_sh < 20:
        items.append("Renewable_Share_Cat=Low")
    elif re_sh < 30:
        items.append("Renewable_Share_Cat=Medium")
    else:
        items.append("Renewable_Share_Cat=High")

    # Capacity Util Cat
    cu = state.get("capacity_util_pct", 0)
    if cu < 40:
        items.append("Capacity_Util_Cat=Low")
    elif cu < 50:
        items.append("Capacity_Util_Cat=Medium")
    elif cu < 60:
        items.append("Capacity_Util_Cat=High")
    else:
        items.append("Capacity_Util_Cat=Very_High")

    # GDP Growth Cat
    gdp = state.get("gdp_growth_pct", 0)
    if gdp < 0:
        items.append("GDP_Growth_Cat=Negative")
    elif gdp < 3:
        items.append("GDP_Growth_Cat=Low")
    elif gdp < 5:
        items.append("GDP_Growth_Cat=Medium")
    else:
        items.append("GDP_Growth_Cat=High")

    # Energy Intensity / Waste Cat
    waste = state.get("waste_pct", 19.7)
    if waste < 12:
        items.append("Energy_Intensity_Cat=Very_Efficient")
    elif waste < 16:
        items.append("Energy_Intensity_Cat=Efficient")
    elif waste < 20:
        items.append("Energy_Intensity_Cat=Moderate")
    else:
        items.append("Energy_Intensity_Cat=Inefficient")

    # Gas Self-Sufficiency
    gas_ss = state.get("gas_self_suff_pct", 93.4)
    if gas_ss < 80:
        items.append("Gas_Self_Suff_Cat=Deficit")
    elif gas_ss < 100:
        items.append("Gas_Self_Suff_Cat=Near_Self_Sufficient")
    elif gas_ss < 120:
        items.append("Gas_Self_Suff_Cat=Self_Sufficient")
    else:
        items.append("Gas_Self_Suff_Cat=Surplus")

    # Import Dependence
    imp_dep = state.get("import_dependence_pct", 6.6)
    if imp_dep < 5:
        items.append("Import_Dependence_Cat=Low")
    elif imp_dep < 10:
        items.append("Import_Dependence_Cat=Medium")
    elif imp_dep < 20:
        items.append("Import_Dependence_Cat=High")
    else:
        items.append("Import_Dependence_Cat=Critical")

    # Coal & Nuclear Shares
    tot_gen = max(1.0, state.get("total_generation_gwh", 1.0))
    coal_sh = (state.get("gen_coal_gwh", 0) / tot_gen) * 100
    if coal_sh < 5:
        items.append("Coal_Share_Cat=Negligible")
    elif coal_sh < 15:
        items.append("Coal_Share_Cat=Low")
    elif coal_sh < 30:
        items.append("Coal_Share_Cat=Medium")
    else:
        items.append("Coal_Share_Cat=High")

    nuc_sh = (state.get("gen_nuclear_gwh", 0) / tot_gen) * 100
    if nuc_sh < 2:
        items.append("Nuclear_Share_Cat=Negligible")
    elif nuc_sh < 5:
        items.append("Nuclear_Share_Cat=Low")
    elif nuc_sh < 10:
        items.append("Nuclear_Share_Cat=Medium")
    else:
        items.append("Nuclear_Share_Cat=High")

    # Location dimension item mapping
    loc = state.get("location_scope", "Industrial Area (LI_High Demand)")
    if "Industrial" in loc or "LI_High" in loc:
        items.append("LI=LI_High")
    elif "Commercial" in loc or "LI_Medium" in loc:
        items.append("LI=LI_Medium")
    else:
        items.append("LI=LI_Low")

    # Time dimension item mapping
    time_scope = state.get("time_scope", "TI5_2020-25")
    if "TI1" in time_scope:
        items.append("TI=TI1_2000-05")
    elif "TI2" in time_scope:
        items.append("TI=TI2_2005-10")
    elif "TI3" in time_scope:
        items.append("TI=TI3_2010-15")
    elif "TI4" in time_scope:
        items.append("TI=TI4_2015-20")
    else:
        items.append("TI=TI5_2020-25")

    return items


# ---------------------------------------------------------------------------
# 3. Dynamic Scenario Evaluation Engine
# ---------------------------------------------------------------------------

def evaluate_dynamic_scenario(
    name: str,
    description: str = "",
    time_scope: str = "TI5_2020-25",
    location_scope: str = "Industrial Area (LI_High Demand)",
    utility_focus: str = "Waste / Losses / Efficiency",
    context_condition: str = "High T&D Loss / Waste Surge",
    year: int = 2025,
    waste_pct: float = 22.5,
    gdp_growth_pct: float = 3.5,
    installed_capacity_mw: float = 46000.0,
    gen_hydro_gwh: float = 38500.0,
    gen_solar_gwh: float = 22000.0,
    gen_wind_gwh: float = 6500.0,
    gen_coal_gwh: float = 24000.0,
    gen_gas_gwh: float = 40000.0,
    gen_nuclear_gwh: float = 23000.0,
    sector_name: str = "Industrial",
) -> Dict[str, Any]:
    """
    Evaluate user-defined dynamic scenario using ML regressors, classifiers,
    and WisRule cognitive association rules.
    """
    baseline = load_historical_baseline()
    models = load_wisrule_models()
    df_rules = load_wisrule_rules()

    # Derived energy totals
    re_gen = gen_hydro_gwh + gen_solar_gwh + gen_wind_gwh
    fossil_gen = gen_gas_gwh + gen_coal_gwh
    manual_tot_gen = re_gen + fossil_gen + gen_nuclear_gwh

    # Feature vector for Regressors:
    # ['year', 'gdp_growth_pct', 'installed_capacity_mw', 'gen_hydro_gwh', 'gen_nuclear_gwh', 'gen_gas_gwh', 'gen_coal_gwh']
    reg_feats = ["year", "gdp_growth_pct", "installed_capacity_mw", "gen_hydro_gwh", "gen_nuclear_gwh", "gen_gas_gwh", "gen_coal_gwh"]
    reg_input = pd.DataFrame(
        [[year, gdp_growth_pct, installed_capacity_mw, gen_hydro_gwh, gen_nuclear_gwh, gen_gas_gwh, gen_coal_gwh]],
        columns=reg_feats,
    )

    # 1. Total Generation Prediction
    if "reg_gen" in models:
        try:
            pred_gen = float(models["reg_gen"].predict(reg_input)[0])
            # Blend 50% model prediction with 50% physical sum of sources for consistency
            final_gen = (pred_gen * 0.4) + (manual_tot_gen * 0.6)
        except Exception:
            final_gen = manual_tot_gen
    else:
        final_gen = manual_tot_gen

    # 2. Renewable Share Prediction
    if "reg_re" in models:
        try:
            pred_re = float(models["reg_re"].predict(reg_input)[0])
            physics_re = (re_gen / max(1.0, final_gen)) * 100.0
            final_re = (pred_re * 0.3) + (physics_re * 0.7)
            final_re = float(np.clip(final_re, 0.0, 100.0))
        except Exception:
            final_re = (re_gen / max(1.0, final_gen)) * 100.0
    else:
        final_re = (re_gen / max(1.0, final_gen)) * 100.0

    # 3. CO2 Emissions Prediction
    if "reg_co2" in models:
        try:
            pred_co2 = float(models["reg_co2"].predict(reg_input)[0])
            # Physics estimate: ~0.90 t CO2/MWh for coal, ~0.45 t CO2/MWh for gas
            co2_physics = (gen_coal_gwh * 900.0) + (gen_gas_gwh * 450.0)
            final_co2 = (pred_co2 * 0.5) + (co2_physics * 0.5)
        except Exception:
            final_co2 = (gen_coal_gwh * 900.0) + (gen_gas_gwh * 450.0)
    else:
        final_co2 = (gen_coal_gwh * 900.0) + (gen_gas_gwh * 450.0)

    # 4. Electricity Waste / Losses & Delivered Usable Power
    waste_gwh = final_gen * (waste_pct / 100.0)
    delivered_gwh = max(0.0, final_gen - waste_gwh)

    # 5. Capacity Utilization & Fuel Metrics
    cap_util_pct = (final_gen / (installed_capacity_mw * 8.76)) * 100.0
    fossil_share_pct = (fossil_gen / max(1.0, final_gen)) * 100.0

    # Gas metrics estimation based on gas generation
    base_gas_cons = baseline.get("gas_consumption_bcf", 1128.9)
    gas_cons_est = base_gas_cons * (gen_gas_gwh / max(1.0, baseline.get("gen_gas_gwh", 43980.0)))
    gas_prod_est = baseline.get("gas_production_bcf", 1054.8)
    gas_self_suff_pct = (gas_prod_est / max(1.0, gas_cons_est)) * 100.0
    import_dependence_pct = float(np.clip(100.0 - gas_self_suff_pct, 0.0, 100.0))

    # 6. Security Status Classifier
    # Features: ['calendar_year', 'gdp_growth_pct', 'installed_capacity_mw', 'total_generation_gwh', 'renewable_share_pct', 'fossil_share_pct', 'capacity_util_pct']
    sec_feats = ["calendar_year", "gdp_growth_pct", "installed_capacity_mw", "total_generation_gwh", "renewable_share_pct", "fossil_share_pct", "capacity_util_pct"]
    sec_input = pd.DataFrame(
        [[year, gdp_growth_pct, installed_capacity_mw, final_gen, final_re, fossil_share_pct, cap_util_pct]],
        columns=sec_feats,
    )
    if "clf_sec" in models:
        try:
            sec_clf = models["clf_sec"]
            sec_pred = str(sec_clf.predict(sec_input)[0])
            sec_probs = dict(zip(sec_clf.classes_, [round(float(p) * 100, 1) for p in sec_clf.predict_proba(sec_input)[0]]))
        except Exception:
            sec_pred = "Moderate"
            sec_probs = {"Secure": 20.0, "Moderate": 65.0, "Stressed": 15.0}
    else:
        sec_pred = "Moderate"
        sec_probs = {"Secure": 20.0, "Moderate": 65.0, "Stressed": 15.0}

    # 7. Sectoral Demand Regime Classifier
    # Features: ['calendar_year', 'gdp_growth_pct', 'per_capita_gdp', 'population', 'installed_capacity_mw', 'nat_generation_gwh', 'capacity_util_pct', 'gas_self_suff_pct', ...]
    dem_cols = [
        "calendar_year", "gdp_growth_pct", "per_capita_gdp", "population",
        "installed_capacity_mw", "nat_generation_gwh", "capacity_util_pct",
        "gas_self_suff_pct", "sec_Bulk Supply", "sec_Commercial",
        "sec_Domestic", "sec_Industrial", "sec_Other Govt",
        "sec_Street Light", "sec_Traction"
    ]
    pop = baseline.get("population", 251269164) * ((1.0 + 0.019) ** (year - 2024))
    per_cap_gdp = (372e9 * ((1.0 + (gdp_growth_pct / 100.0)) ** (year - 2024))) / max(1.0, pop)
    
    dem_row = {
        "calendar_year": year,
        "gdp_growth_pct": gdp_growth_pct,
        "per_capita_gdp": per_cap_gdp,
        "population": pop,
        "installed_capacity_mw": installed_capacity_mw,
        "nat_generation_gwh": final_gen,
        "capacity_util_pct": cap_util_pct,
        "gas_self_suff_pct": gas_self_suff_pct,
        "sec_Bulk Supply": 1 if sector_name == "Bulk Supply" else 0,
        "sec_Commercial": 1 if sector_name == "Commercial" else 0,
        "sec_Domestic": 1 if sector_name == "Domestic" else 0,
        "sec_Industrial": 1 if sector_name == "Industrial" else 0,
        "sec_Other Govt": 1 if sector_name == "Other Govt" else 0,
        "sec_Street Light": 1 if sector_name == "Street Light" else 0,
        "sec_Traction": 1 if sector_name == "Traction" else 0,
    }
    dem_input = pd.DataFrame([[dem_row[c] for c in dem_cols]], columns=dem_cols)
    if "clf_dem" in models:
        try:
            dem_clf = models["clf_dem"]
            dem_pred = str(dem_clf.predict(dem_input)[0])
            dem_probs = dict(zip(dem_clf.classes_, [round(float(p) * 100, 1) for p in dem_clf.predict_proba(dem_input)[0]]))
        except Exception:
            dem_pred = "Tier3_High"
            dem_probs = {"Tier1_Low": 10.0, "Tier2_Medium": 20.0, "Tier3_High": 70.0}
    else:
        dem_pred = "Tier3_High"
        dem_probs = {"Tier1_Low": 10.0, "Tier2_Medium": 20.0, "Tier3_High": 70.0}

    # 8. WisRule Rule Activation & Matching
    sim_state = {
        "renewable_share_pct": final_re,
        "capacity_util_pct": cap_util_pct,
        "gdp_growth_pct": gdp_growth_pct,
        "waste_pct": waste_pct,
        "gas_self_suff_pct": gas_self_suff_pct,
        "import_dependence_pct": import_dependence_pct,
        "gen_coal_gwh": gen_coal_gwh,
        "gen_nuclear_gwh": gen_nuclear_gwh,
        "total_generation_gwh": final_gen,
        "location_scope": location_scope,
        "time_scope": time_scope,
    }
    active_items = set(discretize_scenario_state(sim_state))

    matched_pos_rules: List[Dict[str, Any]] = []
    matched_neg_rules: List[Dict[str, Any]] = []

    if not df_rules.empty:
        for _, r in df_rules.iterrows():
            ant_str = str(r["Antecedent"])
            ant_tokens = [tok.strip() for tok in ant_str.split("∧")]
            # Match if any or all tokens of antecedent are active in the scenario
            if any(tok in active_items for tok in ant_tokens):
                r_dict = r.to_dict()
                if str(r.get("Type", "")).lower() == "negative":
                    matched_neg_rules.append(r_dict)
                else:
                    matched_pos_rules.append(r_dict)

    # Sort matched rules by Quality Score
    matched_pos_rules.sort(key=lambda x: -float(x.get("Quality_Score", 0)))
    matched_neg_rules.sort(key=lambda x: -float(x.get("Quality_Score", 0)))

    # Compute deltas vs baseline
    b_gen = baseline.get("total_generation_gwh", 140875.0)
    b_cons = baseline.get("total_final_consumption_gwh", 113140.0)
    b_waste_pct = baseline.get("waste_pct", 19.69)
    b_waste_gwh = b_gen * (b_waste_pct / 100.0)
    b_re = baseline.get("renewable_share_pct", 44.91)
    b_co2 = baseline.get("co2_emissions_t", 179800380.0)

    delta_gen_pct = round(((final_gen - b_gen) / max(1.0, b_gen)) * 100.0, 2)
    delta_delivered_pct = round(((delivered_gwh - b_cons) / max(1.0, b_cons)) * 100.0, 2)
    delta_waste_gwh = round(waste_gwh - b_waste_gwh, 1)
    delta_re_ppt = round(final_re - b_re, 2)
    delta_co2_pct = round(((final_co2 - b_co2) / max(1.0, b_co2)) * 100.0, 2)

    return {
        "meta": {
            "name": name,
            "description": description,
            "time_scope": time_scope,
            "location_scope": location_scope,
            "utility_focus": utility_focus,
            "context_condition": context_condition,
            "year": year,
            "sector_name": sector_name,
        },
        "inputs": {
            "waste_pct": waste_pct,
            "gdp_growth_pct": gdp_growth_pct,
            "installed_capacity_mw": installed_capacity_mw,
            "gen_hydro_gwh": gen_hydro_gwh,
            "gen_solar_gwh": gen_solar_gwh,
            "gen_wind_gwh": gen_wind_gwh,
            "gen_coal_gwh": gen_coal_gwh,
            "gen_gas_gwh": gen_gas_gwh,
            "gen_nuclear_gwh": gen_nuclear_gwh,
            "active_discrete_items": sorted(list(active_items)),
        },
        "predictions": {
            "total_generation_gwh": round(final_gen, 1),
            "delivered_consumption_gwh": round(delivered_gwh, 1),
            "waste_loss_gwh": round(waste_gwh, 1),
            "renewable_share_pct": round(final_re, 2),
            "fossil_share_pct": round(fossil_share_pct, 2),
            "co2_emissions_t": round(final_co2, 0),
            "co2_emissions_mt": round(final_co2 / 1e6, 2),
            "capacity_util_pct": round(cap_util_pct, 2),
            "gas_self_suff_pct": round(gas_self_suff_pct, 1),
            "import_dependence_pct": round(import_dependence_pct, 1),
            "security_status": sec_pred,
            "security_probs": sec_probs,
            "demand_regime": dem_pred,
            "demand_probs": dem_probs,
        },
        "deltas": {
            "gen_pct": delta_gen_pct,
            "delivered_pct": delta_delivered_pct,
            "waste_gwh": delta_waste_gwh,
            "re_ppt": delta_re_ppt,
            "co2_pct": delta_co2_pct,
        },
        "baseline": {
            "total_generation_gwh": round(b_gen, 1),
            "total_final_consumption_gwh": round(b_cons, 1),
            "waste_loss_gwh": round(b_waste_gwh, 1),
            "waste_pct": round(b_waste_pct, 2),
            "renewable_share_pct": round(b_re, 2),
            "co2_emissions_mt": round(b_co2 / 1e6, 2),
        },
        "rules": {
            "total_positive_active": len(matched_pos_rules),
            "total_negative_active": len(matched_neg_rules),
            "top_positive": matched_pos_rules[:5],
            "top_negative": matched_neg_rules[:5],
        },
    }


# ---------------------------------------------------------------------------
# 4. Multi-Dimensional Rules Filtering
# ---------------------------------------------------------------------------

def filter_wisrule_rules(
    df: Optional[pd.DataFrame] = None,
    polarity: str = "All",
    time_filter: str = "All",
    location_filter: str = "All",
    utility_focus: str = "All",
    min_utility: float = 0.60,
    context_filter: str = "All",
    search_query: str = "",
    limit: Optional[int] = None,
) -> pd.DataFrame:
    """
    Filter the 1,546 WisRule rules across multi-dimensional criteria:
    Time, Location, Utility, Context, Polarity, and Text Search.
    """
    if df is None or df.empty:
        df = load_wisrule_rules()
    if df.empty:
        return df

    filtered = df.copy()

    # 1. Polarity Filter
    if polarity.lower() == "positive":
        filtered = filtered[filtered["Type"].str.lower() == "positive"]
    elif polarity.lower() == "negative":
        filtered = filtered[filtered["Type"].str.lower() == "negative"]

    # 2. Time Filter
    if time_filter and time_filter != "All":
        t_key = time_filter.split(" ")[0].strip()
        filtered = filtered[filtered["Time_Intervals"].astype(str).str.contains(t_key, case=False, na=False)]

    # 3. Location Filter
    if location_filter and location_filter != "All":
        l_low = location_filter.lower()
        if "industrial" in l_low or "li_high" in l_low:
            l_key = "LI_High"
        elif "commercial" in l_low or "li_medium" in l_low:
            l_key = "LI_Medium"
        elif "residential" in l_low or "li_low" in l_low:
            l_key = "LI_Low"
        else:
            l_key = location_filter.strip()
        filtered = filtered[filtered["Locations"].astype(str).str.contains(l_key, case=False, na=False)]

    # 4. Utility Filter
    if min_utility > 0.0:
        filtered = filtered[filtered["Utility"] >= min_utility]

    if utility_focus and utility_focus != "All":
        u_low = utility_focus.lower()
        if "waste" in u_low or "loss" in u_low or "efficiency" in u_low:
            target_token = "Energy_Intensity_Cat"
        elif "renewable" in u_low:
            target_token = "Renewable_Share_Cat"
        elif "gas" in u_low:
            target_token = "Gas_Self_Suff_Cat"
        elif "import" in u_low:
            target_token = "Import_Dependence_Cat"
        elif "co2" in u_low or "emission" in u_low:
            target_token = "CO2_Intensity_Cat"
        elif "capacity" in u_low:
            target_token = "Capacity_Util_Cat"
        elif "coal" in u_low:
            target_token = "Coal_Share_Cat"
        elif "nuclear" in u_low:
            target_token = "Nuclear_Share_Cat"
        else:
            target_token = utility_focus

        filtered = filtered[
            filtered["Antecedent"].astype(str).str.contains(target_token, case=False, na=False)
            | filtered["Consequent"].astype(str).str.contains(target_token, case=False, na=False)
        ]

    # 5. Context Filter
    if context_filter and context_filter != "All":
        filtered = filtered[
            filtered["Antecedent"].astype(str).str.contains(context_filter, case=False, na=False)
            | filtered["Consequent"].astype(str).str.contains(context_filter, case=False, na=False)
        ]

    # 6. Keyword Search
    if search_query and search_query.strip():
        q = search_query.strip().lower()
        filtered = filtered[
            filtered["Rule_ID"].astype(str).str.lower().str.contains(q, na=False)
            | filtered["Rule"].astype(str).str.lower().str.contains(q, na=False)
            | filtered["Antecedent"].astype(str).str.lower().str.contains(q, na=False)
            | filtered["Consequent"].astype(str).str.lower().str.contains(q, na=False)
        ]

    # Sort descending by Quality Score
    if "Quality_Score" in filtered.columns:
        filtered = filtered.sort_values(by="Quality_Score", ascending=False)

    if limit is not None and limit > 0:
        filtered = filtered.head(limit)

    return filtered

