import streamlit as st
import pandas as pd
import io

# --- 1. FUNGSI TERBILANG ---
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

# --- 2. DATA FAKTOR REGIONAL (Indeks Kemahalan Konstruksi) ---
FAKTOR_REGIONAL = {
    "DKI Jakarta (Standar)": 1.00,
    "Jawa Barat": 0.95,
    "Jawa Tengah": 0.88,
    "Jawa Timur": 0.90,
    "Sulawesi Selatan": 1.05,
    "Kalimantan Timur (IKN)": 1.15,
    "Sumatera Utara": 1.02,
    "Papua & Maluku": 1.40
}

# --- 3. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Auto-RAB Pro", page_icon="🏢", layout="wide")
st.title("🏢 Auto-RAB Pro (Cipta Karya 2025)")
st.markdown("Generator RAB Parametrik dengan Penyesuaian Regional, Spesifikasi Ruang, & Rincian AHSP.")

# --- 4. MEMUAT DATABASE ---
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("RAB_AHSP_Lengkap_CiptaKarya_2025.xlsx", sheet_name="Daftar_AHSP", skiprows=2)
        df = df.dropna(subset=['Kode AHSP', 'Uraian Pekerjaan'])
        df['Kode AHSP'] = df['Kode AHSP'].astype(str).str.strip()
        df['Pilihan'] = df['Kode AHSP'] + " - " + df['Uraian Pekerjaan'].astype(str)
        return df
    except:
        st.error("File RAB_AHSP_Lengkap_CiptaKarya_2025.xlsx tidak ditemukan!")
        return pd.DataFrame()

df_ahsp = load_data()

# --- 5. INISIALISASI SESSION STATE ---
if 'rab_data' not in st.session_state:
    st.session_state.rab_data = []
if 'parameter_tersimpan' not in st.session_state:
    st.session_state.parameter_tersimpan = False

# --- 6. SIDEBAR: PARAMETER PROYEK ---
with st.sidebar:
    st.header("⚙️ Parameter Bangunan")
    daerah = st.selectbox("📍 Lokasi Proyek (Indeks Harga):", list(FAKTOR_REGIONAL.keys()))
    
    st.subheader("Ukuran")
    luas_tanah = st.number_input("Luas Tanah (m2):", min_value=10, value=120)
    luas_bangunan = st.number_input("Luas Bangunan (m2):", min_value=10, value=60)
    
    st.subheader("Spesifikasi Ruangan")
    jml_kamar = st.number_input("🛏️ Jumlah Kamar Tidur:", min_value=1, value=2)
    jml_km_wc = st.number_input("🚿 Jumlah Kamar Mandi/WC:", min_value=1, value=1)
    
    st.subheader("Tipe & Kondisi")
    tipe_bangunan = st.selectbox("Tipe Bangunan:", ["Sederhana", "Menengah", "Mewah"])
    jenis_tanah = st.selectbox("Kondisi Tanah:", ["Keras", "Sedang", "Lembek"])
    
    faktor = FAKTOR_REGIONAL[daerah]
    
    # RUMUS EMPIRIS BERDASARKAN RUANGAN
    def hitung_volume(L, tanah, tipe, kmr, wc):
        f_tnh = 0.4 if "Keras" in tanah else (0.5 if "Sedang" in tanah else 0.8)
        f_tp = 1.0 if tipe == "Sederhana" else (1.3 if tipe == "Menengah" else 1.8)
        
        # Prediksi Volume berdasarkan Luas + Ruangan
        return {
            "1.2.1.1.1": L * f_tnh,                           # Galian
            "2.2.2.1.1": (L * 0.35 * f_tp) + (kmr * 1.5),     # Pondasi
            "2.2.1.1.1": L * 0.25 * f_tp,                     # Beton
            "3.6.1.1": (L * 3.0 * f_tp) + (kmr * 12) + (wc * 8), # Dinding Bata
            "3.7.1.1": (L * 6.0 * f_tp) + (kmr * 24) + (wc * 16),# Plesteran
            "3.9.1.1": L * 1.0,                               # Keramik Lantai
            "3.8.1.1": (L * 3.5 * f_tp) + (kmr * 15),         # Pengecatan
            "3.18.1.1": wc * 1.0                              # Sanitair (Wastafel/Kloset untuk tiap WC)
        }

    if st.button("🚀 Generate Draf RAB", use_container_width=True):
        estimasi_vol = hitung_volume(luas_bangunan, jenis_tanah, tipe_bangunan, jml_kamar, jml_km_wc)
        st.session_state.rab_data = [] # Reset data
        
        for kode, vol in estimasi_vol.items():
            cari = df_ahsp[df_ahsp['Kode AHSP'] == kode]
            if not cari.empty:
                item = cari.iloc[0]
                st.session_state.rab_data.append({
                    "Kategori": "Sistem (Prediksi)",
                    "Kode": item['Kode AHSP'],
                    "Pekerjaan": item['Uraian Pekerjaan'],
                    "Sat": item['Satuan'],
                    "Volume": round(vol, 2),
                    "Upah/Sat": float(item['Subtotal UPAH (Rp)']) * faktor if pd.notna(item['Subtotal UPAH (Rp)']) else 0,
                    "Bahan/Sat": float(item['Subtotal BAHAN (Rp)']) * faktor if pd.notna(item['Subtotal BAHAN (Rp)']) else 0,
                    "Alat/Sat": float(item['Subtotal ALAT (Rp)']) * faktor if pd.notna(item['Subtotal ALAT (Rp)']) else 0,
                    "Harga/Sat": float(item['Harga Satuan Total (Rp)']) * faktor if pd.notna(item['Harga Satuan Total (Rp)']) else 0
                })
        st.session_state.parameter_tersimpan = True

