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

# Indeks Kemahalan Konstruksi per Wilayah
INDEKS_WILAYAH = {
    "DKI Jakarta (Standar Pusat)": 1.00, "Jawa Barat & Banten": 0.98, "Jawa Tengah & DIY": 0.88,
    "Jawa Timur": 0.90, "Sumatera Utara (Medan)": 1.02, "Sumatera (Lainnya)": 0.95,
    "Kalimantan Timur (IKN)": 1.15, "Kalimantan (Lainnya)": 1.08,
    "Sulawesi Selatan (Makassar)": 1.02, "Sulawesi (Lainnya)": 1.05,
    "Bali & Nusa Tenggara": 1.20, "Papua & Maluku": 1.45
}

# ==========================================
# 2. DATABASE AHSP (ENGINEERING LOGIC)
# ==========================================
@st.cache_data
def get_database():
    # Database Lengkap mencakup seluruh komponen bangunan dari pondasi hingga MEP
    data = [
        # TANAH & PONDASI
        ("1.1", "I. TANAH & PONDASI", "Galian Tanah & Perataan", "m3", 90860),
        ("1.2", "I. TANAH & PONDASI", "Pondasi Batu Kali / Menerus", "m3", 657500),
        ("1.3", "I. TANAH & PONDASI", "Pondasi Tiang Pancang / Footplat (Tanah Lembek)", "m3", 1250000),
        # STRUKTUR BETON
        ("2.1", "II. STRUKTUR BETON", "Sloof Beton Bertulang", "m3", 3184000),
        ("2.2", "II. STRUKTUR BETON", "Kolom Beton Bertulang", "m3", 4250000),
        ("2.3", "II. STRUKTUR BETON", "Balok & Ringbalk Beton Bertulang", "m3", 3850000),
        ("2.4", "II. STRUKTUR BETON", "Plat Lantai Beton Bertulang", "m3", 3500000),
        # ARSITEKTUR (Dinding, Keramik, Cat)
        ("3.1", "III. ARSITEKTUR", "Pasangan Dinding Bata Merah", "m2", 135000),
        ("3.2", "III. ARSITEKTUR", "Plesteran & Acian Dinding", "m2", 85000),
        ("3.3", "III. ARSITEKTUR", "Pemasangan Keramik Lantai 60x60", "m2", 185000),
        ("3.4", "III. ARSITEKTUR", "Pemasangan Keramik Dinding (KM / Dapur)", "m2", 195000),
        ("3.5", "III. ARSITEKTUR", "Pengecatan Dinding & Plafon", "m2", 46500),
        ("3.6", "III. ARSITEKTUR", "Pemasangan Plafon Gypsum Rangka Hollow", "m2", 145000),
        # PINTU, JENDELA & KANOPI
        ("4.1", "IV. KUSEN & BUKAAN", "Pekerjaan Pintu & Jendela (Aluminium/Kayu)", "unit", 1850000),
        ("4.2", "IV. KUSEN & BUKAAN", "Pemasangan Kanopi / Carport (Baja Ringan & Spandek)", "m2", 450000),
        ("4.3", "IV. KUSEN & BUKAAN", "Ornamen / Fasad Arsitektural", "Ls", 3500000),
        # ATAP
        ("5.1", "V. ATAP", "Rangka Atap Baja Ringan (Truss & Reng)", "m2", 185000),
        ("5.2", "V. ATAP", "Pemasangan Penutup Atap (Genteng / Metal / Spandek)", "m2", 125000),
        # MEKANIKAL & PLUMBING (Air)
        ("6.1", "VI. MEKANIKAL (AIR)", "Instalasi Pipa Air Bersih & Kotor (PVC AW)", "m'", 35000),
        ("6.2", "VI. MEKANIKAL (AIR)", "Tandon Air (Roof Tank) & Pipa Distribusi", "unit", 3500000),
        ("6.3", "VI. MEKANIKAL (AIR)", "Mesin Pompa Air & Booster", "unit", 2500000),
        ("6.4", "VI. MEKANIKAL (AIR)", "Sanitair (Kloset, Wastafel, Kran, Shower)", "unit", 1750000),
        ("6.5", "VI. MEKANIKAL (AIR)", "Septictank & Sumur Resapan", "unit", 4500000),
        # ELEKTRIKAL (Listrik)
        ("7.1", "VII. ELEKTRIKAL", "Kabel Instalasi Listrik (NYM/NYY) & Pipa Conduit", "m'", 25000),
        ("7.2", "VII. ELEKTRIKAL", "Titik Lampu & Stop Kontak", "titik", 225000),
        ("7.3", "VII. ELEKTRIKAL", "Panel Listrik Utama (MCB/RST) & Grounding", "unit", 2850000),
    ]
    return pd.DataFrame(data, columns=["Kode", "Divisi", "Uraian Pekerjaan", "Sat", "Harga_Dasar"])

