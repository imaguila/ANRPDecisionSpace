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
# SELECTORES SIN DUPLICADOS
# --------------------------------------------

# X
x_metric = st.sidebar.selectbox("Eje X", available_metrics)

# Y
y_options = [m for m in available_metrics if m != x_metric]
y_metric = st.sidebar.selectbox("Eje Y", y_options)

# SIZE
size_options = [None] + [m for m in available_metrics if m not in [x_metric, y_metric]]
size_metric = st.sidebar.selectbox("Tamaño (opcional)", size_options)

# COLOR
excluded = [x_metric, y_metric]
if size_metric:
    excluded.append(size_metric)

color_options = [None] + [m for m in available_metrics if m not in excluded]
color_metric = st.sidebar.selectbox("Color (opcional)", color_options)

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
# PREPARAR DATOS (PORCENTAJES)
# --------------------------------------------
plot_df = filtered_df.copy()

metrics_to_check = [x_metric, y_metric, size_metric, color_metric]

for m in metrics_to_check:
    if m and plot_df[m].min() >= 0 and plot_df[m].max() <= 1:
        plot_df[m] = plot_df[m] * 100

# --------------------------------------------
# PLOT
# --------------------------------------------
fig = px.scatter(
    plot_df,
    x=x_metric,
    y=y_metric,
    size=size_metric if size_metric else None,
    color=color_metric if color_metric else None,
    hover_data=["id"] if "id" in df.columns else None,
)

# --------------------------------------------
# ETIQUETAS
# --------------------------------------------
if filtered_df[x_metric].max() <= 1:
    fig.update_xaxes(title=f"{x_metric} (%)")
else:
    fig.update_xaxes(title=x_metric)

if filtered_df[y_metric].max() <= 1:
    fig.update_yaxes(title=f"{y_metric} (%)")
else:
    fig.update_yaxes(title=y_metric)

# --------------------------------------------
# FORMATO EJES
# --------------------------------------------
if filtered_df[x_metric].max() <= 1:
    fig.update_xaxes(tickformat=".1f", ticksuffix="%")

if filtered_df[y_metric].max() <= 1:
    fig.update_yaxes(tickformat=".1f", ticksuffix="%")

# --------------------------------------------
# HOVER FORMAT
# --------------------------------------------
hover_parts = []

# X
if filtered_df[x_metric].max() <= 1:
    hover_parts.append(f"{x_metric}: %{{x:.1f}}%")
else:
    hover_parts.append(f"{x_metric}: %{{x:.2f}}")

# Y
if filtered_df[y_metric].max() <= 1:
    hover_parts.append(f"{y_metric}: %{{y:.1f}}%")
else:
    hover_parts.append(f"{y_metric}: %{{y:.2f}}")

fig.update_traces(hovertemplate="<br>".join(hover_parts))

# --------------------------------------------
# SHOW
# --------------------------------------------
st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------
# PREVIEW
# --------------------------------------------
with st.expander("Datos"):
    cols = [x_metric, y_metric]
    if size_metric:
        cols.append(size_metric)
    if color_metric:
        cols.append(color_metric)

    st.dataframe(filtered_df[cols].head(50))