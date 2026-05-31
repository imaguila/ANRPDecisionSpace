import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import numpy as np
import hdbscan
from sklearn.preprocessing import StandardScaler
from sklearn_extra.cluster import KMedoids
from sklearn.metrics import silhouette_score
from config import PROBLEMAS
from problem import run_pipeline, leer_soluciones, REQUISITOS

# --------------------------------------------
# CONFIGURACIÓN
# --------------------------------------------
st.set_page_config(layout="wide")
st.title("ANRP Decision Space Explorer")
DATA_PATH = "data"

# --------------------------------------------
# FUNCIONES CORE
# --------------------------------------------
@st.cache_data
def load_csv(path):
    return pd.read_csv(path)

def render_scatter_plot(df, x, y, size, color_col, show_ids, key):
    import numpy as np
    import pandas as pd
    import plotly.express as px

    df = df.copy()

    # -----------------------------
    # Hover dinámico
    # -----------------------------
    hover_data = {}
    if "score" in df.columns:
        hover_data["score"] = ':.3f'
    if "score_topsis" in df.columns:
        hover_data["score_topsis"] = ':.3f'
    if "count" in df.columns:
        hover_data["count"] = True
    if "cluster" in df.columns:
        hover_data["cluster"] = True

    # -----------------------------
    # Detectar discreto / continuo
    # -----------------------------
    is_discrete = False

    if color_col and color_col in df.columns:
        if color_col == "group_label":
            is_discrete = True
            df[color_col] = df[color_col].astype(str)

        elif pd.api.types.is_object_dtype(df[color_col]):
            is_discrete = True
            df[color_col] = df[color_col].astype(str)

    # ======================================================
    # ✅ CASO 1: CONTINUO (Weighted, TOPSIS, etc.)
    # ======================================================
    if not is_discrete:

        fig = px.scatter(
            df,
            x=x,
            y=y,
            size=size,
            color=color_col,
            color_continuous_scale=px.colors.sequential.Viridis,
            text="label" if show_ids else None,
            hover_data=hover_data
        )

        # ✅ aplicar opacidad si hay selección
        if "highlight" in df.columns and df["highlight"].any():
            opacity_vals = np.where(df["highlight"], 1.0, 0.25)
            fig.update_traces(marker=dict(opacity=opacity_vals))

        fig.update_layout(
            legend_title_text=color_col if color_col else ""
        )

    # ======================================================
    # ✅ CASO 2: DISCRETO (Clustering, Ranking)
    # ======================================================
    else:

        unique_vals = sorted(df[color_col].dropna().unique().tolist())
        palette = px.colors.qualitative.Plotly

        color_map = {}
        for i, v in enumerate(unique_vals):
            color_map[v] = palette[i % len(palette)]

        fig = px.scatter(
            df,
            x=x,
            y=y,
            size=size,
            color=color_col,
            text="label" if show_ids else None,
            hover_data=hover_data,
            color_discrete_map=color_map
        )

        # ✅ aplicar opacidad también aquí
        if "highlight" in df.columns and df["highlight"].any():
            opacity_vals = np.where(df["highlight"], 1.0, 0.25)
            fig.update_traces(marker=dict(opacity=opacity_vals))

        fig.update_layout(legend_title_text="Groups")

    # -----------------------------
    # Estética
    # -----------------------------
    fig.update_traces(
        textposition="top right",
        textfont=dict(size=10),
        marker=dict(size=10),
        mode='markers+text' if show_ids else 'markers'
    )

    st.plotly_chart(fig, use_container_width=True, key=key)