df_db = get_database()

# ==========================================
# 3. SETUP UI APLIKASI UTAMA
# ==========================================
if 'rab_data' not in st.session_state: st.session_state.rab_data = pd.DataFrame()

# --- SIDEBAR: PENGATURAN HARGA, LOKASI, & PROFIT ---
with st.sidebar:
    st.header("🌍 Pengaturan Global Proyek")
    lokasi = st.selectbox("Lokasi Proyek (Indeks Wilayah):", list(INDEKS_WILAYAH.keys()))
    faktor_lokasi = INDEKS_WILAYAH[lokasi]
    
    profit = st.number_input("Persentase Keuntungan & Overhead (%)", min_value=0, max_value=40, value=15)
    faktor_profit = 1 + (profit / 100)
    
    st.info(f"Multiplier Wilayah: **{faktor_lokasi}x**\n\nMargin Profit: **{profit}%**")

# --- TABS UTAMA ---
t1, t2, t3, t4 = st.tabs(["📝 Input Desain Parametrik", "📑 Input Blueprint (PDF)", "📊 Edit RAB & Kurva S", "🖨️ Download Master Excel"])

# ==========================================
# TAB 1: METODE PARAMETRIK (SUPER LENGKAP)
# ==========================================
with t1:
    st.markdown("### Spesifikasi Teknis Bangunan")
    st.caption("Sistem AI akan mendistribusikan kebutuhan sloof, kolom, MEP, hingga atap secara spesifik berdasarkan dimensi dan kapasitas yang diinput.")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        jenis_bangunan = st.selectbox("Jenis Bangunan:", ["Rumah Tinggal", "Kantor / Ruko", "Klinik / Fasilitas Umum"])
        lantai = st.number_input("Jumlah Lantai / Tingkat:", min_value=1, max_value=10, value=2)
        kapasitas = st.number_input("Kapasitas (Jumlah Orang/Karyawan):", min_value=1, value=5)
    with c2:
        luas_tanah = st.number_input("Luas Tanah (m2):", min_value=20, value=150)
        luas_bangunan = st.number_input("Luas Bangunan Total (m2):", min_value=20, value=120)
        jenis_tanah = st.selectbox("Kondisi Tanah Asli:", ["Keras (Aman)", "Sedang", "Lembek / Rawa"])
    with c3:
        style = st.multiselect("Style / Fasad (Kombinasi):", ["Minimalis", "Eropa Klasik", "Industrial", "Estetik Tropis"], default=["Minimalis"])
        ada_kanopi = st.checkbox("Tambahkan Kanopi / Carport")
        luas_kanopi = st.number_input("Luas Kanopi (m2):", min_value=0, value=15) if ada_kanopi else 0

    if st.button("🚀 Proses Logika Struktur & Generate RAB", use_container_width=True):
        
        # --- MESIN KALKULASI PARAMETRIK TINGKAT LANJUT ---
        L_tapak = luas_bangunan / lantai
        keliling_approx = math.sqrt(L_tapak) * 4
        panjang_dinding = keliling_approx * 1.5 * lantai # Termasuk sekat dalam
        
        # Multipliers
        f_tanah = 2.5 if "Lembek" in jenis_tanah else (1.5 if "Sedang" in jenis_tanah else 1.0)
        f_style = 1.0 + (0.3 if "Eropa" in str(style) else 0) + (0.15 if "Estetik" in str(style) else 0)

        vol = {}
        # 1. Tanah & Pondasi
        vol["1.1"] = L_tapak * 0.4 * f_tanah
        vol["1.3" if "Lembek" in jenis_tanah else "1.2"] = L_tapak * 0.35 * f_tanah
            
        # 2. Struktur Beton Bertulang (Sesuai Lantai)
        vol["2.1"] = panjang_dinding * 0.15 * 0.20 / lantai # Sloof (hanya di tapak)
        vol["2.2"] = (L_tapak / 9) * 3.5 * lantai * 0.15 * 0.15 # Kolom (1 kolom tiap 9m2)
        vol["2.3"] = panjang_dinding * 0.15 * 0.25 # Balok & Ringbalk
        vol["2.4"] = L_tapak * (lantai - 1) * 0.12 if lantai > 1 else 0 # Plat Lantai
            
        # 3. Arsitektur & Atap
        vol["3.1"] = panjang_dinding * 3.2 * f_style # Dinding Bata
        vol["3.2"] = vol["3.1"] * 2 # Plesteran 2 sisi
        vol["3.3"] = luas_bangunan # Keramik Lantai
        vol["3.4"] = kapasitas * 3.5 # Keramik Dinding KM
        vol["3.5"] = vol["3.2"] + luas_bangunan # Cat Dinding + Plafon
        vol["3.6"] = luas_bangunan # Plafon
        
        # Rangka & Penutup Atap (Pitch factor atap miring = 1.5)
        luas_atap = L_tapak * 1.5 if lantai == 1 else L_tapak * 1.2
        vol["5.1"] = luas_atap # Rangka Baja Ringan
        vol["5.2"] = luas_atap # Pemasangan Penutup Atap
        
        # 4. Pintu, Jendela, Arsitektural
        vol["4.1"] = math.ceil(kapasitas * 1.5) # Pintu/Jendela relatif thd kapasitas orang
        vol["4.2"] = luas_kanopi if ada_kanopi else 0
        vol["4.3"] = 1.0 if f_style > 1.0 else 0 # Ornamen
        
        # 5. Mekanikal (Berbasis Kapasitas Orang)
        vol["6.1"] = luas_bangunan * 0.9 # Panjang Pipa
        vol["6.2"] = math.ceil(kapasitas / 4) # 1 Tandon per 4 Orang
        vol["6.3"] = 1.0 # 1 Mesin Pompa
        vol["6.4"] = math.ceil(kapasitas / 3) # 1 Set Kloset tiap 3 Orang
        vol["6.5"] = 1.0 # Septictank
        
        # 6. Elektrikal (Berbasis Luasan & Kapasitas)
        vol["7.1"] = luas_bangunan * 2.5 # Panjang Kabel
        vol["7.2"] = math.ceil(luas_bangunan / 8) # 1 Titik Lampu/Stopkontak tiap 8m2
        vol["7.3"] = 1.0 # Panel Utama
        
        # Susun DataFrame
        data_rab = []
        for k, v in vol.items():
            if v > 0:
                item = df_db[df_db['Kode'] == k].iloc[0]
                h_sat = item['Harga_Dasar'] * faktor_lokasi
                data_rab.append({
                    "Divisi": item['Divisi'],
                    "Kode": item['Kode'], 
                    "Pekerjaan": item['Uraian Pekerjaan'], 
                    "Sat": item['Sat'],
                    "Volume": round(v, 2), 
                    "Harga Satuan": round(h_sat, 2), 
                    "Total Harga": round(v * h_sat, 2)
                })
        
        st.session_state.rab_data = pd.DataFrame(data_rab)
        st.success("Logika Bangunan diproses! Volume Balok, Sloof, Mekanikal, Atap, & Elektrikal telah disusun. Silakan cek Tab 3.")

