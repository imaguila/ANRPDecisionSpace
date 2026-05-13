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
# DETECTAR MÉTRICAS PORCENTUALES (ANTES)
# --------------------------------------------
is_percent = {}

metrics_to_check = [x_metric, y_metric, size_metric, color_metric]

for m in metrics_to_check:
    if m and df[m].min() >= 0 and df[m].max() <= 1:
        is_percent[m] = True
    else:
        is_percent[m] = False

# --------------------------------------------
# PREPARAR DATOS (CONVERSIÓN)
# --------------------------------------------
plot_df = filtered_df.copy()

for m in metrics_to_check:
    if m and is_percent[m]:
        plot_df[m] = plot_df[m] * 100

# --------------------------------------------
# PLOT
# --------------------------------------------
fig = px.scatter(
    filtered_df,
    x=x_metric,
    y=y_metric,
    size=size_metric if size_metric else None,
    color=color_metric if color_metric else None,
    hover_data=["id"] if "id" in df.columns else None,
)

# --------------------------------------------
# ETIQUETAS (solo X e Y)
# --------------------------------------------
if is_percent.get(x_metric, False):
    fig.update_xaxes(title=f"{x_metric} (%)")
else:
    fig.update_xaxes(title=x_metric)

if is_percent.get(y_metric, False):
    fig.update_yaxes(title=f"{y_metric} (%)")
else:
    fig.update_yaxes(title=y_metric)

# --------------------------------------------
# FORMATO EJES (solo X e Y)
# --------------------------------------------
if is_percent.get(x_metric, False):
    fig.update_xaxes(tickformat=".1f", ticksuffix="%")

if is_percent.get(y_metric, False):
    fig.update_yaxes(tickformat=".1f", ticksuffix="%")

# --------------------------------------------
# HOVER FORMAT (completo y consistente)
# --------------------------------------------
hover_parts = []

# X
if is_percent.get(x_metric, False):
    hover_parts.append(f"{x_metric}: %{{x:.1f}}%")
else:
    hover_parts.append(f"{x_metric}: %{{x:.2f}}")

# Y
if is_percent.get(y_metric, False):
    hover_parts.append(f"{y_metric}: %{{y:.1f}}%")
else:
    hover_parts.append(f"{y_metric}: %{{y:.2f}}")

# SIZE
if size_metric:
    if is_percent.get(size_metric, False):
        hover_parts.append(f"{size_metric}: %{{marker.size:.1f}}%")
    else:
        hover_parts.append(f"{size_metric}: %{{marker.size:.2f}}")

# COLOR
if color_metric:
    if is_percent.get(color_metric, False):
        hover_parts.append(f"{color_metric}: %{{marker.color:.1f}}%")
    else:
        hover_parts.append(f"{color_metric}: %{{marker.color:.2f}}")

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