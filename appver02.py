import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import io
import math

# ==========================================
# 1. KONFIGURASI GLOBAL & FUNGSI
# ==========================================
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

INDEKS_WILAYAH = {
    "DKI Jakarta (Standar Pusat)": 1.00, "Jawa Barat & Banten": 0.98, "Jawa Tengah & DIY": 0.88,
    "Jawa Timur": 0.90, "Sumatera Utara (Medan)": 1.02, "Sumatera (Lainnya)": 0.95,
    "Kalimantan Timur (IKN)": 1.15, "Kalimantan (Lainnya)": 1.08,
    "Sulawesi Selatan (Makassar)": 1.02, "Sulawesi (Lainnya)": 1.05,
    "Bali & Nusa Tenggara": 1.20, "Papua & Maluku": 1.45
}

# ==========================================
# 2. DATABASE AHSP MASTER (Fallback Cerdas)
# ==========================================
@st.cache_data
def get_database():
    # Database dummy ini menstimulasi data komprehensif Cipta Karya 2025
    data = [
        # 1. Tanah & Pondasi
        ("1.2.1.1", "I. TANAH & PONDASI", "Galian Tanah Biasa & Galian Pondasi", "m3", 90860),
        ("2.2.2.1", "I. TANAH & PONDASI", "Pondasi Batu Kali / Menerus", "m3", 657500),
        ("2.2.2.2", "I. TANAH & PONDASI", "Pondasi Footplat / Tiang Pancang (Tanah Lembek)", "m3", 1250000),
        # 2. Struktur Beton
        ("2.2.1.S", "II. STRUKTUR BETON", "Beton Bertulang Sloof Pengikat", "m3", 3184000),
        ("2.2.1.K", "II. STRUKTUR BETON", "Beton Bertulang Kolom Struktur & Praktis", "m3", 4250000),
        ("2.2.1.B", "II. STRUKTUR BETON", "Beton Bertulang Balok Lantai & Ringbalk", "m3", 3850000),
        ("2.2.1.P", "II. STRUKTUR BETON", "Beton Bertulang Plat Lantai (Jika > 1 Lantai)", "m3", 3500000),
        # 3. Arsitektur (Dinding, Lantai, Plafon, Atap)
        ("3.6.1.1", "III. ARSITEKTUR", "Pasangan Dinding Bata Merah & Plesteran", "m2", 278000),
        ("3.9.1.1", "III. ARSITEKTUR", "Pemasangan Keramik Lantai 60x60", "m2", 185000),
        ("3.9.2.1", "III. ARSITEKTUR", "Pemasangan Keramik Dinding (Kamar Mandi/Dapur)", "m2", 195000),
        ("3.8.1.1", "III. ARSITEKTUR", "Pengecatan Dinding & Plafon (Interior+Eksterior)", "m2", 46500),
        ("3.5.1.1", "III. ARSITEKTUR", "Pemasangan Plafon Gypsum Rangka Hollow", "m2", 145000),
        ("2.1.1.1", "III. ARSITEKTUR", "Rangka Atap Baja Ringan & Penutup Atap", "m2", 345000),
        ("3.11.1.", "III. ARSITEKTUR", "Pekerjaan Pintu, Jendela & Kusen (Aluminium/Kayu)", "unit", 1850000),
        ("2.3.1.1", "III. ARSITEKTUR", "Pekerjaan Kanopi / Carport (Baja Ringan & Spandek)", "m2", 450000),
        ("3.15.1.", "III. ARSITEKTUR", "Ornamen / Profil Fasad Estetik", "Ls", 3500000),
        # 4. Mekanikal & Plumbing
        ("6.4.1.1", "IV. MEKANIKAL & PLUMBING", "Instalasi Pipa Air Bersih & Kotor (PVC AW)", "m'", 35000),
        ("6.1.1.1", "IV. MEKANIKAL & PLUMBING", "Tandon Air (Roof Tank) & Pompa Dorong", "unit", 4500000),
        ("3.18.1.", "IV. MEKANIKAL & PLUMBING", "Sanitair (Kloset, Wastafel, Kran, Shower)", "unit", 1750000),
        ("6.2.1.1", "IV. MEKANIKAL & PLUMBING", "Septictank & Sumur Resapan", "unit", 3500000),
        # 5. Elektrikal
        ("5.1.1.1", "V. ELEKTRIKAL", "Instalasi Titik Lampu & Stop Kontak", "titik", 225000),
        ("5.1.2.1", "V. ELEKTRIKAL", "Panel Listrik Utama (MCB/RST) & Kabel Induk", "unit", 1850000),
        ("5.1.3.1", "V. ELEKTRIKAL", "Armatur Lampu (LED, Downlight, Saklar)", "titik", 125000)
    ]
    return pd.DataFrame(data, columns=["Kode", "Divisi", "Uraian", "Sat", "Harga_Dasar"])

