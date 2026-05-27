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
    
    opciones_id = selected_df["id"].unique()
    compare_ids = st.multiselect("Pick solutions to compare in Radar", opciones_id)

    if len(compare_ids) < 2:
        st.info("Select at least 2 solutions to compare")
        return

    compare_df = selected_df[selected_df["id"].isin(compare_ids)].copy()
    

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Radar", "👥 Stakeholders", "📋 Requisitos", "🔗 Alineación"])

    # ---------- PERFORMANCE ----------
    with tab1:
        st.subheader("Custom Trade-off Comparison")
        
        numeric_cols = [m for m in available_metrics if pd.api.types.is_numeric_dtype(selected_df[m])]
        selected_radar_metrics = st.multiselect(
            "Select metrics (at least 3)", 
            numeric_cols,
            default=numeric_cols[:3] if len(numeric_cols) >= 3 else None,
            key="perf_metrics"
        )

        if len(selected_radar_metrics) >= 3:
            metric_goals = {}
            cols = st.columns(len(selected_radar_metrics))
            
            for idx, m in enumerate(selected_radar_metrics):
                with cols[idx]:
                    goal = st.selectbox(f"Goal {m}", ["Maximize", "Minimize"], key=f"radar_g_{m}")
                    metric_goals[m] = goal

            radar_df = compare_df.copy()
            low, high = 0.1, 0.9

            for m in selected_radar_metrics:
                mi, ma = radar_df[m].min(), radar_df[m].max()
                if ma > mi:
                    norm = (radar_df[m] - mi) / (ma - mi)
                    if metric_goals[m] == "Minimize":
                        norm = 1.0 - norm
                    radar_df[m] = low + (norm * (high - low))
                else:
                    radar_df[m] = 0.5

            fig_perf = go.Figure()
            for _, row in radar_df.iterrows():
                val = row[selected_radar_metrics].tolist()
                val.append(val[0])
                fig_perf.add_trace(go.Scatterpolar(
                    r=val,
                    theta=selected_radar_metrics + [selected_radar_metrics[0]],
                    fill=None,
                    mode='lines+markers',
                    name=f"ID {int(row['id'])}"
                ))

            fig_perf.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                showlegend=True
            )
            st.plotly_chart(fig_perf, use_container_width=True)

        else:
            st.warning("Select at least 3 metrics.")

    # ---------- STAKEHOLDER ----------
    with tab2:
        st.subheader("Coverage per Stakeholder")
        
        stcov_cols = [c for c in selected_df.columns if c.startswith("stcov_")]
        
        if not stcov_cols:
            st.info("No stakeholder coverage columns (stcov_...) found in dataset.")
        else:
            if len(stcov_cols) < 3:
                st.warning("Need at least 3 stakeholders to create a radar chart.")
            else:
                cov_df = compare_df.copy()
                low, high = 0.1, 0.9

                for c in stcov_cols:
                    mi, ma = cov_df[c].min(), cov_df[c].max()
                    if ma > mi:
                        norm = (cov_df[c] - mi) / (ma - mi)
                        cov_df[c] = low + (norm * (high - low))
                    else:
                        cov_df[c] = 0.5

                fig_cov = go.Figure()
                for _, row in cov_df.iterrows():
                    val = row[stcov_cols].tolist()
                    val.append(val[0])
                    fig_cov.add_trace(go.Scatterpolar(
                        r=val,
                        theta=stcov_cols + [stcov_cols[0]],
                        fill=None,
                        mode='lines+markers',
                        name=f"ID {int(row['id'])}"
                    ))

                fig_cov.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                    showlegend=True
                )
                st.plotly_chart(fig_cov, use_container_width=True)
