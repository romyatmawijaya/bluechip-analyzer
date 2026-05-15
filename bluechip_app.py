import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Analisis Saham Bluechip", layout="wide")

saham_list = {
    "BBCA.JK": "Bank Central Asia",
    "BBRI.JK": "Bank Rakyat Indonesia",
    "BMRI.JK": "Bank Mandiri",
    "BBNI.JK": "Bank Negara Indonesia",
    "TLKM.JK": "Telkom Indonesia",
    "ASII.JK": "Astra International",
    "UNVR.JK": "Unilever Indonesia",
    "ICBP.JK": "Indofood CBP",
    "KLBF.JK": "Kalbe Farma",
    "INDF.JK": "Indofood Sukses Makmur",
    "SMGR.JK": "Semen Indonesia",
    "UNTR.JK": "United Tractors",
    "ADRO.JK": "Adaro Energy",
    "ANTM.JK": "Aneka Tambang",
    "MDKA.JK": "Merdeka Copper Gold"
}

periode_list = {
    "1mo": "1 Bulan",
    "3mo": "3 Bulan",
    "6mo": "6 Bulan",
    "1y": "1 Tahun",
    "2y": "2 Tahun"
}

def analisis_saham(symbol, period):
    try:
        data = yf.download(symbol, period=period, interval="1d", progress=False)
        if data.empty or len(data) < 50:
            return None

        harga_terakhir = data['Close'].iloc[-1].item()
        harga_awal = data['Close'].iloc[0].item()
        perubahan_periode = ((harga_terakhir - harga_awal) / harga_awal) * 100

        data['MA20'] = data['Close'].rolling(window=20).mean()
        data['MA50'] = data['Close'].rolling(window=50).mean()

        ma20 = data['MA20'].iloc[-1].item()
        ma50 = data['MA50'].iloc[-1].item()

        if harga_terakhir > ma20 and ma20 > ma50:
            rekomendasi = "BUY"
            warna = "green"
        elif harga_terakhir < ma20 and ma20 < ma50:
            rekomendasi = "SELL"
            warna = "red"
        else:
            rekomendasi = "HOLD"
            warna = "orange"

        return {
            "Saham": symbol.replace('.JK', ''),
            "Harga": f"Rp {harga_terakhir:,.0f}",
            "Perubahan": f"{perubahan_periode:+.2f}%",
            "Rekomendasi": rekomendasi,
            "Warna": warna
        }
    except:
        return None

st.title("📊 Analisis Saham Bluechip Indonesia")

tab1, tab2 = st.tabs(["Analisis Detail", "Scan Semua Saham"])

with tab1:
    st.write("Pilih saham dan periode untuk lihat grafik, harga, dan rekomendasi")

    col1, col2, col3 = st.columns([2, 1.5, 1])

    with col1:
        saham_pilih = st.selectbox(
            "Pilih Saham",
            options=list(saham_list.keys()),
            format_func=lambda x: f"{x.replace('.JK','')} - {saham_list[x]}"
        )

    with col2:
        periode_pilih = st.selectbox(
            "Pilih Periode",
            options=list(periode_list.keys()),
            format_func=lambda x: periode_list[x],
            index=3
        )

    with col3:
        st.write("")
        st.write("")
        tombol = st.button("Analisis", use_container_width=True, type="primary")

    if tombol:
        with st.spinner("Mengambil data..."):
            data = yf.download(saham_pilih, period=periode_pilih, interval="1d")

        if data.empty or len(data) < 50:
            st.error("