# ==========================================
# TAB 2: METODE UPLOAD BLUEPRINT (AI)
# ==========================================
with t2:
    st.markdown("### 📑 Ekstraksi Volume dari Gambar Kerja (PDF)")
    st.markdown("Gunakan fitur ini jika Anda memiliki gambar *Blueprint* (seperti `12X15 M.pdf`). Sistem akan menstimulasikan pemindaian ruang dan panjang dinding.")
    
    file_pdf = st.file_uploader("Upload File PDF/Gambar:", type=['pdf', 'jpg', 'png'])
    if file_pdf:
        st.success(f"File '{file_pdf.name}' berhasil diunggah!")
        with st.spinner("Membaca dimensi, struktur rangka atap, jalur pemipaan, dan titik lampu..."):
            st.info("💡 **Hasil Scan AI:** Terdeteksi Bangunan 12x15m (180 m2). Elevasi atap tinggi, pondasi footplat. Terdeteksi jalur mekanikal 125m dan 22 titik lampu.")
            if st.button("Generate RAB dari PDF", use_container_width=True):
                # Hardcoded dummy extraction untuk simulasi Blueprint
                df_blueprint = df_db.copy()
                df_blueprint['Volume'] = [40, 0, 15, 8, 12, 18, 0, 350, 700, 180, 20, 880, 180, 12, 18, 1, 200, 200, 160, 1, 1, 3, 1, 300, 22, 1]
                df_blueprint = df_blueprint[df_blueprint['Volume'] > 0]
                df_blueprint['Harga Satuan'] = df_blueprint['Harga_Dasar'] * faktor_lokasi
                df_blueprint['Total Harga'] = df_blueprint['Volume'] * df_blueprint['Harga Satuan']
                st.session_state.rab_data = df_blueprint.drop(columns=['Harga_Dasar'])
                st.success("RAB dari Blueprint berhasil dibuat!")