# --- 7. TABS UTAMA (UI BERSUSUN) ---
tab1, tab2, tab3, tab4 = st.tabs(["📝 RAB & Estimasi", "➕ Tambah Manual", "📊 Summary, AHSP & Print", "📐 Gambar Kerja"])

# TAB 1: DATA RAB (PREDIKSI + MANUAL)
with tab1:
    if not st.session_state.parameter_tersimpan:
        st.info("👈 Silakan atur parameter di menu samping dan klik **Generate Draf RAB**.")
    else:
        st.success(f"Lokasi: **{daerah}** (Indeks {faktor}x) | Bangunan: **{luas_bangunan}m2** ({jml_kamar} Kamar, {jml_km_wc} WC)")
        
        df_rab = pd.DataFrame(st.session_state.rab_data)
        if not df_rab.empty:
            st.markdown("Ubah kolom **Volume** di bawah ini untuk penyesuaian akhir lapangan:")
            edited_df = st.data_editor(
                df_rab,
                column_config={
                    "Kategori": st.column_config.TextColumn("Kategori", disabled=True),
                    "Kode": st.column_config.TextColumn("Kode", disabled=True),
                    "Pekerjaan": st.column_config.TextColumn("Pekerjaan", disabled=True),
                    "Sat": st.column_config.TextColumn("Sat", disabled=True),
                    "Volume": st.column_config.NumberColumn("Volume (Edit) ▼", format="%.2f"),
                    "Harga/Sat": st.column_config.NumberColumn("Harga/Sat (Rp)", format="%.0f", disabled=True),
                },
                hide_index=True, use_container_width=True
            )
            st.session_state.rab_data = edited_df.to_dict('records')

