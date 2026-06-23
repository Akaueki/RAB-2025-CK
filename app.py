import streamlit as st
import pandas as pd
import io
import math

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

# --- 2. DATA FAKTOR REGIONAL ---
FAKTOR_REGIONAL = {
    "DKI Jakarta (Standar)": 1.00, "Jawa Barat": 0.95, "Jawa Tengah": 0.88,
    "Jawa Timur": 0.90, "Sulawesi Selatan": 1.05, "Kalimantan Timur (IKN)": 1.15,
    "Sumatera Utara": 1.02, "Papua & Maluku": 1.40
}

# --- 3. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Auto-RAB Master", page_icon="🏗️", layout="wide")
st.title("🏗️ Auto-RAB Master (Detail AHSP Cipta Karya)")
st.markdown("Generator RAB Parametrik Lengkap: Struktur, Arsitektur, MEP berdasarkan Style & Tingkat Bangunan.")

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
if 'rab_data' not in st.session_state: st.session_state.rab_data = []
if 'parameter_tersimpan' not in st.session_state: st.session_state.parameter_tersimpan = False

# --- 6. SIDEBAR: PARAMETER DETAIL PROYEK ---
with st.sidebar:
    st.header("⚙️ Parameter Bangunan")
    daerah = st.selectbox("📍 Lokasi Proyek:", list(FAKTOR_REGIONAL.keys()))
    
    st.subheader("Dimensi & Ruang")
    luas_tanah = st.number_input("Luas Tanah (m2):", min_value=10, value=120)
    luas_bangunan = st.number_input("Luas Total Bangunan (m2):", min_value=10, value=60)
    jml_kamar = st.number_input("🛏️ Jumlah Kamar:", min_value=0, value=2)
    jml_km_wc = st.number_input("🚿 Jumlah KM/WC:", min_value=0, value=1)
    
    st.subheader("Karakteristik Bangunan")
    jenis_bangunan = st.selectbox("Jenis:", ["Rumah Tinggal", "Kantor / Ruko", "Fasilitas Umum", "Gudang / Pabrik"])
    tingkat_bangunan = st.selectbox("Tingkat (Jumlah Lantai):", [1, 2, 3, 4, 5])
    style_bangunan = st.selectbox("Style / Konstruksi:", [
        "Minimalis Modern (Standar)", 
        "Klasik Mewah (Banyak Profil/Ornamen)", 
        "Temporer / Darurat (Kayu/Baja Ringan, Non-Beton)"
    ])
    jenis_tanah = st.selectbox("Kondisi Tanah Asli:", ["Keras (Aman)", "Sedang", "Lembek (Butuh Pondasi Dalam)"])
    
    faktor_harga = FAKTOR_REGIONAL[daerah]

    # --- ENGINE PREDIKSI VOLUME (RUMUS EMPIRIS DETIL) ---
    def hitung_volume_detail(L_total, lantai, style, tanah, kamar, wc):
        L_dasar = L_total / lantai # Luas tapak dasar
        
        # Multiplier Kondisi Tanah & Style
        f_tanah = 1.0 if "Keras" in tanah else (1.5 if "Sedang" in tanah else 2.5)
        f_mewah = 1.3 if "Klasik" in style else 1.0
        
        is_temporer = "Temporer" in style
        
        estimasi = {}
        
        # 1. PEKERJAAN PERSIAPAN & TANAH
        estimasi["1.1.1.1"] = math.sqrt(L_dasar) * 4 # Pembersihan & Bowplank (Asumsi Keliling)
        estimasi["1.2.1.1.1"] = (L_dasar * 0.4 * f_tanah) if not is_temporer else (L_dasar * 0.1) # Galian Tanah
        
        if not is_temporer:
            # 2. PEKERJAAN STRUKTUR (Pondasi, Beton, Besi, Bekisting)
            estimasi["2.2.2.1.1"] = L_dasar * 0.35 * f_tanah # Pondasi Batu Kali (Bawah)
            
            vol_beton = (L_total * 0.25) * f_mewah # Kolom, Balok, Sloof, Plat
            estimasi["2.2.1.1.1"] = vol_beton # Pengecoran Beton
            estimasi["2.2.1.1.1.a"] = vol_beton * 110 # Pembesian (Asumsi 110kg per m3 beton)
            estimasi["2.4.1.1"] = vol_beton * 4.5 # Bekisting / Formwork (m2)
            
            # 3. PEKERJAAN DINDING (Bata, Plester, Aci)
            luas_dinding = (L_total * 3.2) + (kamar * 12) + (wc * 8)
            estimasi["3.6.1.1"] = luas_dinding * f_mewah # Pasangan Bata / Hebel
            estimasi["3.7.1.1"] = luas_dinding * 2 * f_mewah # Plesteran (2 Sisi)
            estimasi["3.7.1.2"] = luas_dinding * 2 * f_mewah # Acian Dinding
            
        else:
            # STRUKTUR TEMPORER (Kayu, Triplek, Dinding Partisi)
            estimasi["2.6.1.1"] = L_total * 0.05 # Struktur Rangka Kayu (m3)
            estimasi["3.14.1"] = L_total * 2.5 # Dinding Partisi Triplek/Plywood (m2)
        
        # 4. PEKERJAAN LANTAI & ATAP
        if not is_temporer:
            estimasi["3.9.1.1"] = L_total * 0.95 # Keramik Lantai
            estimasi["3.9.2.1"] = wc * 10 # Keramik Dinding Kamar Mandi
        else:
            estimasi["3.9.3.1"] = L_dasar # Rabat Beton Kasar / Plester Lantai
            
        luas_atap = (L_dasar * 1.5) if lantai == 1 else (L_dasar * 1.2)
        estimasi["2.1.1.1"] = luas_atap # Rangka Atap Baja Ringan
        estimasi["3.1.1.1"] = luas_atap # Penutup Atap (Genteng / Seng)
        estimasi["3.5.1.1"] = L_total # Plafon Gypsum / Triplek
        
        # 5. PEKERJAAN KUSEN, PINTU, KACA, & CAT
        jml_bukaan = kamar + wc + (L_total/20) # Asumsi jumlah pintu & jendela
        estimasi["3.11.1.1"] = jml_bukaan * 2.1 # Luasan Pintu (m2)
        estimasi["3.13.1.1"] = jml_bukaan * 6 # Panjang Kusen Aluminium/Kayu (m')
        estimasi["3.12.1.1"] = jml_bukaan * 1.5 * f_mewah # Kaca Jendela (m2)
        
        estimasi["3.8.1.1"] = (luas_dinding * 2) + L_total if not is_temporer else L_total # Pengecatan Tembok & Plafon
        
        # 6. SANITAIR & PIPA
        estimasi["3.18.1.1"] = wc # Kloset
        estimasi["3.18.2.1"] = wc + (kamar*0.5) if "Mewah" in style else wc # Wastafel/Bak Air
        estimasi["6.4.1.1"] = L_total * 0.8 # Pipa Air Bersih / Kotor
        
        return estimasi

    if st.button("🚀 Generate Detail RAB", use_container_width=True):
        estimasi_vol = hitung_volume_detail(luas_bangunan, tingkat_bangunan, style_bangunan, jenis_tanah, jml_kamar, jml_km_wc)
        st.session_state.rab_data = []
        kode_gagal = []
        
        for kode, vol in estimasi_vol.items():
            # Pencarian menggunakan metode .str.contains agar lebih fleksibel terhadap perbedaan versi Excel
            cari = df_ahsp[df_ahsp['Kode AHSP'].str.contains(kode, regex=False, na=False)]
            if not cari.empty:
                item = cari.iloc[0]
                st.session_state.rab_data.append({
                    "Kategori": "Sistem (Prediksi)",
                    "Kode": item['Kode AHSP'],
                    "Pekerjaan": item['Uraian Pekerjaan'],
                    "Sat": item['Satuan'],
                    "Volume": round(vol, 2),
                    "Upah/Sat": float(item['Subtotal UPAH (Rp)']) * faktor_harga if pd.notna(item['Subtotal UPAH (Rp)']) else 0,
                    "Bahan/Sat": float(item['Subtotal BAHAN (Rp)']) * faktor_harga if pd.notna(item['Subtotal BAHAN (Rp)']) else 0,
                    "Alat/Sat": float(item['Subtotal ALAT (Rp)']) * faktor_harga if pd.notna(item['Subtotal ALAT (Rp)']) else 0,
                    "Harga/Sat": float(item['Harga Satuan Total (Rp)']) * faktor_harga if pd.notna(item['Harga Satuan Total (Rp)']) else 0
                })
            else:
                # Jika kode spesifik tidak ditemukan, tambahkan sebagai "Placeholder" agar user tahu
                st.session_state.rab_data.append({
                    "Kategori": "Sistem (Perlu Diisi Manual)",
                    "Kode": kode,
                    "Pekerjaan": f"[ITEM TIDAK DITEMUKAN DI DB] Pekerjaan terkait kode {kode}",
                    "Sat": "Ls",
                    "Volume": round(vol, 2),
                    "Upah/Sat": 0, "Bahan/Sat": 0, "Alat/Sat": 0, "Harga/Sat": 0
                })
                kode_gagal.append(kode)
                
        st.session_state.parameter_tersimpan = True

