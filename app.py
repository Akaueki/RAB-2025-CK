import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import io
import math

# --- 1. KONFIGURASI REGIONAL & INDEKS KEMAHALAN KONSTRUKSI (IKK) ---
# Data sampel Indeks Kemahalan per Provinsi/Kabupaten (Standar Pusat = 1.0)
REGIONAL_INDEX = {
    "Jawa - DKI Jakarta (Standar)": 1.00,
    "Jawa - Surabaya/Sidoarjo": 0.95,
    "Jawa - Bandung/Bodeta": 0.98,
    "Jawa - Kab. Lainnya": 0.88,
    "Sumatera - Medan/Kota Besar": 1.05,
    "Sumatera - Kab. Lainnya": 0.95,
    "Kalimantan - Balikpapan (IKN)": 1.15,
    "Kalimantan - Kab. Lainnya": 1.10,
    "Sulawesi - Makassar/Kota Besar": 1.05,
    "Sulawesi - Kab. Lainnya": 1.00,
    "Papua & Maluku - Kota/Kab": 1.45
}

# --- 2. FUNGSI TERBILANG ---
def terbilang(n):
    angka = ["", "Satu", "Dua", "Tiga", "Empat", "Lima", "Enam", "Tujuh", "Delapan", "Sembilan", "Sepuluh", "Sebelas"]
    n = int(n)
    if n == 0: return "Nol"
    elif n < 12: return angka[n]
    elif n < 20: return terbilang(n - 10) + " Belas"
    elif n < 100: return terbilang(n // 10) + " Puluh " + terbilang(n % 10)
    elif n < 200: return "Seratus " + terbilang(n - 100)
    elif n < 1000: return terbilang(n // 100) + " Ratus " + terbilang(n % 100)
    elif n < 2000: return "Seribu " + terbilang(n - 1000)
    elif n < 1000000: return terbilang(n // 1000) + " Ribu " + terbilang(n % 1000)
    elif n < 1000000000: return terbilang(n // 1000000) + " Juta " + terbilang(n % 1000000)
    elif n < 1000000000000: return terbilang(n // 1000000000) + " Miliar " + terbilang(n % 1000000000)
    else: return "Angka Terlalu Besar"

# --- 3. SETUP HALAMAN ---
st.set_page_config(page_title="RAB AI & Timeline Pro", page_icon="🏢", layout="wide")
st.title("🏢 Auto-RAB AI: Kalkulator Terpadu & S-Curve")

# Load Database Dummy/Asli (Bisa disesuaikan dengan Excel Anda)
@st.cache_data
def load_db():
    try:
        # Mengambil dari file Excel Master yang sudah Anda buat sebelumnya
        df = pd.read_excel("RAB_Analisa_Lengkap_V4.xlsx", sheet_name="3_Daftar_AHSP_Master", skiprows=1)
        return df
    except:
        # Fallback database darurat jika Excel tidak terbaca
        return pd.DataFrame({
            "Kode AHSP": ["1.2.1.1.1", "2.2.2.1.1", "2.2.1.1.1", "3.6.1.1", "3.9.1.1", "2.1.1.1"],
            "Uraian Pekerjaan": ["Galian Tanah Biasa", "Pondasi Batu Kali", "Beton Bertulang K-175", "Pasangan Bata Merah", "Keramik Lantai", "Rangka Atap Baja Ringan"],
            "Satuan": ["m3", "m3", "m3", "m2", "m2", "m2"],
            "Total Harga (Rp)": [90860, 657500, 1184000, 278000, 112000, 298000]
        })

df_db = load_db()

# --- 4. VARIABEL SESSION STATE ---
if 'rab_final' not in st.session_state: st.session_state.rab_final = pd.DataFrame()

# --- 5. SIDEBAR: PENGATURAN HARGA & LOKASI ---
with st.sidebar:
    st.header("🌍 Pengaturan Regional & Keuntungan")
    lokasi = st.selectbox("Wilayah Proyek (Penyesuaian Harga Daerah):", list(REGIONAL_INDEX.keys()))
    faktor_lokasi = REGIONAL_INDEX[lokasi]
    st.info(f"Indeks Kemahalan: **{faktor_lokasi}x** dari standar pusat.")
    
    profit_margin = st.slider("Persentase Keuntungan & Overhead (%)", min_value=0, max_value=30, value=10, step=1)
    faktor_profit = 1 + (profit_margin / 100)

# --- 6. TABS UTAMA APLIKASI ---
tab1, tab2, tab3, tab4 = st.tabs(["📝 Input Form (Parametrik)", "🖼️ Input Gambar (AI Blueprint)", "📊 RAB & S-Curve", "🖨️ Download Excel"])

# ========================================================
# TAB 1: INPUT PARAMETRIK (Terintegrasi)
# ========================================================
with tab1:
    st.markdown("### Konfigurasi Desain Bangunan")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        jenis_bangunan = st.selectbox("Jenis Bangunan", ["Rumah Tinggal", "Kantor / Ruko", "Gudang / Pabrik", "Fasilitas Umum"])
        lantai = st.number_input("Jumlah Tingkat / Lantai", min_value=1, max_value=10, value=1)
        kapasitas = st.number_input("Kapasitas Penghuni (Orang)", min_value=1, value=4)
        
    with col2:
        luas_tanah = st.number_input("Luas Tanah (m2)", min_value=20, value=120)
        luas_bangunan = st.number_input("Total Luas Bangunan (m2)", min_value=20, value=60)
        # Validasi Ruang vs Kapasitas
        kebutuhan_ideal = kapasitas * 9 # Asumsi 1 orang butuh 9m2 ruang gerak ideal
        if luas_bangunan < kebutuhan_ideal:
            st.warning(f"⚠️ Kapasitas {kapasitas} orang idealnya butuh minimal luas {kebutuhan_ideal} m2.")
            
    with col3:
        jenis_tanah = st.selectbox("Kondisi Tanah Asli", ["Keras (Bagus)", "Sedang", "Lembek / Rawa"])
        # Integrasi Tanah -> Pondasi
        if jenis_tanah == "Keras (Bagus)":
            rekomendasi_pondasi = "Pondasi Menerus / Batu Kali"
        elif jenis_tanah == "Sedang":
            rekomendasi_pondasi = "Pondasi Footplat / Cakar Ayam"
        else:
            rekomendasi_pondasi = "Pondasi Tiang Pancang / Strauss Pile (Biaya Tinggi)"
        st.success(f"**Rekomendasi Pondasi:** {rekomendasi_pondasi}")

    st.markdown("### Spesifikasi & Material")
    style_bangunan = st.multiselect("Style Bangunan (Bisa Kombinasi)", ["Minimalis Modern", "Klasik / Eropa", "Industrial (Baja/Ekspos)", "Tradisional Estetik"])
    
    if st.button("🚀 Generate RAB Otomatis", use_container_width=True):
        # Logika Prediksi Volume
        L_dasar = luas_bangunan / lantai
        f_tanah = 1.0 if "Keras" in jenis_tanah else (1.5 if "Sedang" in jenis_tanah else 2.5)
        f_style = 1.0
        if "Klasik / Eropa" in style_bangunan: f_style += 0.3
        if "Industrial (Baja/Ekspos)" in style_bangunan: f_style -= 0.1
        if "Tradisional Estetik" in style_bangunan: f_style += 0.15
        
        estimasi = {
            "1.2.1.1.1": L_dasar * 0.4 * f_tanah, # Galian
            "2.2.2.1.1": L_dasar * 0.35 * f_tanah, # Pondasi (Menyesuaikan tanah)
            "2.2.1.1.1": luas_bangunan * 0.25 * f_style, # Beton
            "3.6.1.1": luas_bangunan * 3.2 * f_style, # Dinding Bata
            "3.9.1.1": luas_bangunan * 1.0, # Keramik
            "2.1.1.1": L_dasar * 1.5 if lantai == 1 else L_dasar * 1.2 # Atap
        }
        
        hasil_rab = []
        for kode, vol in estimasi.items():
            cari = df_db[df_db['Kode AHSP'].astype(str).str.contains(kode, regex=False, na=False)]
            if not cari.empty:
                item = cari.iloc[0]
                harga_dasar = float(item['Total Harga (Rp)']) if 'Total Harga (Rp)' in item else float(item.iloc[-1])
                # Menerapkan IKK Regional dan Profit Margin
                harga_final = harga_dasar * faktor_lokasi * faktor_profit
                
                hasil_rab.append({
                    "Kode AHSP": item['Kode AHSP'],
                    "Pekerjaan": item['Uraian Pekerjaan'],
                    "Sat": item['Satuan'],
                    "Volume": round(vol, 2),
                    "Harga Satuan (Inc Profit & Lokasi)": harga_final,
                    "Total Harga": round(vol, 2) * harga_final
                })
        st.session_state.rab_final = pd.DataFrame(hasil_rab)
        st.success("RAB Berhasil digenerate! Silakan cek Tab 'RAB & S-Curve'.")

# ========================================================
# TAB 2: INPUT GAMBAR BLUEPRINT (AI SIMULATION)
# ========================================================
with tab2:
    st.markdown("### 🖼️ Analisis Gambar Kerja (Blueprint) berbasis AI")
    st.markdown("Unggah file PDF / Denah Anda. Sistem AI (Gemini Vision) akan mendeteksi dimensi ruang, jenis material, dan menghasilkan Volume RAB.")
    
    file_upload = st.file_uploader("Upload Gambar Kerja / PDF Denah", type=["pdf", "png", "jpg", "jpeg"])
    
    if file_upload is not None:
        # Menampilkan PDF/Gambar menggunakan penampil Streamlit
        st.image(file_upload) if "image" in file_upload.type else st.success("File PDF berhasil diunggah.")
        
        with st.spinner("AI sedang memproses gambar untuk mendeteksi dinding, pondasi, dan bukaan..."):
            # SIMULASI LOGIKA AI VISION (Placeholder untuk Google Generative AI API)
            st.info("Mendeteksi: 3 Kamar Tidur, 2 KM/WC, Pondasi Footplat, Luas Total terdeteksi ± 85 m2. Style: Minimalis.")
            
            if st.button("Tarik Volume dari Blueprint ke RAB"):
                # Men-generate RAB dummy berdasarkan deteksi AI
                st.session_state.rab_final = pd.DataFrame([
                    {"Kode AHSP": "1.2.1.1.1", "Pekerjaan": "Galian Tanah (Berdasarkan Denah)", "Sat": "m3", "Volume": 38.5, "Harga Satuan (Inc Profit & Lokasi)": 90860 * faktor_lokasi * faktor_profit, "Total Harga": 38.5 * (90860 * faktor_lokasi * faktor_profit)},
                    {"Kode AHSP": "3.6.1.1", "Pekerjaan": "Pasangan Bata (Deteksi Panjang Dinding AI)", "Sat": "m2", "Volume": 210.4, "Harga Satuan (Inc Profit & Lokasi)": 278000 * faktor_lokasi * faktor_profit, "Total Harga": 210.4 * (278000 * faktor_lokasi * faktor_profit)}
                ])
                st.success("RAB dari Blueprint berhasil dibuat!")

# ========================================================
# TAB 3: TAMPILAN RAB & TIMELINE (S-CURVE)
# ========================================================
with tab3:
    if not st.session_state.rab_final.empty:
        df = st.session_state.rab_final
        
        st.markdown("### 📋 Detail Rencana Anggaran Biaya")
        df['Total Harga'] = df['Volume'] * df['Harga Satuan (Inc Profit & Lokasi)']
        grand_total = df['Total Harga'].sum()
        
        # Tampilkan tabel yang bisa diedit ulang
        edited_df = st.data_editor(df, hide_index=True, use_container_width=True,
                                   column_config={"Harga Satuan (Inc Profit & Lokasi)": st.column_config.NumberColumn(format="Rp %.0f"),
                                                  "Total Harga": st.column_config.NumberColumn(format="Rp %.0f")})
        st.session_state.rab_final = edited_df
        grand_total = edited_df['Total Harga'].sum()
        
        st.metric("💰 GRAND TOTAL RAB (Sudah termasuk Keuntungan & Penyesuaian Daerah)", f"Rp {grand_total:,.0f}")
        st.warning(f"**Terbilang:** *{terbilang(grand_total)} Rupiah*")
        
        st.divider()
        
        # --- LOGIKA S-CURVE & TIMELINE ---
        st.markdown("### 📈 Jadwal Pelaksanaan & Kurva S (S-Curve)")
        waktu_pelaksanaan = st.slider("Estimasi Waktu Pelaksanaan (Minggu):", 4, 52, 12)
        
        # Simulasi Distribusi Bobot Pekerjaan Normal Konstruksi (Kurva S Normal/Lonceng)
        # Menggunakan distribusi Normal (Gaussian) untuk membagi bobot persentase dari 0% ke 100%
        minggu = np.arange(1, waktu_pelaksanaan + 1)
        mean = waktu_pelaksanaan / 2
        std_dev = waktu_pelaksanaan / 4
        bobot_mingguan = np.exp(-0.5 * ((minggu - mean) / std_dev) ** 2)
        bobot_persen = (bobot_mingguan / sum(bobot_mingguan)) * 100
        kumulatif_persen = np.cumsum(bobot_persen)
        
        df_scurve = pd.DataFrame({
            "Minggu Ke-": minggu,
            "Rencana Bobot Mingguan (%)": np.round(bobot_persen, 2),
            "Kumulatif Rencana (%)": np.round(kumulatif_persen, 2),
            "Target Penyerapan Dana (Rp)": np.round((bobot_persen / 100) * grand_total, 0)
        })
        
        # Plot S-Curve menggunakan Plotly Express
        fig = px.line(df_scurve, x="Minggu Ke-", y="Kumulatif Rencana (%)", markers=True, 
                      title=f"Rencana Kurva S (S-Curve) Pelaksanaan {waktu_pelaksanaan} Minggu",
                      labels={"Kumulatif Rencana (%)": "Bobot Prestasi (%)"})
        fig.add_bar(x=df_scurve["Minggu Ke-"], y=df_scurve["Rencana Bobot Mingguan (%)"], name="Bobot Mingguan (%)")
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(df_scurve, hide_index=True, use_container_width=True)
    else:
        st.info("👈 Silakan atur Parameter di Tab 1 atau upload Blueprint di Tab 2 terlebih dahulu.")

# ========================================================
# TAB 4: EXPORT KE EXCEL TERINTEGRASI
# ========================================================
with tab4:
    if not st.session_state.rab_final.empty:
        st.markdown("### 🖨️ Cetak Dokumen Excel Enterprise")
        st.markdown("Dokumen Excel ini akan berisi 3 Lembar: **Summary & Terbilang**, **Rincian RAB**, dan **Jadwal Kurva S**.")
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # Sheet 1: Summary Terbilang
            df_sum = pd.DataFrame({
                "Parameter": ["Lokasi Proyek", "Faktor Indeks Regional", "Profit Margin (%)", "Jenis Bangunan", "GRAND TOTAL", "TERBILANG:"],
                "Detail": [lokasi, faktor_lokasi, profit_margin, "Pembangunan Baru", f"Rp {grand_total:,.0f}", terbilang(grand_total) + " Rupiah"]
            })
            df_sum.to_excel(writer, index=False, sheet_name='1_Summary_Proyek')
            
            # Sheet 2: RAB Detail
            st.session_state.rab_final.to_excel(writer, index=False, sheet_name='2_Rincian_RAB')
            
            # Sheet 3: Kurva S & Timeline
            df_scurve.to_excel(writer, index=False, sheet_name='3_Timeline_Kurva_S')
            
        st.download_button(
            label="📥 Download Excel Enterprise (RAB + Kurva S)",
            data=buffer.getvalue(),
            file_name="RAB_Lengkap_SCurve.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
    else:
        st.info("Data RAB belum tersedia untuk dicetak.")