# TAB 2: TAMBAH AHSP MANUAL
with tab2:
    st.markdown("### Tambahkan Item Pekerjaan Baru / Kustom")
    
    if not df_ahsp.empty:
        pilihan_custom = st.selectbox("Cari AHSP Standar:", ["-- Pilih dari Database --"] + df_ahsp['Pilihan'].tolist())
        col_vol, col_btn = st.columns([3, 1])
        vol_custom = col_vol.number_input("Volume Tambahan:", min_value=0.01, value=1.0)
        
        if col_btn.button("Tambahkan dari DB"):
            if pilihan_custom != "-- Pilih dari Database --":
                data_pilih = df_ahsp[df_ahsp['Pilihan'] == pilihan_custom].iloc[0]
                item_baru = {
                    "Kategori": "Tambahan (Database)",
                    "Kode": data_pilih['Kode AHSP'],
                    "Pekerjaan": data_pilih['Uraian Pekerjaan'],
                    "Sat": data_pilih['Satuan'],
                    "Volume": vol_custom,
                    "Upah/Sat": float(data_pilih['Subtotal UPAH (Rp)']) * faktor if pd.notna(data_pilih['Subtotal UPAH (Rp)']) else 0,
                    "Bahan/Sat": float(data_pilih['Subtotal BAHAN (Rp)']) * faktor if pd.notna(data_pilih['Subtotal BAHAN (Rp)']) else 0,
                    "Alat/Sat": float(data_pilih['Subtotal ALAT (Rp)']) * faktor if pd.notna(data_pilih['Subtotal ALAT (Rp)']) else 0,
                    "Harga/Sat": float(data_pilih['Harga Satuan Total (Rp)']) * faktor if pd.notna(data_pilih['Harga Satuan Total (Rp)']) else 0
                }
                st.session_state.rab_data.append(item_baru)
                st.success("Item berhasil ditambahkan ke RAB!")
                st.rerun()

    st.divider()
    st.markdown("Atau Input **Pekerjaan Borongan / Bebas**:")
    with st.form("form_custom"):
        c1, c2, c3 = st.columns(3)
        nama_kustom = c1.text_input("Nama Pekerjaan:")
        sat_kustom = c2.text_input("Satuan (ls/m2/m3):", value="ls")
        vol_kustom = c3.number_input("Volume:", value=1.0)
        
        h_upah = st.number_input("Total Harga Upah/Satuan (Rp):", value=0)
        h_bahan = st.number_input("Total Harga Bahan/Satuan (Rp):", value=0)
        h_alat = st.number_input("Total Harga Alat/Satuan (Rp):", value=0)
        
        if st.form_submit_button("Tambahkan Borongan"):
            st.session_state.rab_data.append({
                "Kategori": "Tambahan (Manual)",
                "Kode": "KUSTOM",
                "Pekerjaan": nama_kustom,
                "Sat": sat_kustom,
                "Volume": vol_kustom,
                "Upah/Sat": h_upah,
                "Bahan/Sat": h_bahan,
                "Alat/Sat": h_alat,
                "Harga/Sat": h_upah + h_bahan + h_alat
            })
            st.success("Pekerjaan Borongan ditambahkan!")
            st.rerun()

