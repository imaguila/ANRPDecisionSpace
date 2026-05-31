from problem import calcular_indicadores, REQUISITOS


def detectar_indicadores_posibles(df):
    posibles = []

    for nombre, requisitos in REQUISITOS.items():
        if all(col in df.columns for col in requisitos):
            posibles.append(nombre)

    return posibles


def aplicar_enrichment(df, selected_indicators):
    if not selected_indicators:
        return df

    return calcular_indicadores(df, selected_indicators)

