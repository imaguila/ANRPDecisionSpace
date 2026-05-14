import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# --------------------------------------------
# CONFIGURACIÓN Y CONSTANTES
# --------------------------------------------
st.set_page_config(layout="wide", page_title="Next Release Problem")
DATA_PATH = "data"

# --------------------------------------------
# FUNCIONES DE UTILIDAD (MODULARIZACIÓN)
# --------------------------------------------

@st.cache_data
def load_csv(path):
    """Carga segura de archivos CSV."""
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()

def normalize_series(series):
    """Aplica Min-Max scaling evitando división por cero."""
    min_val, max_val = series.min(), series.max()
    if max_val > min_val:
        return (series - min_val) / (max_val - min_val)
    return series * 0.0

def render_scatter_plot(df, x, y, size, color_col, show_ids):
    """Renderiza un gráfico de dispersión con configuración estándar."""
    label_col = "label" if show_ids else None
    
    fig = px.scatter(
        df, x=x, y=y, size=size,
        color=color_col,
        text=label_col,
        symbol="highlight",
        symbol_map={True: "x", False: "circle"},
        hover_data=["id"]
    )
    
    fig.update_traces(
        textposition="top right",
        textfont=dict(size=10),
        marker=dict(size=8, line=dict(width=1, color='DarkSlateGrey'))
    )
    return fig

def plot_radar(selected_df, available_metrics):
    """Genera el gráfico de radar comparativo."""
    st.markdown("---")
    st.subheader("Detailed Comparison (Radar)")

    unique_ids = selected_df["id"].unique()
    compare_ids = st.multiselect("Pick solutions to compare (max 5)", unique_ids)

    if len(compare_ids) < 2:
        st.info("Select at least 2 solutions to compare")
        return

    compare_df = selected_df[selected_df["id"].isin(compare_ids)].copy()
    num_metrics = [m for m in available_metrics if pd.api.types.is_numeric_dtype(compare_df[m])]

    # Normalizar solo para el radar
    radar_data = compare_df.copy()
    for m in num_metrics:
        radar_data[m] = normalize_series(radar_data[m])

    fig = go.Figure()
    for _, row in radar_data.iterrows():
        values = row[num_metrics].tolist()
        values.append(values[0]) # Cerrar el círculo
        fig.add_trace(go.Scatterpolar(
            r=values, 
            theta=num_metrics + [num_metrics[0]],
            mode='lines', 
            name=f"ID {int(row['id'])}"
        ))

    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------
# LOGICA DE DATOS
# --------------------------------------------
st.title("Assisted Next Release Problem")

# Cargar archivos disponibles
if not os.path.exists(DATA_PATH):
    st.error(f"Folder '{DATA_PATH}' not found.")
    st.stop()

files = [f for f in os.listdir(DATA_PATH) if f.endswith(".csv") and "metrics" not in f]
if not files:
    st.error("No datasets found")
    st.stop()

selected_file = st.sidebar.selectbox("Dataset", files)
df = load_csv(os.path.join(DATA_PATH, selected_file))

# Cargar métricas de configuración
opt_df = load_csv(os.path.join(DATA_PATH, "optimization_metrics.csv"))
qual_df = load_csv(os.path.join(DATA_PATH, "quality_metrics.csv"))

available_opt = [m for m in opt_df.columns if m in df.columns]
available_qual = [m for m in qual_df.columns if m in df.columns]
available_metrics = available_opt + available_qual

if len(available_metrics) < 2:
    st.error("Not enough metrics found in the CSV columns.")
    st.stop()

# --------------------------------------------
# ESTADO DE SESIÓN Y SIDEBAR
# --------------------------------------------
if "groups" not in st.session_state: st.session_state.groups = []
if "show_comparison" not in st.session_state: st.session_state.show_comparison = False

if st.sidebar.button("Reset graphs"): st.session_state.groups = []
if st.sidebar.button("Add graph"): st.session_state.groups.append([None, None, None])
if st.sidebar.button("Toggle Comparison View"): st.session_state.show_comparison = not st.session_state.show_comparison