# TAB 3: SUMMARY, AHSP & PRINTOUT
with tab3:
    if len(st.session_state.rab_data) > 0:
        df_final = pd.DataFrame(st.session_state.rab_data)
        
        # Kalkulasi Total
        df_final['Total Upah'] = df_final['Volume'] * df_final['Upah/Sat']
        df_final['Total Bahan'] = df_final['Volume'] * df_final['Bahan/Sat']
        df_final['Total Alat'] = df_final['Volume'] * df_final['Alat/Sat']
        df_final['Jumlah Harga'] = df_final['Volume'] * df_final['Harga/Sat']
        
        g_upah = df_final['Total Upah'].sum()
        g_bahan = df_final['Total Bahan'].sum()
        g_alat = df_final['Total Alat'].sum()
        g_total = df_final['Jumlah Harga'].sum()
        
        st.markdown("### 📊 Rekapitulasi Akhir")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("👷 Upah Tenaga Kerja", f"Rp {g_upah:,.0f}")
        c2.metric("🧱 Material / Bahan", f"Rp {g_bahan:,.0f}")
        c3.metric("🚜 Sewa Alat", f"Rp {g_alat:,.0f}")
        c4.metric("💰 GRAND TOTAL", f"Rp {g_total:,.0f}")
        
        st.warning(f"**Terbilang:** *{terbilang(g_total)} Rupiah*")
        
        # --- TABEL AHSP TERPAKAI ---
        st.divider()
        st.markdown("### 📑 Daftar Analisa Harga Satuan (AHSP) Terpakai")
        st.info("Berikut adalah rincian harga satuan dasar (Upah, Bahan, Alat) untuk pekerjaan yang digunakan dalam proyek ini.")
        
        # Memilih kolom yang relevan untuk AHSP terpakai
        df_ahsp_terpakai = df_final[['Kode', 'Pekerjaan', 'Sat', 'Upah/Sat', 'Bahan/Sat', 'Alat/Sat', 'Harga/Sat']].copy()
        
        # Menampilkan di layar
        st.dataframe(
            df_ahsp_terpakai.style.format({
                "Upah/Sat": "Rp {:,.0f}", 
                "Bahan/Sat": "Rp {:,.0f}", 
                "Alat/Sat": "Rp {:,.0f}", 
                "Harga/Sat": "Rp {:,.0f}"
            }), 
            use_container_width=True,
            hide_index=True
        )
        
        # --- TOMBOL EXCEL DOWNLOAD ---
        st.divider()
        st.markdown("### 🖨️ Cetak & Download")
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # Sheet 1: Detail Volume & Total RAB
            df_final.to_excel(writer, index=False, sheet_name='Detail_RAB')
            
            # Sheet 2: AHSP Terpakai
            df_ahsp_terpakai.to_excel(writer, index=False, sheet_name='AHSP_Terpakai')
            
            # Sheet 3: Summary & Parameter
            df_sum = pd.DataFrame({
                "Kategori Biaya": ["Tenaga Kerja", "Bahan/Material", "Peralatan", "Overhead / Profit", "GRAND TOTAL RAB"],
                "Total (Rp)": [g_upah, g_bahan, g_alat, g_total - (g_upah+g_bahan+g_alat), g_total]
            })
            df_param = pd.DataFrame({
                "Parameter Proyek": ["Lokasi/Daerah", "Luas Tanah", "Luas Bangunan", "Jumlah Kamar", "Jumlah KM/WC", "Tipe", "Kondisi Tanah"],
                "Nilai": [daerah, f"{luas_tanah} m2", f"{luas_bangunan} m2", jml_kamar, jml_km_wc, tipe_bangunan, jenis_tanah]
            })
            
            df_sum.to_excel(writer, index=False, sheet_name='Summary_RAB', startrow=0)
            df_param.to_excel(writer, index=False, sheet_name='Summary_RAB', startrow=len(df_sum)+3)
            
        st.download_button(
            label="📥 Download Laporan RAB Lengkap (Excel)", 
            data=buffer.getvalue(), 
            file_name=f"Laporan_RAB_{tipe_bangunan}_{daerah}.xlsx", 
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
            use_container_width=True,
            type="primary"
        )
    else:
        st.info("Data RAB masih kosong. Silakan Generate Draf terlebih dahulu.")

# TAB 4: GAMBAR KERJA (BLUEPRINT)
with tab4:
    if st.session_state.parameter_tersimpan:
        st.markdown(f"### 📐 Referensi Gambar Kerja (Denah & Fasad)")
        st.caption(f"Visualisasi skematik untuk bangunan Tipe {tipe_bangunan} dengan {jml_kamar} Kamar Tidur dan {jml_km_wc} Kamar Mandi.")
        
        st.markdown("#### 1. Denah Skematik (Floor Plan)")
        st.markdown(f"")
        
        st.markdown("#### 2. Fasad Bangunan (Elevasi)")
        st.markdown(f"")
        
        st.info(f"💡 **Tips Lapangan:** Sesuaikan penempatan aktual pintu dan jendela dengan arah mata angin dan saluran drainase di lokasi (Kondisi tanah: {jenis_tanah}).")
    else:
        st.info("Generate RAB terlebih dahulu untuk memunculkan Gambar Kerja yang sesuai dengan spesifikasi Anda.")
