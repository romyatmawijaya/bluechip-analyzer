import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Bluechip Stock Analyzer", layout="wide")

st.title("📊 Bluechip Stock Analyzer")
st.write("Cek performa saham bluechip Indonesia + sinyal teknikal sederhana")

saham_list = {
    "BBCA": "Bank Central Asia",
    "BBRI": "Bank Rakyat Indonesia",
    "BMRI": "Bank Mandiri",
    "TLKM": "Telkom Indonesia",
    "ASII": "Astra International"
}

def hitung_rsi(data, periode=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periode).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periode).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_signal(data):
    ma50 = data['MA50'].iloc[-1]
    ma200 = data['MA200'].iloc[-1]
    rsi = data['RSI'].iloc[-1]
    close = data['Close'].iloc[-1]

    signal = "HOLD"
    alasan = []

    if ma50 > ma200 and close > ma50:
        signal = "BUY"
        alasan.append("Golden Cross: MA50 di atas MA200 dan harga di atas MA50")
    elif ma50 < ma200 and close < ma50:
        signal = "SELL"
        alasan.append("Death Cross: MA50 di bawah MA200 dan harga di bawah MA50")

    if rsi > 70:
        alasan.append(f"RSI {rsi:.1f}: Overbought, waspada koreksi")
    elif rsi < 30:
        alasan.append(f"RSI {rsi:.1f}: Oversold, potensi rebound")
    else:
        alasan.append(f"RSI {rsi:.1f}: Netral")

    return signal, " | ".join(alasan)

mode = st.radio("Mode:", ["Analisis 1 Saham", "Bandingin Saham"])
periode = st.selectbox("Periode:", ["3mo", "6mo", "1y", "2y", "5y"], index=2)

if mode == "Analisis 1 Saham":
    saham_pilih = st.selectbox("Pilih Saham:", list(saham_list.keys()),
                               format_func=lambda x: f"{x} - {saham_list[x]}")

    if st.button("Analisis"):
        with st.spinner("Ambil data..."):
            ticker = yf.Ticker(saham_pilih + ".JK")
            data = ticker.history(period=periode)

            if len(data) < 200:
                st.error("Data kurang dari 200 hari. Pilih periode 1y atau lebih.")
            else:
                data['MA50'] = data['Close'].rolling(window=50).mean()
                data['MA200'] = data['Close'].rolling(window=200).mean()
                data['RSI'] = hitung_rsi(data)

                signal, alasan = get_signal(data)

                st.subheader(f"{saham_pilih} - {saham_list[saham_pilih]}")

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Harga Sekarang", f"Rp {data['Close'].iloc[-1]:,.0f}")
                col2.metric("MA50", f"Rp {data['MA50'].iloc[-1]:,.0f}")
                col3.metric("MA200", f"Rp {data['MA200'].iloc[-1]:,.0f}")
                col4.metric("RSI", f"{data['RSI'].iloc[-1]:.1f}")

                if signal == "BUY":
                    st.success(f"**Sinyal: BUY**")
                elif signal == "SELL":
                    st.error(f"**Sinyal: SELL**")
                else:
                    st.info(f"**Sinyal: HOLD**")

                st.write(f"**Alasan:** {alasan}")

                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'],
                                             low=data['Low'], close=data['Close'], name='Harga'))
                fig.add_trace(go.Scatter(x=data.index, y=data['MA50'], line=dict(color='orange', width=1), name='MA50'))
                fig.add_trace(go.Scatter(x=data.index, y=data['MA200'], line=dict(color='purple', width=1), name='MA200'))
                fig.update_layout(title=f"Grafik {saham_pilih} + MA", xaxis_rangeslider_visible=False, height=500)
                st.plotly_chart(fig, use_container_width=True)

else:
    saham_banding = st.multiselect("Pilih 2-4 Saham:", list(saham_list.keys()), max_selections=4,
                                   format_func=lambda x: f"{x} - {saham_list[x]}")

    if st.button("Bandingin") and len(saham_banding) >= 2:
        with st.spinner("Ambil data..."):
            fig = go.Figure()
            for saham in saham_banding:
                ticker = yf.Ticker(saham + ".JK")
                data = ticker.history(period=periode)
                normalized = (data['Close'] / data['Close'].iloc[0]) * 100
                fig.add_trace(go.Scatter(x=data.index, y=normalized, name=saham))

            fig.update_layout(title="Perbandingan Performa Saham", yaxis_title="Index 100 = Harga Awal")
            st.plotly_chart(fig, use_container_width=True)

st.write("---")
st.caption("Sinyal berdasarkan MA Crossover & RSI. Ini bukan saran investasi. DYOR.")