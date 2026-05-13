import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(layout="wide")
st.title("Metrics Dashboard")

DATA_PATH = "data"

# --------------------------------------------
# LOAD DATA
# --------------------------------------------
@st.cache_data
def load_csv(path):
    return pd.read_csv(path)

# datasets disponibles
files = [f for f in os.listdir(DATA_PATH) if f.endswith(".csv") and f != "metrics.csv"]
selected_file = st.sidebar.selectbox("Dataset", files)

df = load_csv(os.path.join(DATA_PATH, selected_file))

# métricas posibles (catálogo)
metrics_df = load_csv(os.path.join(DATA_PATH, "metrics.csv"))
all_metrics = metrics_df.columns.tolist()

# --------------------------------------------
# DETECTAR MÉTRICAS DISPONIBLES
# --------------------------------------------
available_metrics = [m for m in all_metrics if m in df.columns]

if len(available_metrics) < 2:
    st.error("No hay suficientes métricas en el dataset")
    st.stop()

# --------------------------------------------
# SELECTORES
# --------------------------------------------
x_metric = st.sidebar.selectbox("Eje X", available_metrics, index=0)
y_metric = st.sidebar.selectbox("Eje Y", available_metrics, index=1)

# --------------------------------------------
# FILTRO EN X
# --------------------------------------------
min_val = float(df[x_metric].min())
max_val = float(df[x_metric].max())

x_range = st.sidebar.slider(
    f"Rango {x_metric}",
    min_val,
    max_val,
    (min_val, max_val)
)

filtered_df = df[
    (df[x_metric] >= x_range[0]) &
    (df[x_metric] <= x_range[1])
]



# --------------------------------------------
# PLOT
# --------------------------------------------
fig = px.scatter(
    filtered_df,
    x=x_metric,
    y=y_metric,
    hover_data=["id"] if "id" in df.columns else None,
)

st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------
# PREVIEW
# --------------------------------------------
with st.expander("Datos"):
    st.dataframe(filtered_df[[x_metric, y_metric]].head(50))