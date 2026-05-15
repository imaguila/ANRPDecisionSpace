import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# --------------------------------------------
# CONFIGURACIÓN Y CARGA
# --------------------------------------------
st.set_page_config(layout="wide")
st.title("Assisted Next Release Problem")
DATA_PATH = "data"

@st.cache_data
def load_csv(path):
    return pd.read_csv(path)

def normalize_series(series):
    min_val, max_val = series.min(), series.max()
    if max_val > min_val:
        return (series - min_val) / (max_val - min_val)
    return series * 0.0

# --------------------------------------------
# CARGA DE ARCHIVOS
# --------------------------------------------
if not os.path.exists(DATA_PATH):
    st.error("Data folder not found"); st.stop()

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
# ESTADO DE SESIÓN
# --------------------------------------------
if "groups" not in st.session_state:
    st.session_state.groups = []

if st.sidebar.button("Reset graphs"):
    st.session_state.groups = []
    st.rerun()

# Lógica para el botón "Add": solo si sobran métricas
used_metrics_all = [m for g in st.session_state.groups for m in g if m]
remaining_for_add = [m for m in available_metrics if m not in used_metrics_all]

if len(remaining_for_add) >= 2:
    if st.sidebar.button("Add graph"):
        # Añadimos un grupo con las 2 primeras métricas libres que encontremos
        st.session_state.groups.append([remaining_for_add[0], remaining_for_add[1], None])
        st.rerun()

show_ids = st.sidebar.checkbox("Show IDs on plots", value=False)

# --------------------------------------------
# FILTROS Y SELECCIÓN (Ranking/Score)
# --------------------------------------------
st.sidebar.markdown("### Filters")
filtered_df = df.copy()
for m in available_metrics:
    if pd.api.types.is_numeric_dtype(df[m]):
        min_v, max_v = float(df[m].min()), float(df[m].max())
        if min_v != max_v:
            v_range = st.sidebar.slider(f"{m}", min_v, max_v, (min_v, max_v), key=f"f_{m}")
            filtered_df = filtered_df[(filtered_df[m] >= v_range[0]) & (filtered_df[m] <= v_range[1])]

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
        selected_df["count"] = selected_df["count"].astype(int).astype(str)
        selected_df = selected_df.sort_values("count", ascending=False)

# Highlight y Labels
selected_ids = st.multiselect("Select solutions to unmask", selected_df["id"].unique())
selected_df["highlight"] = selected_df["id"].isin(selected_ids)
if show_ids:
    if mode == "Ranking-based":
        selected_df["label"] = selected_df.apply(lambda r: str(int(r["id"])) if (r["highlight"] or int(r.get("count", 0)) >= threshold) else "", axis=1)
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
    
    # 1. Calculamos qué están usando TODOS LOS DEMÁS grupos
    used_by_others = [m for idx, g in enumerate(st.session_state.groups) if idx != i for m in g if m]
    
    # 2. El "Universo" para este grupo son las métricas no usadas por otros
    available_here = [m for m in available_metrics if m not in used_by_others]

    if len(available_here) < 2:
        st.warning("No metrics left for this graph.")
        continue

    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Forzamos a que el valor actual esté en la lista, si no, cogemos el primero disponible
        curr_x = group[0] if group[0] in available_here else available_here[0]
        x = st.selectbox(f"X Axis {i}", available_here, index=available_here.index(curr_x), key=f"x_{i}")
    
    with col2:
        # Y no puede ser X
        y_options = [m for m in available_here if m != x]
        curr_y = group[1] if group[1] in y_options else y_options[0]
        y = st.selectbox(f"Y Axis {i}", y_options, index=y_options.index(curr_y), key=f"y_{i}")
    
    with col3:
        # Size no puede ser ni X ni Y
        s_options = [None] + [m for m in available_here if m not in [x, y]]
        curr_s = group[2] if group[2] in s_options else None
        s_idx = s_options.index(curr_s) if curr_s in s_options else 0
        size = st.selectbox(f"Size {i}", s_options, index=s_idx, key=f"s_{i}")

    # ACTUALIZACIÓN INMEDIATA DEL STATE
    st.session_state.groups[i] = [x, y, size]

    # Renderizado de los dos gráficos del grupo
    cA, cB = st.columns(2)
    with cA:
        fig1 = px.scatter(selected_df, x=x, y=y, size=None, color=color_col,
                         text="label" if show_ids else None, symbol="highlight",
                         symbol_map={True: "x", False: "circle"})
        fig1.update_traces(textposition="top right", mode='markers+text' if show_ids else 'markers')
        st.plotly_chart(fig1, use_container_width=True, key=f"figA_{i}")
    
    with colB: # Usamos colB para el segundo gráfico si existe 'size'
        if size:
            fig2 = px.scatter(selected_df, x=x, y=size, size=y, color=color_col,
                             text="label" if show_ids else None, symbol="highlight",
                             symbol_map={True: "x", False: "circle"})
            fig2.update_traces(textposition="top right", mode='markers+text' if show_ids else 'markers')
            st.plotly_chart(fig2, use_container_width=True, key=f"figB_{i}")
        else:
            st.info("Select Size for comparison")

# --------------------------------------------
# COMPARISON (RADAR)
# --------------------------------------------
if st.sidebar.button("Show/Hide Radar"):
    st.session_state.show_comparison = not st.session_state.show_comparison
    st.rerun()

if st.session_state.show_comparison:
    st.markdown("---")
    compare_ids = st.multiselect("Compare solutions", selected_df["id"].unique(), key="radar_sel")
    if len(compare_ids) >= 2:
        c_df = selected_df[selected_df["id"].isin(compare_ids)].copy()
        c_metrics = [m for m in available_metrics if pd.api.types.is_numeric_dtype(c_df[m])]
        fig_r = go.Figure()
        for _, row in c_df.iterrows():
            v = []
            for m in c_metrics:
                mi, ma = selected_df[m].min(), selected_df[m].max()
                v.append((row[m]-mi)/(ma-mi) if ma>mi else 0.5)
            v.append(v[0])
            fig_r.add_trace(go.Scatterpolar(r=v, theta=c_metrics+[c_metrics[0]], fill='toself', name=f"ID {row['id']}"))
        st.plotly_chart(fig_r, use_container_width=True)

with st.expander("Data"):
    st.dataframe(selected_df.head(100))