def plot_radar(selected_df, available_metrics, group_col=None):
    st.markdown("---")

    df_for_compare = selected_df

    # -------------------------------
    # NUEVO: capa extra -> seleccionar GRUPO (cluster o count)
    # -------------------------------
    if group_col is not None and group_col in df_for_compare.columns:

        groups = sorted(df_for_compare[group_col].dropna().astype(str).unique().tolist())
        group_options = ["All"] + groups

        chosen_group = st.selectbox(
            "Group to analyze (cluster / ranking-group)",
            group_options,
            index=0,
            key="cmp_group_select"
        )

        if chosen_group != "All":
            df_for_compare = df_for_compare[df_for_compare[group_col].astype(str) == str(chosen_group)]

    # -------------------------------
    # Selección de IDs SOLO dentro del grupo elegido
    # -------------------------------
    opciones_id = df_for_compare["id"].unique()
    compare_ids = st.multiselect("Pick solutions to compare in Radar", opciones_id)

    if len(compare_ids) < 2:
        st.info("Select at least 2 solutions to compare")
        return

    compare_df = df_for_compare[df_for_compare["id"].isin(compare_ids)].copy()

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Comparative Profile",
        "👥 Stakeholder Impact",
        "📋 Requirement Composition",
        "🔗 Stakeholder–Requirement Alignment"
    ])

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

        # ----------------------------------
        # ✅ No hay stakeholders
        # ----------------------------------
        if not stcov_cols:
            st.info("No stakeholder coverage columns (stcov_...) found in dataset.")

        else:

            # ----------------------------------
            # ✅ ordenar por relevancia
            # ----------------------------------
            stcov_cols = sorted(
                stcov_cols,
                key=lambda c: selected_df[c].mean(),
                reverse=True
            )

            # ----------------------------------
            # ✅ selección manual (clave)
            # ----------------------------------
            selected_st = st.multiselect(
                "Select stakeholders to display",
                stcov_cols,
                default=stcov_cols[:min(6, len(stcov_cols))]
            )

            # ✅ aplicar selección
            if selected_st:
                stcov_cols = selected_st
            else:
                stcov_cols = []

            st.caption(f"Showing {len(stcov_cols)} stakeholders")

            # ----------------------------------
            # ⚠️ asegurar mínimo
            # ----------------------------------
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


# ---------- NUEVA PESTAÑA: ALINEACIÓN STAKEHOLDERS + FILA RESUMEN ----------
    with tab4:
        st.subheader("Stakeholder-Requirement Alignment Matrix")
        st.write("Visualizing which requirements satisfy each stakeholder's specific interests and their final release status.")

        # 1. Identificar columnas
        req_cols = [c for c in selected_df.columns if c.startswith("req_")]
        st_cols = [c for c in selected_df.columns if c.startswith("stcov_")]

        # Desplegable para analizar una solución concreta
        focus_id = st.selectbox("Select Solution to analyze alignment", compare_df["id"].unique(), key="align_sel")
        row_focus = compare_df[compare_df["id"] == focus_id].iloc[0]

        if not req_cols or not st_cols:
            st.info("Required data columns (req_ or stcov_) missing.")
        else:
          
            alignment_data = []
            # Generamos las filas de los Stakeholders normales
            for st_name in st_cols:
                row_values = []
                for req_name in req_cols:
                    # Simulación: Aquí decides si el Stakeholder propuso el requisito
                    proposed_by_stake = (hash(st_name + req_name) % 3 == 0) 
                    is_included = row_focus[req_name] == 1
                    
                    if proposed_by_stake and is_included:
                        val = 2  # Solicitado e incluido (Verde brillante)
                    elif proposed_by_stake and not is_included:
                        val = 1  # Solicitado pero fuera (Gris medio)
                    else:
                        val = 0  # No solicitado (Gris muy claro)
                    row_values.append(val)
                alignment_data.append(row_values)

            # --- LA FILA RESUMEN (RIZANDO MÁS EL RIZO) ---
            # Añadimos la fila final que mira directamente si el req está en la solución (1) o no (0)
            summary_row = []
            for req_name in req_cols:
                if row_focus[req_name] == 1:
                    summary_row.append(3) # Incluido en el release (Verde Oscuro)
                else:
                    summary_row.append(1) # Fuera del release (Gris Medio)
            alignment_data.append(summary_row)

            # Creamos la lista de nombres para el eje Y incluyendo nuestro resumen
            y_labels = [s.replace("stcov_", "Stakeholder ") for s in st_cols] + ["📦 RELEASE STATUS"]

            # Crear DataFrame para el Heatmap
            align_df = pd.DataFrame(alignment_data, index=y_labels, columns=req_cols)

            # 2. Construir el Heatmap con Escala de 4 colores discretos
            fig_align = px.imshow(
                align_df,
                labels=dict(x="Requirements", y="Alignment Status", color="Status"),
                x=req_cols,
                y=y_labels,
                # Definimos los cortes exactos de color para 0, 1, 2 y 3
                color_continuous_scale=[
                    [0.0, "#f8f9fa"],   # 0: Sin interés (Blanco/Gris suave)
                    [0.33, "#adb5bd"],  # 1: Fuera del Release / Deuda (Gris medio)
                    [0.66, "#00e676"],  # 2: Solicitado e Incluido (Verde brillante)
                    [1.0, "#00695c"]    # 3: Fila Resumen - ¡En el Release! (Verde Oscuro Azulado)
                ]
            )

            # Diseño limpio del gráfico
            fig_align.update_layout(
                template="plotly_white",
                coloraxis_showscale=False, # Ocultamos barra de escala continua
                xaxis=dict(tickangle=-45, tickfont=dict(size=11, color="black")),
                yaxis=dict(tickfont=dict(size=11, color="black")),
                height=450
            )

            # Espaciado de celdas y caja de información al pasar el ratón (Hover)
            fig_align.update_traces(
                xgap=3, ygap=3,
                hovertemplate="<b>%{y}</b><br>Requirement: %{x}<extra></extra>"
            )

            st.plotly_chart(fig_align, use_container_width=True)
            
            # Leyenda explicativa interactiva en columnas abajo del gráfico
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown("⚪ **Not requested**")
            c2.markdown("🔘 **Requested (Not included) / Excluded from the Release**")
            c3.markdown("🟢 **Requested and Included (Stakeholder)**")
            c4.markdown("🌲 **Included in the Final Release (Summary Row)**")