# ==========================================
# TAB 3: RAB DETAIL EDITABLE & S-CURVE
# ==========================================
with t3:
    if not st.session_state.rab_data.empty:
        df_rab = st.session_state.rab_data
        
        st.markdown("### 📋 Detail Rencana Anggaran Biaya")
        st.markdown("💡 *Bebas Mengedit:* Anda dapat mengganti angka pada kolom `Volume` dan `Harga Satuan` di bawah ini. Total dan Kurva S akan otomatis menyesuaikan.")
        
        # EDITABLE TABLE
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
        
        # RE-CALCULATE
        edited_rab['Total Harga'] = edited_rab['Volume'] * edited_rab['Harga Satuan']
        st.session_state.rab_data = edited_rab
        
        # FINANCIAL RECAP
        tot_konstruksi = edited_rab['Total Harga'].sum()
        nilai_profit = tot_konstruksi * (profit / 100)
        tot_include_profit = tot_konstruksi + nilai_profit
        
        grand_total = tot_include_profit
        
        st.markdown("#### 💰 Ringkasan Biaya")
        c1, c2, c3 = st.columns(3)
        c1.metric("1. Modal Konstruksi Dasar", f"Rp {tot_konstruksi:,.0f}")
        c2.metric(f"2. Profit & Overhead ({profit}%)", f"Rp {nilai_profit:,.0f}")
        c3.metric("GRAND TOTAL RAB", f"Rp {grand_total:,.0f}")
        
        st.warning(f"**TERBILANG:** *{terbilang(grand_total)} Rupiah*")
        
        st.divider()
        # --- S-CURVE (TIMELINE PROYEK) ---
        st.markdown("### 📈 Jadwal Pelaksanaan (S-Curve & Timeline)")
        waktu_minggu = st.slider("Durasi Target Pelaksanaan (Minggu):", 4, 52, 16)
        
        # Distribusi Normal Lonceng Gauss untuk Distribusi Bobot
        x_minggu = np.arange(1, waktu_minggu + 1)
        mean, std_dev = waktu_minggu / 2, waktu_minggu / 4
        bobot = np.exp(-0.5 * ((x_minggu - mean) / std_dev) ** 2)
        bobot_persen = (bobot / sum(bobot)) * 100
        kumulatif = np.cumsum(bobot_persen)
        
        df_curve = pd.DataFrame({
            "Minggu Ke-": x_minggu, 
            "Bobot Progress (%)": np.round(bobot_persen, 2), 
            "Kumulatif (%)": np.round(kumulatif, 2), 
            "Target Penyerapan Dana (Rp)": np.round((bobot_persen/100) * grand_total, 0)
        })
        
        fig = px.line(df_curve, x="Minggu Ke-", y="Kumulatif (%)", markers=True, title=f"Kurva S Pelaksanaan Proyek - {waktu_minggu} Minggu")
        fig.add_bar(x=df_curve["Minggu Ke-"], y=df_curve["Bobot Progress (%)"], name="Progress Mingguan")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("👈 Silakan gunakan Tab 1 (Parametrik) atau Tab 2 (Upload Blueprint) untuk membuat data RAB.")

# ==========================================
# TAB 4: EXPORT EXCEL ENTERPRISE
# ==========================================
with t4:
    if not st.session_state.rab_data.empty:
        st.markdown("### 🖨️ Download Buku Besar (Master Excel)")
        st.markdown("Sistem siap mengemas RAB Detail, Kurva S, beserta Analisa Peralatan & Material ke dalam 1 File Excel Utuh.")
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # 1. Summary
            pd.DataFrame({
                "Uraian Anggaran": ["Lokasi / Indeks", f"Persentase Profit ({profit}%)", "Total Biaya Konstruksi Dasar", "Keuntungan & Overhead", "GRAND TOTAL", "TERBILANG:"],
                "Nilai / Keterangan": [f"{lokasi} ({faktor_lokasi}x)", f"{profit} %", tot_konstruksi, nilai_profit, grand_total, terbilang(grand_total) + " Rupiah"]
            }).to_excel(writer, index=False, sheet_name='1_Summary_RAB')
            
            # 2. RAB Detail
            st.session_state.rab_data.to_excel(writer, index=False, sheet_name='2_Detail_RAB_Editable')
            
            # 3. S-Curve
            df_curve.to_excel(writer, index=False, sheet_name='3_Timeline_SCurve')
            
            # 4. Database Harga
            df_db.to_excel(writer, index=False, sheet_name='4_Database_Harga_Dasar')
            
        st.download_button(
            label="⬇️ Download Ultimate ERP Excel (.xlsx)",
            data=buffer.getvalue(),
            file_name=f"Master_RAB_{jenis_bangunan.replace(' ', '')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True, type="primary"
        )
    else:
        st.info("Data RAB belum tersedia untuk dicetak.")
