import pandas as pd
import os


def load_csv(uploaded_file):
    return pd.read_csv(uploaded_file)


def preparar_df_csv(df):
    df = df.copy()
    return df
