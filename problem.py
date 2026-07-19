import pandas as pd
import numpy as np
from config import PROBLEMAS

EPS = 1e-9


INDICADORES = {

    "productivity": lambda df:
        df["satisfaction"] / np.maximum(df["effort"], EPS),

    "effectiveness": lambda df:
        df["satisfaction"] / np.maximum(df["cost"], EPS),

    "squandering": lambda df:
        (df["effort"].max() - df["effort"]) / np.maximum(df["effort"].max(), EPS),

    "dirtiness": lambda df:
        np.where(
            df.get("dissatisfaction", 0) == 0,
            0,
            df["dissatisfaction"] / np.maximum(df["effort"], EPS)
        ),

    "annoyance": lambda df:
        np.where(
            df.get("dissatisfaction", 0) == 0,
            0,
            df["dissatisfaction"] / np.maximum(df["satisfaction"], EPS)
        ),

    "stickiness": lambda df:
        df["prevalence"] / np.maximum(df["effort"], EPS),

    "robustness": lambda df:
        df["satisfaction"] / np.maximum(df["inestability"], EPS),

    "fragility": lambda df:
        (df["prevalence"] * df["inestability"]) /
        np.maximum(df["effort"], EPS),

    "response": lambda df:
        np.where(
            df["time"] == 0,
            0,
            df["time"] / np.maximum(df["effort"], EPS)
        ),

    "opportunity": lambda df:
        np.where(
            df["satisfaction"] == 0,
            0,
            df["satisfaction"] / np.maximum(df["time"], EPS)
        ),
    "usage_efficiency": lambda df:
        (df["prevalence"] / df["cost"].replace(0, np.nan)).fillna(0),

    "scope": lambda df:
        df.filter(like="req_").sum(axis=1) /
        np.maximum(len(df.filter(like="req_").columns), EPS)


}




REQUISITOS = {
    "productivity": ["satisfaction", "effort"],
    "effectiveness": ["satisfaction", "cost"],
    "dirtiness": ["dissatisfaction", "effort"],
    "annoyance": ["dissatisfaction", "satisfaction"],
    "stickiness": ["prevalence", "effort"],
    "robustness": ["satisfaction", "inestability"],
    "fragility": ["prevalence", "inestability", "effort"],
    "response": ["time", "effort"],
    "opportunity": ["satisfaction", "time"],
    "usage_efficiency": ["prevalence", "cost"],
    "scope": [],
    "squandering": ["effort"]
}



def leer_soluciones(config):
    import pandas as pd
    import numpy as np

    # 1️⃣ Leer fichero
    df = pd.read_csv(
        config["path_sol"],
        header=None,
        sep=r"\s+",
        engine="python"
    )

    # 2️⃣ Eliminar columnas completamente vacías
    df = df.dropna(axis=1, how='all')

    # 3️⃣ Eliminar columnas basura (como | o \)
    df = df.loc[:, ~(df.astype(str).apply(lambda col: col.str.contains(r"[|\\]")).any())]

    # 4️⃣ Asegurar que todo lo posible es numérico
    df = df.apply(pd.to_numeric, errors='coerce')

    # 5️⃣ Definir columnas esperadas
    columnas_metricas = config["metricas"]
    columnas_req = [f"req_{i+1}" for i in range(config["num_req"])]

    total_cols = len(columnas_metricas) + len(columnas_req)

    # 6️⃣ Si hay columnas extra → cortar
    if df.shape[1] > total_cols:
        print(f"[INFO] Columnas extra detectadas: {df.shape[1]} → {total_cols}")
        df = df.iloc[:, :total_cols]

    # 7️⃣ Validación
    if df.shape[1] < total_cols:
        raise ValueError(f"Faltan columnas: {df.shape[1]} < {total_cols}")

    # 8️⃣ Asignar nombres
    df.columns = columnas_metricas + columnas_req

    # 9️⃣ ID
    df["id"] = range(1, len(df) + 1)
    df.reset_index(drop=True, inplace=True)

    return df


def leer_problema(config):
    if config["path_prob"] is None:
        return None

    return pd.read_csv(
        config["path_prob"],
        sep=r"\s+",
        engine="python"
    )


def calcular_stakeholders(df, problema, prefix):

    if problema is None or prefix is None:
        return df

    clientes = [c for c in problema.columns if c.startswith(prefix)]
    cols_req = [c for c in df.columns if c.startswith('req_')]

    # ✅ convertir a números (CLAVE)
    matriz_req = df[cols_req].apply(pd.to_numeric, errors='coerce').values
    matriz_val = problema[clientes].apply(pd.to_numeric, errors='coerce').values

    valor = np.dot(matriz_req, matriz_val)

    total = problema[clientes].apply(pd.to_numeric, errors='coerce').sum()

    for i, c in enumerate(clientes):
        df[f"stcov_{c}"] = valor[:, i] / (total[c] + 1e-9)

    return df


def calcular_matriz_solicitud(problema, prefix, threshold=0):
    """
    Matriz real (no simulada) de solicitud stakeholder-requisito.

    Devuelve un DataFrame booleano de tamaño (num_requisitos x num_stakeholders):
    True si ese stakeholder asignó a ese requisito un valor > threshold en la
    elicitación (vij), es decir, si realmente lo solicitó/valoró.

    El orden de las filas coincide con el orden de columnas_req usado en
    leer_soluciones/calcular_stakeholders, así que la fila j corresponde
    siempre a req_{j+1}.
    """
    if problema is None or prefix is None:
        return None

    clientes = [c for c in problema.columns if c.startswith(prefix)]
    matriz_val = problema[clientes].apply(pd.to_numeric, errors='coerce').values

    solicitado = matriz_val > threshold
    return pd.DataFrame(solicitado, columns=clientes)


def calcular_indicadores(df, indicadores_a_usar):
    nuevas = {}

    for nombre in indicadores_a_usar:

        if nombre not in INDICADORES:
            print(f"{nombre} no existe")
            continue

        requisitos = REQUISITOS.get(nombre, [])

        if all(col in df.columns for col in requisitos):
            try:
                nuevas[nombre] = INDICADORES[nombre](df)
            except Exception:
                print(f"Error en {nombre}")
        else:
            print(f"Saltando {nombre} (faltan columnas)")

    return pd.concat([df, pd.DataFrame(nuevas)], axis=1)



def run_pipeline(nombre_problema, indicadores):
    config = PROBLEMAS[nombre_problema]

    df = leer_soluciones(config)
    problema = leer_problema(config)

    df = calcular_indicadores(df, indicadores)
    df = calcular_stakeholders(df, problema, config["stakeholders_prefix"])

    matriz_solicitud = calcular_matriz_solicitud(problema, config["stakeholders_prefix"])

    return df, matriz_solicitud
