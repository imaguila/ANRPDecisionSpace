import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(layout="wide")
st.title("Assisted NRP")

DATA_PATH = "data"

# --------------------------------------------
# LOAD DATA
# --------------------------------------------
@st.cache_data
def load_csv(path):
    return pd.read_csv(path)

# problems
files = [f for f in os.listdir(DATA_PATH) if f.endswith(".csv") and f != "metrics.csv"]
selected_file = st.sidebar.selectbox("Dataset", files)

df = load_csv(os.path.join(DATA_PATH, selected_file))

# métricas posibles (catálogo)
metrics_df = load_csv(os.path.join(DATA_PATH, "metrics.csv"))
all_metrics = metrics_df.columns.tolist()

# --------------------------------------------
# METRICS DETECTION
# --------------------------------------------
available_metrics = [m for m in all_metrics if m in df.columns]

if len(available_metrics) < 2:
    st.error("There are not enough metrics")
    st.stop()

# --------------------------------------------
# SELECTORS No  duplicated
# --------------------------------------------

# X
x_metric = st.sidebar.selectbox("X", available_metrics)

# Y
y_options = [m for m in available_metrics if m != x_metric]
y_metric = st.sidebar.selectbox("Y", y_options)

# SIZE
size_options = [None] + [m for m in available_metrics if m not in [x_metric, y_metric]]
size_metric = st.sidebar.selectbox("Dot size (optional)", size_options)

# COLOR
excluded = [x_metric, y_metric]
if size_metric:
    excluded.append(size_metric)

color_options = [None] + [m for m in available_metrics if m not in excluded]
color_metric = st.sidebar.selectbox("Color (optional)", color_options)
# --------------------------------------------
# FILTERS (todas las dimensiones)
# --------------------------------------------
st.sidebar.markdown("### Filters")

filtered_df = df.copy()

# X
x_range = st.sidebar.slider(
    f"Range {x_metric}",
    float(df[x_metric].min()),
    float(df[x_metric].max()),
    (float(df[x_metric].min()), float(df[x_metric].max()))
)

filtered_df = filtered_df[
    (filtered_df[x_metric] >= x_range[0]) &
    (filtered_df[x_metric] <= x_range[1])
]

# Y
y_range = st.sidebar.slider(
    f"Range {y_metric}",
    float(df[y_metric].min()),
    float(df[y_metric].max()),
    (float(df[y_metric].min()), float(df[y_metric].max()))
)

filtered_df = filtered_df[
    (filtered_df[y_metric] >= y_range[0]) &
    (filtered_df[y_metric] <= y_range[1])
]

# SIZE
if size_metric:
    size_range = st.sidebar.slider(
        f"Range {size_metric}",
        float(df[size_metric].min()),
        float(df[size_metric].max()),
        (float(df[size_metric].min()), float(df[size_metric].max()))
    )

    filtered_df = filtered_df[
        (filtered_df[size_metric] >= size_range[0]) &
        (filtered_df[size_metric] <= size_range[1])
    ]

# COLOR
if color_metric:
    color_range = st.sidebar.slider(
        f"Range {color_metric}",
        float(df[color_metric].min()),
        float(df[color_metric].max()),
        (float(df[color_metric].min()), float(df[color_metric].max()))
    )

    filtered_df = filtered_df[
        (filtered_df[color_metric] >= color_range[0]) &
        (filtered_df[color_metric] <= color_range[1])
    ]

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

fig.update_xaxes(title=x_metric)
fig.update_yaxes(title=y_metric)

# --------------------------------------------
# HOVER FORMAT (2 decimales, sin errores)
# --------------------------------------------
hover_parts = [
    f"{x_metric}: %{{x:.2f}}",
    f"{y_metric}: %{{y:.2f}}",
]

# SIZE
if size_metric:
    hover_parts.append(f"{size_metric}: %{{marker.size:.2f}}")

# COLOR
if color_metric:
    hover_parts.append(f"{color_metric}: %{{marker.color:.2f}}")

fig.update_traces(hovertemplate="<br>".join(hover_parts))

# --------------------------------------------
# SHOW
# --------------------------------------------
st.plotly_chart(fig, use_container_width=True)
