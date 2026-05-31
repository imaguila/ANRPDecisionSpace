import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn_extra.cluster import KMedoids
from sklearn.metrics import silhouette_score
import hdbscan


def mcdm_topsis(df, metrics):

    X = df[metrics].values.astype(float)
    X_norm = X / np.sqrt((X**2).sum(axis=0))

    weights = np.ones(len(metrics)) / len(metrics)
    X_weighted = X_norm * weights

    ideal = X_weighted.max(axis=0)
    nadir = X_weighted.min(axis=0)

    dist_pos = np.sqrt(((X_weighted - ideal)**2).sum(axis=1))
    dist_neg = np.sqrt(((X_weighted - nadir)**2).sum(axis=1))

    score = dist_neg / (dist_pos + dist_neg + 1e-9)

    df["mcdm_score"] = score
    return df.sort_values("mcdm_score", ascending=False)


def clustering_kmedoids(df, metrics, k=3):

    X = StandardScaler().fit_transform(df[metrics])

    model = KMedoids(n_clusters=k, random_state=0)
    labels = model.fit_predict(X)

    df["cluster"] = labels

    try:
        score = silhouette_score(X, labels)
    except:
        score = None

    return df, score


def clustering_hdbscan(df, metrics):

    X = StandardScaler().fit_transform(df[metrics])
    labels = hdbscan.HDBSCAN().fit_predict(X)

    df["cluster"] = labels
    return df


def efficiency_ratio(df, num, den):

    df["efficiency"] = df[num] / np.maximum(df[den], 1e-9)
    return df.sort_values("efficiency", ascending=False)


def ranking_based(df, metrics, n_top):

    ranks = []

    for m in metrics:
        ranks.append(df.sort_values(m, ascending=False).head(n_top))

    counts = pd.concat(ranks).groupby("id").size().reset_index(name="count")

    return df.merge(counts, on="id", how="left").fillna(0)