# --------------------------------------------
# DATA SOURCE + DATA PREPARATION
# --------------------------------------------


st.sidebar.markdown("## 🧩  Input and Preparation")

# 1. Creamos dos columnas dentro de la barra lateral
# La primera columna es más ancha para el texto; la segunda es para el botón
col_texto, col_btn = st.sidebar.columns([2.5, 1], vertical_alignment="center")

with col_texto:
    # Usamos el markdown con el tamaño de texto que te gusta
    st.markdown("Select data source")

with col_btn:
    # Un botón pequeño de reset justo al lado
    if st.button("🔄 Reset", use_container_width=True):
        st.session_state.clear()
        st.success("Reset ✔️")
        st.rerun()

# 2. Creamos el radio button ocultando su label nativo
data_mode = st.sidebar.radio(
    "Select data source", # Se mantiene por accesibilidad
    [
        "📂 Load enriched solution set",
        "🧱 Build from NRP instance"
    ],
    label_visibility="collapsed" # <--- Oculta el título gigante nativo
)
# ============================================
# 1) CSV MODE (TU FLUJO ORIGINAL)
# ============================================
if data_mode == "📂 Load enriched solution set":

    uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

    if uploaded_file is None:
        st.warning("Please upload a dataset with indicators.")
        st.stop()

    df = pd.read_csv(uploaded_file)

    st.sidebar.success(f"{len(df)} solutions loaded from CSV")

# ============================================
# 2) PIPELINE MODE (PREPARADO PARA FUTURO)
# ============================================
else:

    st.sidebar.markdown("## 🧪 Semantic enrichment")

    # -------------------------------
    # Selección de problema
    # -------------------------------
    problem_name = st.sidebar.selectbox(
        "NRP dataset from literature",
        list(PROBLEMAS.keys()),
        key="problem_selector"
    )

    config = PROBLEMAS[problem_name]

    # -------------------------------
    # Leer datos base (sin indicadores)
    # -------------------------------
    df_base = leer_soluciones(config)

    # -------------------------------
    # Detectar indicadores posibles
    # -------------------------------
    available_indicators = []

    for ind, reqs in REQUISITOS.items():
        if all(col in df_base.columns for col in reqs):
            available_indicators.append(ind)

    # -------------------------------
    # Selección indicadores
    # -------------------------------
    default_indicators = config.get("indicadores_default", [])


    selected_indicators = st.sidebar.multiselect(
        "Indicators",
        available_indicators,
        default=[i for i in default_indicators if i in available_indicators],
        key="indicators_selector"
    )


    # -------------------------------
    # Ejecutar pipeline
    # -------------------------------
    @st.cache_data
    def build_df(problem_name, selected_indicators):
        return run_pipeline(problem_name, selected_indicators)

    df = build_df(problem_name, selected_indicators)

    st.sidebar.success(f"{len(df)} solutions enriched")

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

if "selected_ids" not in st.session_state: st.session_state.selected_ids = []
if "focus_mode" not in st.session_state: st.session_state.focus_mode = False

used_now = [m for g in st.session_state.groups for m in g if m]
remaining = [m for m in available_metrics if m not in used_now]

