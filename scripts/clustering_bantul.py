# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.cluster.hierarchy as sch
from scipy.cluster.hierarchy import fcluster
from sklearn.preprocessing import StandardScaler
from scipy.stats import zscore

# Fungsi untuk memberi label pada cluster berdasarkan nilai rata-rata
def label_cluster(x, overall_mean):
    if x > overall_mean * 1.2:
        return "Tinggi"
    elif x < overall_mean * 0.8:
        return "Rendah"
    return "Sedang"

def do_clustering(df_input):
    global df_final, features_used, rekomendasi_wisata

    # 1. Load data
    nama_tempat = df_input.iloc[:, 0]
    df_numeric = df_input.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')

    # ---------------------- 2. Imputasi nilai kosong ----------------------
    df_numeric_row_filled = df_numeric.apply(lambda row: row.fillna(row.mean()), axis=1)
    df_filled = df_numeric_row_filled.copy()
    df_filled.insert(0, "Nama Tempat", nama_tempat)

    # ---------------------- 3. Deteksi & penanganan outlier ----------------------
    features = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

    z_scores = pd.DataFrame(zscore(df_filled[features]), columns=features)
    threshold_z = 3
    df_adjusted = df_filled.copy()

    for col in features:
        col_z = z_scores[col].abs()
        max_valid = df_filled.loc[col_z <= threshold_z, col].max()
        df_adjusted[col] = np.where(col_z > threshold_z, max_valid, df_filled[col])

    # ---------------------- 4. Normalisasi ----------------------
    data_scaled = zscore(df_adjusted[features].values)
    df_normalized = pd.DataFrame(data_scaled, columns=features)
    df_normalized.insert(0, "Nama Tempat", nama_tempat)

    # ---------------------- 5. Clustering dengan metode & threshold konsisten ----------------------
    linkage_method = 'complete'
    threshold_distance = 10  

    linkage_matrix = sch.linkage(data_scaled, method=linkage_method)
    cluster_labels = fcluster(linkage_matrix, t=threshold_distance, criterion='distance')

    # ---------------------- 6. Simpan Hasil Clustering ----------------------
    df_cleaned = df_adjusted.copy()
    df_cleaned["Cluster"] = cluster_labels

    # ---------------------- 7. Label Cluster ----------------------
    cluster_summary = df_cleaned.groupby("Cluster")[features].mean()
    overall_mean = df_cleaned[features].mean().mean()
    cluster_summary["Label"] = cluster_summary.mean(axis=1).apply(lambda x: label_cluster(x, overall_mean))
    cluster_summary = cluster_summary.reset_index()

    df_cleaned["Cluster"] = df_cleaned["Cluster"].astype(np.int64)
    cluster_summary["Cluster"] = cluster_summary["Cluster"].astype(np.int64)
    df_cleaned = df_cleaned.merge(cluster_summary[["Cluster", "Label"]], on="Cluster", how="left")

    # ---------------------- 8. Simpan Output Global ----------------------
    df_final = df_cleaned
    features_used = features
    rekomendasi_wisata = df_cleaned[df_cleaned["Label"] == "Tinggi"][["Nama Tempat", "Cluster"]]

    return df_cleaned, features, rekomendasi_wisata

# Fungsi untuk menggambar dendrogram
def plot_dendrogram(df_final, features_used, ax=None):
    if df_final is None:
        raise ValueError("Jalankan do_clustering(df_input) terlebih dahulu.")
    scaler = StandardScaler()
    data_scaled = scaler.fit_transform(df_final[features_used])
    linkage_matrix = sch.linkage(data_scaled, method='complete')
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 5))
    sch.dendrogram(linkage_matrix, ax=ax)
    ax.set_title("Dendrogram - Complete Linkage")
    ax.axhline(y=10, color='r', linestyle='--')
