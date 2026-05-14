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
# ADD GRAPH
# --------------------------------------------
used_metrics = [m for g in st.session_state.groups for m in g if m]
remaining_metrics = [m for m in available_metrics if m not in used_metrics]

if len(remaining_metrics) >= 2:
    if st.sidebar.button("Add graph"):
        st.session_state.groups.append([None, None, None])

# --------------------------------------------
# SHOW IDS
# --------------------------------------------
show_ids = st.sidebar.checkbox("Show IDs on plots", value=False)

# --------------------------------------------
# FILTERS
# --------------------------------------------
st.sidebar.markdown("### Filters")
filtered_df = df.copy()

for m in available_metrics:
    if pd.api.types.is_numeric_dtype(df[m]):
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
    ["None", "Score-based", "Ranking-based"]
)

selected_df = filtered_df.copy()

metrics_max, metrics_min, selected_metrics = [], [], []

# --------------------------------------------
# MODE NONE ✅
# --------------------------------------------
if mode == "None":
    pass

# --------------------------------------------
# MODE SCORE
# --------------------------------------------
elif mode == "Score-based":

    metrics_max = st.sidebar.multiselect(
        "Metrics to maximize",
        available_quality_metrics
    )

    metrics_min = st.sidebar.multiselect(
        "Metrics to minimize",
        [m for m in available_quality_metrics if m not in metrics_max]
    )

    if metrics_max or metrics_min:

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

        n_top = st.sidebar.slider(
            "Top N (Score)",
            1,
            min(50, len(temp_df)),
            10
        )

        selected_df = temp_df.sort_values("score", ascending=False).head(n_top)

# --------------------------------------------
# MODE RANKING
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

# --------------------------------------------
# THRESHOLD (solo si NO es None)
# --------------------------------------------
threshold = 0

if mode != "None":

    n_metrics = (
        len(selected_metrics) if mode == "Ranking-based"
        else len(metrics_max) + len(metrics_min)
    )

    threshold = max(1, n_metrics - 1)

    st.sidebar.write(f"Highlight threshold: count ≥ {threshold}")

# --------------------------------------------
# HIGHLIGHT
# --------------------------------------------
selected_ids = st.multiselect("Select solutions", selected_df["id"].unique())

selected_df["highlight"] = selected_df["id"].isin(selected_ids)

# --------------------------------------------
# LABELS
# --------------------------------------------
if show_ids:

    if mode == "None":
        selected_df["label"] = selected_df["id"].astype(str)

    else:
        selected_df["label"] = selected_df.apply(
            lambda row: str(row["id"])
            if row["highlight"] or row.get("count", 0) >= threshold
            else "",
            axis=1
        )

else:
    selected_df["label"] = ""

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
        y = st.selectbox(f"Y {i}", [m for m in available if m != x], key=f"y_{i}")

    with col3:
        size = st.selectbox(
            f"Size {i}",
            [None] + [m for m in available if m not in [x, y]],
            key=f"size_{i}"
        )

    st.session_state.groups[i] = [x, y, size]

    color_col = "count" if "count" in selected_df.columns else None

    colA, colB = st.columns(2)

    with colA:
        fig1 = px.scatter(
            selected_df,
            x=x,
            y=y,
            size=size,
            color=color_col,
            text=selected_df["label"],
            symbol="highlight",
            symbol_map={True: "x", False: "circle"}
        )
        
        # ✅ AQUÍ VA (la mejora)
        fig1.update_traces(
            textposition="top right",
            textfont=dict(size=10),
            marker=dict(size=8)  # opcional pero mejora visibilidad
        )

        st.plotly_chart(fig1, use_container_width=True)

    with colB:
        if size:
            fig2 = px.scatter(
                selected_df,
                x=x,
                y=size,
                size=y,
                color=color_col,
                text=selected_df["label"],
                symbol="highlight"
            )
            # ✅ AQUÍ VA (la mejora)
            fig2.update_traces(
                textposition="top right",
                textfont=dict(size=10),
                marker=dict(size=8)  # opcional pero mejora visibilidad
            )
            st.plotly_chart(fig2, use_container_width=True)
            


        else:
            st.info("Add a third dimension")

# --------------------------------------------
# DATA PREVIEW
# --------------------------------------------
with st.expander("Data preview"):
    st.write(f"Showing {len(selected_df)} solutions")

    cols_show = [c for c in selected_df.columns if c != "highlight"]
    df_preview = selected_df[cols_show].head(100)

    styled_df = df_preview.style.apply(
        lambda row: [
            'background-color: lightyellow' if row["id"] in selected_ids else ''
            for _ in row
        ],
        axis=1
    )

    st.dataframe(styled_df)


def plot_radar(selected_df, available_metrics):

    st.markdown("###  Detailed review of selected solution")

    compare_ids = st.multiselect(
        "Pick solutions to compare (max 4 recommended)",
        selected_df["id"].unique()
    )

    if len(compare_ids) < 2:
        st.info("Select at least 2 solutions to compare")
        return

    compare_df = selected_df[selected_df["id"].isin(compare_ids)].copy()

    # métricas numéricas
    compare_metrics = [
        m for m in available_metrics
        if pd.api.types.is_numeric_dtype(compare_df[m])
    ]

    # ✅ normalizar para comparabilidad
    for m in compare_metrics:
        min_val = compare_df[m].min()
        max_val = compare_df[m].max()

        if max_val > min_val:
            compare_df[m] = (compare_df[m] - min_val) / (max_val - min_val)

    import plotly.graph_objects as go

    fig = go.Figure()

    for _, row in compare_df.iterrows():

        values = row[compare_metrics].tolist()
        values.append(values[0])

        metrics_loop = compare_metrics + [compare_metrics[0]]

        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=metrics_loop,
            mode='lines',   # ✅ solo línea
            name=f"ID {int(row['id'])}"
        ))


    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        title="Solution Comparison (Radar)",
        showlegend=True
    )

    st.plotly_chart(fig, use_container_width=True)    



#####################

# --------------------------------------------
# COMPARISON
# --------------------------------------------
plot_radar(selected_df, available_metrics)
