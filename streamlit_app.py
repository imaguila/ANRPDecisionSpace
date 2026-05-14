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

files = [f for f in os.listdir(DATA_PATH) if f.endswith(".csv") and "metrics" not in f]

if not files:
    st.error("No datasets found")
    st.stop()

selected_file = st.sidebar.selectbox("Dataset", files)
df = load_csv(os.path.join(DATA_PATH, selected_file))

# --------------------------------------------
# METRICS
# --------------------------------------------
opt_df = load_csv(os.path.join(DATA_PATH, "optimization_metrics.csv"))
optimization_metrics = opt_df.columns.tolist()

qual_df = load_csv(os.path.join(DATA_PATH, "quality_metrics.csv"))
quality_metrics = qual_df.columns.tolist()

available_optimization_metrics = [m for m in optimization_metrics if m in df.columns]
available_quality_metrics = [m for m in quality_metrics if m in df.columns]

available_metrics = available_optimization_metrics + available_quality_metrics

if len(available_metrics) < 2:
    st.error("There are not enough metrics")
    st.stop()

# --------------------------------------------
# SESSION STATE
# --------------------------------------------
if "groups" not in st.session_state:
    st.session_state.groups = []

if st.sidebar.button("Reset graphs"):
    st.session_state.groups = []

# --------------------------------------------
# PREVIEW
# --------------------------------------------
with st.expander("Full preview"):
    st.write(f"Showing all {len(df)} solutions")
    st.dataframe(df, use_container_width=True)

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
# SELECTION MODE
# --------------------------------------------
st.sidebar.markdown("### Selection")

mode = st.sidebar.selectbox(
    "Selection mode",
    ["Score-based", "Ranking-based"]
)

selected_df = filtered_df.copy()

# --------------------------------------------
# MODE 1: SCORE
# --------------------------------------------
if mode == "Score-based":

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

        for m in metrics_max + metrics_min:
            min_val = temp_df[m].min()
            max_val = temp_df[m].max()

            if max_val > min_val:
                temp_df[m + "_norm"] = (temp_df[m] - min_val) / (max_val - min_val)
            else:
                temp_df[m + "_norm"] = 0

        score = 0

        if metrics_max:
            score += temp_df[[m + "_norm" for m in metrics_max]].mean(axis=1)

        if metrics_min:
            score -= temp_df[[m + "_norm" for m in metrics_min]].mean(axis=1)

        temp_df["score"] = score

        selected_df = temp_df.sort_values("score", ascending=False).head(n_top)

        st.sidebar.success(f"{len(selected_df)} solutions selected")

# --------------------------------------------
# MODE 2: RANKING (MIN/MAX POR MÉTRICA)
# --------------------------------------------
elif mode == "Ranking-based":

    selected_metrics = st.sidebar.multiselect(
        "Quality metrics",
        available_quality_metrics
    )

    n_top = st.sidebar.slider(
        "Top N per metric",
        1,
        min(50, len(filtered_df)),
        10
    )

    # dirección por métrica
    metric_goals = {}

    for m in selected_metrics:
        metric_goals[m] = st.sidebar.selectbox(
            f"{m}",
            ["Maximize", "Minimize"],
            key=f"goal_{m}"
        )

    if selected_metrics:

        ranking_lists = []

        for m in selected_metrics:

            goal = metric_goals[m]

            if goal == "Maximize":
                top_df = filtered_df.sort_values(m, ascending=False).head(n_top)
            else:
                top_df = filtered_df.sort_values(m, ascending=True).head(n_top)

            ranking_lists.append(top_df)

        combined_df = pd.concat(ranking_lists)

        counts = combined_df.groupby("id").size().reset_index(name="count")

        selected_df = filtered_df.merge(counts, on="id", how="left")
        selected_df["count"] = selected_df["count"].fillna(0)

        selected_df = selected_df.sort_values("count", ascending=False)

        st.sidebar.success("Ranking computed")

# --------------------------------------------
# ADD GRAPH
# --------------------------------------------
used_metrics = [m for g in st.session_state.groups for m in g if m]
remaining_metrics = [m for m in available_metrics if m not in used_metrics]

if len(remaining_metrics) >= 2:
    if st.sidebar.button("Add graph"):
        st.session_state.groups.append([None, None, None])

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

    color_col = "count" if ("count" in selected_df.columns) else None

    fig = px.scatter(
        selected_df,
        x=x,
        y=y,
        size=size if size else None,
        color=color_col,
        hover_data=["id"] if "id" in df.columns else None,
        color_continuous_scale="Viridis"
    )

    fig.update_xaxes(title=x, tickformat=".2f")
    fig.update_yaxes(title=y, tickformat=".2f")

    hover_parts = [
        f"{x}: %{{x:.2f}}",
        f"{y}: %{{y:.2f}}"
    ]

    if size:
        hover_parts.append(f"{size}: %{{marker.size:.2f}}")

    if color_col:
        hover_parts.append("matches: %{marker.color}")

    fig.update_traces(hovertemplate="<br>".join(hover_parts))

    st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------
# DATA PREVIEW
# --------------------------------------------
with st.expander("Data preview"):
    st.write(f"Showing {len(selected_df)} solutions")
    st.dataframe(selected_df.head(100))