import streamlit as st
import pandas as pd
import hdbscan
from sklearn.preprocessing import StandardScaler
from sklearn_extra.cluster import KMedoids
from sklearn.metrics import silhouette_score

from input_panel import render_input_panel
from metrics_catalog import get_metric_sets
from ui_plots import render_scatter_plot, plot_radar

# --------------------------------------------
# CONFIGURACIÓN
# --------------------------------------------
st.set_page_config(layout="wide")
st.title("ANRP Decision Space Explorer")
DATA_PATH = "data"

# --------------------------------------------
# DATA SOURCE + DATA PREPARATION
# --------------------------------------------
df = render_input_panel()

# --------------------------------------------
# METRICS
# --------------------------------------------
available_opt, available_qual, available_metrics = get_metric_sets(df, DATA_PATH)

# --------------------------------------------
# SESSION STATE
# --------------------------------------------
if "groups" not in st.session_state:
    st.session_state.groups = []

if "show_comparison" not in st.session_state:
    st.session_state.show_comparison = False

if "selected_ids" not in st.session_state:
    st.session_state.selected_ids = []

if "focus_mode" not in st.session_state:
    st.session_state.focus_mode = False



# --------------------------------------------
# VISUAL WORKSPACE
# --------------------------------------------
used_now = [m for g in st.session_state.groups for m in g if m]
remaining = [m for m in available_metrics if m not in used_now]

st.sidebar.markdown("## 🗺️ Visual Workspace")
st.sidebar.caption("Manage 2D views of the decision space")

# Estado del workspace
n_maps = len(st.session_state.groups)
can_add_map = len(remaining) >= 2
can_reset_workspace = n_maps > 0

# Texto de ayuda contextual
st.sidebar.caption(
    f"Active maps: {n_maps} · Remaining metrics available for new maps: {len(remaining)}"
)




# Botones en paralelo


st.html("""
    <style>
    /* Estilo para el botón de reset usando su clave única */
    div[data-testid="stActionButtonElement"] button[key="reset_workspace_btn"] {
        color: #ff4b4b;
        border-color: #ff4b4b;
    }
    </style>
""")


# col_reset, col_add = st.sidebar.columns(2)
col_reset, col_add = st.sidebar.columns([0.35, 0.65])
with col_reset:
    if st.button(
        "Reset",
        use_container_width=True,
        disabled=not can_reset_workspace,
        key="reset_workspace_btn",
        type="secondary"
    ):
        st.session_state.groups = []
        st.session_state.show_comparison = False
        st.rerun()

with col_add:
    if st.button(
        "New decision map",
        use_container_width=True,
        disabled=not can_add_map,
        key="add_map_btn",
        type="primary"
    ):
        st.session_state.groups.append([remaining[0], remaining[1], None])
        st.rerun()

# Mensajes de ayuda
if not can_add_map:
    st.sidebar.info("No remaining available metrics")

if can_reset_workspace:
    st.sidebar.caption("'Reset' clears maps, but keeps data")

show_ids = st.sidebar.checkbox(
    "Show IDs on plots",
    value=False,
    help="Display solution identifiers directly on the maps."
)



# --------------------------------------------
# CONTEXT FRAMING
# --------------------------------------------
st.sidebar.markdown("## 🎛️ Context Framing")

filtered_df = df.copy()

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


# Guardar explícitamente el subconjunto actual derivado de la lente ROI
roi_df = selected_df.copy()

# --------------------------------------------
# HIGHLIGHT + LABELS
# --------------------------------------------

# Guardamos explícitamente el subconjunto actual derivado del framing + lens.
# Esto representa la ROI/subset estructural actual antes de aplicar foco manual.
roi_df = selected_df.copy()

selected_ids = st.multiselect(
    "Highlight candidate solutions",
    options=roi_df["id"].tolist(),
    default=st.session_state.selected_ids,
    key="selected_ids",
    help="Manually mark solutions for visual tracking or focused analysis."
)

roi_df["highlight"] = roi_df["id"].isin(selected_ids)

if show_ids:
    if mode == "Ranking-based":
        roi_df["label"] = roi_df.apply(
            lambda r: str(int(r["id"])) if (r["highlight"] or int(r.get("count", 0)) >= threshold) else "",
            axis=1
        )
    else:
        roi_df["label"] = roi_df["id"].astype(str)
else:
    roi_df["label"] = ""

