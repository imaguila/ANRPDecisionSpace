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

def render_scatter_plot(df, x, y, size, color_col, show_ids, key):
    # Determinamos si hay etiquetas que mostrar
    has_labels = show_ids and "label" in df.columns and not df["label"].replace("", None).isnull().all()
    df["highlight_label"] = df["highlight"].map({
        True: "Hide",
        False: "hide"
    })

    fig = px.scatter(
        df, x=x, y=y, size=size,
        color=color_col,
        text="label" if show_ids else None,
        symbol="highlight_label",
        symbol_map={"Hide": "triangle-up", "hide": "circle"},
        color_discrete_sequence=px.colors.qualitative.Plotly
    )
    
    fig.update_traces(
        textposition="top right",
        textfont=dict(size=10),
        marker=dict(size=10),
        mode='markers+text' if show_ids else 'markers'
    )
    st.plotly_chart(fig, use_container_width=True, key=key)
def plot_radar(selected_df, available_metrics):
    st.markdown("---")
    st.subheader("Custom Detailed Comparison (Kiviat)")

    # 1. Selección de soluciones a comparar
    opciones_id = selected_df["id"].unique()
    compare_ids = st.multiselect("1. Pick solutions to compare", opciones_id)

    if len(compare_ids) < 2:
        st.info("Select at least 2 solutions to compare")
        return

    # 2. Configuración dinámica de dimensiones del Radar
    st.markdown("#### 2. Configure Radar Dimensions")
    
    # Multiselect para elegir qué métricas entran al radar
    selected_radar_metrics = st.multiselect(
        "Select metrics (at least 3)", 
        [m for m in available_metrics if pd.api.types.is_numeric_dtype(selected_df[m])],
        default=available_metrics[:3] if len(available_metrics) >=3 else None
    )

    if len(selected_radar_metrics) < 3:
        st.warning("Please select at least 3 metrics to generate the radar chart.")
        return

    # Diccionario para guardar el objetivo de cada métrica elegida
    metric_goals = {}
    cols = st.columns(len(selected_radar_metrics))
    
    for idx, m in enumerate(selected_radar_metrics):
        with cols[idx]:
            # El usuario decide si para esta métrica "Mejor" es Max o Min
            goal = st.selectbox(f"Goal for {m}", ["Maximize", "Minimize"], key=f"radar_g_{m}")
            metric_goals[m] = goal

    # Preparar datos
    compare_df = selected_df[selected_df["id"].isin(compare_ids)].copy()
    
    # Ajuste de escala: Margen del 10% para evitar colapsos
    low_limit = 0.1
    high_limit = 0.9

    for m in selected_radar_metrics:
        min_v = compare_df[m].min()
        max_v = compare_df[m].max()
        
        if max_v > min_v:
            norm_val = (compare_df[m] - min_v) / (max_v - min_v)
            
            # Aplicar inversión según la decisión del usuario en el selectbox
            if metric_goals[m] == "Minimize":
                norm_val = 1.0 - norm_val
            
            compare_df[m] = low_limit + (norm_val * (high_limit - low_limit))
        else:
            compare_df[m] = 0.5

    # Crear el gráfico
    fig = go.Figure()
    for _, row in compare_df.iterrows():
        values = row[selected_radar_metrics].tolist()
        values.append(values[0])
        
        fig.add_trace(go.Scatterpolar(
            r=values, 
            theta=selected_radar_metrics + [selected_radar_metrics[0]],
            fill=None,
            mode='lines+markers',
            name=f"ID {int(row['id'])}",
            hovertemplate="Métrica: %{theta}<br>Puntaje relativo: %{r:.2%}<extra></extra>"
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True, 
                range=[0, 1],
                tickvals=[low_limit, 0.5, high_limit],
                ticktext=["Peor", "Media", "Mejor"],
                gridcolor="lightgrey"
            )
        ),
        title="Custom Trade-off Comparison (Outer is Better)",
        showlegend=True
    )
    st.plotly_chart(fig, use_container_width=True)
# --------------------------------------------
# CARGA DE DATOS
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
if "groups" not in st.session_state: st.session_state.groups = []
if "show_comparison" not in st.session_state: st.session_state.show_comparison = False

if st.sidebar.button("Reset graphs"): 
    st.session_state.groups = []; st.rerun()

# Lógica de exclusión para añadir nuevo gráfico
used_now = [m for g in st.session_state.groups for m in g if m]
remaining = [m for m in available_metrics if m not in used_now]

if len(remaining) >= 2:
    if st.sidebar.button("Add graph"):
        st.session_state.groups.append([remaining[0], remaining[1], None])
        st.rerun()

if st.sidebar.button("Show/Hide comparison view"):
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
        # Convertir a string para colores sólidos (DISCRETOS)
        selected_df["count"] = selected_df["count"].astype(int).astype(str)
        selected_df = selected_df.sort_values("count", ascending=False)

# --------------------------------------------
# HIGHLIGHT Y LABELS
# --------------------------------------------
selected_ids = st.multiselect("Select solutions to **unmask**  ▲", selected_df["id"].unique())
selected_df["highlight"] = selected_df["id"].isin(selected_ids)

if show_ids:
    if mode == "Ranking-based":
        selected_df["label"] = selected_df.apply(
            lambda r: str(int(r["id"])) if (r["highlight"] or int(r.get("count", 0)) >= threshold) else "", axis=1
        )
    else:
        selected_df["label"] = selected_df["id"].astype(str)
else:
    selected_df["label"] = ""

# --------------------------------------------
# DIBUJAR GRÁFICOS (CON EXCLUSIÓN DINÁMICA)
# --------------------------------------------
color_col = "count" if "count" in selected_df.columns else None

for i, group in enumerate(st.session_state.groups):
    st.subheader(f"Trade-off Map {i+1}")
    
    # Calcular qué usan otros gráficos para excluirlos
    others = [m for idx, g in enumerate(st.session_state.groups) if idx != i for m in g if m]
    available_here = [m for m in available_metrics if m not in others]

    if len(available_here) < 2:
        st.warning("No more metrics available for this group.")
        continue

    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Buscamos el índice para que no se resetee al cambiar otras cosas
        curr_x = group[0] if group[0] in available_here else available_here[0]
        x = st.selectbox(f"X Axis {i}", available_here, index=available_here.index(curr_x), key=f"x_{i}")
    
    with col2:
        y_opts = [m for m in available_here if m != x]
        curr_y = group[1] if group[1] in y_opts else y_opts[0]
        y = st.selectbox(f"Y Axis {i}", y_opts, index=y_opts.index(curr_y), key=f"y_{i}")
    
    with col3:
        s_opts = [None] + [m for m in available_here if m not in [x, y]]
        curr_s = group[2] if group[2] in s_opts else None
        size = st.selectbox(f"Size {i}", s_opts, index=s_opts.index(curr_s), key=f"s_{i}")

    # Guardamos en el estado para que el siguiente gráfico sepa qué no usar
    st.session_state.groups[i] = [x, y, size]

    cA, cB = st.columns(2)
    with cA:
        render_scatter_plot(selected_df, x, y, None, color_col, show_ids, key=f"p1_{i}")
    with cB:
        if size:
            render_scatter_plot(selected_df, x, size, y, color_col, show_ids, key=f"p2_{i}")
        else:
            st.info("Select a metric in 'Size' to enable comparison.")

# --------------------------------------------
# RADAR Y PREVIEW
# --------------------------------------------
if st.session_state.show_comparison:
    plot_radar(selected_df, available_metrics)

with st.expander("Data preview"):
    st.dataframe(selected_df.head(100))