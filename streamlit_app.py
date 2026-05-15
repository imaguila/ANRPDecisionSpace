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

def render_scatter_plot(df, x, y, size, color_col, show_ids):
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
        # symbol_map={True: "x", False: "circle"}
        symbol_map={"Hide": "triangle-up", "hide": "circle"},
        color_discrete_sequence=px.colors.qualitative.Plotly
    )
    
    # Forzamos a Plotly a renderizar el texto
    if show_ids:
        fig.update_traces(textposition="top center", mode='markers+text')
    else:
        fig.update_traces(mode='markers')

    fig.update_traces(marker=dict(size=10))
    return fig

def plot_radar(df_para_comparar, available_metrics):
    """
    Genera el radar comparando solo las soluciones que pasaron 
    el filtrado y la selección actual.
    """
    st.markdown("---")
    st.subheader("Detailed Comparison of Selected Solutions")

    # Solo permitimos elegir entre lo que está "vivo" en el dataframe actual
    opciones_disponibles = df_para_comparar["id"].unique()
    
    if len(opciones_disponibles) < 2:
        st.warning("Not enough solutions after filtering to perform a comparison (min. 2).")
        return

    compare_ids = st.multiselect(
        "Pick solutions from current selection to compare",
        options=opciones_disponibles,
        help="Only showing solutions that passed your current filters/selection mode."
    )

    if len(compare_ids) < 2:
        st.info("Select at least 2 solutions from the list above to generate the radar chart.")
        return

    # Filtrar el dataframe ya filtrado
    compare_df = df_para_comparar[df_para_comparar["id"].isin(compare_ids)].copy()
    
    # Métricas numéricas disponibles
    metrics_to_plot = [m for m in available_metrics if pd.api.types.is_numeric_dtype(compare_df[m])]

    fig = go.Figure()

    for _, row in compare_df.iterrows():
        # Normalizamos los valores solo para este gráfico para que la escala sea 0-1
        values = []
        for m in metrics_to_plot:
            min_v = df_para_comparar[m].min()
            max_v = df_para_comparar[m].max()
            if max_v > min_v:
                norm_val = (row[m] - min_v) / (max_v - min_v)
            else:
                norm_val = 0.5 # Valor neutro si no hay variación
            values.append(norm_val)
            
        # Cerrar el gráfico circular
        values.append(values[0])
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=metrics_to_plot + [metrics_to_plot[0]],
            fill='toself',
            name=f"ID {int(row['id'])}"
        ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=True,
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)


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
# ESTADO Y SIDEBAR
# --------------------------------------------
if "groups" not in st.session_state: st.session_state.groups = []
if "show_comparison" not in st.session_state: st.session_state.show_comparison = False

if st.sidebar.button("Reset graphs"): st.session_state.groups = []
if st.sidebar.button("Add graph"): st.session_state.groups.append([None, None, None])
if st.sidebar.button("Show comparison"): st.session_state.show_comparison = not st.session_state.show_comparison

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
            v_range = st.sidebar.slider(f"{m}", min_v, max_v, (min_v, max_v), key=f"f_{m}")
            filtered_df = filtered_df[(filtered_df[m] >= v_range[0]) & (filtered_df[m] <= v_range[1])]

# --------------------------------------------
# SELECCIÓN Y SCORE
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
    sel_metrics = st.sidebar.multiselect("Quality metrics", available_qual)
    n_top = st.sidebar.slider("Top N per metric", 1, min(50, len(filtered_df)), 10)
    if sel_metrics:
        ranks = []
        for m in sel_metrics:
            goal = st.sidebar.selectbox(f"{m}", ["Maximize", "Minimize"], key=f"g_{m}")
            ranks.append(filtered_df.sort_values(m, ascending=(goal == "Minimize")).head(n_top))
        counts = pd.concat(ranks).groupby("id").size().reset_index(name="count")
        selected_df = filtered_df.merge(counts, on="id", how="left").fillna(0)
        # Convertimos a string para tener colores sólidos en Plotly
        selected_df["count"] = selected_df["count"].astype(int).astype(str)
        selected_df = selected_df.sort_values("count", ascending=False)
        threshold = max(1, len(sel_metrics) - 1)

