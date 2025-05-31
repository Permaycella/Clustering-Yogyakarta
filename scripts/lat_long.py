import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from geopy.distance import geodesic
import streamlit as st
import os

def load_lokasi(selected_daerah):
    file_path = f"data/Jarak {selected_daerah}.xlsx"
    if os.path.exists(file_path):
        return pd.read_excel(file_path)
    else:
        return pd.DataFrame(columns=["Nama Tempat", "Latitude", "Longitude"])

# Fungsi untuk menyimpan data Latitude dan Longitude ke file
def save_lokasi(selected_daerah, df_lokasi):
    data_path = f"data/Jarak {selected_daerah}.xlsx"
    df_lokasi.to_excel(data_path, index=False)
    st.success(f"Data berhasil disimpan di {data_path}")

# Fungsi Haversine (tidak digunakan, tapi disiapkan jika perlu)
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)

    a = np.sin(delta_phi/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c

def compute_distance_matrix(df):
    # Bersihkan nama kolom (hilangkan spasi dan jadikan lowercase)
    df.columns = df.columns.str.strip().str.lower()

    # Cek apakah kolom latitude dan longitude ada
    if "latitude" not in df.columns or "longitude" not in df.columns:
        st.error("Kolom 'Latitude' atau 'Longitude' tidak ditemukan di data!")
        st.write("Kolom yang ditemukan:", df.columns.tolist())
        return pd.DataFrame()  # Kembalikan dataframe kosong untuk menghindari error

    latitudes = df["latitude"].values
    longitudes = df["longitude"].values

    distance_matrix = []
    for i in range(len(df)):
        row_distances = []
        for j in range(len(df)):
            loc1 = (latitudes[i], longitudes[i])
            loc2 = (latitudes[j], longitudes[j])
            distance = geodesic(loc1, loc2).kilometers
            row_distances.append(distance)
        distance_matrix.append(row_distances)

    distance_df = pd.DataFrame(distance_matrix, columns=df['nama tempat'], index=df['nama tempat'])
    return distance_df

# Fungsi untuk menampilkan heatmap
def plot_heatmap(distance_matrix):
    plt.figure(figsize=(10, 8))
    sns.heatmap(distance_matrix, annot=True, fmt=".1f", cmap="YlGnBu", cbar_kws={'label': 'Jarak (km)'})
    plt.title("Heatmap Jarak Antar Tempat Wisata")
    plt.xlabel("Tempat Wisata")
    plt.ylabel("Tempat Wisata")
    plt.tight_layout()
    st.pyplot(plt)  # Untuk menampilkan heatmap di Streamlit

# Fungsi utama Streamlit interface
def main():
    st.title("Visualisasi Jarak Antar Tempat Wisata")

    selected_daerah = st.selectbox("Pilih Daerah", ["Bantul", "Mojokerto", "Yogyakarta"])

    df_lokasi = load_lokasi(selected_daerah)

    if not df_lokasi.empty:
        distance_df = compute_distance_matrix(df_lokasi)

        if not distance_df.empty:
            st.write("Matriks Jarak Antar Tempat Wisata:")
            st.dataframe(distance_df)

            plot_heatmap(distance_df)
        else:
            st.error("Matriks jarak tidak dapat dihitung.")
    else:
        st.error("Data lokasi kosong, pastikan file data sudah lengkap.")

if __name__ == "__main__":
    main()