# ---------- NUEVA PESTAÑA: REQUISITOS ----------
    with tab3:
        st.subheader("Requirements Included in Selected Solutions")
        
        # Detectamos dinámicamente cualquier columna que empiece por "req_"
        req_cols = [c for c in selected_df.columns if c.startswith("req_")]
        
        if not req_cols:
            st.info("No requirement columns (req_...) found in dataset.")
        else:
            # Preparamos los datos: Filas como IDs de solución y columnas como Requisitos
            req_df = compare_df.set_index("id")[req_cols].copy()
            
            # Convertimos el ID a string para el eje Y
            req_df.index = [f"ID {int(i)}" for i in req_df.index]
            
            # MAPA DE COLOR CON CONTRASTE ALTO:
            fig_req = px.imshow(
                req_df,
                labels=dict(x="Requirements", y="Solutions", color="Status"),
                x=req_cols,
                y=req_df.index,
                color_continuous_scale=[[0, "#e0e0e0"], [1, "#00e676"]] # Gris Claro vs Verde Brillante Puro
            )
            
            # Configuramos el diseño del gráfico de forma correcta
            fig_req.update_layout(
                template="plotly_white", # Fondo blanco limpio
                coloraxis_showscale=False, # Ocultamos la barra lateral de colores
                xaxis=dict(
                    tickangle=-45, 
                    showgrid=False, # Quitamos líneas de cuadrícula del fondo
                    tickfont=dict(size=11, color="black") # ¡CORREGIDO AQUÍ! (Era tickfont, no textfont)
                ),
                yaxis=dict(
                    autorange="reversed", 
                    showgrid=False,
                    tickfont=dict(size=11, color="black") # ¡CORREGIDO AQUÍ! (Era tickfont, no textfont)
                ),
                margin=dict(l=50, r=50, t=30, b=50) # Ajustamos márgenes
            )
            
            # Añadimos bordes blancos muy marcados para separar las celdas claramente
            fig_req.update_traces(
                xgap=3, 
                ygap=3,
                hovertemplate="<b>%{y}</b><br>Requirement: %{x}<br>Status: %{z} (1=Included, 0=Excluded)<extra></extra>"
            )
            
            st.plotly_chart(fig_req, use_container_width=True)


# ---------- NUEVA PESTAÑA: ALINEACIÓN STAKEHOLDERS (EL "RIZO") ----------
    with tab4:
        st.subheader("Stakeholder-Requirement Alignment Matrix")
        st.write("Visualizing which requirements satisfy each stakeholder's specific interests.")

        # 1. Identificar columnas
        req_cols = [c for c in selected_df.columns if c.startswith("req_")]
        st_cols = [c for c in selected_df.columns if c.startswith("stcov_")]

        # Para esta visualización, lo mejor es analizar UNA solución a la vez 
        # o comparar una 'maestra' contra el interés de los stakeholders.
        focus_id = st.selectbox("Select Solution to analyze alignment", compare_df["id"].unique(), key="align_sel")
        row_focus = compare_df[compare_df["id"] == focus_id].iloc[0]

        if not req_cols or not st_cols:
            st.info("Required data columns (req_ or stcov_) missing.")
        else:
            # --- Lógica de Simulación de Mapeo (Personalizable) ---
            # En un proyecto real, aquí cargarías la matriz Stakeholder vs Requisito.
            # Aquí creamos una matriz donde 'activamos' la relación si el requisito influye en el coverage.
            import numpy as np
            
            alignment_data = []
            for st_name in st_cols:
                row_values = []
                for req_name in req_cols:
                    # SIMULACIÓN: Decidimos si el Stakeholder propuso el requisito.
                    # En tu caso, podrías cargar un CSV con este mapeo. 
                    # Aquí usamos una lógica determinista simple para el ejemplo:
                    proposed_by_stake = (hash(st_name + req_name) % 3 == 0) 
                    
                    is_included = row_focus[req_name] == 1
                    
                    if proposed_by_stake and is_included:
                        val = 2  # ¡Éxito! Propuesto y cumplido
                    elif proposed_by_stake and not is_included:
                        val = 1  # Deuda: Propuesto pero fuera
                    else:
                        val = 0  # No le interesa
                    row_values.append(val)
                alignment_data.append(row_values)

            # Crear DataFrame para el gráfico
            align_df = pd.DataFrame(alignment_data, index=st_cols, columns=req_cols)

            # 2. Construir el Heatmap con Intensidades
            # 0: Sin interés (Gris muy claro)
            # 1: Propuesto pero NO incluido (Gris oscuro/Rojo suave)
            # 2: Propuesto E INCLUIDO (Verde brillante)
            fig_align = px.imshow(
                align_df,
                labels=dict(x="Requirements", y="Stakeholders", color="Alignment"),
                x=req_cols,
                y=[s.replace("stcov_", "Stakeholder ") for s in st_cols],
                color_continuous_scale=[
                    [0, "#f8f9fa"],   # Sin relación
                    [0.5, "#adb5bd"], # Deuda (Gris medio)
                    [1, "#00e676"]    # Cumplido (Verde)
                ]
            )

            fig_align.update_layout(
                template="plotly_white",
                coloraxis_showscale=False,
                xaxis=dict(tickangle=-45, tickfont=dict(size=10)),
                yaxis=dict(tickfont=dict(size=10)),
                height=400
            )

            fig_align.update_traces(
                xgap=2, ygap=2,
                hovertemplate="<b>%{y}</b><br>Requirement: %{x}<br>Status: %{z}<extra></extra>"
            )

            st.plotly_chart(fig_align, use_container_width=True)
            
            # Leyenda personalizada
            c1, c2, c3 = st.columns(3)
            c1.markdown("⚪ **No solicitado**")
            c2.markdown("🔘 **Solicitado (No incluido)**")
            c3.markdown("🟢 **Solicitado e Incluido**")