if len(remaining) >= 2:
    if st.sidebar.button("Add decision-space map"):
        st.session_state.groups.append([remaining[0], remaining[1], None])
        st.rerun()

if st.sidebar.button("🆚Toggle comparative support view"):
    st.session_state.show_comparison = not st.session_state.show_comparison
    st.rerun()


focus_mode = st.sidebar.checkbox(
    "🎯 SOI Focus Mode",
    help="Highlight = visual emphasis | Focus = restrict analysis to selected SOI",
    key="focus_mode"

)

st.sidebar.caption("Highlight = visual emphasis | Focus = restrict analysis to selected SOI")

show_ids = st.sidebar.checkbox("Show IDs on plots", value=False)


# --------------------------------------------
# FILTROS
# --------------------------------------------

st.sidebar.markdown("## 🎛️ Context Framing")

filtered_df = df.copy()

# Separar métricas
available_opt = [m for m in opt_df.columns if m in df.columns]
available_qual = [m for m in qual_df.columns if m in df.columns]

# -------- OPTIMIZATION METRICS --------
st.sidebar.markdown("#### 🔵 :blue[Optimization objectives]")

for m in available_opt:
    if pd.api.types.is_numeric_dtype(df[m]):
        min_v, max_v = float(df[m].min()), float(df[m].max())
        if min_v != max_v:

            val_range = st.sidebar.slider(
                f"{m}",
                min_v,
                max_v,
                (min_v, max_v),
                key=f"opt_{m}"
            )

            filtered_df = filtered_df[
                (filtered_df[m] >= val_range[0]) &
                (filtered_df[m] <= val_range[1])
            ]

# -------- QUALITY METRICS --------
st.sidebar.markdown("#### 🟢 :green[Quality Indicators]")

for m in available_qual:
    if pd.api.types.is_numeric_dtype(df[m]):
        min_v, max_v = float(df[m].min()), float(df[m].max())
        if min_v != max_v:

            val_range = st.sidebar.slider(
                f"{m}",
                min_v,
                max_v,
                (min_v, max_v),
                key=f"qual_{m}"
            )

            filtered_df = filtered_df[
                (filtered_df[m] >= val_range[0]) &
                (filtered_df[m] <= val_range[1])
            ]

# --------------------------------------------
# SELECCIÓN
# -------------------------------------------- 
st.sidebar.markdown("## 🔍 ROI Identification Lens")
mode_label = st.sidebar.selectbox(
    "🔍ROI Identification Lens",
    [
        "Exploratory view",
        "🔵 Preference lens (MCDA)",
        "🟢 Diversity lens",
        "🟣 Efficiency lens",
        "🟠 Domain-specific lens",
    ],
    label_visibility="collapsed"
)

mode_map = {
    "Exploratory view": "None",
    "🔵 Preference lens (MCDA)": "MCDM",
    "🟢 Diversity lens": "Clustering",
    "🟣 Efficiency lens": "Efficiency-Ratio",
    "🟠 Domain-specific lens": "Ranking-based",
}


mode = mode_map[mode_label]

selected_df = filtered_df.copy()
threshold = 0

# IMPORTANTE: esta variable controla el color en los plots
color_col = None