# --------------------------------------------
# SOI FOCUS + COMPARATIVE SUPPORT
# --------------------------------------------

st.sidebar.markdown("## 🎯 Candidate Focus and Comparison")

focus_mode = st.sidebar.checkbox(
    "Focus on highlighted solutions",
    help="Keep candidates highlighted in context, or restrict analysis to them.",
    key="focus_mode"
)

st.sidebar.caption(
    "Highlight marks candidate solutions visually. Focus restricts maps, preview, and comparison to the highlighted subset."
)

st.sidebar.checkbox(
    "Open detailed comparison",
    key="show_comparison"
)

# ----------------------------------
# Focus mode → filtrar datos reales
# ----------------------------------
selected_df = roi_df.copy()

if focus_mode and roi_df["highlight"].any():
    selected_df = roi_df[roi_df["highlight"]].copy()

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
        x = st.selectbox(
            f"X Axis {i}",
            available_here,
            index=available_here.index(curr_x),
            key=f"x_{i}"
        )
    
    with col2:
        y_opts = [m for m in available_here if m != x]
        curr_y = group[1] if group[1] in y_opts else y_opts[0]
        y = st.selectbox(
            f"Y Axis {i}",
            y_opts,
            index=y_opts.index(curr_y),
            key=f"y_{i}"
        )
    
    with col3:
        s_opts = [None] + [m for m in available_here if m not in [x, y]]
        curr_s = group[2] if group[2] in s_opts else None
        size = st.selectbox(
            f"Size {i}",
            s_opts,
            index=s_opts.index(curr_s),
            key=f"s_{i}"
        )

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

# --------------------------------------------
# RADAR / DETAILED COMPARISON
# --------------------------------------------

if st.session_state.show_comparison:

    st.markdown("### 🆚 Detailed comparison")

    # Si el usuario ha activado focus y hay highlights,
    # la comparación se hace automáticamente sobre el subconjunto focalizado.
    if focus_mode and roi_df["highlight"].any():
        df_compare_base = selected_df.copy()
        st.caption("Comparison source: focused highlighted subset")

    else:
        compare_options = ["Current ROI subset"]

        if roi_df["highlight"].any():
            compare_options.append("Highlighted candidates")

        compare_source = st.radio(
            "Comparison source",
            compare_options,
            horizontal=True,
            key="comparison_source"
        )

        if compare_source == "Highlighted candidates":
            df_compare_base = roi_df[roi_df["highlight"] == True].copy()
        else:
            df_compare_base = roi_df.copy()

    # Detectar columna de agrupación (cluster o count)
    group_col = None

    if "cluster_str" in df_compare_base.columns:
        group_col = "cluster_str"
    elif "cluster" in df_compare_base.columns:
        group_col = "cluster"

    if group_col is None:
        if "count_str" in df_compare_base.columns:
            group_col = "count_str"
        elif "count" in df_compare_base.columns:
            group_col = "count"

    plot_radar(df_compare_base, available_metrics, group_col=group_col)

# --------------------------------------------
# CURRENT DECISION SUBSET + EXPORT
# --------------------------------------------

col_titulo, col_btn1, col_btn2 = st.columns([2, 1, 1], vertical_alignment="center")

with col_titulo:
    st.markdown("📋 Current decision subset")

st.caption(f"Highlighted: {(roi_df['highlight']).sum()} solutions")

csv_data = selected_df.drop(columns=["highlight", "label"], errors="ignore")

with col_btn1:
    st.download_button(
        label="⬇️ Export current subset",
        data=csv_data.to_csv(index=False),
        file_name="current_subset.csv",
        mime="text/csv",
        use_container_width=True
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

# --------------------------------------------
# PREVIEW
with st.expander("Preview", expanded=False):
    df_preview = selected_df.copy()
    
    # 1. Si "id" existe, lo ponemos como índice antes de borrar las demás columnas
    if "id" in df_preview.columns:
        df_preview = df_preview.set_index("id")
        
    # 2. Ocultamos el resto de columnas de control (quitamos "id" de esta lista)
    columnas_a_ocultar = ["highlight", "highlight_label", "label"]
    df_preview = df_preview.drop(
        columns=[col for col in columnas_a_ocultar if col in df_preview.columns]
    )
    
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

# st.caption(f"Highlighted: {(selected_df['highlight']).sum()} solutions")
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