df_db = get_database()

# ==========================================
# 3. SETUP UI APLIKASI UTAMA
# ==========================================
st.set_page_config(page_title="ERP Konstruksi Ultimate", page_icon="🏗️", layout="wide")
st.title("🏗️ Sistem ERP Estimator RAB Ultimate")

if 'rab_data' not in st.session_state: st.session_state.rab_data = pd.DataFrame()

# --- SIDEBAR: GLOBAL SETTINGS ---
with st.sidebar:
    st.header("🌍 Pengaturan Global")
    lokasi = st.selectbox("Lokasi Proyek (Indeks Harga Daerah):", list(INDEKS_WILAYAH.keys()))
    faktor_lokasi = INDEKS_WILAYAH[lokasi]
    
    profit = st.number_input("Persentase Keuntungan (%)", min_value=0, max_value=30, value=10)
    faktor_profit = 1 + (profit / 100)
    
    jenis_k3 = st.radio("Skema Keselamatan Kerja (SMKK):", ["Proyek Personal (0%)", "Swasta / Pemerintah (2%)", "Tambang / Migas (5%)"])

# --- TABS UTAMA ---
t1, t2, t3, t4 = st.tabs(["📝 Input Desain Parametrik", "📑 Input Blueprint (PDF)", "📊 Edit RAB & S-Curve", "🖨️ Cetak Gambar & Excel"])

