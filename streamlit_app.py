import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(layout="wide")
st.title("Assisted Next Release Problem")

DATA_PATH = "data"

# --------------------------------------------
# LOAD DATA
# --------------------------------------------
@st.cache_data
def load_csv(path):
    return pd.read_csv(path)

# datasets
files = [f for f in os.listdir(DATA_PATH) if f.endswith(".csv") and "metrics" not in f]

if not files:
    st.error("No datasets found")
    st.stop()

selected_file = st.sidebar.selectbox("Dataset", files)
df = load_csv(os.path.join(DATA_PATH, selected_file))

# --------------------------------------------
# METRICS CATALOG (2 FILES)
# --------------------------------------------
opt_df = load_csv(os.path.join(DATA_PATH, "optimization_metrics.csv"))
optimization_metrics = opt_df.columns.tolist()

qual_df = load_csv(os.path.join(DATA_PATH, "quality_metrics.csv"))
quality_metrics = qual_df.columns.tolist()

# --------------------------------------------
# AVAILABLE METRICS
# --------------------------------------------
available_optimization_metrics = [m for m in optimization_metrics if m in df.columns]
available_quality_metrics = [m for m in quality_metrics if m in df.columns]

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
if st.sidebar.button("Resetr graphs"):
    st.session_state.groups = []


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
# FILTERS
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
# SELECTION MODE (MULTI QUALITY + MIN/MAX)
# --------------------------------------------
st.sidebar.markdown("### Selection")

use_selection = st.sidebar.checkbox("Activate selection mode")

selected_df = filtered_df.copy()

if use_selection:

    if len(available_quality_metrics) == 0:
        st.sidebar.warning("No quality metrics available")
    else:
        # Separated selection
        metrics_max = st.sidebar.multiselect(
            "Metrics to maximize",
            available_quality_metrics,
            key="max_metrics"
        )

        metrics_min = st.sidebar.multiselect(
            "Metrics to minimize",
            [m for m in available_quality_metrics if m not in metrics_max],
            key="min_metrics"
        )

        if len(metrics_max) + len(metrics_min) > 0:

            n_top = st.sidebar.slider(
                "Number of solutions",
                1,
                min(50, len(filtered_df)),
                10
            )

            temp_df = filtered_df.copy()

            # --------------------------------------------
            # NORMALIZACIÓN
            # --------------------------------------------
            for m in metrics_max + metrics_min:
                min_val = temp_df[m].min()
                max_val = temp_df[m].max()

                if max_val > min_val:
                    temp_df[m + "_norm"] = (temp_df[m] - min_val) / (max_val - min_val)
                else:
                    temp_df[m + "_norm"] = 0

            # --------------------------------------------
            # SCORE
            # --------------------------------------------
            score = 0

            if len(metrics_max) > 0:
                score += temp_df[[m + "_norm" for m in metrics_max]].mean(axis=1)

            if len(metrics_min) > 0:
                score -= temp_df[[m + "_norm" for m in metrics_min]].mean(axis=1)

            temp_df["score"] = score

            # seleccionar mejores (siempre max score)
            selected_df = temp_df.sort_values("score", ascending=False).head(n_top)

            st.sidebar.success(f"{len(selected_df)} solutions selected")




# --------------------------------------------
# DRAW GRAPHS
# --------------------------------------------
for i, group in enumerate(st.session_state.groups):

    st.subheader(f"Graph {i+1}")

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
        size = st.selectbox(f"Size {i}", size_options, key=f"size_{i}")

    st.session_state.groups[i] = [x, y, size]

    # --------------------------------------------
    # PLOT
    # --------------------------------------------
    fig = px.scatter(
        selected_df,
        x=x,
        y=y,
        size=size if size else None,
        hover_data=["id"] if "id" in df.columns else None,
    )

    fig.update_xaxes(title=x, tickformat=".2f")
    fig.update_yaxes(title=y, tickformat=".2f")

    hover_parts = [
        f"{x}: %{{x:.2f}}",
        f"{y}: %{{y:.2f}}"
    ]

    if size:
        hover_parts.append(f"{size}: %{{marker.size:.2f}}")

    fig.update_traces(hovertemplate="<br>".join(hover_parts))

    st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------
# DATA PREVIEW
# --------------------------------------------
with st.expander("Data preview"):
    st.write(f"Showing {len(selected_df)} solutions")
    st.dataframe(selected_df.head(100))