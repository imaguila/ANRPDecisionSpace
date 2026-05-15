import streamlit as st
import pandas as pd
import plotly.express as px
import os
import plotly.graph_objects as go

# --------------------------------------------
# CONFIGURACIÓN Y CARGA
# --------------------------------------------
st.set_page_config(layout="wide")
st.title("Assisted Next Release Problem")
DATA_PATH = "data"

@st.cache_data
def load_csv(path):
    return pd.read_csv(path)

# --------------------------------------------
# FUNCIONES DE RENDERIZADO (MODULARIZADAS)
# --------------------------------------------
def render_scatter_plot(df, x, y, size, color_col, show_ids, key):
    # Forzamos modo texto si show_ids es True
    fig = px.scatter(
        df, x=x, y=y, size=size,
        color=color_col,
        text="label" if show_ids else None,
        symbol="highlight",
        symbol_map={True: "x", False: "circle"},
        color_discrete_sequence=px.colors.qualitative.Plotly # Colores sólidos
    )
    
    fig.update_traces(
        textposition="top right",
        textfont=dict(size=10),
        marker=dict(size=10),
        mode='markers+text' if show_ids else 'markers'
    )
    st.plotly_chart(fig, use_container_width=True, key=key)

def plot_radar(selected_df, available_metrics):
    st.markdown("### Detailed review of selected solution")
    opciones = selected_df["id"].unique()
    compare_ids = st.multiselect("Pick solutions to compare (max 4 recommended)", opciones)

    if len(compare_ids) < 2:
        st.info("Select at least 2 solutions to compare")
        return

    compare_df = selected_df[selected_df["id"].isin(compare_ids)].copy()
    compare_metrics = [m for m in available_metrics if pd.api.types.is_numeric_dtype(compare_df[m])]

    # Normalización relativa al grupo comparado
    for m in compare_metrics:
        min_v, max_v = compare_df[m].min(), compare_df[m].max()
        if max_v > min_v:
            compare_df[m] = (compare_df[m] - min_v) / (max_v - min_v)

    fig = go.Figure()
    for _, row in compare_df.iterrows():
        values = row[compare_metrics].tolist()
        values.append(values[0])
        fig.add_trace(go.Scatterpolar(
            r=values, theta=compare_metrics + [compare_metrics[0]],
            mode='lines', fill='toself', name=f"ID {int(row['id'])}"
        ))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,1])), showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------
# LOGICA DE DATOS
# --------------------------------------------
files = [f for f in os.listdir(DATA_PATH) if f.endswith(".csv") and "metrics" not in f]
if not files:
    st.error("No datasets found"); st.stop()

selected_file = st.sidebar.selectbox("Dataset", files)
df = load_csv(os.path.join(DATA_PATH, selected_file))

opt_df = load_csv(os.path.join(DATA_PATH, "optimization_metrics.csv"))
qual_df = load_csv(os.path.join(DATA_PATH, "quality_metrics.csv"))
available_metrics = [m for m in list(opt_df.columns) + list(qual_df.columns) if m in df.columns]
available_qual = [m for m in qual_df.columns if m in df.columns]

# --------------------------------------------
# SESSION STATE Y BOTONES
# --------------------------------------------
if "groups" not in st.session_state: st.session_state.groups = []
if "show_comparison" not in st.session_state: st.session_state.show_comparison = False

if st.sidebar.button("Reset graphs"): 
    st.session_state.groups = []; st.rerun()

# Lógica de exclusión para el botón Add
used_metrics_all = [m for g in st.session_state.groups for m in g if m]
remaining_metrics = [m for m in available_metrics if m not in used_metrics_all]

if len(remaining_metrics) >= 2:
    if st.sidebar.button("Add graph"):
        st.session_state.groups.append([None, None, None])
        st.rerun()

if st.sidebar.button("Show/Hide comparison"):
    st.session_state.show_comparison = not st.session_state.show_comparison
    st.rerun()

show_ids = st.sidebar.checkbox("Show IDs on plots", value=False)

# --------------------------------------------
# FILTROS
# --------------------------------------------
st.sidebar.markdown("### Filters")
filtered_df = df.copy()
for m in available_metrics:
    if pd.api.types.is_numeric_dtype(df[m]):
        min_v, max_v = float(df[m].min()), float(df[m].max())
        if min_v != max_v:
            val_range = st.sidebar.slider(f"{m}", min_v, max_v, (min_v, max_v), key=f"f_{m}")
            filtered_df = filtered_df[(filtered_df[m] >= val_range[0]) & (filtered_df[m] <= val_range[1])]