# --------------------------------------------
# HIGHLIGHT Y ETIQUETAS (CORREGIDO)
# --------------------------------------------
selected_ids = st.multiselect("Solution unmasking  ▲", selected_df["id"].unique())
selected_df["highlight"] = selected_df["id"].isin(selected_ids)

if show_ids:
    if mode == "None":
        selected_df["label"] = selected_df["id"].astype(str)
    elif mode == "Score-based":
        # En Score-based, como ya es un Top N reducido, mostramos todos los IDs de ese Top
        selected_df["label"] = selected_df["id"].astype(str)
    elif mode == "Ranking-based":
        # En Ranking usamos el umbral de coincidencias
        selected_df["label"] = selected_df.apply(
            lambda r: str(int(r["id"])) if (r["highlight"] or int(r.get("count", 0)) >= threshold) else "",
            axis=1
        )
else:
    selected_df["label"] = ""

# --------------------------------------------
# DIBUJAR GRÁFICOS
# --------------------------------------------
# Aseguramos que si existe 'count', se mantenga como categoría (string)
if "count" in selected_df.columns:
    color_col = "count"
    # Re-ordenamos para que la leyenda de colores salga 3, 2, 1, 0
    selected_df = selected_df.sort_values("count", ascending=False)
else:
    color_col = None

# color_col = "count" if "count" in selected_df.columns else None

for i, group in enumerate(st.session_state.groups):
    st.subheader(f"Trade-off Map {i+1}")
    c1, c2, c3 = st.columns(3)
    with c1: x = st.selectbox(f"X {i}", available_metrics, key=f"x_{i}")
    with c2: y = st.selectbox(f"Y {i}", [m for m in available_metrics if m != x], key=f"y_{i}")
    with c3: size = st.selectbox(f"Size {i}", [None] + [m for m in available_metrics if m not in [x, y]], key=f"s_{i}")
    
    st.session_state.groups[i] = [x, y, size]
    
    colA, colB = st.columns(2)
    with colA:
        # Añadimos key=f"chart_A_{i}"
        st.plotly_chart(
            render_scatter_plot(selected_df, x, y, None, color_col, show_ids), 
            use_container_width=True,
            key=f"chart_A_{i}"
        )
    with colB:
        if size:
            # Añadimos key=f"chart_B_{i}"
            st.plotly_chart(
                render_scatter_plot(selected_df, x, size, y, color_col, show_ids), 
                use_container_width=True,
                key=f"chart_B_{i}"
            )
        else:
            st.info("Add a third dimension")
# --------------------------------------------
# COMPARISON & PREVIEW (CONSOLIDADOS)
# --------------------------------------------
if st.session_state.show_comparison:
    # Invocamos la función modular que definimos arriba
    # Esta ya contiene el multiselect, la lógica de filtrado y el gráfico
    plot_radar(selected_df, available_metrics)

with st.expander("Data preview"):
    st.write(f"Showing {len(selected_df)} solutions after filtering/selection")
    
    # Lista de columnas a ocultar para que la tabla sea legible
    cols_to_drop = ["highlight", "label"]
    # Solo intentamos dropear las que realmente existan en el DF actual
    existing_cols_to_drop = [c for c in cols_to_drop if c in selected_df.columns]
    
    df_display = selected_df.drop(columns=existing_cols_to_drop).head(100)
    
    # Aplicar estilo para resaltar las filas seleccionadas manualmente
    # (Usamos el índice original para verificar el highlight antes del drop)
    def highlight_selected(row):
        is_highlighted = selected_df.loc[row.name, "highlight"] if "highlight" in selected_df.columns else False
        return ['background-color: #154360' if is_highlighted else '' for _ in row]

    st.dataframe(df_display.style.apply(highlight_selected, axis=1))
    