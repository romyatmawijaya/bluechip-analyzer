import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(page_title="Analisis Saham Bluechip", layout="wide")

saham_list = {
    "BBCA.JK": "Bank Central Asia",
    "BBRI.JK": "Bank Rakyat Indonesia",
    "BBNI.JK": "Bank Negara Indonesia",
    "BMRI.JK": "Bank Mandiri",
    "TLKM.JK": "Telkom Indonesia",
    "ASII.JK": "Astra International",
    "UNVR.JK": "Unilever Indonesia",
    "GOTO.JK": "GoTo Gojek Tokopedia"
}

periode_list = {
    "1mo": "1 Bulan",
    "3mo": "3 Bulan",
    "6mo": "6 Bulan",
    "1y": "1 Tahun",
    "2y": "2 Tahun",
    "5y": "5 Tahun",
    "max": "Semua Data"
}

st.title("📊 Analisis Saham Bluechip Indonesia")
st.write("Pilih saham dan periode untuk lihat grafik dan harga terakhir")

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
        index=0
    )

with col3:
    st.write("")
    st.write("")
    tombol = st.button("Analisis", use_container_width=True)

if tombol:
    try:
        with st.spinner("Mengambil data..."):
            data = yf.download(saham_pilih, period=periode_pilih, interval="1d")

        if data.empty:
            st.error("Data tidak ditemukan untuk saham ini.")
        else:
            harga_terakhir = data['Close'].iloc[-1].item()
            harga_sebelumnya = data['Close'].iloc[-2].item()
            perubahan = harga_terakhir - harga_sebelumnya
            persen_perubahan = (perubahan / harga_sebelumnya) * 100

            st.metric(
                label="Harga Terakhir",
                value=f"Rp {harga_terakhir:,.0f}",
                delta=f"{perubahan:,.0f} ({persen_perubahan:.2f}%)"
            )

            fig = go.Figure(data=[go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                increasing_line_color='green',
                decreasing_line_color='red'
            )])

            fig.update_layout(
                title=f"Grafik {saham_pilih.replace('.JK','')} - {periode_list[periode_pilih]}",
                xaxis_title="Tanggal",
                yaxis_title="Harga (Rp)",
                xaxis_rangeslider_visible=False,
                height=500
            )

            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Terjadi error: {e}")
