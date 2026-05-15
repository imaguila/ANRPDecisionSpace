import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# --------------------------------------------
# CONFIGURACIÓN
# --------------------------------------------
st.set_page_config(layout="wide")
st.title("Assisted Next Release Problem")
DATA_PATH = "data"

# --------------------------------------------
# FUNCIONES CORE
# --------------------------------------------
@st.cache_data
def load_csv(path):
    return pd.read_csv(path)

def normalize_series(series):
    min_val, max_val = series.min(), series.max()
    if max_val > min_val:
        return (series - min_val) / (max_val - min_val)
    return series * 0.0

# --------------------------------------------
# CARGA DE DATOS
# --------------------------------------------
if not os.path.exists(DATA_PATH):
    st.error("Data folder not found")
    st.stop()

files = [f for f in os.listdir(DATA_PATH) if f.endswith(".csv") and "metrics" not in f]
if not files:
    st.error("No datasets found")
    st.stop()

selected_file = st.sidebar.selectbox("Dataset", files)
df = load_csv(os.path.join(DATA_PATH, selected_file))

opt_df = load_csv(os.path.join(DATA_PATH, "optimization_metrics.csv"))
qual_df = load_csv(os.path.join(DATA_PATH, "quality_metrics.csv"))

available_metrics = [m for m in list(opt_df.columns) + list(qual_df.columns) if m in df.columns]
available_qual = [m for m in qual_df.columns if m in df.columns]

# --------------------------------------------
# ESTADO DE LA SESIÓN
# --------------------------------------------
if "groups" not in st.session_state:
    st.session_state.groups = []
if "show_comparison" not in st.session_state:
    st.session_state.show_comparison = False

if st.sidebar.button("Reset graphs"):
    st.session_state.groups = []
    st.rerun()

# Lógica para añadir gráfico respetando métricas disponibles
used_all = [m for g in st.session_state.groups for m in g if m]
remaining_total = [m for m in available_metrics if m not in used_all]

if len(remaining_total) >= 2:
    if st.sidebar.button("Add graph"):
        # Inicializamos con las dos primeras disponibles
        st.session_state.groups.append([remaining_total[0], remaining_total[1], None])
        st.rerun()

if st.sidebar.button("Show/Hide Comparison"):
    st.session_state.show_comparison = not st.session_state.show_comparison

show_ids = st.sidebar.checkbox("Show IDs on plots", value=False)

# --------------------------------------------
# SIDEBAR: FILTROS
# --------------------------------------------
st.sidebar.markdown("### Filters")
filtered_df = df.copy()
for m in available_metrics:
    if pd.api.types.is_numeric_dtype(df[m]):
        min_v, max_v = float(df[m].min()), float(df[m].max())
        if min_v != max_v:
            v_range = st.sidebar.slider(f"{m}", min_v, max_v, (min_v, max_v), key=f"f_{m}")
            filtered_df = filtered_df[(filtered_df[m] >= v_range[0]) & (filtered_df[m] <= v_range[1])]

# --------------------------------------------
# SIDEBAR: MODOS DE SELECCIÓN
# --------------------------------------------
st.sidebar.markdown("### Selection")
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
        n_top = st.sidebar.slider("Top N", 1, min(100, len(selected_df)), 10)
        selected_df = selected_df.sort_values("score", ascending=False).head(n_top)
        threshold = 1

elif mode == "Ranking-based":
    sel_metrics = st.sidebar.multiselect("Quality metrics", available_qual)
    n_top = st.sidebar.slider("Top N per metric", 1, min(100, len(filtered_df)), 10)
    if sel_metrics:
        ranks = []
        for m in sel_metrics:
            goal = st.sidebar.selectbox(f"Goal for {m}", ["Maximize", "Minimize"], key=f"g_{m}")
            ranks.append(filtered_df.sort_values(m, ascending=(goal == "Minimize")).head(n_top))
        counts = pd.concat(ranks).groupby("id").size().reset_index(name="count")
        selected_df = filtered_df.merge(counts, on="id", how="left").fillna(0)
        threshold = max(1, len(sel_metrics) - 1)
        # Importante: para colores sólidos en Plotly convertimos a string
        selected_df["count"] = selected_df["count"].astype(int).astype(str)
        selected_df = selected_df.sort_values("count", ascending=False)

# --------------------------------------------
# HIGHLIGHT Y ETIQUETAS
# --------------------------------------------
selected_ids = st.multiselect("Unmask specific IDs ▲", selected_df["id"].unique())
selected_df["highlight"] = selected_df["id"].isin(selected_ids)

