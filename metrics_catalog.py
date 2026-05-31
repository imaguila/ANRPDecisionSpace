import os
import pandas as pd
import streamlit as st
from column_rules import is_excluded_column


@st.cache_data
def load_csv(path):
    return pd.read_csv(path)


def get_metric_sets(df, data_path):
    """
    Returns:
        - available_opt: optimization objectives present in df
        - available_qual: quality attributes present in df
        - available_metrics: union of both
    """

    opt_df = load_csv(os.path.join(data_path, "optimization_metrics.csv"))
    qual_df = load_csv(os.path.join(data_path, "quality_metrics.csv"))

    opt_catalog = list(opt_df.columns)
    qual_catalog = list(qual_df.columns)

    # Keep only numeric, non-structural columns
    analysis_cols = [
        c for c in df.columns
        if pd.api.types.is_numeric_dtype(df[c]) and not is_excluded_column(c)
    ]

    # Optimization objectives explicitly listed in the catalog
    available_opt = [c for c in analysis_cols if c in opt_catalog]

    # Known quality attributes from the catalog
    available_qual_catalog = [c for c in analysis_cols if c in qual_catalog]

    # Extra uploaded numeric attributes not in any catalog:
    # treat them as custom quality attributes
    available_qual_extra = [
        c for c in analysis_cols
        if c not in opt_catalog and c not in qual_catalog
    ]

    available_qual = available_qual_catalog + available_qual_extra
    available_metrics = available_opt + available_qual

    return available_opt, available_qual, available_metrics