# --- 7. TABS UTAMA (UI BERSUSUN) ---
tab1, tab2, tab3, tab4 = st.tabs(["📝 Detail RAB & Volume", "➕ Tambah AHSP Manual", "📊 Print & Summary Lengkap", "📐 Info & Blueprint"])

# TAB 1: DATA RAB (PREDIKSI + MANUAL)
with tab1:
    if not st.session_state.parameter_tersimpan:
        st.info("👈 Silakan atur parameter bangunan di menu samping dan klik **Generate Detail RAB**.")
    else:
        st.success(f"**{jenis_bangunan} {tingkat_bangunan} Lantai** | Style: {style_bangunan} | Luas: {luas_bangunan}m2 | Lokasi: {daerah}")
        
        df_rab = pd.DataFrame(st.session_state.rab_data)
        if not df_rab.empty:
            st.markdown("⚠️ **Review Mode:** Cek prediksi sistem. Anda dapat mengubah langsung angka pada kolom **Volume** di bawah ini.")
            edited_df = st.data_editor(
                df_rab,
                column_config={
                    "Kategori": st.column_config.TextColumn("Kategori", disabled=True),
                    "Kode": st.column_config.TextColumn("Kode AHSP", disabled=True),
                    "Pekerjaan": st.column_config.TextColumn("Item Pekerjaan", disabled=True),
                    "Sat": st.column_config.TextColumn("Sat", disabled=True),
                    "Volume": st.column_config.NumberColumn("Volume (Edit) ▼", format="%.2f"),
                    "Harga/Sat": st.column_config.NumberColumn("Harga/Sat (Rp)", format="%.0f", disabled=True),
                },
                hide_index=True, use_container_width=True, height=500
            )
            st.session_state.rab_data = edited_df.to_dict('records')