if show_ids:
    if mode == "Ranking-based":
        # Convertimos count a int solo para comparar con threshold
        selected_df["label"] = selected_df.apply(
            lambda r: str(int(r["id"])) if (r["highlight"] or int(r.get("count", 0)) >= threshold) else "",
            axis=1
        )
    else:
        selected_df["label"] = selected_df["id"].astype(str)
else:
    selected_df["label"] = ""

# --------------------------------------------
# DIBUJAR GRÁFICOS (RESTRICCIÓN DINÁMICA)
# --------------------------------------------
color_col = "count" if "count" in selected_df.columns else None

for i, group in enumerate(st.session_state.groups):
    st.subheader(f"Trade-off Map {i+1}")
    
    # 1. Calculamos métricas usadas por OTROS gráficos
    others = [m for idx, g in enumerate(st.session_state.groups) if idx != i for m in g if m]
    # 2. Filtramos el universo disponible para este bloque
    available_here = [m for m in available_metrics if m not in others]

    if len(available_here) < 2:
        st.warning("Not enough metrics left.")
        continue

    c1, c2, c3 = st.columns(3)
    
    with c1:
        curr_x = group[0] if group[0] in available_here else available_here[0]
        x = st.selectbox(f"X Axis {i}", available_here, index=available_here.index(curr_x), key=f"x_{i}")
    
    with c2:
        y_opts = [m for m in available_here if m != x]
        curr_y = group[1] if group[1] in y_opts else y_opts[0]
        y = st.selectbox(f"Y Axis {i}", y_opts, index=y_opts.index(curr_y), key=f"y_{i}")
    
    with c3:
        s_opts = [None] + [m for m in available_here if m not in [x, y]]
        curr_s = group[2] if group[2] in s_opts else None
        s_idx = s_options.index(curr_s) if curr_s in s_options else 0
        size = st.selectbox(f"Size {i}", s_opts, index=s_idx, key=f"s_{i}")

    # Actualizamos el estado para la siguiente ejecución/gráfico
    st.session_state.groups[i] = [x, y, size]

    # Gráficos
    colA, colB = st.columns(2)
    
    # Configuración común para los trazos
    def get_fig(df_in, x_axis, y_axis, size_axis, key_p):
        fig = px.scatter(
            df_in, x=x_axis, y=y_axis, size=size_axis,
            color=color_col,
            text="label" if show_ids else None,
            symbol="highlight",
            symbol_map={True: "x", False: "circle"},
            color_discrete_sequence=px.colors.qualitative.Plotly
        )
        fig.update_traces(textposition="top right", mode='markers+text' if show_ids else 'markers')
        return fig

    with colA:
        st.plotly_chart(get_fig(selected_df, x, y, None, f"fA{i}"), use_container_width=True, key=f"chartA{i}")
    
    with colB:
        if size:
            # En el segundo gráfico, el eje Y es la métrica de tamaño
            st.plotly_chart(get_fig(selected_df, x, size, y, f"fB{i}"), use_container_width=True, key=f"chartB{i}")
        else:
            st.info("Select a metric in 'Size' to see the comparative trade-off.")

# --------------------------------------------
# RADAR COMPARISON
# --------------------------------------------
if st.session_state.show_comparison:
    st.markdown("---")
    st.subheader("Radar Comparison")
    ids_to_compare = st.multiselect("Select IDs to compare", selected_df["id"].unique())
    
    if len(ids_to_compare) >= 2:
        comp_df = selected_df[selected_df["id"].isin(ids_to_compare)].copy()
        # Solo métricas numéricas
        num_metrics = [m for m in available_metrics if pd.api.types.is_numeric_dtype(comp_df[m])]
        
        fig_radar = go.Figure()
        for _, row in comp_df.iterrows():
            values = []
            for m in num_metrics:
                mi, ma = selected_df[m].min(), selected_df[m].max()
                values.append((row[m]-mi)/(ma-mi) if ma > mi else 0.5)
            values.append(values[0]) # cerrar círculo
            fig_radar.add_trace(go.Scatterpolar(
                r=values, theta=num_metrics + [num_metrics[0]], 
                fill='toself', name=f"ID {int(row['id'])}"
            ))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])))
        st.plotly_chart(fig_radar, use_container_width=True)

# --------------------------------------------
# DATA PREVIEW
# --------------------------------------------
with st.expander("Data Preview"):
    st.dataframe(selected_df.head(100))