show_ids = st.sidebar.checkbox("Show IDs on plots", value=False)

# --------------------------------------------
# FILTROS DINÁMICOS
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
# MODOS DE SELECCIÓN
# --------------------------------------------
mode = st.sidebar.selectbox("Selection mode", ["None", "Score-based", "Ranking-based"])
selected_df = filtered_df.copy()
threshold = 0

if mode == "Score-based":
    m_max = st.sidebar.multiselect("Maximize", available_qual)
    m_min = st.sidebar.multiselect("Minimize", [m for m in available_qual if m not in m_max])
    
    if m_max or m_min:
        score = 0
        for m in m_max: score += normalize_series(selected_df[m])
        for m in m_min: score -= normalize_series(selected_df[m])
        selected_df["score"] = score
        n_top = st.sidebar.slider("Top N", 1, min(50, len(selected_df)), 10)
        selected_df = selected_df.sort_values("score", ascending=False).head(n_top)
        threshold = 1

elif mode == "Ranking-based":
    sel_metrics = st.sidebar.multiselect("Metrics", available_qual)
    n_top = st.sidebar.slider("Top N per metric", 1, min(50, len(selected_df)), 10)
    
    if sel_metrics:
        rank_dfs = []
        for m in sel_metrics:
            goal = st.sidebar.selectbox(f"Goal: {m}", ["Max", "Min"], key=f"g_{m}")
            rank_dfs.append(filtered_df.sort_values(m, ascending=(goal == "Min")).head(n_top))
        
        counts = pd.concat(rank_dfs).groupby("id").size().reset_index(name="count")
        selected_df = filtered_df.merge(counts, on="id", how="left").fillna(0)
        selected_df = selected_df.sort_values("count", ascending=False)
        threshold = max(1, len(sel_metrics) - 1)

# --------------------------------------------
# HIGHLIGHT Y ETIQUETAS
# --------------------------------------------
selected_ids = st.multiselect("Select solutions to highlight", selected_df["id"].unique())
selected_df["highlight"] = selected_df["id"].isin(selected_ids)

if show_ids:
    count_col = "count" if "count" in selected_df.columns else "id" # Fallback
    selected_df["label"] = selected_df.apply(
        lambda r: str(int(r["id"])) if r["highlight"] or (mode != "None" and r.get("count", 0) >= threshold) else "", 
        axis=1
    )

# --------------------------------------------
# RENDERIZADO DE GRÁFICOS
# --------------------------------------------
color_param = "count" if "count" in selected_df.columns else None

for i, group in enumerate(st.session_state.groups):
    st.subheader(f"Graph {i+1}")
    cols = st.columns(3)
    
    with cols[0]: x = st.selectbox(f"X axis", available_metrics, key=f"x{i}")
    with cols[1]: y = st.selectbox(f"Y axis", [m for m in available_metrics if m != x], key=f"y{i}")
    with cols[2]: size = st.selectbox(f"Size", [None] + [m for m in available_metrics if m not in [x, y]], key=f"s{i}")
    
    st.session_state.groups[i] = [x, y, size]
    
    plot_cols = st.columns(2)
    with plot_cols[0]:
        st.plotly_chart(render_scatter_plot(selected_df, x, y, None, color_param, show_ids), use_container_width=True)
    with plot_cols[1]:
        if size:
            st.plotly_chart(render_scatter_plot(selected_df, x, size, y, color_param, show_ids), use_container_width=True)
        else:
            st.info("Select a 'Size' metric to enable the second plot.")

# --------------------------------------------
# COMPARISON & PREVIEW
# --------------------------------------------
if st.session_state.show_comparison:
    plot_radar(selected_df, available_metrics)

with st.expander("Data Preview"):
    st.dataframe(selected_df.head(100).style.apply(
        lambda r: ['background-color: #3e3e3e' if r["highlight"] else '' for _ in r], axis=1
    ))