# --------------------------------------------
# DATA SOURCE 
# --------------------------------------------
source = st.sidebar.radio("Data source", ["Built-in", "Upload CSV"])

if source == "Built-in":
    if not os.path.exists(DATA_PATH):
        st.error("Data folder not found")
        st.stop()

    files = [f for f in os.listdir(DATA_PATH) if f.endswith(".csv") and "metrics" not in f]
    if not files:
        st.error("No datasets found")
        st.stop()

    selected_file = st.sidebar.selectbox("Dataset", files)
    df = load_csv(os.path.join(DATA_PATH, selected_file))

else:
    uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file is None:
        st.stop()
    df = pd.read_csv(uploaded_file)

# --------------------------------------------
# METRICS
# --------------------------------------------
opt_df = load_csv(os.path.join(DATA_PATH, "optimization_metrics.csv"))
qual_df = load_csv(os.path.join(DATA_PATH, "quality_metrics.csv"))
available_metrics = [m for m in list(opt_df.columns) + list(qual_df.columns) if m in df.columns]
available_qual = [m for m in qual_df.columns if m in df.columns]

# --------------------------------------------
# SESSION STATE
# --------------------------------------------
if "groups" not in st.session_state: st.session_state.groups = []
if "show_comparison" not in st.session_state: st.session_state.show_comparison = False

if st.sidebar.button("Reset graphs"): 
    st.session_state.groups = []; st.rerun()

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
# SELECCIÓN
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
        selected_df["count"] = selected_df["count"].astype(int).astype(str)
        selected_df = selected_df.sort_values("count", ascending=False)

# --------------------------------------------
# HIGHLIGHT + LABELS
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
# GRÁFICOS
# --------------------------------------------
color_col = "count" if "count" in selected_df.columns else None

for i, group in enumerate(st.session_state.groups):
    st.subheader(f"Trade-off Map {i+1}")
    
    others = [m for idx, g in enumerate(st.session_state.groups) if idx != i for m in g if m]
    available_here = [m for m in available_metrics if m not in others]

    if len(available_here) < 2:
        st.warning("No more metrics available for this group.")
        continue

    col1, col2, col3 = st.columns(3)
    
    with col1:
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
# RADAR
# --------------------------------------------
if st.session_state.show_comparison:
    plot_radar(selected_df, available_metrics)

# --------------------------------------------
# PREVIEW
# --------------------------------------------
with st.expander("Data preview"):
    # Hacemos una copia para no alterar los datos reales del programa
    df_preview = selected_df.copy()
    
    # Lista de columnas técnicas creadas por el código que queremos ocultar
    columnas_a_ocultar = ["id","highlight", "highlight_label", "label"]
    
    # Las eliminamos de la vista si existen
    df_preview = df_preview.drop(columns=[col for col in columnas_a_ocultar if col in df_preview.columns])
    
    # Mostramos la tabla limpia
    st.dataframe(df_preview.head(100))