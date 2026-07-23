import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def calculate_jaccard_distance_matrix(binary_matrix):
    """Calcula la distancia de Jaccard promedio entre soluciones (diversidad interna)."""
    if len(binary_matrix) <= 1:
        return 0.0
    
    intersection = np.dot(binary_matrix, binary_matrix.T)
    sum_rows = binary_matrix.sum(axis=1)
    union = sum_rows[:, None] + sum_rows[None, :] - intersection
    
    with np.errstate(divide='ignore', invalid='ignore'):
        similarity = np.where(union == 0, 1.0, intersection / union)
    
    n = len(binary_matrix)
    mask = ~np.eye(n, dtype=bool)
    distances = 1.0 - similarity[mask]
    return float(np.mean(distances)) if len(distances) > 0 else 0.0


def process_lenses_with_baseline(file_pattern="*.csv"):
    """
    Lee los CSVs y usa el archivo '*_full.csv' como línea base de comparación.
    """
    file_paths = glob.glob(file_pattern)
    if not file_paths:
        print(f"No se encontraron archivos con el patrón '{file_pattern}'.")
        return None, None, None

    # Identificar el archivo base (_full)
    full_file = next((f for f in file_paths if os.path.basename(f).replace('.csv', '').endswith('_full')), None)
    
    if full_file is None:
        print("⚠️ No se encontró ningún archivo que termine en '_full.csv'. Se procesará sin línea base.")
        full_ids = set()
        total_full_solutions = 0
    else:
        df_full = pd.read_csv(full_file)
        full_ids = set(df_full['id'].values) if 'id' in df_full.columns else set(df_full.index)
        total_full_solutions = len(full_ids)
        print(f" Línea base detectada: '{os.path.basename(full_file)}' con {total_full_solutions} soluciones totales.")

    req_cols = [f'req_{i}' for i in range(1, 19)]
    stcov_cols = [f'stcov_c{i}' for i in range(1, 6)]
    
    summary_list = []
    lens_solutions_dict = {}

    for path in file_paths:
        lens_name = os.path.basename(path).replace('.csv', '')
        df = pd.read_csv(path)
        
        # Identificadores de soluciones
        current_ids = set(df['id'].values) if 'id' in df.columns else set(df.index)
        df = df.drop_duplicates(subset=['id']) if 'id' in df.columns else df
        lens_solutions_dict[lens_name] = current_ids

        # Cobertura respecto al conjunto FULL
        if total_full_solutions > 0:
            pct_full_coverage = (len(current_ids.intersection(full_ids)) / total_full_solutions) * 100.0
        else:
            pct_full_coverage = np.nan

        available_reqs = [c for c in req_cols if c in df.columns]
        req_matrix = df[available_reqs].values if available_reqs else np.array([])
        available_stcov = [c for c in stcov_cols if c in df.columns]
        
        diversity = calculate_jaccard_distance_matrix(req_matrix) if len(req_matrix) > 0 else 0.0

        metrics = {
            'Lens': lens_name,
            'Is_Baseline': lens_name.endswith('_full'),
            'Num_Solutions': len(df),
            'Pct_Full_Coverage': pct_full_coverage,
            'Avg_Satisfaction': df['satisfaction'].mean() if 'satisfaction' in df.columns else np.nan,
            'Avg_Effort': df['effort'].mean() if 'effort' in df.columns else np.nan,
            'Avg_Productivity': df['productivity'].mean() if 'productivity' in df.columns else np.nan,
            'Avg_Scope': df['scope'].mean() if 'scope' in df.columns else np.nan,
            'Avg_Squandering': df['squandering'].mean() if 'squandering' in df.columns else np.nan,
            'Avg_ST_Coverage': df[available_stcov].mean().mean() if available_stcov else np.nan,
            'Internal_Diversity_Jaccard': diversity
        }
        summary_list.append(metrics)

    summary_df = pd.DataFrame(summary_list)

    # Matriz de Solapamiento entre Lenses
    lens_names = list(lens_solutions_dict.keys())
    overlap_matrix = pd.DataFrame(index=lens_names, columns=lens_names, dtype=float)

    for l1 in lens_names:
        for l2 in lens_names:
            s1, s2 = lens_solutions_dict[l1], lens_solutions_dict[l2]
            union = len(s1.union(s2))
            overlap_matrix.loc[l1, l2] = len(s1.intersection(s2)) / union if union > 0 else 0.0

    return summary_df, overlap_matrix, total_full_solutions


