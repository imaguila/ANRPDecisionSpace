import pandas as pd

def columnas_analisis(df):

    exclude_patterns = ["req_", "stcov_"]
    exclude_exact = ["id"]

    cols = []

    for c in df.columns:
        if c in exclude_exact:
            continue

        if any(c.startswith(p) for p in exclude_patterns):
            continue

        if pd.api.types.is_numeric_dtype(df[c]):
            cols.append(c)

    return cols