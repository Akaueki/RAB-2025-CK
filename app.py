import streamlit as st
import pandas as pd
import io
import math

# --- 1. FUNGSI TERBILANG (ANGKA KE HURUF) ---
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
    else: return "Angka terlalu besar"

# --- 2. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Auto-RAB Cipta Karya", page_icon="🏢", layout="wide")
st.title("🏢 Generator RAB Otomatis (Parametrik)")
st.markdown("Input parameter bangunan, biarkan sistem menghasilkan Draf RAB lengkap untuk Anda.")
st.divider()

# --- 3. MEMUAT DATABASE AHSP ---
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("RAB_AHSP_Lengkap_CiptaKarya_2025.xlsx", sheet_name="Daftar_AHSP", skiprows=2)
        df = df.dropna(subset=['Kode AHSP', 'Uraian Pekerjaan'])
        # Membersihkan spasi pada kode
        df['Kode AHSP'] = df['Kode AHSP'].astype(str).str.strip()
        return df
    except:
        st.error("File Database RAB_AHSP_Lengkap_CiptaKarya_2025.xlsx tidak ditemukan!")
        return pd.DataFrame()

df_ahsp = load_data()

# --- 4. INPUT PARAMETER PROYEK ---
with st.sidebar:
    st.header("⚙️ Parameter Bangunan")
    luas_tanah = st.number_input("Luas Tanah (m2):", min_value=10, value=120)
    luas_bangunan = st.number_input("Luas Bangunan (m2):", min_value=10, value=60)
    
    jenis_bangunan = st.selectbox("Jenis Bangunan:", ["Rumah Tinggal", "Ruko", "Fasilitas Umum"])
    tipe_bangunan = st.selectbox("Tipe Bangunan:", ["Sederhana", "Menengah", "Mewah"])
    jenis_tanah = st.selectbox("Kondisi Tanah Asli:", ["Keras (Galian Sedikit)", "Sedang", "Lembek (Galian Dalam)"])
    
    generate_btn = st.button("🚀 Generate RAB Otomatis", use_container_width=True)

# --- 5. LOGIKA RUMUS EMPIRIS (PARAMETRIK) ---
# Fungsi ini menebak kebutuhan volume berdasarkan Luas Bangunan (L)
def hitung_volume_parametrik(L, tanah, tipe):
    # Faktor pengali tanah
    f_tanah = 0.4 if "Keras" in tanah else (0.5 if "Sedang" in tanah else 0.8)
    # Faktor pengali atap/arsitektur
    f_tipe = 1.2 if tipe == "Sederhana" else (1.5 if tipe == "Menengah" else 2.0)
    
    estimasi = {
        "A.2.2.1.1": L * f_tanah,               # Galian Tanah Biasa
        "A.3.2.1.2": L * 0.35 * f_tipe,         # Pondasi Batu Kali
        "A.4.1.1.5": L * 0.25 * f_tipe,         # Beton Sloof/Kolom K-175
        "A.4.4.1.1": L * 3.2 * f_tipe,          # Pasangan Dinding Bata
        "A.4.4.2.2": L * 6.4 * f_tipe,          # Plesteran Dinding (2 sisi)
        "A.4.4.3.35": L * 1.0,                  # Lantai Keramik Dalam
        "A.4.7.1.10": L * 3.5 * f_tipe          # Pengecatan Tembok Baru
    }
    return estimasi

# --- 6. PROSES GENERATE & TAMPILAN ---
if 'rab_generated' not in st.session_state:
    st.session_state.rab_generated = False

if generate_btn:
    st.session_state.estimasi_vol = hitung_volume_parametrik(luas_bangunan, jenis_tanah, tipe_bangunan)
    
    tabel_draf = []
    for kode, vol in st.session_state.estimasi_vol.items():
        # Cari data AHSP berdasarkan kode
        cari = df_ahsp[df_ahsp['Kode AHSP'] == kode]
        if not cari.empty:
            item = cari.iloc[0]
            tabel_draf.append({
                "Kode": item['Kode AHSP'],
                "Pekerjaan": item['Uraian Pekerjaan'],
                "Sat": item['Satuan'],
                "Volume": round(vol, 2), # Default hasil prediksi
                "Upah/Sat": float(item['Subtotal UPAH (Rp)']),
                "Bahan/Sat": float(item['Subtotal BAHAN (Rp)']),
                "Alat/Sat": float(item['Subtotal ALAT (Rp)']),
                "Harga/Sat": float(item['Harga Satuan Total (Rp)'])
            })
    
    st.session_state.df_draf = pd.DataFrame(tabel_draf)
    st.session_state.rab_generated = True