def plot_baseline_dashboard(summary_df, overlap_matrix, output_filename="lens_baseline_dashboard.png"):
    """
    Genera el dashboard comparativo destacando el dataset _full como baseline (sin warnings de Seaborn).
    """
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Identificar la fila baseline
    baseline_row = summary_df[summary_df['Is_Baseline']]
    non_baseline = summary_df[~summary_df['Is_Baseline']]

    # --- 1. Trade-off: Satisfacción vs Esfuerzo (Resaltando _full) ---
    sns.scatterplot(
        data=non_baseline, x='Avg_Effort', y='Avg_Satisfaction', 
        hue='Lens', s=180, ax=axes[0, 0], palette='tab10'
    )
    if not baseline_row.empty:
        # Dibujar _full con un marcador de estrella roja más grande
        axes[0, 0].scatter(
            baseline_row['Avg_Effort'], baseline_row['Avg_Satisfaction'],
            color='crimson', s=350, marker='*', label='_full (Línea Base)', zorder=5
        )
    
    for _, row in summary_df.iterrows():
        fontw = 'bold' if row['Is_Baseline'] else 'normal'
        axes[0, 0].annotate(
            row['Lens'], 
            (row['Avg_Effort'], row['Avg_Satisfaction']),
            xytext=(6, 6), textcoords='offset points', fontsize=9, fontweight=fontw
        )
        
    axes[0, 0].set_title('1. Posicionamiento: Satisfacción vs Esfuerzo ( Estrella = _full)', fontsize=11, fontweight='bold')
    axes[0, 0].set_xlabel('Esfuerzo Promedio')
    axes[0, 0].set_ylabel('Satisfacción Promedio')

    # --- 2. Porcentaje de Soluciones Retenidas respecto a _full ---
    sns.barplot(
        data=summary_df.sort_values(by='Pct_Full_Coverage', ascending=False), 
        x='Pct_Full_Coverage', y='Lens', hue='Lens', legend=False,
        ax=axes[0, 1], palette='rocket'
    )
    axes[0, 1].set_title('2. % Cobertura del Total de Soluciones (respecto a _full)', fontsize=11, fontweight='bold')
    axes[0, 1].set_xlabel('% Soluciones Retenidas')
    axes[0, 1].set_xlim(0, 105)

    # --- 3. Productividad Promedio ---
    sns.barplot(
        data=summary_df.sort_values(by='Avg_Productivity', ascending=False), 
        x='Avg_Productivity', y='Lens', hue='Lens', legend=False,
        ax=axes[1, 0], palette='viridis'
    )
    axes[1, 0].set_title('3. Productividad Promedio (Satisfaction / Effort)', fontsize=11, fontweight='bold')
    axes[1, 0].set_xlabel('Productividad')

    # --- 4. Solapamiento de Soluciones entre Lenses (Heatmap) ---
    sns.heatmap(
        overlap_matrix, annot=True, fmt='.2f', cmap='Blues', 
        cbar=True, ax=axes[1, 1], vmin=0, vmax=1
    )
    axes[1, 1].set_title('4. Solapamiento de Soluciones (Índice Jaccard)', fontsize=11, fontweight='bold')
    axes[1, 1].tick_params(axis='x', rotation=25)

    plt.tight_layout()
    plt.savefig(output_filename, dpi=300)
    plt.show()
    print(f" Dashboard con Baseline guardado sin advertencias en '{output_filename}'")

# ==========================================
# EJECUCIÓN
# ==========================================
if __name__ == "__main__":
    summary_df, overlap_matrix, total_solutions = process_lenses_with_baseline(file_pattern="*.csv")
    
    if summary_df is not None:
        print("\n=== RESUMEN COMPARATIVO REFERENCIADO A _FULL ===")
        cols_to_show = ['Lens', 'Num_Solutions', 'Pct_Full_Coverage', 'Avg_Satisfaction', 'Avg_Effort', 'Avg_Productivity']
        print(summary_df[cols_to_show].to_string(index=False))
        
        plot_baseline_dashboard(summary_df, overlap_matrix)