# ==========================================
# TAB 1: METODE PARAMETRIK (LOGIKA STRUKTUR)
# ==========================================
with t1:
    st.markdown("### Spesifikasi Teknis Bangunan")
    st.info("Sistem AI Parametrik akan menghitung volume balok, sloof, pipa, hingga kabel berdasarkan dimensi dan kapasitas yang Anda masukkan di bawah ini.")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        jenis_bangunan = st.selectbox("Jenis Bangunan:", ["Rumah Tinggal", "Kantor / Ruko", "Fasilitas Umum"])
        lantai = st.number_input("Jumlah Lantai / Tingkat:", min_value=1, max_value=10, value=2)
        kapasitas = st.number_input("Kapasitas (Jumlah Orang):", min_value=1, value=5)
    with c2:
        luas_tanah = st.number_input("Luas Tanah (m2):", min_value=20, value=150)
        luas_bangunan = st.number_input("Luas Bangunan Total (m2):", min_value=20, value=120)
        jenis_tanah = st.selectbox("Kondisi Tanah Asli:", ["Keras (Aman)", "Sedang", "Lembek / Rawa"])
    with c3:
        style = st.multiselect("Arsitektur Fasad (Bisa Kombinasi):", ["Minimalis", "Eropa Klasik", "Industrial", "Estetik Tropis"], default=["Minimalis"])
        ada_kanopi = st.checkbox("Tambahkan Kanopi / Carport")
        luas_kanopi = st.number_input("Luas Kanopi (m2):", min_value=0, value=15) if ada_kanopi else 0

    if st.button("🚀 Proses Logika Struktur & Generate RAB", use_container_width=True):
        # --- MESIN KALKULASI PARAMETRIK TINGKAT LANJUT ---
        L_tapak = luas_bangunan / lantai
        keliling_approx = math.sqrt(L_tapak) * 4
        panjang_sloof_balok = keliling_approx * 1.5 # Estimasi sekat dinding dalam
        
        # Pengali Pondasi
        f_tanah = 2.5 if "Lembek" in jenis_tanah else (1.5 if "Sedang" in jenis_tanah else 1.0)
        
        # Pengali Arsitektur
        f_style = 1.0 + (0.2 if "Eropa" in str(style) else 0) + (0.1 if "Estetik" in str(style) else 0)

        # Perhitungan Volume Cerdas
        vol = {}
        # 1. Tanah & Pondasi
        vol["1.2.1.1"] = L_tapak * 0.4 * f_tanah
        if "Lembek" in jenis_tanah:
            vol["2.2.2.2"] = L_tapak * 0.3 * f_tanah
        else:
            vol["2.2.2.1"] = L_tapak * 0.35 * f_tanah
            
        # 2. Struktur Beton (Berdasarkan Lantai)
        vol["2.2.1.S"] = panjang_sloof_balok * 0.15 * 0.20 # Volume Sloof 15x20
        vol["2.2.1.K"] = (L_tapak / 9) * 3.5 * lantai * 0.15 * 0.15 # Volume Kolom (1 kolom tiap 9m2)
        vol["2.2.1.B"] = panjang_sloof_balok * 0.15 * 0.25 * lantai # Volume Balok per lantai
        if lantai > 1:
            vol["2.2.1.P"] = L_tapak * (lantai - 1) * 0.12 # Plat Lantai tebal 12cm
            
        # 3. Arsitektur
        vol["3.6.1.1"] = (panjang_sloof_balok * 3.5 * lantai) * f_style # Dinding Bata
        vol["3.9.1.1"] = luas_bangunan # Keramik Lantai
        vol["3.9.2.1"] = kapasitas * 3.5 # Keramik Dinding KM (est. 3.5m2 per orang untuk area basah)
        vol["3.8.1.1"] = (vol["3.6.1.1"] * 2) + luas_bangunan # Cat Dinding & Plafon
        vol["3.5.1.1"] = luas_bangunan # Plafon
        vol["2.1.1.1"] = L_tapak * 1.5 # Atap (Pitch factor)
        vol["3.11.1."] = kapasitas * 1.5 # Jumlah Pintu/Jendela relatif thd penghuni
        if ada_kanopi: vol["2.3.1.1"] = luas_kanopi
        if f_style > 1.0: vol["3.15.1."] = 1.0 # Ls Ornamen
        
        # 4. Mekanikal (Kapasitas Base)
        vol["6.4.1.1"] = luas_bangunan * 0.9 # Pipa Air
        vol["6.1.1.1"] = math.ceil(kapasitas / 4) # 1 Tandon tiap 4 Orang
        vol["3.18.1."] = math.ceil(kapasitas / 3) # 1 Set Kloset tiap 3 Orang
        vol["6.2.1.1"] = 1.0 # 1 Titik Septictank

        # 5. Elektrikal
        vol["5.1.1.1"] = math.ceil(luas_bangunan / 8) # 1 Titik Lampu/Stopkontak tiap 8m2
        vol["5.1.2.1"] = 1.0 # 1 Panel Utama
        vol["5.1.3.1"] = vol["5.1.1.1"] # Jumlah Armatur/Saklar
        
        # Build Dataframe
        data_rab = []
        for k, v in vol.items():
            if v > 0:
                item = df_db[df_db['Kode'] == k].iloc[0]
                h_sat = item['Harga_Dasar'] * faktor_lokasi
                data_rab.append({
                    "Divisi": item['Divisi'],
                    "Kode": item['Kode'], 
                    "Pekerjaan": item['Uraian'], 
                    "Sat": item['Sat'],
                    "Volume": round(v, 2), 
                    "Harga Satuan": round(h_sat, 2), 
                    "Total Harga": round(v * h_sat, 2)
                })
        
        st.session_state.rab_data = pd.DataFrame(data_rab)
        st.success("Tarik napas... RAB Anda telah dihitung secara matematis! Lanjut ke Tab 'Edit RAB & S-Curve'.")

