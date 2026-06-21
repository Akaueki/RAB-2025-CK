import streamlit as st
import pandas as pd
import io

# --- 1. PENGATURAN HALAMAN ---
st.set_page_config(page_title="RAB Cipta Karya 2025", page_icon="🏗️", layout="centered")

st.title("🏗️ Aplikasi RAB Cipta Karya 2025")
st.markdown("Kalkulator Rencana Anggaran Biaya Otomatis berdasarkan 2.500+ data AHSP.")
st.divider()

# --- 2. MEMUAT DATABASE EXCEL ---
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("RAB_CiptaKarya_2025.xlsm", sheet_name="Daftar_AHSP", skiprows=2)
        df = df.dropna(subset=['Kode AHSP', 'Uraian Pekerjaan'])
        # Gabungkan kode dan uraian untuk dropdown pencarian
        df['Pilihan'] = df['Kode AHSP'].astype(str) + " - " + df['Uraian Pekerjaan'].astype(str)
        return df
    except Exception as e:
        st.error("File Database Excel tidak ditemukan. Pastikan file berada di folder yang sama.")
        return pd.DataFrame()

df_ahsp = load_data()

# --- 3. MEMBUAT PENYIMPANAN SEMENTARA (KERANJANG RAB) ---
if 'tabel_rab' not in st.session_state:
    st.session_state.tabel_rab = []

# --- 4. ANTARMUKA PENCARIAN & INPUT ---
if not df_ahsp.empty:
    st.subheader("🔍 Tambah Pekerjaan Baru")
    
    # Dropdown dengan fitur pencarian (Ketik nama pekerjaan, otomatis muncul)
    pilihan_user = st.selectbox("Cari Pekerjaan (Ketik nama material/pekerjaan):", df_ahsp['Pilihan'].tolist())
    
    col1, col2 = st.columns([2, 1])
    with col1:
        volume = st.number_input("Masukkan Volume:", min_value=0.01, value=1.0, step=0.1)
    
    data_pilih = df_ahsp[df_ahsp['Pilihan'] == pilihan_user].iloc[0]
    with col2:
        st.info(f"Satuan: **{data_pilih['Satuan']}**")

    # Tombol Tambah ke RAB
    if st.button("➕ Tambahkan ke RAB", type="primary", use_container_width=True):
        upah = float(data_pilih['Subtotal UPAH (Rp)']) * volume
        bahan = float(data_pilih['Subtotal BAHAN (Rp)']) * volume
        alat = float(data_pilih['Subtotal ALAT (Rp)']) * volume
        total_harga = float(data_pilih['Harga Satuan Total (Rp)']) * volume
        
        item_baru = {
            "Kode AHSP": data_pilih['Kode AHSP'],
            "Uraian Pekerjaan": data_pilih['Uraian Pekerjaan'],
            "Vol": volume,
            "Sat": data_pilih['Satuan'],
            "Total Upah": upah,
            "Total Bahan": bahan,
            "Total Alat": alat,
            "Jumlah Harga": total_harga
        }
        st.session_state.tabel_rab.append(item_baru)
        st.success(f"Berhasil ditambahkan: {data_pilih['Uraian Pekerjaan']}")

# --- 5. ANTARMUKA HASIL RAB (KERANJANG) ---
st.divider()
st.subheader("📋 Daftar Pekerjaan RAB Anda")

if len(st.session_state.tabel_rab) > 0:
    df_hasil = pd.DataFrame(st.session_state.tabel_rab)
    
    # Tampilkan tabel di aplikasi
    st.dataframe(
        df_hasil.style.format({
            "Total Upah": "Rp {:,.0f}", 
            "Total Bahan": "Rp {:,.0f}", 
            "Total Alat": "Rp {:,.0f}", 
            "Jumlah Harga": "Rp {:,.0f}"
        }), 
        use_container_width=True
    )
    
    # Hitung Grand Total
    grand_total = df_hasil['Jumlah Harga'].sum()
    st.metric("GRAND TOTAL BIAYA (Termasuk Overhead 10%)", f"Rp {grand_total:,.0f}")
    
    # Tombol Hapus Semua
    if st.button("🗑️ Hapus Semua Daftar"):
        st.session_state.tabel_rab = []
        st.rerun()

    # --- 6. EXPORT KE EXCEL ---
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_hasil.to_excel(writer, index=False, sheet_name='Hasil_RAB')
    
    st.download_button(
        label="📥 Download Hasil RAB (Excel)",
        data=buffer.getvalue(),
        file_name="Laporan_RAB_Lapangan.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
else:
    st.info("Belum ada pekerjaan yang ditambahkan. Silakan cari dan tambah pekerjaan di atas.")