# --------------------------------------------
# MCDM (Weighted + TOPSIS unificado)
# --------------------------------------------
if mode == "MCDM":

    st.sidebar.markdown("### Multi-criteria Preference")

    # -------------------------------
    # Método de evaluación
    # -------------------------------
    method = st.sidebar.radio(
        "Method",
        ["Weighted Sum", "TOPSIS"]
    )

    # -------------------------------
    # Selección de criterios
    # -------------------------------
    m_max = st.sidebar.multiselect("Maximize", available_qual)
    m_min = st.sidebar.multiselect(
        "Minimize",
        [m for m in available_qual if m not in m_max]
    )

    criteria = m_max + m_min

    if criteria:

        df_temp = selected_df.copy()

        # =====================================================
        # ✅ WEIGHTED SUM
        # =====================================================
        if method == "Weighted Sum":

            score = 0

            for m in criteria:
                mi, ma = df_temp[m].min(), df_temp[m].max()
                norm = (df_temp[m] - mi) / (ma - mi) if ma > mi else 0

                if m in m_max:
                    score += norm
                else:
                    score -= norm

            df_temp["score"] = score
            score_col = "score"

        # =====================================================
        # ✅ TOPSIS
        # =====================================================
        else:

            norm_df = df_temp[criteria].copy()

            # normalización vectorial
            for m in criteria:
                denom = (norm_df[m]**2).sum() ** 0.5
                if denom != 0:
                    norm_df[m] = norm_df[m] / denom

            ideal = {}
            anti_ideal = {}

            for m in criteria:
                if m in m_max:
                    ideal[m] = norm_df[m].max()
                    anti_ideal[m] = norm_df[m].min()
                else:
                    ideal[m] = norm_df[m].min()
                    anti_ideal[m] = norm_df[m].max()

            d_plus = []
            d_minus = []

            for i in range(len(norm_df)):
                row = norm_df.iloc[i]

                dp = sum((row[m] - ideal[m])**2 for m in criteria) ** 0.5
                dm = sum((row[m] - anti_ideal[m])**2 for m in criteria) ** 0.5

                d_plus.append(dp)
                d_minus.append(dm)

            df_temp["score_topsis"] = [
                dm / (dp + dm) if (dp + dm) != 0 else 0
                for dp, dm in zip(d_plus, d_minus)
            ]

            score_col = "score_topsis"

        # -------------------------------
        # Top N
        # -------------------------------
        n = st.sidebar.slider(
            "Top N",
            1,
            len(df_temp),
            min(10, len(df_temp))
        )

        selected_df = df_temp.sort_values(score_col, ascending=False).head(n)

        color_col = score_col


# ----------------------------------
# DIVERSITY METHODS
# ------------------

elif mode == "Clustering":

    st.sidebar.markdown("### Clustering")

    # -------------------------------
    # Selección de método
    # -------------------------------
    cluster_method = st.sidebar.radio(
        "Clustering method",
        ["K-Medoids", "HDBSCAN"]
    )

    # -------------------------------
    # Selección de métricas
    # -------------------------------
    cluster_metrics = st.sidebar.multiselect(
        "Metrics for clustering",
        available_metrics,
        default=available_metrics[:2]
    )

    if cluster_metrics and len(cluster_metrics) >= 2:

        # -------------------------------
        # Preparar datos
        # -------------------------------
        X = selected_df[cluster_metrics].values

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # ==========================================================
        # ✅ CASO 1: K-MEDOIDS (tu código actual mejorado)
        # ==========================================================
        if cluster_method == "K-Medoids":

            k_mode = st.sidebar.radio(
                "Number of clusters",
                ["Manual", "Auto (Silhouette)"]
            )

            if k_mode == "Manual":
                k = st.sidebar.slider(
                    "k clusters",
                    2,
                    min(10, len(selected_df)),
                    3
                )

            else:
                best_k = 2
                best_score = -1

                for k_test in range(2, min(10, len(X_scaled))):
                    try:
                        model = KMedoids(
                            n_clusters=k_test,
                            method='pam',
                            random_state=123
                        )
                        labels_test = model.fit_predict(X_scaled)

                        if len(set(labels_test)) > 1:
                            score = silhouette_score(X_scaled, labels_test)

                            if score > best_score:
                                best_score = score
                                best_k = k_test
                    except:
                        pass

                k = best_k
                st.sidebar.info(f"Optimal k (silhouette): {k}")

            model = KMedoids(
                n_clusters=k,
                method='pam',
                random_state=123
            )

            labels = model.fit_predict(X_scaled)

        # ==========================================================
        # ✅ CASO 2: HDBSCAN (NUEVO MÉTODO)
        # ==========================================================
        else:

            st.sidebar.markdown("#### HDBSCAN configuration")

            mode_size = st.sidebar.radio(
                "Cluster size",
                ["Auto (recommended)", "Manual"]
            )

            N = len(selected_df)

            if mode_size == "Auto (recommended)":

                option = st.sidebar.selectbox(
                    "Cluster granularity",
                    ["Small (~5%)", "Medium (~10%)", "Large (~20%)"],
                    index=1
                )

                if option == "Small (~5%)":
                    min_cluster_size = max(2, int(0.05 * N))
                elif option == "Medium (~10%)":
                    min_cluster_size = max(2, int(0.10 * N))
                else:
                    min_cluster_size = max(2, int(0.20 * N))

                st.sidebar.info(f"min_cluster_size = {min_cluster_size}")

            else:
                min_cluster_size = st.sidebar.slider(
                    "Min cluster size",
                    2,
                    len(selected_df),
                    max(2, int(0.1 * N))
                )

            model = hdbscan.HDBSCAN(
                min_cluster_size=min_cluster_size
            )

            labels = model.fit_predict(X_scaled)


        # -------------------------------
        # Métricas de clustering (info)
        # -------------------------------

        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        noise_ratio = (labels == -1).sum() / len(labels)

        st.sidebar.info(f"Clusters: {n_clusters} | Noise: {noise_ratio:.2%}")


        # -------------------------------
        # Guardar resultados (común)
        # -------------------------------
        selected_df["cluster"] = labels

        # Convertir a string para visualización
        selected_df["cluster_str"] = selected_df["cluster"].astype(str)

        # Manejar ruido de HDBSCAN (-1)
        selected_df["cluster_str"] = selected_df["cluster_str"].replace("-1", "Noise")

        # Tamaño por grupo
        cluster_sizes = selected_df.groupby("cluster_str")["id"].transform("size")

        selected_df["group_label"] = (
            "Cluster " +
            selected_df["cluster_str"] +
            " (n=" +
            cluster_sizes.astype(str) +
            ")"
        )

        color_col = "group_label"

