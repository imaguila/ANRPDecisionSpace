# %% [markdown]
# # Matriz de Comparación Dos a Dos - Espacios de Decisión NRP (Nueva Configuración)

# %%
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# 1. Definición del nuevo set de 10 archivos (Formato estándar de 42 requisitos)
archivos_nuevos = {
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

# 2. Carga, filtrado de métricas clave y unificación en DataFrame maestro
lista_df = []

print("Procesando los nuevos datasets...")
for nombre_perfil, ruta_archivo in archivos_nuevos.items():
    if os.path.exists(ruta_archivo):
        df_temp = pd.read_csv(ruta_archivo)
        
        # Extraemos las tres dimensiones de análisis bidimensional
        df_reducido = df_temp[['satisfaction', 'effort', 'time']].copy()
        df_reducido['Perfil'] = nombre_perfil
        lista_df.append(df_reducido)
    else:
        print(f"⚠️ Archivo ausente ignorado: {ruta_archivo}")

# Concatenación de la nueva estructura
df_maestro = pd.concat(lista_df, ignore_index=True)
print(f"¡Unificación completada con éxito!")
print(f"Total de perfiles activos: {df_maestro['Perfil'].nunique()}")
print(f"Total de soluciones mapeadas en el espacio: {len(df_maestro)}")

# %%
# 3. DISEÑO Y GENERACIÓN DE LA MATRIZ CRUZADA DOS A DOS
print("\nDibujando matriz de dispersión cruzada...")

sns.set_theme(style="ticks")

# Paleta discreta profesional de 10 colores diferenciados
palette_10 = sns.color_palette("tab10", 10)

# Inicializamos la cuadrícula PairGrid excluyendo la simetría duplicada (corner=True)
g = sns.PairGrid(
    df_maestro, 
    hue="Perfil", 
    vars=['effort', 'satisfaction', 'time'], 
    palette=palette_10,
    corner=True,
    height=3.5
)

# Configuración de las diagonales: Curvas de densidad estimadas (KDE)
g.map_diag(sns.kdeplot, fill=True, alpha=0.12, warn_singular=False)

# Configuración de los cruces bidimensionales externos: Gráficos de dispersión discretos
g.map_offdiag(sns.scatterplot, size=12, alpha=0.55, linewidth=0)

# Ajuste fino de anotaciones, leyendas estéticas y títulos primarios
g.add_legend(title="Estrategia / Filtro de Espacio", adjust_subtitles=True)
g.fig.suptitle("Análisis Cruzado Dos a Dos: Estructuración del Espacio de Decisión", y=1.03, fontsize=15, fontweight='bold')

# 4. GUARDADO DE LA IMAGEN EN LA CARPETA DE TRABAJO
nombre_salida = "nueva_matriz_estructuracion.png"
plt.savefig(nombre_salida, dpi=300, bbox_inches='tight')

print(f"🎉 ¡Proceso finalizado! Gráfico exportado como: '{nombre_salida}'")
plt.show()
# %%
