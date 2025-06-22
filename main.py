import streamlit as st
st.set_page_config(page_title="Dashboard Wisata", layout="wide")

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import dendrogram, linkage
import base64
from sklearn.preprocessing import MinMaxScaler

from scripts import (
    clustering_bantul,
    clustering_sleman,
    clustering_kulon_progo,
    clustering_gunung_kidul,
    clustering_kota_yogyakarta,
    lat_long
)

# Fungsi untuk menambahkan background
def add_bg_from_local(image_file):
    with open(image_file, "rb") as image:
        encoded = base64.b64encode(image.read()).decode()
    st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpeg;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}
        </style>
    """, unsafe_allow_html=True)

add_bg_from_local("images/d.jpg")

# Login session
if "login" not in st.session_state:
    st.session_state.login = False

if "page" not in st.session_state:
    st.session_state.page = "data_wisata"

if not st.session_state.login:
    st.subheader("\U0001F511 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "admin" and password == "admin":
            st.session_state.login = True
            st.rerun()
        else:
            st.error("Username atau Password Salah!")
    st.stop()

# Halaman: Data Kunjungan Wisata
if st.session_state.page == "data_wisata":
    # Pilih daerah (Hanya tampil di halaman data_wisata)
    daerah_options = {
        "Kabupaten Bantul": clustering_bantul,
        "Kabupaten Sleman": clustering_sleman,
        "Kabupaten Kulon Progo": clustering_kulon_progo,
        "Kabupaten Gunung Kidul": clustering_gunung_kidul,
        "Kota Yogyakarta": clustering_kota_yogyakarta
    }
    
    selected_daerah = st.sidebar.selectbox(
        "Pilih Daerah",
        list(daerah_options.keys()),
        index=list(daerah_options.keys()).index(
            st.session_state.get("selected_daerah", list(daerah_options.keys())[0])
        )
    )

    # Update session state jika daerah dipilih ulang
    if selected_daerah != st.session_state.get("selected_daerah", ""):
        st.session_state.selected_daerah = selected_daerah
        st.session_state.selected_clustering = daerah_options[selected_daerah]
        st.rerun()
    else:
        selected_daerah = st.session_state.selected_daerah
        selected_clustering = st.session_state.selected_clustering

    # Menampilkan data berdasarkan daerah yang dipilih
    st.title(f"\U0001F4CA Data Kunjungan Wisata - {selected_daerah}")

    # Load data
    data_path = f"data/Data {selected_daerah} 2023.xlsx"
    df_input = pd.read_excel(data_path, sheet_name=0)
    if "Unnamed: 0" in df_input.columns:
        df_input.rename(columns={"Unnamed: 0": "Nama Tempat"}, inplace=True)
    df_lokasi = lat_long.load_lokasi(selected_daerah)

    # Simpan df_input ke session agar bisa diakses di halaman lain
    st.session_state.df_input = df_input
    df_display = df_input.iloc[:, :13]
    st.data_editor(df_display, use_container_width=True, height=500, disabled=True)

    col1, col2 = st.columns(2)
    with col1:
        edit_index = st.selectbox("Pilih Baris untuk Edit:", df_display.index)
        if st.button("✏️ Edit Data"):
            st.session_state.edit_index = edit_index
    with col2:
        delete_index = st.selectbox("Pilih Baris untuk Hapus:", df_display.index)
        if st.button("🗑️ Hapus Data"):
            # Dapatkan nama tempat yang akan dihapus
            nama_tempat = df_input.loc[delete_index, "Nama Tempat"]
            # Hapus data tempat wisata di df_input
            df_input.drop(delete_index, inplace=True)
            # Hapus data tempat wisata yang sesuai di df_lokasi
            df_lokasi = df_lokasi[df_lokasi["Nama Tempat"] != nama_tempat]
            # Simpan perubahan pada file Excel data wisata
            df_input.to_excel(data_path, sheet_name="Sheet2", index=False)
            # Simpan perubahan pada file latlong
            selected_daerah = st.session_state.selected_daerah
            file_latlong = f"data/Jarak {selected_daerah}.xlsx"
            df_lokasi.to_excel(file_latlong, index=False)
            # Menyimpan perubahan ke session state
            st.session_state.df_input = df_input
            st.session_state.df_lokasi = df_lokasi
            st.success(f"Data untuk {nama_tempat} berhasil dihapus dari Data Kunjungan dan Latitude/Longitude!")
            st.rerun()

    if "edit_index" in st.session_state:
        st.subheader("\U0001F4DD Edit Data Kunjungan")
        idx = st.session_state.edit_index
        with st.form("edit_form"):
            new_data = {}
            for col in df_display.columns:
                input_val = st.text_input(col, str(df_display.at[idx, col]))
                if col != "Nama Tempat":
                    try:
                        input_val = float(input_val.replace(",", ""))  # Parsing as float
                    except ValueError:
                        input_val = np.nan
                new_data[col] = input_val

            if st.form_submit_button("Simpan"):
                for col in df_display.columns:
                    df_input.at[idx, col] = new_data[col]
                df_input.to_excel(data_path, sheet_name="Sheet2", index=False)
                st.success("Data berhasil diperbarui!")
                del st.session_state.edit_index
                st.rerun()

    with st.expander("➕ Tambah Data Kunjungan Wisatawan"):
        new_entry = {}
        for col in df_display.columns:
            value = st.text_input(f"{col}")
            if col != "Nama Tempat":
                try:
                    value = float(value.replace(",", ""))
                except ValueError:
                    value = np.nan
            new_entry[col] = value

        if st.button("Tambah Data"):
            df_input.loc[len(df_input)] = new_entry
            df_input.to_excel(data_path, sheet_name="Sheet2", index=False)
            st.success("Data Kunjungan Wisatawan berhasil ditambahkan!")
            st.rerun()

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➡️ Lanjut ke Latitude & Longitude", use_container_width=True):
            st.session_state.page = "latlong"
            st.rerun()

# Halaman: Latitude & Longitude
if st.session_state.page == "latlong":
    st.title("📍 Data Latitude & Longitude")
    selected_daerah = st.session_state.selected_daerah
    file_latlong = f"data/Jarak {selected_daerah}.xlsx"

    try:
        df_lokasi = lat_long.load_lokasi(selected_daerah)
        st.session_state.df_lokasi = df_lokasi
    except Exception as e:
        st.error(f"Gagal memuat data latlong dari file: {e}")
        df_lokasi = pd.DataFrame(columns=["Nama Tempat", "Latitude", "Longitude"])
        st.session_state.df_lokasi = df_lokasi
    else:
        df_lokasi = st.session_state.df_lokasi

    df_input = st.session_state.df_input

    # Ambil nama tempat dari data kunjungan
    tempat_kunjungan = df_input["Nama Tempat"].unique()
    tempat_latlong = df_lokasi["Nama Tempat"].unique()
    selected_daerah = st.session_state.selected_daerah
    file_latlong = f"data/Jarak {selected_daerah}.xlsx"

    # Menentukan tempat-tempat yang belum memiliki koordinat
    tempat_baru = df_input[~df_input["Nama Tempat"].isin(df_lokasi["Nama Tempat"])]["Nama Tempat"].tolist()

    # Cek jika ada tempat yang belum memiliki koordinat
    if tempat_baru:
        st.warning("⚠️ Ada tempat yang belum memiliki koordinat. Silakan lengkapi.")
        for tempat in tempat_baru:
            with st.form(f"form_{tempat}"):
                st.markdown(f"**{tempat}**")
                lat = st.text_input(f"Latitude untuk {tempat}")
                lon = st.text_input(f"Longitude untuk {tempat}")
                if st.form_submit_button("Simpan"):
                    if lat and lon:
                        new_data = {"Nama Tempat": tempat, "Latitude": lat, "Longitude": lon}
                        df_lokasi = pd.concat([df_lokasi, pd.DataFrame([new_data])], ignore_index=True)
                        st.session_state.df_lokasi = df_lokasi
                        df_lokasi.to_excel(file_latlong, index=False)
                        st.success(f"Koordinat untuk {tempat} berhasil disimpan!")
                        st.rerun()
                    else:
                        st.error("Latitude dan Longitude harus diisi!")

    st.data_editor(df_lokasi, use_container_width=True, height=500, disabled=True)
    # Form edit koordinat
    if not df_lokasi.empty:
        with st.expander("✏️ Edit Koordinat Tempat"):
            tempat_edit = st.selectbox("Pilih tempat:", df_lokasi["Nama Tempat"])
            lat_edit = st.text_input("Latitude baru", value=str(df_lokasi[df_lokasi["Nama Tempat"] == tempat_edit]["Latitude"].values[0]))
            lon_edit = st.text_input("Longitude baru", value=str(df_lokasi[df_lokasi["Nama Tempat"] == tempat_edit]["Longitude"].values[0]))
            if st.button("Simpan Perubahan Koordinat"):
                df_lokasi.loc[df_lokasi["Nama Tempat"] == tempat_edit, "Latitude"] = lat_edit
                df_lokasi.loc[df_lokasi["Nama Tempat"] == tempat_edit, "Longitude"] = lon_edit
                st.session_state.df_lokasi = df_lokasi
                df_lokasi.to_excel(file_latlong, index=False)
                st.success(f"Koordinat untuk {tempat_edit} berhasil diperbarui!")
                st.rerun()

    # Navigasi
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔙 Kembali ke Data Kunjungan Wisatawan", use_container_width=True):
            st.session_state.page = "data_wisata"
            st.rerun()
    with col2:
        if tempat_baru:
            st.button("➡️ Proses Clustering", use_container_width=True, disabled=True)
            st.info("Lengkapi semua koordinat terlebih dahulu.")
        else:
            if st.button("➡️ Proses Clustering", use_container_width=True):
                st.session_state.page = "clustering"
                st.rerun()

import streamlit as st
import importlib
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import pydeck as pdk
from scripts import lat_long  # Mengimpor modul lat_long.py untuk perhitungan jarak

# Halaman: Clustering
if st.session_state.page == "clustering":
    st.markdown(
    "<h1 style='text-align: center;'>Hasil Clustering</h1>",
    unsafe_allow_html=True
)
    selected_daerah = st.session_state.selected_daerah.lower().replace(" ", "_")
    try:
        clustering_scripts = importlib.import_module(f"scripts.clustering_{selected_daerah.replace('kabupaten_', '')}") # Mencoba mengimpor modul sesuai dengan daerah yang dipilih
    except ModuleNotFoundError:
        st.error(f"Modul untuk {selected_daerah} tidak ditemukan di folder 'scripts'.")
        st.stop()  # Berhenti jika modul tidak ditemukan

    # Panggil fungsi di dalam modul seperti biasa
    df_input = st.session_state.df_input
    df_cleaned, features, rekomendasi, df_filled = clustering_scripts.do_clustering(df_input)
    st.dataframe(df_filled.round(0))
    
    # Dendrogram
    st.subheader("📊Dendrogram")
    fig, ax = plt.subplots(figsize=(10, 5))
    clustering_scripts.plot_dendrogram(df_cleaned, features, ax=ax)
    st.pyplot(fig)
    st.subheader("📋 Hasil Clustering")
    st.dataframe(df_cleaned)

    # Jarak Antar Tempat Wisata
    st.subheader("🗺 Jarak Antar Tempat Wisata")
    import os

    # Tentukan path untuk file latlong
    file_latlong = f"Jarak {selected_daerah}.xlsx"

    if not os.path.exists(file_latlong):
        df_lokasi = pd.DataFrame(columns=["Nama Tempat", "Latitude", "Longitude"])
        df_lokasi.to_excel(file_latlong, index=False)
    else:
        df_lokasi = pd.read_excel(file_latlong)

    # Load data latlong dari session state atau file
    if "df_lokasi" not in st.session_state:
        try:
            df_lokasi = pd.read_excel(file_latlong)
            df_lokasi.columns = df_lokasi.columns.astype(str).str.strip()  # <- LETAKKAN DI SINI
            st.session_state.df_lokasi = df_lokasi
        except Exception as e:
            st.error(f"Gagal memuat data latlong: {e}")
            df_lokasi = pd.DataFrame()
    else:
        df_lokasi = st.session_state.df_lokasi
        df_lokasi.columns = df_lokasi.columns.astype(str).str.strip()  # <- DAN JUGA DI SINI UNTUK MEMASTIKAN

    # Pastikan kolom-kolom di df_lokasi memiliki format yang benar
    if not df_lokasi.empty:
        df_lokasi.columns = df_lokasi.columns.astype(str).str.strip().str.title()  # Konversi kolom menjadi string terlebih dahulu

    # Pastikan kolom 'Nama Tempat' ada di df_lokasi dan df_cleaned
    if 'Nama Tempat' in df_lokasi.columns and 'Nama Tempat' in df_cleaned.columns:
        df_cleaned = pd.merge(df_cleaned, df_lokasi, on="Nama Tempat", how="left")
    else:
        st.error("Kolom 'Nama Tempat' tidak ditemukan di salah satu DataFrame!")
        st.stop()

    # Lakukan clustering dan tampilkan heatmap
    df_cleaned, features, rekomendasi, df_filled = clustering_scripts.do_clustering(df_input)
    if not df_lokasi.empty:
        df_with_coords = pd.merge(df_cleaned, df_lokasi, on="Nama Tempat", how="left")
        # Pastikan tidak ada nilai NaN di kolom koordinat
        df_with_coords = df_with_coords.dropna(subset=["Latitude", "Longitude"])
        # Hitung jarak pakai dataframe yang sudah ada koordinatnya
        distance_matrix = lat_long.compute_distance_matrix(df_with_coords)
        st.dataframe(distance_matrix)  # Tampilkan matriks jarak

    st.subheader("🗺 Maps Jarak Antar Tempat Wisata")
    # Gabungkan data latlong ke hasil clustering (df_cleaned)
    df_map = pd.merge(df_cleaned, df_lokasi[["Nama Tempat", "Latitude", "Longitude"]], on="Nama Tempat", how="left")

    # Pastikan tidak ada koordinat yang hilang
    if df_map[["Latitude", "Longitude"]].isnull().any().any():
        st.warning("Beberapa tempat wisata tidak memiliki koordinat. Pastikan data latlong cocok di kedua tabel.")
    else:
        # Normalisasi isi label cluster
        df_map["Cluster"] = df_map["Cluster"].astype(str).str.strip().str.title()  # Jika belum pasti konsisten

        # Fungsi pewarnaan sesuai label
        def get_color(label):
            if label == "Tinggi":
                return [0, 128, 0, 180]    # Hijau
            elif label == "Sedang":
                return [255, 165, 0, 180]  # Oranye
            elif label == "Rendah":
                return [200, 30, 0, 180]   # Merah
            else:
                return [100, 100, 100, 180]  # Default abu-abu jika tidak dikenali

        # Terapkan warna ke DataFrame
        df_map["color"] = df_map["Label"].apply(get_color)

        # Pydeck layer
        scatter_layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_map,
            get_position='[Longitude, Latitude]',
            get_color='color',
            get_radius=300,
            pickable=True
        )

        # Tampilan awal peta
        view_state = pdk.ViewState(
            latitude=df_map["Latitude"].mean(),
            longitude=df_map["Longitude"].mean(),
            zoom=10,
            pitch=0
        )

        # Tampilkan peta
        st.pydeck_chart(pdk.Deck(
            map_style='mapbox://styles/mapbox/light-v9',
            initial_view_state=view_state,
            layers=[scatter_layer],
            tooltip={"text": "{Nama Tempat} - {Label}"}
        ))

    # Tombol Navigasi
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔙 Kembali ke Latitude & Longitude", use_container_width=True):
            st.session_state.page = "latlong"
            st.rerun()
    with col2:
        if st.button("🔙Logout", use_container_width=True):
            st.session_state.page = "login"
            st.session_state.login = False  # Menambahkan ini untuk reset status login
            st.rerun()

    
    