# --------------------------------------------
# SELECCIÓN (SCORE / RANKING)
# --------------------------------------------
mode = st.sidebar.selectbox("Selection mode", ["None", "Score-based", "Ranking-based"])
selected_df = filtered_df.copy()
threshold = 0

if mode == "Score-based":
    m_max = st.sidebar.multiselect("Maximize", available_qual)
    m_min = st.sidebar.multiselect("Minimize", [m for m in available_qual if m not in m_max])
    if m_max or m_min:
        score = 0
        for m in m_max + m_min:
            mi, ma = selected_df[m].min(), selected_df[m].max()
            norm = (selected_df[m] - mi) / (ma - mi) if ma > mi else 0
            score = (score + norm) if m in m_max else (score - norm)
        selected_df["score"] = score
        n = st.sidebar.slider("Top N", 1, min(50, len(selected_df)), 10)
        selected_df = selected_df.sort_values("score", ascending=False).head(n)
        threshold = 1

elif mode == "Ranking-based":
    sel_metrics = st.sidebar.multiselect("Quality metrics", available_qual)
    n_top = st.sidebar.slider("Top N per metric", 1, min(50, len(filtered_df)), 10)
    if sel_metrics:
        ranks = []
        for m in sel_metrics:
            goal = st.sidebar.selectbox(f"Goal for {m}", ["Maximize", "Minimize"], key=f"g_{m}")
            ranks.append(filtered_df.sort_values(m, ascending=(goal == "Minimize")).head(n_top))
        counts = pd.concat(ranks).groupby("id").size().reset_index(name="count")
        selected_df = filtered_df.merge(counts, on="id", how="left").fillna(0)
        threshold = max(1, len(sel_metrics) - 1)
        selected_df["count"] = selected_df["count"].astype(int).astype(str) # Colores sólidos
        selected_df = selected_df.sort_values("count", ascending=False)

# --------------------------------------------
# HIGHLIGHT Y LABELS
# --------------------------------------------
selected_ids = st.multiselect("Select solutions", selected_df["id"].unique())
selected_df["highlight"] = selected_df["id"].isin(selected_ids)

if show_ids:
    if mode == "None":
        selected_df["label"] = selected_df["id"].astype(str)
    else:
        # Usamos int() para la comparación aunque sea string para el color
        selected_df["label"] = selected_df.apply(
            lambda r: str(int(r["id"])) if (r["highlight"] or int(r.get("count", 0)) >= threshold) else "", axis=1
        )
else:
    selected_df["label"] = ""

# --------------------------------------------
# DIBUJAR GRÁFICOS (CON EXCLUSIÓN MUTUA)
# --------------------------------------------
color_col = "count" if "count" in selected_df.columns else None

for i, group in enumerate(st.session_state.groups):
    st.subheader(f"Graph {i+1}")
    
    # Esta es tu lógica original de exclusión recuperada:
    other_groups_metrics = [m for idx, g in enumerate(st.session_state.groups) if idx != i for m in g if m]
    available_here = [m for m in available_metrics if m not in other_groups_metrics]

    if len(available_here) < 2:
        st.warning("Not enough metrics remaining for this graph.")
        continue

    col1, col2, col3 = st.columns(3)
    with col1:
        x = st.selectbox(f"X Axis {i}", available_here, key=f"x_{i}")
    with col2:
        y_opts = [m for m in available_here if m != x]
        y = st.selectbox(f"Y Axis {i}", y_opts, key=f"y_{i}")
    with col3:
        s_opts = [None] + [m for m in available_here if m not in [x, y]]
        size = st.selectbox(f"Size {i}", s_opts, key=f"size_{i}")

    st.session_state.groups[i] = [x, y, size]

    colA, colB = st.columns(2)
    with colA:
        render_scatter_plot(selected_df, x, y, None, color_col, show_ids, key=f"plot_a_{i}")
    with colB:
        if size:
            render_scatter_plot(selected_df, x, size, y, color_col, show_ids, key=f"plot_b_{i}")
        else:
            st.info("Add a third dimension")

# --------------------------------------------
# COMPARISON Y PREVIEW
# --------------------------------------------
if st.session_state.show_comparison:
    plot_radar(selected_df, available_metrics)

with st.expander("Data preview"):
    st.dataframe(selected_df.head(100))