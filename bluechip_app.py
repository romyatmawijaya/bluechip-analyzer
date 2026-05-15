import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Bluechip Stock Analyzer", layout="wide")

st.title("📊 Bluechip Stock Analyzer")
st.write("Cek performa saham bluechip Indonesia dengan cepat")

# List 15 saham bluechip paling liquid IDX
saham_list = {
    'BBCA.JK': 'Bank Central Asia',
    'BBRI.JK': 'Bank BRI',
    'BMRI.JK': 'Bank Mandiri',
    'BBNI.JK': 'Bank Negara Indonesia',
    'TLKM.JK': 'Telkom Indonesia',
    'GOTO.JK': 'GoTo Gojek Tokopedia',
    'UNVR.JK': 'Unilever Indonesia',
    'ICBP.JK': 'Indofood CBP',
    'INDF.JK': 'Indofood Sukses Makmur',
    'HMSP.JK': 'H.M. Sampoerna',
    'GGRM.JK': 'Gudang Garam',
    'ACES.JK': 'Ace Hardware Indonesia',
    'ASII.JK': 'Astra International',
    'ADRO.JK': 'Adaro Energy',
    'PGAS.JK': 'Perusahaan Gas Negara'
}

col1, col2 = st.columns(2)

with col1:
    saham_pilih = st.selectbox(
        "Pilih Saham",
        options=list(saham_list.keys()),
        format_func=lambda x: f"{x.replace('.JK','')} - {saham_list[x]}"
    )

with col2:
    periode = st.selectbox(
        "Periode",
        options=['1mo', '3mo', '6mo', '1y', '2y', '5y'],
        index=3
    )

if st.button("Analisis"):
    try:
        data = yf.download(saham_pilih, period=periode, progress=False)

        if data.empty:
            st.error("Data tidak ditemukan. Coba ganti saham atau periode.")
        else:
            st.subheader(f"Grafik Harga {saham_list[saham_pilih]}")

            fig = go.Figure(data=[go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close']
            )])

            fig.update_layout(xaxis_rangeslider_visible=False, height=500)
            st.plotly_chart(fig, use_container_width=True)

            # Tampilkan data terakhir
            harga_terakhir = data['Close'].iloc[-1]
            harga_sebelumnya = data['Close'].iloc[-2]
            perubahan = harga_terakhir - harga_sebelumnya
            persen_perubahan = (perubahan / harga_sebelumnya) * 100

            st.metric(
                label="Harga Terakhir",
                value=f"Rp {harga_terakhir:,.0f}",
                delta=f"{perubahan:,.0f} ({persen_perubahan:.2f}%)"
            )

    except Exception as e:
        st.error(f"Gagal ambil data: {e}")
