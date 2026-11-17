"""
core/year_filter.py -- Global Year Range Filter Management.

Manages the active starting and ending year filter across all dashboards.
- Historical dashboards (Home, Q6, Q9) apply both start_year and end_year.
- Predicted / Forecast dashboards (Q1, Q2, Q3, Q4, Q5, Q7, Q8, Q10) only update
  their starting year (start_year), keeping the forecast horizon (up to 2035) active.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
import pandas as pd
import streamlit as st

_FILTER_FILE = Path(__file__).resolve().parent.parent / "config" / "year_filter.json"


def _get_db_bounds() -> Tuple[int, int]:
    """Get the true min and max years available in the database."""
    try:
        from core.data_entry import get_first_year, get_latest_year
        return int(get_first_year()), int(get_latest_year())
    except Exception:
        return 1999, 2024


def get_default_range() -> Tuple[int, int]:
    """Returns the default full year range (min_year, max_year)."""
    return _get_db_bounds()


def get_year_filter() -> Tuple[int, int]:
    """Return the currently active (start_year, end_year) tuple.
    
    Checks st.session_state first, then persistent JSON file, then DB bounds.
    """
    min_yr, max_yr = _get_db_bounds()

    # 1. Check session state
    if "year_filter_start" in st.session_state and "year_filter_end" in st.session_state:
        try:
            s = int(st.session_state["year_filter_start"])
            e = int(st.session_state["year_filter_end"])
            if s <= e:
                return max(min_yr, s), min(max_yr, e)
        except Exception:
            pass

    # 2. Check JSON file
    if _FILTER_FILE.exists():
        try:
            with open(_FILTER_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                s = int(data.get("start_year", min_yr))
                e = int(data.get("end_year", max_yr))
                if s <= e:
                    # Sync to session state
                    st.session_state["year_filter_start"] = s
                    st.session_state["year_filter_end"] = e
                    return max(min_yr, s), min(max_yr, e)
        except Exception:
            pass

    # 3. Default to full bounds
    return min_yr, max_yr


def set_year_filter(start_year: int, end_year: int) -> None:
    """Set and persist the global year filter."""
    start_year = int(start_year)
    end_year = int(end_year)
    if start_year > end_year:
        start_year, end_year = end_year, start_year

    st.session_state["year_filter_start"] = start_year
    st.session_state["year_filter_end"] = end_year

    try:
        _FILTER_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_FILTER_FILE, "w", encoding="utf-8") as f:
            json.dump({"start_year": start_year, "end_year": end_year}, f, indent=2)
    except Exception:
        pass

    # Clear cached query results so all dashboards recalculate with the new range
    try:
        st.cache_data.clear()
    except Exception:
        pass


def reset_year_filter() -> None:
    """Reset the filter back to the full database range."""
    min_yr, max_yr = _get_db_bounds()
    st.session_state["year_filter_start"] = min_yr
    st.session_state["year_filter_end"] = max_yr

    if _FILTER_FILE.exists():
        try:
            _FILTER_FILE.unlink()
        except Exception:
            pass

    try:
        st.cache_data.clear()
    except Exception:
        pass


def is_filter_active() -> bool:
    """Returns True if the current filter restricts the full year range."""
    min_yr, max_yr = _get_db_bounds()
    s, e = get_year_filter()
    return (s > min_yr) or (e < max_yr)


def filter_historical_df(df: pd.DataFrame, year_col: str = "calendar_year") -> pd.DataFrame:
    """Filter historical DataFrame to [start_year, end_year].
    
    If the year column is missing or DataFrame is empty, returns original df.
    """
    if df is None or df.empty:
        return df

    col = year_col
    if col not in df.columns:
        for c in ["calendar_year", "year", "year_id", "fiscal_year"]:
            if c in df.columns:
                col = c
                break
        else:
            return df

    start_yr, end_yr = get_year_filter()
    try:
        mask = (pd.to_numeric(df[col], errors="coerce") >= start_yr) & (
            pd.to_numeric(df[col], errors="coerce") <= end_yr
        )
        return df[mask].copy()
    except Exception:
        return df


def filter_predicted_df(df: pd.DataFrame, year_col: str = "calendar_year") -> pd.DataFrame:
    """Filter predicted/forecast DataFrame so starting year is >= start_year.
    
    Crucial: Does NOT filter by end_year so that future forecasted / predicted
    data (e.g. up to 2035) remains intact and accessible.
    """
    if df is None or df.empty:
        return df

    col = year_col
    if col not in df.columns:
        for c in ["calendar_year", "year", "year_id", "fiscal_year"]:
            if c in df.columns:
                col = c
                break
        else:
            return df

    start_yr, _ = get_year_filter()
    try:
        mask = pd.to_numeric(df[col], errors="coerce") >= start_yr
        return df[mask].copy()
    except Exception:
        return df

