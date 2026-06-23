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

# --- 2. SETUP HALAMAN ---
st.set_page_config(page_title="Kalkulator RAB & SMKK", page_icon="🏗️", layout="wide")
st.title("🏗️ Sistem Estimator RAB Pro (Cipta Karya 2025)")

# --- 3. MEMUAT DATABASE ---
@st.cache_data
def load_data():
    try:
        # Load data dari master yang baru saja kita kerjakan
        df_ahsp = pd.read_excel("RAB_Analisa_Lengkap_V4.xlsx", sheet_name="3_Daftar_AHSP_Master", skiprows=1)
        df_ahsp = df_ahsp.dropna(subset=['Kode AHSP', 'Uraian Pekerjaan'])
        df_ahsp['Kode AHSP'] = df_ahsp['Kode AHSP'].astype(str).str.strip()
        df_ahsp['Pilihan'] = df_ahsp['Kode AHSP'] + " - " + df_ahsp['Uraian Pekerjaan'].astype(str)
        return df_ahsp
    except:
        st.error("File RAB_Analisa_Lengkap_V4.xlsx tidak ditemukan!")
        return pd.DataFrame()

df_ahsp = load_data()

# --- 4. SESSION STATE (Keranjang Belanja) ---
if 'rab_data' not in st.session_state: st.session_state.rab_data = []

# --- 5. SIDEBAR: PENGATURAN UMUM ---
with st.sidebar:
    st.header("⚙️ Pengaturan Proyek")
    nama_proyek = st.text_input("Nama Proyek:", "Pembangunan Fasilitas X")
    
    st.subheader("Skema K3 (SMKK)")
    jenis_proyek = st.radio("Sistem Keselamatan:", [
        "Proyek Personal (Tanpa K3)", 
        "Proyek Swasta / Pemerintah", 
        "Proyek Tambang (Ekstra Ketat)"
    ])
    
def hitung_smkk(total_konst, jenis):
    if "Personal" in jenis: return 0
    persen = 0.05 if "Tambang" in jenis else 0.02
    return total_konst * persen

# --- 6. TAMPILAN TABS ---
t1, t2, t3 = st.tabs(["➕ Input RAB (Manual Volume)", "🚜 Analisa Harga Alat", "🖨️ Print & Rangkuman"])

# TAB 1: INPUT MANUAL (Ganti metode Auto dengan Manual)
with t1:
    st.markdown("### Cari dan Tambahkan Pekerjaan ke RAB")
    
    if not df_ahsp.empty:
        # Form Pencarian
        with st.form("tambah_item"):
            col_search, col_vol, col_btn = st.columns([3, 1, 1])
            pilihan = col_search.selectbox("Cari AHSP Cipta Karya:", df_ahsp['Pilihan'].tolist())
            volume = col_vol.number_input("Input Volume:", min_value=0.01, value=1.0, step=0.1)
            submit = col_btn.form_submit_button("Tambahkan ke RAB")
            
            if submit:
                item = df_ahsp[df_ahsp['Pilihan'] == pilihan].iloc[0]
                st.session_state.rab_data.append({
                    "Kode": item['Kode AHSP'], "Pekerjaan": item['Uraian Pekerjaan'],
                    "Sat": item['Satuan'], "Volume": volume,
                    "Upah/Sat": float(item['Upah (Rp)']) if pd.notna(item['Upah (Rp)']) else 0,
                    "Bahan/Sat": float(item['Bahan (Rp)']) if pd.notna(item['Bahan (Rp)']) else 0,
                    "Alat/Sat": float(item['Alat (Rp)']) if pd.notna(item['Alat (Rp)']) else 0,
                    "Harga/Sat": float(item['Total Harga (Rp)']) if pd.notna(item['Total Harga (Rp)']) else 0
                })
                st.success(f"Berhasil ditambahkan: {item['Uraian Pekerjaan']}")

    st.divider()
    st.markdown("### 📋 Daftar Pekerjaan RAB Anda")
    if len(st.session_state.rab_data) > 0:
        df_rab = pd.DataFrame(st.session_state.rab_data)
        edited_df = st.data_editor(
            df_rab,
            column_config={
                "Kode": st.column_config.TextColumn(disabled=True),
                "Pekerjaan": st.column_config.TextColumn(disabled=True),
                "Volume": st.column_config.NumberColumn("Volume (Bisa Edit) ▼", format="%.2f"),
                "Harga/Sat": st.column_config.NumberColumn(format="Rp %.0f", disabled=True),
            },
            hide_index=True, use_container_width=True
        )
        st.session_state.rab_data = edited_df.to_dict('records')
        
        if st.button("Kosongkan RAB"):
            st.session_state.rab_data = []
            st.rerun()

