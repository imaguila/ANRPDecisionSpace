import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(layout="wide")
st.title("Multiobjective Optimization Dashboard")

# --------------------------------------------
# CONFIG
# --------------------------------------------
DATA_PATH = "data"

# --------------------------------------------
# LOAD DATA
# --------------------------------------------
@st.cache_data
def load_data(path):
    return pd.read_csv(path)

files = [f for f in os.listdir(DATA_PATH) if f.endswith(".csv")]

if not files:
    st.error("No hay datasets en la carpeta data/")
    st.stop()

selected_file = st.sidebar.selectbox("Selecciona dataset", files)

df = load_data(os.path.join(DATA_PATH, selected_file))

# --------------------------------------------
# VALIDATION
# --------------------------------------------
coverage_cols = [c for c in df.columns if c.startswith("stcov")]

if len(coverage_cols) == 0:
    st.error("El dataset no tiene columnas stcov_*")
    st.stop()

# --------------------------------------------
# FEATURES
# --------------------------------------------
df["mean_coverage"] = df[coverage_cols].mean(axis=1)

# --------------------------------------------
# SIDEBAR
# --------------------------------------------
st.sidebar.markdown("### Filtros")

max_effort = st.sidebar.slider(
    "Max effort",
    float(df["effort"].min()),
    float(df["effort"].max()),
    float(df["effort"].max())
)

filtered = df[df["effort"] <= max_effort]

st.sidebar.markdown("### Info dataset")
st.sidebar.write("Filas:", df.shape[0])
st.sidebar.write("Columnas:", df.shape[1])

# --------------------------------------------
# MAIN LAYOUT
# --------------------------------------------
col1, col2 = st.columns([2, 1])

# --------------------------------------------
# SCATTER
# --------------------------------------------
with col1:
    st.subheader("Effort vs Satisfaction")

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
# COVERAGE
# --------------------------------------------
with col2:
    st.subheader("Coverage")

    coverage_fig = px.line(
        filtered,
        x="id",
        y=coverage_cols,
    )

    st.plotly_chart(coverage_fig, use_container_width=True)

# --------------------------------------------
# DATA PREVIEW