##-------------------
#   Efficincy based
#------------------


elif mode == "Efficiency-Ratio":

    st.sidebar.markdown("### Efficiency (Benefit/Cost)")

    benefit = st.sidebar.selectbox(
        "Benefit (maximize)", 
        available_qual, 
        key="eff_benefit"
    )

    cost = st.sidebar.selectbox(
        "Cost (minimize)", 
        available_metrics, 
        key="eff_cost"
    )

    # protección
    if benefit == cost:
        st.warning("Benefit and Cost must be different metrics")
        st.stop()

    # slider primero

    n = st.sidebar.slider(
        "Top N efficient solutions",
        1,
        len(selected_df),
        min(10, len(selected_df)),
        key="eff_topn"
    )

    # calcular score
    selected_df = selected_df.copy()
 
    cost_safe = selected_df[cost].replace(0, 1e-9)
    selected_df["efficiency_score"] = selected_df[benefit] / cost_safe

    # ordenar
    selected_df = selected_df.sort_values("efficiency_score", ascending=False).head(n)

    color_col = "efficiency_score"

# --------------------------------------------
# RANKING BASED (count SIN NORMALIZAR)
# --------------------------------------------
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

        selected_df["count"] = selected_df["count"].astype(int)
        selected_df["count_str"] = selected_df["count"].astype(str)

        group_sizes = selected_df.groupby("count")["id"].transform("size")

        selected_df["group_label"] = (
            "Matches = " + selected_df["count"].astype(str) + 
            " (n=" + group_sizes.astype(str) + ")"
        )
        color_col = "group_label"

# --------------------------------------------
# NONE
# --------------------------------------------
else:
    color_col = None

# --------------------------------------------
# HIGHLIGHT + LABELS
# --------------------------------------------


selected_ids = st.multiselect(
    "Select candidate SOI",
    options=selected_df["id"].tolist(),
    default=st.session_state.selected_ids,
    key="selected_ids"
)



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


# ----------------------------------
# 🎯 Focus mode → filtrar datos reales
# ----------------------------------
if focus_mode and selected_df["highlight"].any():
    selected_df = selected_df[selected_df["highlight"]].copy()


if focus_mode:
    st.sidebar.caption(f"{len(selected_df)} solutions in focus")



# --------------------------------------------
# GRÁFICOS
# --------------------------------------------

for i, group in enumerate(st.session_state.groups):
    st.subheader(f"Decision-Space Map {i+1}")
    
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

    df_plot = selected_df.copy()

    cA, cB = st.columns(2)
    with cA:
        render_scatter_plot(df_plot, x, y, None, color_col, show_ids, key=f"p1_{i}")
    with cB:
        if size:
            render_scatter_plot(df_plot, x, size, y, color_col, show_ids, key=f"p2_{i}")
        else:
            st.info("Select a metric in 'Size' to enable comparison.")

# RADAR