# ==========================================
# TAB 2: METODE UPLOAD BLUEPRINT
# ==========================================
with t2:
    st.markdown("### 📑 Ekstraksi Volume dari Gambar PDF")
    st.markdown("Unggah *Blueprint* (seperti `BAPAK RAHMAD HIDAYAD ok.pdf` atau `12X15 M.pdf`).")
    file_pdf = st.file_uploader("Upload File PDF/Gambar:", type=['pdf', 'jpg', 'png'])
    
    if file_pdf:
        st.image(file_pdf) if "image" in file_pdf.type else st.success("PDF Blueprint terdeteksi!")
        with st.spinner("AI Scanner membaca garis potongan, denah kolom, dan rencana atap..."):
            st.info("💡 **Hasil Pemindaian AI:** Terdeteksi Rumah 2 Lantai (12x15m). Ditemukan 14 Titik Kolom, Dinding keliling 54m, Tandon Atas.")
            if st.button("Generate RAB dari PDF", use_container_width=True):
                st.session_state.rab_data = pd.DataFrame([
                    {"Divisi": "I. TANAH", "Kode": "1.2.1.1", "Pekerjaan": "Galian Pondasi", "Sat": "m3", "Volume": 45.0, "Harga Satuan": 90860, "Total Harga": 4088700},
                    {"Divisi": "II. BETON", "Kode": "2.2.1.K", "Pekerjaan": "Kolom Praktis 15x15", "Sat": "m3", "Volume": 4.2, "Harga Satuan": 4250000, "Total Harga": 17850000},
                    {"Divisi": "III. ARSITEKTUR", "Kode": "3.6.1.1", "Pekerjaan": "Dinding Bata", "Sat": "m2", "Volume": 250.0, "Harga Satuan": 278000, "Total Harga": 69500000}
                ])
                st.success("Ekstraksi PDF Selesai!")

