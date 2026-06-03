
import streamlit as st
import pandas as pd
from config import PROBLEMAS
from problem import run_pipeline, leer_soluciones
from enrichment import detectar_indicadores_posibles, aplicar_enrichment


def render_input_panel():
    """Render the input/preparation sidebar and return the active dataframe."""

    st.sidebar.markdown(
        "## 🏷️  Input and Preparation",
        help="Load precomputed Pareto fronts, including requirements and objetive functions values."
        )

    # Reset button aligned with title
    col_texto, col_btn = st.sidebar.columns([2, 1.5], vertical_alignment="center")

    with col_texto:
        st.markdown(
            "Select data source",        
            help="• Build from NRP instance: Parses a raw literature benchmark dataset and prepares it for custom indicator generation.\n\n• Load enriched solution set: Directly loads an already processed and structured CSV file containing pre-calculated metrics."
        )

    with col_btn:
        if st.button("🔄 Reset data", use_container_width=True):
            st.session_state.clear()
            st.success("Reset ✔️")
            st.rerun()

    data_mode = st.sidebar.radio(
        "Select data source",
        [
            "📥 Build from NRP instance",
            "📂 Load enriched solution set"
        ],
        label_visibility="collapsed",
        )

    # ============================================
    # 1) CSV MODE
    # ============================================
    if data_mode == "📂 Load enriched solution set":
        uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

        if uploaded_file is None:
            st.warning("Please upload a dataset with indicators.")
            st.stop()

        df = pd.read_csv(uploaded_file)
        st.sidebar.success(f"{len(df)} solutions loaded from CSV")

        # Enrichment for uploaded datasets
        possible_indicators = detectar_indicadores_posibles(df)

        if possible_indicators:
            st.sidebar.markdown("## 🎨 Semantic enrichment")

            selected_indicators = st.sidebar.multiselect(
                "Indicators",
                possible_indicators,
                default=[],
                help="Select the attributes to include; only those with a recognized calculation method based on the loaded data are displayed."
            )

            df = aplicar_enrichment(df, selected_indicators)
        else:
            st.sidebar.info("No derived indicators can be computed from the uploaded data.")

        return df

    # ============================================
    # 2) PIPELINE MODE
    # ============================================
    st.sidebar.markdown(
        "## 🎨 Semantic Enrichment",
        help="Allows adding computed metrics dynamically to the current dataset."
    )

    # 1. Obtenemos la lista de llaves de los problemas  
    lista_problemas = list(PROBLEMAS.keys())

    # 2. Averiguamos de forma segura qué problema está seleccionado actualmente
    if "problem_selector" in st.session_state:
        problema_actual = st.session_state["problem_selector"]
    else:
        problema_actual = lista_problemas[0] # El primero por defecto (BAGNALL)

    # 3. Extraemos el paper correspondiente de forma segura
    texto_ayuda = PROBLEMAS[problema_actual].get("paper", "No bibliographic reference available.")

    # 4. Renderizamos el selectbox usando la ayuda dinámica corregida
    problem_name = st.sidebar.selectbox(
        "NRP dataset from literature",
        lista_problemas,
        key="problem_selector",
        help=texto_ayuda
    )

   

    config = PROBLEMAS[problem_name]
    df_base = leer_soluciones(config)

    available_indicators = detectar_indicadores_posibles(df_base)

    default_indicators = config.get("indicadores_default", [])

    selected_indicators = st.sidebar.multiselect(
        "Indicators",
        available_indicators,
        default=[i for i in default_indicators if i in available_indicators],
        key="indicators_selector",
        help="Select the attributes to include; only those with a recognized calculation method based on the loaded data are displayed."
    )

    @st.cache_data
    def build_df(problem_name, selected_indicators):
        return run_pipeline(problem_name, selected_indicators)

    df = build_df(problem_name, selected_indicators)
    st.sidebar.success(f"{len(df)} solutions enriched")

    return df