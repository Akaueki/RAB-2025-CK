import streamlit as st
import pandas as pd
import io

# --- FUNGSI TERBILANG ---
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

st.set_page_config(page_title="RAB & Blueprint Manager", page_icon="🏗️", layout="wide")
st.title("🏗️ Sistem Estimator RAB Terpadu")

# --- LOAD DATABASE EXCEL MASTER ---
@st.cache_data
def load_data():
    try:
        # Load AHSP
        df = pd.read_excel("RAB_Manual_Excel_Clean_Final.xlsx", sheet_name="3_Daftar_AHSP", skiprows=1)
        df = df.dropna(subset=['Kode AHSP', 'Uraian Pekerjaan'])
        df['Kode AHSP'] = df['Kode AHSP'].astype(str).str.strip()
        df['Pilihan'] = df['Kode AHSP'] + " - " + df['Uraian Pekerjaan'].astype(str)
        return df
    except:
        return pd.DataFrame()

df_ahsp = load_data()

# --- STATE KERANJANG ---
if 'rab_data' not in st.session_state: st.session_state.rab_data = []

# --- TAMPILAN TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["📝 Pembuatan RAB", "📑 Analisa Alat", "📐 Gambar Blueprint", "🖨️ Summary & Print"])

# TAB 1: PEMBUATAN RAB
with tab1:
    st.markdown("### Cari dan Tambahkan Pekerjaan ke RAB")
    if not df_ahsp.empty:
        with st.form("tambah_item"):
            col1, col2, col3 = st.columns([3, 1, 1])
            pilihan = col1.selectbox("Cari Pekerjaan (Bisa Ketik):", df_ahsp['Pilihan'].tolist())
            volume = col2.number_input("Volume (M/M2/M3):", min_value=0.01, value=1.0, step=0.1)
            submit = col3.form_submit_button("➕ Tambahkan")
            
            if submit:
                item = df_ahsp[df_ahsp['Pilihan'] == pilihan].iloc[0]
                st.session_state.rab_data.append({
                    "Kode": item['Kode AHSP'], 
                    "Pekerjaan": item['Uraian Pekerjaan'],
                    "Sat": item['Satuan'], 
                    "Volume": volume,
                    "Harga/Sat": float(item['Harga Satuan Total (Rp)'])
                })
                st.success(f"Masuk keranjang: {item['Uraian Pekerjaan']}")

    st.divider()
    st.markdown("### 📋 Daftar Pekerjaan RAB Anda")
    if len(st.session_state.rab_data) > 0:
        df_rab = pd.DataFrame(st.session_state.rab_data)
        edited_df = st.data_editor(
            df_rab,
            column_config={
                "Kode": st.column_config.TextColumn(disabled=True),
                "Pekerjaan": st.column_config.TextColumn(disabled=True),
                "Sat": st.column_config.TextColumn(disabled=True),
                "Volume": st.column_config.NumberColumn("Volume (Edit) ▼", format="%.2f"),
                "Harga/Sat": st.column_config.NumberColumn(format="Rp %.0f", disabled=True),
            },
            hide_index=True, use_container_width=True
        )
        st.session_state.rab_data = edited_df.to_dict('records')
        
        if st.button("Kosongkan RAB"):
            st.session_state.rab_data = []
            st.rerun()
    else:
        st.info("RAB masih kosong.")

# TAB 2: ANALISA ALAT
with tab2:
    st.subheader("💡 Kalkulator Analisa Sewa Alat Berat (Bina Marga)")
    st.caption("Hitung biaya operasi dan penyusutan alat berat untuk dimasukkan ke penawaran proyek.")
    c1, c2 = st.columns(2)
    nama_alat = c1.text_input("Nama Peralatan:", "Excavator")
    harga_alat = c1.number_input("Harga Beli / Pokok Alat (Rp):", value=150000000)
    jam_thn = c1.number_input("Jam Operasional / Tahun:", value=2000)
    
    bbm_jam = c2.number_input("Konsumsi BBM (Liter/Jam):", value=5.0)
    harga_bbm = c2.number_input("Harga BBM (Rp/Liter):", value=12000)
    
    # Hitungan Bina Marga
    penyusutan = ((harga_alat - (0.1 * harga_alat)) * 0.15) / jam_thn
    biaya_opr = (bbm_jam * harga_bbm) + (0.125 * harga_alat / jam_thn)
    sewa_jam = penyusutan + biaya_opr
    
    st.success(f"**Total Sewa {nama_alat} Per Jam: Rp {sewa_jam:,.0f}**")
    st.markdown(f"> *Rincian: Penyusutan (Rp {penyusutan:,.0f}) + Operasi (Rp {biaya_opr:,.0f})*")

# TAB 3: GAMBAR BLUEPRINT
with tab3:
    st.subheader("📐 Arsip Gambar Kerja & Blueprint")
    st.markdown("Pilih referensi gambar struktur dari file yang telah diunggah.")
    pilihan_pdf = st.radio("Pilih Gambar Bangunan:", ["Bapak Rahmad Hidayad (2 Lantai)", "Andi Mangkona (Konsep 12x15m)"])
    
    if "Rahmad" in pilihan_pdf:
        st.info("Denah dan Rencana Pondasi untuk Rumah Tinggal 2 Lantai (Bapak Rahmad Hidayad)")
        st.markdown("")
        st.markdown("")
    else:
        st.info("Konsep Rumah 2 Lantai 12x15m (Bapak Andi Mangkona)")
        st.markdown("")
        st.markdown("")
        
    st.caption("Gunakan referensi ukuran pada gambar ini untuk mengisi manual kolom 'Volume' di Tab 1 (RAB).")

# TAB 4: SUMMARY & PRINT
with tab4:
    if len(st.session_state.rab_data) > 0:
        df_fin = pd.DataFrame(st.session_state.rab_data)
        df_fin['Jumlah Harga'] = df_fin['Volume'] * df_fin['Harga/Sat']
        total_konstruksi = df_fin['Jumlah Harga'].sum()
        
        st.markdown("### 1. Masukkan Biaya Keselamatan (SMKK)")
        biaya_smkk = st.number_input("Total Biaya SMKK / K3 (Rp):", min_value=0, value=0, step=100000)
        grand_total = total_konstruksi + biaya_smkk
        
        st.markdown("### 2. Rekapitulasi Akhir")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Konstruksi", f"Rp {total_konstruksi:,.0f}")
        c2.metric("Total SMKK", f"Rp {biaya_smkk:,.0f}")
        c3.metric("💰 GRAND TOTAL", f"Rp {grand_total:,.0f}")
        
        terbilang_teks = terbilang(grand_total) + " Rupiah"
        st.warning(f"**Terbilang:** *{terbilang_teks}*")
        
        # EXPORT EXCEL PRINT
        st.divider()
        st.markdown("### 🖨️ Cetak & Unduh")
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_fin.to_excel(writer, index=False, sheet_name='1_RAB_Detail')
            pd.DataFrame({
                "Rangkuman": ["Total Biaya Konstruksi", "Total Biaya SMKK", "GRAND TOTAL", "TERBILANG:"],
                "Nilai": [total_konstruksi, biaya_smkk, grand_total, terbilang_teks]
            }).to_excel(writer, index=False, sheet_name='2_Summary')
            
        st.download_button(
            "📥 Download RAB Output (Excel)", 
            buffer.getvalue(), 
            "RAB_Output.xlsx", 
            "application/vnd.ms-excel", 
            use_container_width=True, type="primary"
        )
    else:
        st.info("Selesaikan pengisian RAB di Tab 1 untuk memunculkan Rangkuman dan Cetak Excel.")
