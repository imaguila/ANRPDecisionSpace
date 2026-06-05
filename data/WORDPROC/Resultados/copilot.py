# %% [markdown]
# # Decision Space Analysis + Student MUST Percentage
# This script computes:
# 1) Requirement selection frequency across the 10 post-optimization strategy profiles
# 2) Student MUST percentage (MoSCoW: total_m only), aligned with the reduced 42-requirement space
# 3) Comparative academic-ready heatmaps

# %%
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np

# -----------------------------
# 1. CONFIGURATION
# -----------------------------
file_profiles = {
    'Framed group': 'framed.csv',
    'Domain-specific': 'domain.csv',
    'Efficiency-Productivity-Squandering': 'efici-product-squan.csv',
    'HDBSCAN all values': 'hdbscan-todo.csv',
    'HDBSCAN objective': 'hdbscan-efsatimsmall2.csv',
    'K-Medioids g0 allvalues': 'kmedio-3-0todo.csv',
    'K-Medioids g2 allvalues': 'kmedio-3-2todo.csv',
    'K-Medioids 2-0 objective': 'kmedio-2-0effsattime.csv',
    'TOPSIS': 'topsis.csv',
    'Weighted sum': 'weight.csv'
}

mapping_file = 'requirements_mapping_50_to_42.csv'
moscow_file = 'moscow_students.csv'
target_requirements = [f"req_{i}" for i in range(1, 43)]

# -----------------------------
# 2. LOAD REQUIREMENT MAPPING
# -----------------------------
req_name_mapping = {f"req_{i}": f"Requirement {i}" for i in range(1, 43)}
df_map = None

if os.path.exists(mapping_file):
    df_map = pd.read_csv(mapping_file)

    if {'mapped_req_42', 'reduced_name'}.issubset(df_map.columns):
        df_map_unique = (
            df_map.drop_duplicates(subset=['mapped_req_42'])
                  .sort_values('mapped_req_42')
        )
        req_name_mapping = {
            f"req_{int(row['mapped_req_42'])}": row['reduced_name']
            for _, row in df_map_unique.iterrows()
        }
    else:
        print(f"⚠️ El archivo '{mapping_file}' no contiene 'mapped_req_42' y 'reduced_name'.")
else:
    print(f"⚠️ Warning: Mapping file '{mapping_file}' not found. Using generic IDs.")

# -----------------------------
# 3. DECISION SPACE FREQUENCIES
# -----------------------------
profile_frequencies = {}

print("Calculating decision space frequencies...")
for profile_name, file_path in file_profiles.items():
    if os.path.exists(file_path):
        df_temp = pd.read_csv(file_path)

        valid_reqs = [col for col in target_requirements if col in df_temp.columns]

        if valid_reqs:
            frequency_series = df_temp[valid_reqs].mean() * 100
            frequency_series = frequency_series.reindex(target_requirements)
            profile_frequencies[profile_name] = frequency_series
        else:
            print(f"⚠️ No valid req columns found in {file_path}")
    else:
        print(f"⚠️ Missing profile file: {file_path}")

df_decision_space = pd.DataFrame(profile_frequencies)

# Mantener IDs internos y traducir visualmente después
df_decision_space = df_decision_space.reindex(target_requirements)

print("Decision space built.")

# -----------------------------
# 4. FUNCTION TO DETECT JOIN COLUMNS
# -----------------------------
def detect_merge_column(df_mapping, df_moscow):
    candidate_pairs = [
        ('original_id', 'original_id'),
        ('req_50', 'original_id'),
        ('source_id', 'original_id'),
        ('requirement_id_50', 'original_id'),
        ('name_en', 'name_en'),
        ('name_es', 'name_es'),
    ]

    for left_col, right_col in candidate_pairs:
        if left_col in df_mapping.columns and right_col in df_moscow.columns:
            return left_col, right_col

    return None, None

# -----------------------------
# 5. LOAD & PROCESS STUDENT MUST PERCENTAGE
# -----------------------------
df_must_42 = None

