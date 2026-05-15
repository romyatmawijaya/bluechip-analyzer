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
    "2y": "2 Tahun"
}

st.title("📊 Analisis Saham Bluechip Indonesia")
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
    try:
        with st.spinner("Mengambil data..."):
            data = yf.download(saham_pilih, period=periode_pilih, interval="1d")

        if data.empty or len(data) < 50:
            st.error("Data tidak cukup untuk analisis. Coba pilih periode lebih panjang.")
        else:
            harga_terakhir = data['Close'].iloc[-1].item()
            harga_sebelumnya = data['Close'].iloc[-2].item()
            perubahan = harga_terakhir - harga_sebelumnya
            persen_perubahan = (perubahan / harga_sebelumnya) * 100

            # Hitung Moving Average
            data['MA20'] = data['Close'].rolling(window=20).mean()
            data['MA50'] = data['Close'].rolling(window=50).mean()

            ma20 = data['MA20'].iloc[-1].item()
            ma50 = data['MA50'].iloc[-1].item()

            # Logika rekomendasi
            if harga_terakhir > ma20 and ma20 > ma50:
                rekomendasi = "🟢 BUY"
                alasan = "Harga di atas MA20 dan MA20 di atas MA50. Trend naik kuat."
                warna = "green"
            elif harga_terakhir < ma20 and ma20 < ma50:
                rekomendasi = "🔴 SELL"
                alasan = "Harga di bawah MA20 dan MA20 di bawah MA50. Trend turun."
                warna = "red"
            else:
                rekomendasi = "🟡 HOLD"
                alasan = "Trend sideways/tidak jelas. Tunggu konfirmasi arah."
                warna = "orange"

            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.metric(
                    label="Harga Terakhir",
                    value=f"Rp {harga_terakhir:,.0f}",
                    delta=f"{perubahan:,.0f} ({persen_perubahan:.2f}%)"
                )
            with col_m2:
                st.markdown(f"### Rekomendasi: <span style='color:{warna}'>{rekomendasi}</span>", unsafe_allow_html=True)
                st.caption(alasan)

            # Grafik lengkap
            fig = go.Figure(data=[
                go.Candlestick(
                    x=data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'],
                    increasing_line_color='green',
                    decreasing_line_color='red',
                    name='Harga'
                ),
                go.Scatter(x=data.index, y=data['MA20'], line=dict(color='blue', width=1.5), name='MA 20'),
                go.Scatter(x=data.index, y=data['MA50'], line=dict(color='orange', width=1.5), name='MA 50')
            ])

            fig.update_layout(
                title=f"Grafik {saham_pilih.replace('.JK','')} - {periode_list[periode_pilih]}",
                xaxis_title="Tanggal",
                yaxis_title="Harga (Rp)",
                xaxis_rangeslider_visible=False,
                height=550,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )

            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Terjadi error: {e}")
