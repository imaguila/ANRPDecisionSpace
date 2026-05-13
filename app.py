import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.title("Multiobjective Optimization Dashboard")

df = pd.read_csv("dataset.csv")

coverage_cols = [c for c in df.columns if c.startswith("stcov")]

df["mean_coverage"] = df[coverage_cols].mean(axis=1)

# --------------------------------------------
# Sidebar
# --------------------------------------------

max_effort = st.sidebar.slider(
    "Max effort",
    float(df["effort"].min()),
    float(df["effort"].max()),
    float(df["effort"].max())
)

filtered = df[df["effort"] <= max_effort]

# --------------------------------------------
# Scatter
# --------------------------------------------

fig = px.scatter(
    filtered,
    x="effort",
    y="satisfaction",
    size="mean_coverage",
    color="squandering",
    hover_data=["id"],
)

st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------
# Coverage
# --------------------------------------------

coverage_fig = px.line(
    filtered,
    x="id",
    y=coverage_cols,
)

st.plotly_chart(coverage_fig, use_container_width=True)