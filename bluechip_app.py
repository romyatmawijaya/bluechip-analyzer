import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np

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

def hitung_rsi(data, periode=14):
    delta = data['Close'].diff()
    gain = delta.clip(lower=0).rolling(window=periode).mean()
    loss = -delta.clip(upper=0).rolling(window=periode).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def hitung_estimasi_waktu(data, target_persen):
    """Estimasi hari untuk capai target berdasarkan return harian historis"""
    returns = data['Close'].pct_change().dropna()
    avg_return = returns.mean()
    std_return = returns.std()

    if abs(avg_return) < 0.0001:
        return None, None

    # Estimasi hari = ln(1+target) / avg_return
    target_decimal = target_persen / 100
    estimasi_hari = np.log(1 + target_decimal) / avg_return

    # Range +/- 1 std deviasi
    hari_min = np.log(1 + target_decimal) / (avg_return + std_return)
    hari_max = np.log(1 + target_decimal) / max(avg_return - std_return, 0.0001)

    if estimasi_hari < 0 or estimasi_hari > 365:
        return None, None

    return int(estimasi_hari), (int(hari_min), int(hari_max))

def analisis_saham(symbol, period):
    try:
        data = yf.download(symbol, period=period, interval="1d", progress=False)
        if data.empty or len(data) < 50:
            return None

        harga_terakhir = data['Close'].iloc[-1].item()
        harga_awal = data['Close'].iloc[0].item()
        harga_tertinggi = data['High'].max().item()
        volume_terakhir = data['Volume'].iloc[-1].item()
        volume_rata = data['Volume'].rolling(20).mean().iloc[-1].item()

        perubahan_periode = ((harga_terakhir - harga_awal) / harga_awal) * 100
        jarak_high = (harga_terakhir / harga_tertinggi) * 100

        data['EMA20'] = data['Close'].ewm(span=20, adjust=False).mean()
        data['EMA50'] = data['Close'].ewm(span=50, adjust=False).mean()
        data['RSI'] = hitung_rsi(data)

        ema20 = data['EMA20'].iloc[-1].item()
        ema50 = data['EMA50'].iloc[-1].item()
        rsi = data['RSI'].iloc[-1].item()

        # Hitung estimasi waktu
        est_5_up, range_5_up = hitung_estimasi_waktu(data, 5)
        est_10_up, range_10_up = hitung_estimasi_waktu(data, 10)
        est_15_up, range_15_up = hitung_estimasi_waktu(data, 15)
        est_5_down, range_5_down = hitung_estimasi_waktu(data, -5)
        est_10_down, range_10_down = hitung_estimasi_waktu(data, -10)
        est_15_down, range_15_down = hitung_estimasi_waktu(data, -15)

        if harga_terakhir > ema20 and ema20 > ema50:
            if jarak_high >= 95 or rsi >= 70:
                rekomendasi = "WASPADA"
                alasan = f"Trend naik tapi RSI {rsi:.1f} overbought / harga {jarak_high:.1f}% dari ATH."
                warna = "orange"
            else:
                rekomendasi = "BUY"
                alasan = f"Trend naik kuat. EMA20 > EMA50. RSI {rsi:.1f} masih sehat."
                warna = "green"
        elif harga_terakhir < ema20 and ema20 < ema50:
            rekomendasi = "SELL"
            alasan = f"Trend turun. EMA20 < EMA50. RSI {rsi:.1f}."
            warna = "red"
        else:
            rekomendasi = "HOLD"
            alasan = f"Trend sideways. RSI {rsi:.1f}."
            warna = "orange"

        return {
            "Saham": symbol.replace('.JK', ''),
            "Harga": f"Rp {harga_terakhir:,.0f}",
            "Perubahan": f"{perubahan_periode:+.2f}%",
            "Volume": f"{volume_terakhir/1000000:.1f}jt",
            "RSI": f"{rsi:.1f}",
            "Rekomendasi": rekomendasi,
            "Alasan": alasan,
            "Warna": warna,
            "Est_5_Up": est_5_up, "Range_5_Up": range_5_up,
            "Est_10_Up": est_10_up, "Range_10_Up": range_10_up,
            "Est_15_Up": est_15_up, "Range_15_Up": range_15_up,
            "Est_5_Down": est_5_down, "Range_5_Down": range_5_down,
            "Est_10_Down": est_10_down, "Range_10_Down": range_10_down,
            "Est_15_Down": est_15_down, "Range_15_Down": range_15_down
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
            st.error("Data tidak cukup untuk analisis. Coba pilih periode lebih panjang.")
        else:
            harga_terakhir = data['Close'].iloc[-1].item()
            harga_awal = data['Close'].iloc[0].item()
            harga_tertinggi = data['High'].max().item()
            harga_terendah = data['Low'].min().item()
            volume_terakhir = data['Volume'].iloc[-1].item()
            volume_rata = data['Volume'].rolling(20).mean().iloc[-1].item()

            perubahan_harian = harga_terakhir - data['Close'].iloc[-2].item()
            persen_harian = (perubahan_harian / data['Close'].iloc[-2].item()) * 100
            perubahan_periode = harga_terakhir - harga_awal
            persen_periode = (perubahan_periode / harga_awal) * 100
            jarak_high = (harga_terakhir / harga_tertinggi) * 100

            data['EMA20'] = data['Close'].ewm(span=20, adjust=False).mean()
            data['EMA50'] = data['Close'].ewm(span=50, adjust=False).mean()
            data['RSI'] = hitung_rsi(data)

            ema20 = data['EMA20'].iloc[-1].item()
            ema50 = data['EMA50'].iloc[-1].item()
            rsi = data['RSI'].iloc[-1].item()

            # Logika rekomendasi
            if harga_terakhir > ema20 and ema20 > ema50:
                if jarak_high >= 95 or rsi >= 70:
                    rekomendasi = "⚠️ WASPADA"
                    alasan = f"Trend naik tapi RSI {rsi:.1f} overbought / harga {jarak_high:.1f}% dari ATH. Risiko koreksi."
                    warna = "orange"
                else:
                    rekomendasi = "🟢 BUY"
                    alasan = f"Trend naik kuat. EMA20 > EMA50. RSI {rsi:.1f} masih sehat."
                    warna = "green"
            elif harga_terakhir < ema20 and ema20 < ema50:
                rekomendasi = "🔴 SELL"
                alasan = f"Trend turun. EMA20 < EMA50. RSI {rsi:.1f}."
                warna = "red"
            else:
                rekomendasi = "🟡 HOLD"
                alasan = f"Trend sideways. RSI {rsi:.1f}. Tunggu konfirmasi."
                warna = "orange"

            # Tampilkan metrik
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.metric("Harga Terakhir", f"Rp {harga_terakhir:,.0f}", f"{perubahan_harian:,.0f} ({persen_harian:.2f}%)")
            with col_m2:
                st.metric("Perubahan Periode", f"{persen_periode:+.2f}%", f"Rp {perubahan_periode:,.0f}")
            with col_m3:
                st.metric("Volume", f"{volume_terakhir/1000000:.1f}jt", f"{(volume_terakhir/volume_rata):.1f}x rata2 20 hari")
            with col_m4:
                st.metric("RSI 14", f"{rsi:.1f}", f"High: Rp {harga_tertinggi:,.0f}")

            st.markdown(f"### Rekomendasi: <span style='color:{warna}'>{rekomendasi}</span>", unsafe_allow_html=True)
            st.caption(alasan)

            # Estimasi waktu target naik & turun
            est_5_up, range_5_up = hitung_estimasi_waktu(data, 5)
            est_10_up, range_10_up = hitung_estimasi_waktu(data, 10)
            est_15_up, range_15_up = hitung_estimasi_waktu(data, 15)
            est_5_down, range_5_down = hitung_estimasi_waktu(data, -5)
            est_10_down, range_10_down = hitung_estimasi_waktu(data, -10)
            est_15_down, range_15_down = hitung_estimasi_waktu(data, -15)

            if est_5_up or est_5_down:
                st.subheader("📈 Estimasi Waktu Capai Target")

                col_t1, col_t2 = st.columns(2)

                with col_t1:
                    st.markdown("**Target Naik**")
                    if est_5_up:
                        st.metric("Naik 5%", f"±{est_5_up} hari", f"Range {range_5_up[0]}-{range_5_up[1]} hari")
                    if est_10_up:
                        st.metric("Naik 10%", f"±{est_10_up} hari", f"Range {range_10_up[0]}-{range_10_up[1]} hari")
                    if est_15_up:
                        st.metric("Naik 15%", f"±{est_15_up} hari", f"Range {range_15_up[0]}-{range_15_up[1]} hari")

                with col_t2:
                    st.markdown("**Target Turun / Stop Loss**")
                    if est_5_down:
                        st.metric("Turun 5%", f"±{est_5_down} hari", f"Range {range_5_down[0]}-{range_5_down[1]} hari")
                    if est_10_down:
                        st.metric("Turun 10%", f"±{est_10_down} hari", f"Range {range_10_down[0]}-{range_10_down[1]} hari")
                    if est_15_down:
                        st.metric("Turun 15%", f"±{est_15_down} hari", f"Range {range_15_down[0]}-{range_15_down[1]} hari")

                st.caption("Estimasi berdasarkan rata-rata return harian historis. Bukan jaminan. Pakai untuk manajemen risiko.")

            # Grafik
            fig = go.Figure(data=[
                go.Candlestick(
                    x=data.index, open=data['Open'], high=data['High'],
                    low=data['Low'], close=data['Close'],
                    increasing_line_color='green', decreasing_line_color='red', name='Harga'
                ),
                go.Scatter(x=data.index, y=data['EMA20'], line=dict(color='blue', width=1.5), name='EMA 20'),
                go.Scatter(x=data.index, y=data['EMA50'], line=dict(color='orange', width=1.5), name='EMA 50')
            ])
            fig.update_layout(
                title=f"Grafik {saham_pilih.replace('.JK','')} - {periode_list[periode_pilih]}",
                xaxis_title="Tanggal", yaxis_title="Harga (Rp)",
                xaxis_rangeslider_visible=False, height=550
            )
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.write("Scan otomatis 15 saham. Pilih periode untuk screening.")
    col1, col2 = st.columns([2, 1])
    with col1:
        periode_scan = st.selectbox(
            "Periode Screening",
            options=list(periode_list.keys()),
            format_func=lambda x: periode_list[x],
            index=3,
            key="scan_period"
        )

    if st.button("🔍 Scan Sekarang", use_container_width=True, type="primary"):
        hasil = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, symbol in enumerate(saham_list.keys()):
            status_text.text(f"Scanning {symbol.replace('.JK', '')}...")
            hasil_analisis = analisis_saham(symbol, periode_scan)
            if hasil_analisis:
                hasil.append(hasil_analisis)
            progress_bar.progress((i + 1) / len(saham_list))

        status_text.text("Selesai!")

        if hasil:
            df = pd.DataFrame(hasil)

            st.subheader("🟢 BUY")
            df_buy = df[df['Rekomendasi'] == 'BUY']
            if not df_buy.empty:
                st.dataframe(df_buy[['Saham', 'Harga', 'Perubahan', 'Volume', 'RSI']],
                            use_container_width=True, hide_index=True)
            else:
                st.info("Tidak ada saham BUY saat ini.")

            st.subheader("⚠️ WASPADA")
            df_waspada = df[df['Rekomendasi'] == 'WASPADA']
            if not df_waspada.empty:
                st.dataframe(df_waspada[['Saham', 'Harga', 'Perubahan', 'Volume', 'RSI']],
                            use_container_width=True, hide_index=True)

            st.subheader("🔴 SELL")
            df_sell = df[df['Rekomendasi'] == 'SELL']
            if not df_sell.empty:
                st.dataframe(df_sell[['Saham', 'Harga', 'Perubahan', 'Volume', 'RSI']],
                            use_container_width=True, hide_index=True)

        progress_bar.empty()

st.caption("⚠️ Ini analisis teknikal sederhana. Bukan nasihat keuangan. Selalu cek fundamental & berita.")