# TAB 2: TAMBAH AHSP MANUAL
with tab2:
    st.markdown("### Tambahkan Item Pekerjaan Baru / Kustom")
    
    if not df_ahsp.empty:
        pilihan_custom = st.selectbox("Cari AHSP dari Database Master:", ["-- Pilih dari Database --"] + df_ahsp['Pilihan'].tolist())
        col_vol, col_btn = st.columns([3, 1])
        vol_custom = col_vol.number_input("Volume Tambahan:", min_value=0.01, value=1.0)
        
        if col_btn.button("Tambahkan Item Standar"):
            if pilihan_custom != "-- Pilih dari Database --":
                data_pilih = df_ahsp[df_ahsp['Pilihan'] == pilihan_custom].iloc[0]
                item_baru = {
                    "Kategori": "Tambahan (Database)", "Kode": data_pilih['Kode AHSP'],
                    "Pekerjaan": data_pilih['Uraian Pekerjaan'], "Sat": data_pilih['Satuan'],
                    "Volume": vol_custom,
                    "Upah/Sat": float(data_pilih['Subtotal UPAH (Rp)']) * faktor_harga if pd.notna(data_pilih['Subtotal UPAH (Rp)']) else 0,
                    "Bahan/Sat": float(data_pilih['Subtotal BAHAN (Rp)']) * faktor_harga if pd.notna(data_pilih['Subtotal BAHAN (Rp)']) else 0,
                    "Alat/Sat": float(data_pilih['Subtotal ALAT (Rp)']) * faktor_harga if pd.notna(data_pilih['Subtotal ALAT (Rp)']) else 0,
                    "Harga/Sat": float(data_pilih['Harga Satuan Total (Rp)']) * faktor_harga if pd.notna(data_pilih['Harga Satuan Total (Rp)']) else 0
                }
                st.session_state.rab_data.append(item_baru)
                st.success("Item berhasil ditambahkan ke RAB!")
                st.rerun()

    st.divider()
    st.markdown("Atau Input **Pekerjaan Borongan Lumpsum**:")
    with st.form("form_custom"):
        c1, c2, c3 = st.columns(3)
        nama_kustom = c1.text_input("Nama Pekerjaan:")
        sat_kustom = c2.text_input("Satuan (ls/m2/m3):", value="ls")
        vol_kustom = c3.number_input("Volume:", value=1.0)
        
        h_upah = st.number_input("Total Harga Upah/Satuan (Rp):", value=0)
        h_bahan = st.number_input("Total Harga Bahan/Satuan (Rp):", value=0)
        h_alat = st.number_input("Total Harga Alat/Satuan (Rp):", value=0)
        
        if st.form_submit_button("Tambahkan Pekerjaan Lumpsum"):
            st.session_state.rab_data.append({
                "Kategori": "Tambahan (Lumpsum Manual)", "Kode": "KUSTOM",
                "Pekerjaan": nama_kustom, "Sat": sat_kustom, "Volume": vol_kustom,
                "Upah/Sat": h_upah, "Bahan/Sat": h_bahan, "Alat/Sat": h_alat,
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
        
        st.markdown("### 📊 Rekapitulasi Rencana Anggaran Biaya")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("👷 Upah Tenaga Kerja", f"Rp {g_upah:,.0f}")
        c2.metric("🧱 Material / Bahan", f"Rp {g_bahan:,.0f}")
        c3.metric("🚜 Sewa Alat", f"Rp {g_alat:,.0f}")
        c4.metric("💰 GRAND TOTAL", f"Rp {g_total:,.0f}")
        
        st.success(f"**TERBILANG:** *{terbilang(g_total)} Rupiah*")
        
        # --- TABEL AHSP TERPAKAI ---
        st.divider()
        with st.expander("Lihat Rincian Analisa Harga Satuan (AHSP) Terpakai"):
            st.info("Tabel ini menunjukkan harga dasar (Upah, Bahan, Alat) PER SATUAN dari item yang digunakan dalam RAB ini.")
            df_ahsp_terpakai = df_final[['Kode', 'Pekerjaan', 'Sat', 'Upah/Sat', 'Bahan/Sat', 'Alat/Sat', 'Harga/Sat']].copy()
            st.dataframe(
                df_ahsp_terpakai.style.format({
                    "Upah/Sat": "Rp {:,.0f}", "Bahan/Sat": "Rp {:,.0f}", 
                    "Alat/Sat": "Rp {:,.0f}", "Harga/Sat": "Rp {:,.0f}"
                }), 
                use_container_width=True, hide_index=True
            )
        
        # --- EXCEL EXPORT (PRINTOUT) ---
        st.divider()
        st.markdown("### 🖨️ Cetak Dokumen Excel Lengkap")
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False, sheet_name='RAB_Volume_Harga')
            df_ahsp_terpakai.to_excel(writer, index=False, sheet_name='Analisa_Terpakai')
            
            df_sum = pd.DataFrame({
                "Rekapitulasi Biaya": ["Tenaga Kerja", "Bahan/Material", "Peralatan", "Overhead / Profit (Jika ada)", "TOTAL RENCANA ANGGARAN"],
                "Total (Rp)": [g_upah, g_bahan, g_alat, g_total - (g_upah+g_bahan+g_alat), g_total]
            })
            df_param = pd.DataFrame({
                "Spesifikasi Proyek": ["Lokasi", "Jenis", "Style", "Tingkat", "Luas Bangunan", "Jumlah Kamar", "Jumlah KM/WC", "Kondisi Tanah"],
                "Data": [daerah, jenis_bangunan, style_bangunan, f"{tingkat_bangunan} Lantai", f"{luas_bangunan} m2", jml_kamar, jml_km_wc, jenis_tanah]
            })
            df_sum.to_excel(writer, index=False, sheet_name='Summary', startrow=0)
            df_param.to_excel(writer, index=False, sheet_name='Summary', startrow=len(df_sum)+3)
            
        st.download_button(
            label="📥 Download Master RAB (RAB, Rincian AHSP, & Summary)", 
            data=buffer.getvalue(), 
            file_name=f"RAB_{jenis_bangunan}_{tingkat_bangunan}Lt_{daerah}.xlsx", 
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
            use_container_width=True, type="primary"
        )
    else:
        st.info("Data RAB masih kosong.")

# TAB 4: GAMBAR KERJA (BLUEPRINT)
with tab4:
    if st.session_state.parameter_tersimpan:
        st.markdown(f"### 📐 Referensi Skematik")
        st.caption(f"Spesifikasi: {jenis_bangunan} | {tingkat_bangunan} Lantai | Style: {style_bangunan}")
        
        st.info(f"💡 **Rekomendasi Konstruksi:** Karena Anda memilih Kondisi Tanah **{jenis_tanah}**, pastikan kedalaman galian dan struktur pondasi disesuaikan dengan daya dukung tanah aktual.")
        
        st.markdown("#### 1. Denah Skematik (Floor Plan)")
        st.markdown(f"")
        
        st.markdown("#### 2. Fasad Bangunan (Elevasi Eksterior)")
        tipe_img = "temporary wooden cabin" if "Temporer" in style_bangunan else style_bangunan.lower()
        st.markdown(f"")
    else:
        st.info("Generate RAB terlebih dahulu untuk memunculkan spesifikasi teknis dan visualisasi.")