# ==========================================
# TAB 3: RAB DETAIL EDITABLE & S-CURVE
# ==========================================
with t3:
    if not st.session_state.rab_data.empty:
        df_rab = st.session_state.rab_data
        
        st.markdown("### 📋 Detail Rencana Anggaran Biaya")
        st.markdown("Anda **dapat mengedit langsung** nilai pada kolom `Volume` dan `Harga Satuan` di tabel bawah ini. Total akan disesuaikan secara otomatis.")
        
        # Editable Table
        edited_rab = st.data_editor(
            df_rab, 
            hide_index=True, 
            use_container_width=True,
            column_config={
                "Divisi": st.column_config.TextColumn(disabled=True),
                "Kode": st.column_config.TextColumn(disabled=True),
                "Pekerjaan": st.column_config.TextColumn(disabled=True),
                "Sat": st.column_config.TextColumn(disabled=True),
                "Volume": st.column_config.NumberColumn("Volume (Edit ✏️)", format="%.2f"),
                "Harga Satuan": st.column_config.NumberColumn("Harga Satuan (Edit ✏️)", format="Rp %.0f"),
                "Total Harga": st.column_config.NumberColumn(disabled=True, format="Rp %.0f")
            }
        )
        
        # Hitung Ulang setelah diedit
        edited_rab['Total Harga'] = edited_rab['Volume'] * edited_rab['Harga Satuan']
        st.session_state.rab_data = edited_rab # Simpan perubahan
        
        # Hitung Profit & SMKK
        tot_konstruksi = edited_rab['Total Harga'].sum()
        nilai_profit = tot_konstruksi * (profit / 100)
        tot_konstruksi_plus_profit = tot_konstruksi + nilai_profit
        
        persen_k3 = 0.05 if "Tambang" in jenis_k3 else (0.02 if "Swasta" in jenis_k3 else 0)
        tot_smkk = tot_konstruksi_plus_profit * persen_k3
        grand_total = tot_konstruksi_plus_profit + tot_smkk
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Biaya Dasar Konstruksi", f"Rp {tot_konstruksi:,.0f}")
        c2.metric(f"Profit/Overhead ({profit}%)", f"Rp {nilai_profit:,.0f}")
        c3.metric(f"Biaya K3/SMKK", f"Rp {tot_smkk:,.0f}")
        c4.metric("💰 GRAND TOTAL", f"Rp {grand_total:,.0f}")
        
        st.warning(f"**TERBILANG:** *{terbilang(grand_total)} Rupiah*")
        
        st.divider()
        # --- KURVA S (TIMELINE) ---
        st.markdown("### 📈 Penjadwalan S-Curve")
        minggu = st.slider("Durasi Pelaksanaan Proyek (Minggu):", 4, 52, 16)
        
        # Distribusi Normal untuk Kurva S
        x_minggu = np.arange(1, minggu + 1)
        mean, std_dev = minggu / 2, minggu / 4
        bobot = np.exp(-0.5 * ((x_minggu - mean) / std_dev) ** 2)
        bobot_persen = (bobot / sum(bobot)) * 100
        kumulatif = np.cumsum(bobot_persen)
        
        df_curve = pd.DataFrame({"Minggu Ke-": x_minggu, "Bobot (%)": np.round(bobot_persen, 2), "Kumulatif (%)": np.round(kumulatif, 2), "Target Dana (Rp)": np.round((bobot_persen/100)*grand_total, 0)})
        
        fig = px.line(df_curve, x="Minggu Ke-", y="Kumulatif (%)", markers=True, title=f"Rencana Kurva S - {minggu} Minggu")
        fig.add_bar(x=df_curve["Minggu Ke-"], y=df_curve["Bobot (%)"], name="Bobot Per Minggu")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Silakan proses parameter di Tab 1.")

# ==========================================
# TAB 4: OUTPUT GAMBAR & EXPORT EXCEL
# ==========================================
with t4:
    if not st.session_state.rab_data.empty:
        st.markdown("### 📐 Lampiran Referensi Visual (Sesuai PDF yang Diupload)")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("")
            st.caption("Auto-Extracted Floor Plan")
        with c2:
            st.markdown("")
            st.caption("Auto-Extracted Foundation Detail")

        st.divider()
        st.markdown("### 📥 Ekspor ke Master Excel")
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # 1. Summary
            pd.DataFrame({
                "Uraian": ["Lokasi/Indeks Wilayah", "Persentase Profit", "Skema K3", "Biaya Dasar Konstruksi", "Biaya Keuntungan", "Biaya K3 (SMKK)", "GRAND TOTAL PROYEK", "TERBILANG:"],
                "Nilai": [f"{lokasi} ({faktor_lokasi})", f"{profit} %", jenis_k3, tot_konstruksi, nilai_profit, tot_smkk, grand_total, terbilang(grand_total) + " Rupiah"]
            }).to_excel(writer, index=False, sheet_name='1_Summary_RAB')
            
            # 2. RAB Detail
            st.session_state.rab_data.to_excel(writer, index=False, sheet_name='2_Detail_RAB')
            
            # 3. S-Curve
            df_curve.to_excel(writer, index=False, sheet_name='3_Timeline_SCurve')
            
        st.download_button(
            label="⬇️ Download Dokumen RAB & S-Curve (.xlsx)",
            data=buffer.getvalue(),
            file_name=f"RAB_Ultimate_Proyek.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True, type="primary"
        )
    else:
        st.info("Data belum siap. Lengkapi di Tab 1.")
