
import os
import pandas as pd
import streamlit as st


@st.cache_data
def load_csv(path):
    return pd.read_csv(path)


def get_metric_sets(df, data_path):
    """Load optimization/quality metric catalogs and intersect them with the current dataframe."""
    opt_df = load_csv(os.path.join(data_path, "optimization_metrics.csv"))
    qual_df = load_csv(os.path.join(data_path, "quality_metrics.csv"))

    available_metrics = [m for m in list(opt_df.columns) + list(qual_df.columns) if m in df.columns]
    available_opt = [m for m in opt_df.columns if m in df.columns]
    available_qual = [m for m in qual_df.columns if m in df.columns]

    return available_opt, available_qual, available_metrics