# TAB 2: ANALISA ALAT
with t2:
    st.subheader("💡 Kalkulator Sewa Alat Berat (Penyusutan + Opr)")
    c1, c2 = st.columns(2)
    harga_alat = c1.number_input("Harga Beli / Pokok Alat (Rp):", value=150000000)
    jam_thn = c1.number_input("Jam Operasional / Tahun:", value=2000)
    bbm_jam = c2.number_input("Konsumsi BBM (Liter/Jam):", value=5.0)
    harga_bbm = c2.number_input("Harga BBM (Rp/Liter):", value=12000)
    
    penyusutan = ((harga_alat - (0.1 * harga_alat)) * 0.15) / jam_thn
    biaya_opr = (bbm_jam * harga_bbm) + (0.125 * harga_alat / jam_thn)
    sewa_jam = penyusutan + biaya_opr
    
    st.success(f"**Total Harga Sewa Per Jam: Rp {sewa_jam:,.0f}**")
    st.caption(f"Rincian: Penyusutan (Rp {penyusutan:,.0f}) + Operasional (Rp {biaya_opr:,.0f})")

# TAB 3: SUMMARY & PRINT
with t3:
    if len(st.session_state.rab_data) > 0:
        df_fin = pd.DataFrame(st.session_state.rab_data)
        df_fin['Jumlah Harga'] = df_fin['Volume'] * df_fin['Harga/Sat']
        total_konstruksi = df_fin['Jumlah Harga'].sum()
        
        biaya_smkk = hitung_smkk(total_konstruksi, jenis_proyek)
        grand_total = total_konstruksi + biaya_smkk
        
        st.markdown(f"### 📊 Rangkuman RAB: {nama_proyek}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Biaya Konstruksi Murni", f"Rp {total_konstruksi:,.0f}")
        c2.metric(f"Biaya SMKK ({jenis_proyek})", f"Rp {biaya_smkk:,.0f}")
        c3.metric("💰 GRAND TOTAL", f"Rp {grand_total:,.0f}")
        
        st.warning(f"**TERBILANG:** *{terbilang(grand_total)} Rupiah*")
        
        # EXPORT EXCEL PRINT
        st.divider()
        st.markdown("### 🖨️ Cetak & Unduh")
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # 1. Rincian Volume & Total
            df_fin.to_excel(writer, index=False, sheet_name='1_RAB_Utama')
            
            # 2. AHSP Terpakai Saja (Untuk Lampiran/Justifikasi Harga)
            df_terpakai = df_fin[['Kode', 'Pekerjaan', 'Sat', 'Upah/Sat', 'Bahan/Sat', 'Alat/Sat', 'Harga/Sat']]
            df_terpakai.to_excel(writer, index=False, sheet_name='2_Lampiran_Harga_Satuan')
            
            # 3. SMKK Detail
            pd.DataFrame({
                "Uraian K3 (SMKK)": ["Dokumen RKK", "Sosialisasi & Promosi K3", "Alat Pelindung Diri (APD)", "Asuransi / BPJS Ketenagakerjaan", "Rambu & Perlengkapan Lalu Lintas"],
                "Alokasi Dana": [biaya_smkk*0.05, biaya_smkk*0.1, biaya_smkk*0.5, biaya_smkk*0.2, biaya_smkk*0.15]
            }).to_excel(writer, index=False, sheet_name='3_Analisa_SMKK')
            
            # 4. Summary & Terbilang
            pd.DataFrame({
                "Kategori": ["Total Biaya Konstruksi", "Total Biaya Keselamatan (SMKK)", "GRAND TOTAL PROYEK", "TERBILANG:"],
                "Nilai": [f"Rp {total_konstruksi:,.0f}", f"Rp {biaya_smkk:,.0f}", f"Rp {grand_total:,.0f}", f"{terbilang(grand_total)} Rupiah"]
            }).to_excel(writer, index=False, sheet_name='4_Summary_Print')
            
        st.download_button(
            "📥 Download RAB Lengkap untuk Di-print (Excel)", 
            buffer.getvalue(), 
            f"RAB_{nama_proyek}.xlsx", 
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
            use_container_width=True, type="primary"
        )
    else:
        st.info("RAB masih kosong. Silakan cari dan tambahkan pekerjaan di Tab Input RAB.")