# JIKA RAB SUDAH DI-GENERATE
if st.session_state.rab_generated:
    st.success(f"Draf RAB untuk {jenis_bangunan} {tipe_bangunan} (Luas {luas_bangunan} m2) berhasil dibuat!")
    st.markdown("### 📝 Cek & Edit Volume Pekerjaan")
    st.info("Anda dapat langsung mengubah angka pada kolom **Volume** di bawah ini untuk penyesuaian akhir lapangan.")
    
    # 6A. DATA EDITOR (USER BISA MENGGANTI VOLUME OTOMATIS)
    edited_df = st.data_editor(
        st.session_state.df_draf,
        column_config={
            "Kode": st.column_config.TextColumn("Kode", disabled=True),
            "Pekerjaan": st.column_config.TextColumn("Pekerjaan", disabled=True),
            "Sat": st.column_config.TextColumn("Sat", disabled=True),
            "Volume": st.column_config.NumberColumn("Volume (Edit Sini) ▼", format="%.2f", step=1.0),
            "Harga/Sat": st.column_config.NumberColumn("Harga/Sat", format="Rp %.0f", disabled=True),
        },
        hide_index=True,
        use_container_width=True
    )
    
    # 6B. KALKULASI REAL-TIME SETELAH DIEDIT
    edited_df['Total Upah'] = edited_df['Volume'] * edited_df['Upah/Sat']
    edited_df['Total Bahan'] = edited_df['Volume'] * edited_df['Bahan/Sat']
    edited_df['Total Alat'] = edited_df['Volume'] * edited_df['Alat/Sat']
    edited_df['Jumlah Harga'] = edited_df['Volume'] * edited_df['Harga/Sat']
    
    # 6C. SUMMARY KEBUTUHAN (UPAH, BAHAN, ALAT)
    grand_upah = edited_df['Total Upah'].sum()
    grand_bahan = edited_df['Total Bahan'].sum()
    grand_alat = edited_df['Total Alat'].sum()
    grand_total = edited_df['Jumlah Harga'].sum()
    
    st.divider()
    st.markdown("### 📊 Summary RAB & Kebutuhan")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👷 Total Biaya Tenaga Kerja", f"Rp {grand_upah:,.0f}")
    c2.metric("🧱 Total Biaya Bahan/Material", f"Rp {grand_bahan:,.0f}")
    c3.metric("🚜 Total Biaya Alat", f"Rp {grand_alat:,.0f}")
    c4.metric("💰 GRAND TOTAL RAB (Inc. Overhead)", f"Rp {grand_total:,.0f}")
    
    # 6D. PENYEBUTAN HURUF (TERBILANG)
    terbilang_teks = terbilang(grand_total) + " Rupiah"
    st.warning(f"**Terbilang:** *{terbilang_teks}*")
    
    # 6E. PRINTOUT / DOWNLOAD EXCEL DETAIL
    st.markdown("### 🖨️ Cetak Dokumen")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        edited_df.to_excel(writer, index=False, sheet_name='Detail_RAB')
        # Buat sheet summary
        df_sum = pd.DataFrame({
            "Kategori": ["Biaya Tenaga Kerja", "Biaya Bahan/Material", "Biaya Peralatan", "Overhead / Profit", "GRAND TOTAL"],
            "Total (Rp)": [grand_upah, grand_bahan, grand_alat, grand_total - (grand_upah+grand_bahan+grand_alat), grand_total]
        })
        df_sum.to_excel(writer, index=False, sheet_name='Summary_RAB')
        
    st.download_button(
        label="📥 Download Detail RAB, AHSP & Summary (Excel)",
        data=buffer.getvalue(),
        file_name=f"RAB_{jenis_bangunan}_{luas_bangunan}m2.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )
