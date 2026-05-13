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


plot_df = filtered_df.copy()

# detectar métricas en [0,1] y convertir a %
metrics_to_check = [x_metric, y_metric, size_metric, color_metric]

for m in metrics_to_check:
    if m and plot_df[m].max() <= 1:
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

labels = {}

for m in [x_metric, y_metric, size_metric, color_metric]:
    if m and filtered_df[m].max() <= 1:
        labels[m] = f"{m} (%)"

fig.update_layout(xaxis_title=labels.get(x_metric, x_metric),
                  yaxis_title=labels.get(y_metric, y_metric))

# añadir símbolo % si procede
if filtered_df[x_metric].max() <= 1:
    fig.update_xaxes(ticksuffix="%")

if filtered_df[y_metric].max() <= 1:
    fig.update_yaxes(ticksuffix="%")
    
# formato de porcentajes
for axis in ["xaxis", "yaxis"]:
    fig.update_layout(**{
        axis: dict(tickformat=".1f")  # 1 decimal
    })



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