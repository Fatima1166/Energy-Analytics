"""
Configuration for Question 3 -- Bottlenecks in Achieving Planned Targets.

NOTE  Benchmarks are no longer defined here.  They are loaded from the
      ``dim_target`` database table by :mod:`core.targets` (with the official
      ARE Policy 2019 renewable-share target layered on top), and the KPI card
      definitions live in ``core.targets.KPI_SPEC``.  Keeping a second copy of
      the targets in this file is what previously let the dashboard show a 10%
      loss benchmark while the database held 28.23%.
"""

DASHBOARD_TITLE = "Bottlenecks in Achieving Planned Targets"
DEFAULT_YEAR_RANGE = (2002, 2035)
DEFAULT_BASELINE_YEAR = 2010
DEFAULT_REFERENCE_YEAR = 2024
PROJECT_END = 2035