if st.session_state.show_comparison:

    # 1) Base para comparar: si hay "unmask", usar solo highlight=True
    if "highlight" in selected_df.columns and selected_df["highlight"].any():
        df_compare_base = selected_df[selected_df["highlight"] == True].copy()
    else:
        df_compare_base = selected_df.copy()

    # 2) Detectar columna de agrupación (cluster o count)
    group_col = None

    # Clustering (preferimos cluster_str si existe)
    if "cluster_str" in df_compare_base.columns:
        group_col = "cluster_str"
    elif "cluster" in df_compare_base.columns:
        group_col = "cluster"

    # Ranking (si no hay clustering)
    if group_col is None:
        if "count_str" in df_compare_base.columns:
            group_col = "count_str"
        elif "count" in df_compare_base.columns:
            group_col = "count"

    plot_radar(df_compare_base, available_metrics, group_col=group_col)


col_titulo, col_btn1, col_btn2 = st.columns([2, 1, 1], vertical_alignment="center")

with col_titulo:
    # Usamos un subheader o markdown en lugar del texto del expander tradicional
    st.markdown("📋 Current decision subset")

# Preparamos los datos para la descarga
csv_data = selected_df.drop(columns=["highlight", "label"], errors="ignore")

with col_btn1:
    st.download_button(
        label="⬇️ Export current subset",
        data=csv_data.to_csv(index=False),
        file_name="current_subset.csv",
        mime="text/csv",
        use_container_width=True # Para que se adapte bien al tamaño de la columna
    )

with col_btn2:
    if "highlight" in selected_df.columns and selected_df["highlight"].any():
        st.download_button(
            label="⬇️ Export selected SOI",
            data=selected_df[selected_df["highlight"]].to_csv(index=False),
            file_name="SOI.csv",
            mime="text/csv",
            use_container_width=True
        )

# --- DESPLEGABLE CON LOS DATOS ---
# Ahora el expander solo envuelve a la tabla y queda justo debajo de los botones
with st.expander("Preview", expanded=False):
    df_preview = selected_df.copy()
    columnas_a_ocultar = ["id", "highlight", "highlight_label", "label"]
    df_preview = df_preview.drop(columns=[col for col in columnas_a_ocultar if col in df_preview.columns])
    st.dataframe(df_preview.head(100), use_container_width=True)


# --------------------------------------------
# PREVIEW
# --------------------------------------------
# with st.expander("Current decision subset"):
    # Hacemos una copia para no alterar los datos reales del programa
#    df_preview = selected_df.copy()
    
    # Lista de columnas técnicas creadas por el código que queremos ocultar
#    columnas_a_ocultar = ["id","highlight", "highlight_label", "label"]
    
    # Las eliminamos de la vista si existen
#    df_preview = df_preview.drop(columns=[col for col in columnas_a_ocultar if col in df_preview.columns])
    
    # Mostramos la tabla limpia
#    st.dataframe(df_preview.head(100))

#st.caption("📥 Export results")

#csv_data = selected_df.drop(columns=["highlight", "label"], errors="ignore")

#col1, col2 = st.columns(2)

#with col1:
#    st.download_button(
#        label="⬇️ Export current subset",
#        data=csv_data.to_csv(index=False),
#        file_name="current_subset.csv",
#        mime="text/csv"
#    )

#with col2:
#    if "highlight" in selected_df.columns and selected_df["highlight"].any():
#        st.download_button(
#            label="⬇️ Export selected SOI",
#            data=selected_df[selected_df["highlight"]].to_csv(index=False),
#            file_name="SOI.csv",
#            mime="text/csv"
#        )

st.caption(f"Highlighted: {(selected_df['highlight']).sum()} solutions")
    # ----------------------------------
# 🥇 Top solutions (non-intrusive)
# ----------------------------------
#if mode in ["MCDM", "Efficiency-Ratio"] and len(selected_df) >= 1:

#    top_n = min(3, len(selected_df))

#    top_ids = selected_df.head(top_n)["id"].astype(int).tolist()

#    st.caption("### 🥇 Top solutions (current method)")
#    st.caption(", ".join([f"ID {i}" for i in top_ids]))



# ----------------------------------
# 📊 Quick insights (non-intrusive)
# ----------------------------------
#if len(selected_df) >= 2:
#
#    numeric_cols = selected_df.select_dtypes(include="number").columns.tolist()

#    exclude_cols = ["id"]
#    numeric_cols = [c for c in numeric_cols if c not in exclude_cols]

#    if numeric_cols:

#        means = selected_df[numeric_cols].mean()

#        top_metrics = means.sort_values(ascending=False).head(3)

#        items = [f"**{m}**: {v:.3f}" for m, v in top_metrics.items()]
#        st.markdown("📊 Quick insights:  "+" | ".join(items))

