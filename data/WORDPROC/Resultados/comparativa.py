# %% [markdown]
# # Comparativa de Soluciones para el Problema NRP en VS Code

# %%
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Configurar estilo visual limpio
sns.set_theme(style="whitegrid")

# Diccionario con los archivos que queremos comparar
archivos = {
    'TOPSIS 50': 'topsis50.csv',
    'Weighted 50': 'weited50.csv',
    'Prod Effort': 'prodeffort.csv',
    'Clustering Objetivos': 'clustering objetivos.csv'
}

# 1. GENERAR VISIÓN GENERAL EN TEXTO (Se imprimirá en tu terminal)
print("=" * 60)
print("        RESUMEN COMPARATIVO DE DATASETS (MÉDIAS)")
print("=" * 60)

dfs_cargados = {}

for nombre, ruta in archivos.items():
    if os.path.exists(ruta):
        df = pd.read_csv(ruta)
        dfs_cargados[nombre] = df
        
        # Calcular métricas clave
        avg_sat = df['satisfaction'].mean()
        avg_eff = df['effort'].mean()
        avg_time = df['time'].mean()
        num_soluciones = len(df)
        
        print(f"📌 {nombre:22} | Soluciones: {num_soluciones:3} | Sat. Media: {avg_sat:7.1f} | Esfuerzo Medio: {avg_eff:6.1f}")
    else:
        print(f"❌ Archivo no encontrado: {ruta}")

print("=" * 60)

# 2. GENERAR GRÁFICO COMPARATIVO MULTI-METODOLOGÍA
plt.figure(figsize=(11, 7))

# Colores predefinidos para identificar cada archivo fácilmente
colores = {'TOPSIS 50': '#1f77b4', 'Weighted 50': '#ff7f0e', 'Prod Effort': '#2ca02c', 'Clustering Objetivos': '#d62728'}

for nombre, df in dfs_cargados.items():
    sns.scatterplot(
        data=df,
        x='effort',
        y='satisfaction',
        label=nombre,
        color=colores.get(nombre, '#7f7f7f'),
        alpha=0.6,
        s=60
    )

# Configuración de etiquetas y diseño del gráfico
plt.title('Frente de Soluciones NRP: Comparativa entre Enfoques', fontsize=14, fontweight='bold', pad=15)
plt.xlabel('Esfuerzo Requerido (Minimizar)', fontsize=12)
plt.ylabel('Satisfacción del Cliente (Maximizar)', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend(title="Metodología / Dataset", loc="lower right", frameon=True)

# Ajuste estricto de márgenes
plt.tight_layout()

# GUARDAR COMO IMAGEN (Por si no te salta la ventana gráfica, la verás en tu explorador de archivos)
nombre_grafico = "comparativa_soluciones_nrp.png"
plt.savefig(nombre_grafico, dpi=300)
print(f"\n🎉 ¡Gráfico guardado con éxito! Busca el archivo '{nombre_grafico}' en tu carpeta de VS Code.")

# Mostrar el gráfico (si usas la celda interactiva # %%, aparecerá a la derecha)
plt.show()
# %%


# %% [markdown]
# # Matriz de Comparación Bidimensional (Dos a Dos) de todos los Perfiles NRP
# %% [markdown]
# # Matriz de Comparación Bidimensional (Dos a Dos) de todos los Perfiles NRP

# %%
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# 1. Definir la lista con tus 10 perfiles/archivos
archivos_todos = {
    'Domain Specific': 'domainspecific.csv',
    'Scops Quan': 'scopsquan.csv',
    'Oports Quan': 'oportsquan.csv',
    'Prod Effort': 'prodeffort.csv',
    'HDBSCAN Medium Todo': 'hdbscanmediuntodo.csv',
    'HDBSCAN Medium Obj': 'hdbscanmediumobj.csv',
    'Clustering Todo': 'clusteringTodo.csv',
    'Clustering Objetivos': 'clustering objetivos.csv',
    'TOPSIS 50': 'topsis50.csv',
    'Weighted 50': 'weited50.csv'
}

# 2. Cargar y unificar todos los datasets en un único DataFrame maestro
lista_df = []

print("Cargando y procesando perfiles...")
for nombre_perfil, ruta_archivo in archivos_todos.items():
    if os.path.exists(ruta_archivo):
        df_temp = pd.read_csv(ruta_archivo)
        
        # Filtramos solo las métricas universales para la comparativa cruzada
        df_reducido = df_temp[['satisfaction', 'effort', 'time']].copy()
        
        # Etiquetamos a qué perfil pertenece cada fila de soluciones
        df_reducido['Perfil'] = nombre_perfil
        lista_df.append(df_reducido)
    else:
        print(f"⚠️ Archivo no encontrado saltado: {ruta_archivo}")

# Concatenamos todo en un único bloque de datos
df_maestro = pd.concat(lista_df, ignore_index=True)
print(f"¡Listo! Se han unificado {df_maestro['Perfil'].nunique()} perfiles con un total de {len(df_maestro)} soluciones.")

# %%
# 3. CONFIGURAR Y GENERAR LA MATRIZ DE GRÁFICOS DOS A DOS
print("Generando matriz de gráficos cruzados (esto puede tardar unos segundos)...")

sns.set_theme(style="ticks")
palette_10 = sns.color_palette("tab10", 10)

# Creamos el PairGrid (Matriz de gráficos cruzados) - CORREGIDO AQUÍ
g = sns.PairGrid(
    df_maestro, 
    hue="Perfil", 
    vars=['effort', 'satisfaction', 'time'], 
    palette=palette_10,
    corner=True,  # Evita duplicar gráficos simétricos para que sea más limpio de leer
    height=3.5
)

# Definir qué va en las diagonales (Distribución/Densidad de cada variable por perfil)
g.map_diag(sns.kdeplot, fill=True, alpha=0.15, warn_singular=False)

# Definir qué va fuera de la diagonal (Gráficos de dispersión cruzados dos a dos)
g.map_offdiag(sns.scatterplot, size=10, alpha=0.6, linewidth=0)

# Añadir títulos dinámicos a los ejes y ajustar leyenda
g.add_legend(title="Perfiles / Enfoques NRP")
g.fig.suptitle("Matriz de Trade-offs Dos a Dos de Todos los Perfiles", y=1.02, fontsize=16, fontweight='bold')

# 4. GUARDAR E IMPRIMIR EL RESULTADO EN VS CODE
nombre_imagen = "matriz_todos_los_perfiles.png"
plt.savefig(nombre_imagen, dpi=300, bbox_inches='tight')
print(f"🎉 ¡Éxito! Gráfico de matriz guardado en tu carpeta como: '{nombre_imagen}'")

# Mostrar en el panel interactivo de VS Code
plt.show()
# %%
