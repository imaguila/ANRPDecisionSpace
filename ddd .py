import streamlit as st
import pandas as pd

from config import PROBLEMAS
from problem import run_pipeline, leer_soluciones

from enrichment import detectar_indicadores_posibles, aplicar_enrichment
from feature_selection import columnas_analisis
from visualization import scatter_plot, radar_plot

# ============================================
# CONFIG
# ============================================

st.set_page_config(layout="wide")
st.title("ANRP Decision Space Explorer")

# ============================================
# INPUT
# ============================================

st.sidebar.markdown("## 🧩 Input and Preparation")

data_mode = st.sidebar.radio(
    "Select data source",
    ["📂 CSV", "🧱 NRP"],
    label_visibility="collapsed"
)

# ============================================
# DATA LOADING
# ============================================

if data_mode == "📂 CSV":

    uploaded_file = st.sidebar.file_uploader("Upload CSV")

    if uploaded_file is None:
        st.stop()

    df = pd.read_csv(uploaded_file)

else:

    problem_name = st.sidebar.selectbox("Dataset", list(PROBLEMAS.keys()))

    config = PROBLEMAS[problem_name]

    df_base = leer_soluciones(config)

    posibles = detectar_indicadores_posibles(df_base)

    selected = st.sidebar.multiselect("Indicators", posibles)

    @st.cache_data
    def build_df(problem, inds):
        return run_pipeline(problem, inds)

    df = build_df(problem_name, selected)

# ============================================
# ENRICHMENT
# ============================================

posibles = detectar_indicadores_posibles(df)

selected = st.sidebar.multiselect("Indicators", posibles)

df = aplicar_enrichment(df, selected)

# ============================================
# FEATURE SELECTION
# ============================================

cols = columnas_analisis(df)

if len(cols) < 2:
    st.error("Not enough metrics")
    st.stop()

# ============================================
# CONTEXT FRAMING
# ============================================

filtered_df = df.copy()

for c in cols:
    min_v, max_v = df[c].min(), df[c].max()

    if min_v != max_v:
        lo, hi = st.sidebar.slider(c, min_v, max_v, (min_v, max_v))
        filtered_df = filtered_df[(filtered_df[c] >= lo) & (filtered_df[c] <= hi)]

# ============================================
# VISUALIZATION
# ============================================

x = st.selectbox("X axis", cols)
y = st.selectbox("Y axis", cols, index=1)

fig = scatter_plot(filtered_df, x, y)

st.plotly_chart(fig)

# ============================================
# SOI
# ============================================

ids = st.multiselect("Select SOI", filtered_df["id"].tolist() if "id" in df else [])

filtered_df["highlight"] = filtered_df["id"].isin(ids) if "id" in df else False

# ============================================
# RADAR
# ============================================

if len(ids) > 0:
    radar = radar_plot(filtered_df[filtered_df["highlight"]], cols[:5])
    st.plotly_chart(radar)