if os.path.exists(moscow_file):
    df_moscow = pd.read_csv(moscow_file)

    if 'total_m' not in df_moscow.columns:
        raise ValueError(f"El archivo {moscow_file} debe contener la columna 'total_m'")

    # Detectar automáticamente cuántos alumnos hay a partir de al1, al2, ...
    student_cols = [c for c in df_moscow.columns if c.startswith('al')]
    n_students = len(student_cols)

    if n_students == 0:
        raise ValueError("No se han encontrado columnas de alumnos tipo 'al1', 'al2', ...")

    # Porcentaje MUST por requisito original
    df_moscow['must_pct'] = (df_moscow['total_m'] / n_students) * 100

    if df_map is not None and 'mapped_req_42' in df_map.columns:
        left_col, right_col = detect_merge_column(df_map, df_moscow)

        if left_col is not None:
            df_moscow_merge = df_moscow.merge(
                df_map,
                left_on=right_col,
                right_on=left_col,
                how='left'
            )

            df_moscow_merge = df_moscow_merge.dropna(subset=['mapped_req_42']).copy()
            df_moscow_merge['mapped_req_42'] = df_moscow_merge['mapped_req_42'].astype(int)
            df_moscow_merge['req_id_42'] = df_moscow_merge['mapped_req_42'].apply(lambda x: f"req_{x}")

            # IMPORTANTE:
            # si varios requisitos originales caen en el mismo requisito reducido,
            # utilizamos la MEDIA del porcentaje MUST para mantener escala 0-100.
            df_must_42 = (
                df_moscow_merge.groupby('req_id_42', as_index=False)['must_pct']
                               .mean()
            )

            df_must_42 = df_must_42.set_index('req_id_42')
            df_must_42 = df_must_42.rename(columns={'must_pct': 'Must (%)'})

            # Mantener exactamente el mismo orden que el decision space
            df_must_42 = df_must_42.reindex(df_decision_space.index)

        else:
            print("⚠️ No se encontró columna compatible para unir mapping y moscow.")
    else:
        print("⚠️ No mapping file válido; no se puede proyectar total_m al espacio reducido de 42 requisitos.")
else:
    print(f"⚠️ No se encontró {moscow_file}")

# -----------------------------
# 6. LABELS FOR DISPLAY
# -----------------------------
display_labels = [req_name_mapping.get(req, req) for req in df_decision_space.index]

# Exportar resumen combinado
if df_must_42 is not None and not df_must_42.empty:
    df_summary = df_decision_space.copy()
    df_summary['Must (%)'] = df_must_42['Must (%)']
    df_summary.index = display_labels
    df_summary.to_csv("decision_space_with_students_must_percentage.csv", encoding='utf-8-sig')
    print("✅ Summary exported: decision_space_with_students_must_percentage.csv")

# -----------------------------
# 7. VISUALIZATION
# -----------------------------
sns.set_theme(style="ticks")

if df_must_42 is not None and not df_must_42.empty:
    fig, axes = plt.subplots(
        1, 2,
        figsize=(20, 14),
        gridspec_kw={'width_ratios': [4.8, 1.1]}
    )

    # Heatmap principal: selección automática
    sns.heatmap(
        df_decision_space,
        cmap="YlGnBu",
        annot=True,
        fmt=".1f",
        linewidths=.5,
        cbar_kws={'label': '% of solutions in the group including the requirement'},
        yticklabels=display_labels,
        ax=axes[0]
    )
    axes[0].set_title(
        "Decision Space Analysis: Requirement Selection Frequency by Strategy",
        fontsize=14,
        fontweight='bold',
        pad=14
    )
    axes[0].set_xlabel("Post-Optimization Strategies / Filters", fontsize=12, labelpad=10)
    axes[0].set_ylabel("System Requirements (Mapped Names)", fontsize=12, labelpad=10)
    axes[0].tick_params(axis='x', rotation=45, labelsize=10)
    axes[0].tick_params(axis='y', labelsize=10)

    # Heatmap lateral: porcentaje Must de estudiantes
    sns.heatmap(
        df_must_42,
        cmap="OrRd",   # otro color, visualmente muy claro
        annot=True,
        fmt=".1f",
        linewidths=.5,
        cbar_kws={'label': '% of students marking the requirement as MUST'},
        yticklabels=False,   # ya aparecen en el panel izquierdo
        ax=axes[1]
    )
    axes[1].set_title(
        "Student Priority\n(MUST %)",
        fontsize=14,
        fontweight='bold',
        pad=14
    )
    axes[1].set_xlabel("")
    axes[1].set_ylabel("")
    axes[1].tick_params(axis='x', rotation=0, labelsize=10)

    plt.tight_layout()

    output_filename = "decision_space_requirements_with_students_must_percentage.png"
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"🎉 Plot successfully exported as: '{output_filename}'")
    plt.show()

else:
    # Fallback: solo el heatmap principal
    plt.figure(figsize=(14, 12))
    sns.heatmap(
        df_decision_space,
        cmap="YlGnBu",
        annot=True,
        fmt=".1f",
        linewidths=.5,
        cbar_kws={'label': '% of solutions in the group including the requirement'},
        yticklabels=display_labels
    )
    plt.title(
        "Decision Space Analysis: Requirement Selection Frequency by Strategy",
        fontsize=14,
        fontweight='bold',
        y=1.02
    )
    plt.xlabel("Post-Optimization Strategies / Filters", fontsize=12, labelpad=10)
    plt.ylabel("System Requirements (Mapped Names)", fontsize=12, labelpad=10)
    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.yticks(fontsize=10)
    plt.tight_layout()

    output_filename = "decision_space_requirements.png"
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"🎉 Plot successfully exported as: '{output_filename}'")
    plt.show()

# %%