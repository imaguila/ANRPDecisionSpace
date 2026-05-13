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

# datasets
files = [f for f in os.listdir(DATA_PATH) if f.endswith(".csv") and f != "metrics.csv"]

if not files:
    st.error("No datasets found")
    st.stop()

selected_file = st.sidebar.selectbox("Dataset", files)
df = load_csv(os.path.join(DATA_PATH, selected_file))


# --------------------------------------------
# METRICS CATALOG 
# --------------------------------------------
metrics_df = pd.read_csv(os.path.join(DATA_PATH, "metrics.csv"), header=None)

optimization_metrics = metrics_df.iloc[0].dropna().tolist()
quality_metrics = metrics_df.iloc[1].dropna().tolist()

# --------------------------------------------
# AVAILABLE METRICS
# --------------------------------------------
available_optimization_metrics = [
    m for m in optimization_metrics if m in df.columns
]

available_quality_metrics = [
    m for m in quality_metrics if m in df.columns
]

available_metrics = available_optimization_metrics + available_quality_metrics

if len(available_metrics) < 2:
    st.error("There are not enough metrics")
    st.stop()

# --------------------------------------------
# SESSION STATE (graphs)
# --------------------------------------------
if "groups" not in st.session_state:
    st.session_state.groups = []

# reset
if st.sidebar.button("Reset graphs"):
    st.session_state.groups = []

# --------------------------------------------
# FILTERS (GLOBAL)
# --------------------------------------------
st.sidebar.markdown("### Filters")

filtered_df = df.copy()

for m in available_metrics:
    min_val = float(df[m].min())
    max_val = float(df[m].max())

    if min_val != max_val:
        val_range = st.sidebar.slider(
            f"{m}",
            min_val,
            max_val,
            (min_val, max_val),
            key=f"filter_{m}"
        )

        filtered_df = filtered_df[
            (filtered_df[m] >= val_range[0]) &
            (filtered_df[m] <= val_range[1])
        ]

# --------------------------------------------
# ADD GRAPH BUTTON
# --------------------------------------------
used_metrics = [m for g in st.session_state.groups for m in g if m]
remaining_metrics = [m for m in available_metrics if m not in used_metrics]

st.sidebar.markdown("### Visualizations")

if len(remaining_metrics) >= 2:
    if st.sidebar.button("Add graph"):
        st.session_state.groups.append([None, None, None])

# --------------------------------------------
# DRAW GRAPHS
# --------------------------------------------
for i, group in enumerate(st.session_state.groups):

    st.subheader(f"Graph {i+1}")

    # recalcular métricas disponibles
    used_metrics = [
        m for idx, g in enumerate(st.session_state.groups)
        if idx != i for m in g if m
    ]

    available = [m for m in available_metrics if m not in used_metrics]

    col1, col2, col3 = st.columns(3)

    with col1:
        x = st.selectbox(f"X {i}", available, key=f"x_{i}")

    with col2:
        y_options = [m for m in available if m != x]
        y = st.selectbox(f"Y {i}", y_options, key=f"y_{i}")

    with col3:
        size_options = [None] + [m for m in available if m not in [x, y]]
        size = st.selectbox(f"Size {i} (optional)", size_options, key=f"size_{i}")

    # guardar selección
    st.session_state.groups[i] = [x, y, size]

    # --------------------------------------------
    # PLOT
    # --------------------------------------------
    fig = px.scatter(
        filtered_df,
        x=x,
        y=y,
        size=size if size else None,
        hover_data=["id"] if "id" in df.columns else None,
    )

    fig.update_xaxes(title=x, tickformat=".2f")
    fig.update_yaxes(title=y, tickformat=".2f")

    # hover limpio
    hover_parts = [
        f"{x}: %{{x:.2f}}",
        f"{y}: %{{y:.2f}}",
    ]

    if size:
        hover_parts.append(f"{size}: %{{marker.size:.2f}}")

    fig.update_traces(hovertemplate="<br>".join(hover_parts))

    st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------
# DATA PREVIEW
# --------------------------------------------
with st.expander("Data preview"):
    st.dataframe(filtered_df.head(100))