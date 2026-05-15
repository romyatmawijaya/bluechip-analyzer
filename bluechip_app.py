import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import subprocess

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

    if len(returns) == 0:
        return None, None

    avg_return = returns.mean().item()
    std_return = returns.std().item()

    if abs(avg_return) < 0.0001:
        return None, None

    target_decimal = target_persen / 100

    # Fix: Kalau target turun dan avg_return positif, pakai volatilitas sebagai estimasi
    if target_persen < 0 and avg_return > 0:
        if std_return > 0:
            estimasi_hari = abs(target_decimal) / std_return
            hari_min = estimasi_hari * 0.5
            hari_max = estimasi_hari * 2
            return int(estimasi_hari), (int(hari_min), int(hari_max))
        else:
            return None, None

    estimasi_hari = np.log(1 + target_decimal) / avg_return

    if estimasi_hari < 0 or estimasi_hari > 365:
        return None, None

    hari_min = np.log(1 + target_decimal) / (avg_return + std_return)
    hari_max = np.log(1 + target_decimal) / max(avg_return - std_return, 0.0001)

    return int(estimasi_hari), (int(hari_min), int(hari_max))

def get_berita_saham(nama_saham, ticker):
    try:
        query = f"{nama_saham} {ticker.replace('.JK','')} saham berita terbaru"
        result = subprocess.run([
            "python", "-c",
            f"import requests; from bs4 import BeautifulSoup; "
            f"r=requests.get('https://www.google.com/search?q={query}&tbm=nws', headers={{'User-Agent':'Mozilla/5.0'}}); "
            f"s=BeautifulSoup(r.text,'html.parser'); "
            f"items=[(a.get_text(),a['href']) for a in s.select('a[href^=\"/url?q=\"]')[:3]]; "
            f"print('\\n'.join([f'{{t}}|{{u}}' for t,u in items]))"
        ], capture_output=True, text=True, timeout=10)
        lines = result.stdout.strip().split('\n')
        berita = []
        for line in lines:
            if '|' in line:
                title, url = line.split('|', 1)
                if title and 'google' not in url:
                    berita.append({"judul": title, "url": url})
        return berita
    except:
        return []

def hitung_level_harga(data, rekomendasi):
    harga_terakhir = data['Close'].iloc[-1].item()
    ema20 = data['EMA20'].iloc[-1].item()
    ema50 = data['EMA50'].iloc[-1].item()
    support = data['Low'].rolling(20).min().iloc[-1].item()
    resistance = data['High'].rolling(20).max().iloc[-1].item()

    pot_buy = pot_sell = cut_loss = take_profit = None

    if rekomendasi == "HOLD" and ema20 < ema50:
        pot_buy = min(support * 1.02, ema20 * 0.98)
        cut_loss = support * 0.97
        take_profit = resistance * 0.98

    elif rekomendasi == "HOLD" and ema20 > ema50:
        pot_sell = max(resistance * 0.98, ema20 * 1.02)
        cut_loss = support * 0.97
        take_profit = harga_terakhir * 1.05

    elif rekomendasi == "SELL":
        pot_sell = harga_terakhir * 1.01
        cut_loss = harga_terakhir * 1.03
        take_profit = support * 0.98

    elif rekomendasi == "BUY":
        pot_buy = harga_terakhir
        cut_loss = support * 0.97
        take_profit = resistance * 0.98

    elif rekomendasi == "WASPADA":
        cut_loss = harga_terakhir * 0.95
        take_profit = harga_terakhir * 1.03

    return {
        "Pot_Buy": round(pot_buy) if pot_buy else None,
        "Pot_Sell": round(pot_sell) if pot_sell else None,
        "Cut_Loss": round(cut_loss) if cut_loss else None,
        "Take_Profit": round(take_profit) if take_profit else None
    }

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

        if harga_terakhir > ema20 and ema20 > ema50:
            if jarak_high >= 95 or rsi >= 70:
                rekomendasi = "WASPADA"
                alasan = f"Harga di atas EMA20 & EMA50, tapi RSI {rsi:.1f} overbought dan harga {jarak_high:.1f}% dari ATH. Risiko koreksi tinggi."
                warna = "orange"
            else:
                rekomendasi = "BUY"
                alasan = f"Harga Rp {harga_terakhir:,.0f} di atas EMA20. EMA20 {ema20:,.0f} > EMA50 {ema50:,.0f}. RSI {rsi:.1f} momentum naik sehat."
                warna = "green"
        elif harga_terakhir < ema20 and ema20 < ema50:
            rekomendasi = "SELL"
            alasan = f"Harga Rp {harga_terakhir:,.0f} di bawah EMA20. EMA20 {ema20:,.0f} < EMA50 {ema50:,.0f}. RSI {rsi:.1f} tekanan jual."
            warna = "red"
        else:
            rekomendasi = "HOLD"
            alasan = f"Harga Rp {harga_terakhir:,.0f} di area EMA20 {ema20:,.0f} dan EMA50 {ema50:,.0f}. RSI {rsi:.1f} pasar sideways."
            warna = "orange"

        levels = hitung_level_harga(data, rekomendasi)

        return {
            "Saham": symbol.replace('.JK', ''),
            "Harga": f"Rp {harga_terakhir:,.0f}",
            "Perubahan": f"{perubahan_periode:+.2f}%",
            "Volume": f"{volume_terakhir/1000000:.1f}jt",
            "RSI": f"{rsi:.1f}",
            "Rekomendasi": rekomendasi,
            "Alasan": alasan,
            "Warna": warna,
            **levels
        }
    except:
        return None

st.title("📊 Analisis Saham Bluechip Indonesia")

tab1, tab2 = st.tabs(["Analisis Detail", "Scan Semua Saham"])

with tab1:
    col1, col2, col3 = st.columns([2, 1.5, 1])
    with col1:
        saham_pilih = st.selectbox(
            "Pilih Saham",
            options=list(saham_list.keys()),
            format_func=lambda x: f"{x.replace('.JK','')} - {saham_list[x]}"
        )
    with col2:
        periode_pilih = st.selectbox(
            "Periode",
            options=list(periode_list.keys()),
            format_func=lambda x: periode_list[x],
            index=3
        )
    with col3:
        st.write("")
        st.write("")
        tombol = st.button("Analisis", use_container_width=True, type="primary")

    if tombol:
        with st.spinner("Mengambil data & berita..."):
            data = yf.download(saham_pilih, period=periode_pilih, interval="1d")
            berita = get_berita_saham(saham_list[saham_pilih], saham_pilih)

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

            if harga_terakhir > ema20 and ema20 > ema50:
                if jarak_high >= 95 or rsi >= 70:
                    rekomendasi = "⚠️ WASPADA"
                    alasan = f"Trend naik tapi RSI {rsi:.1f} overbought / harga {jarak_high:.1f}% dari ATH. Risiko koreksi."
                    warna = "orange"
                else:
                    rekomendasi = "🟢 BUY"
                    alasan = f"Harga di atas EMA20 & EMA50. EMA20 memotong EMA50 ke atas. RSI {rsi:.1f} belum overbought. Momentum bullish."
                    warna = "green"
            elif harga_terakhir < ema20 and ema20 < ema50:
                rekomendasi = "🔴 SELL"
                alasan = f"Harga di bawah EMA20 & EMA50. EMA20 memotong EMA50 ke bawah. RSI {rsi:.1f} menunjukkan tekanan jual."
                warna = "red"
            else:
                rekomendasi = "🟡 HOLD"
                alasan = f"Harga bergerak sideways di sekitar EMA20 {ema20:,.0f} dan EMA50 {ema50:,.0f}. RSI {rsi:.1f}. Tunggu konfirmasi arah."
                warna = "orange"

            levels = hitung_level_harga(data, rekomendasi.replace("🟢 ", "").replace("🔴 ", "").replace("⚠️ ", "").replace("🟡 ", ""))

            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.metric("Harga Terakhir", f"Rp {harga_terakhir:,.0f}", f"{perubahan_harian:,.0f} ({persen_harian:.2f}%)")
            with col_m2:
                st.metric("Perubahan Periode", f"{persen_periode:+.2f}%", f"Rp {perubahan_periode:,.0f}")
            with col_m3:
                st.metric("Volume", f"{volume_terakhir/1000000:.1f}jt", f"{(volume_terakhir/volume_rata):.1f}x rata2")
            with col_m4:
                st.metric("RSI 14", f"{rsi:.1f}", f"{'Overbought' if rsi >= 70 else 'Oversold' if rsi <= 30 else 'Netral'}")

            st.markdown("---")
            col_h1, col_h2 = st.columns(2)
            with col_h1:
                st.markdown("**📈 Harga Tertinggi 1 Tahun**")
                st.markdown(f"<h2 style='color:#00C853; margin:0;'>Rp {harga_tertinggi:,.0f}</h2>", unsafe_allow_html=True)
            with col_h2:
                st.markdown("**📉 Harga Terendah 1 Tahun**")
                st.markdown(f"<h2 style='color:#D32F2F; margin:0;'>Rp {harga_terendah:,.0f}</h2>", unsafe_allow_html=True)

            st.markdown(f"**Posisi Sekarang: {jarak_high:.1f}% dari ATH**")
            st.progress(min(jarak_high / 100, 1.0))

            if jarak_high >= 95:
                st.warning(f"Harga sudah dekat ATH. Hanya {100-jarak_high:.1f}% lagi ke Rp {harga_tertinggi:,.0f}")

            st.markdown(f"### Rekomendasi: <span style='color:{warna}'>{rekomendasi}</span>", unsafe_allow_html=True)

            with st.expander("📝 Lihat Alasan Lengkap", expanded=True):
                st.write(alasan)
                st.caption(f"EMA20: Rp {ema20:,.0f} | EMA50: Rp {ema50:,.0f}")

            if levels["Pot_Buy"] or levels["Pot_Sell"]:
                st.subheader("🎯 Level Harga")
                col_l1, col_l2, col_l3, col_l4 = st.columns(4)
                with col_l1:
                    if levels["Pot_Buy"]:
                        st.metric("Potential Buy", f"Rp {levels['Pot_Buy']:,.0f}")
                with col_l2:
                    if levels["Pot_Sell"]:
                        st.metric("Potential Sell", f"Rp {levels['Pot_Sell']:,.0f}")
                with col_l3:
                    if levels["Cut_Loss"]:
                        st.metric("Cut Loss", f"Rp {levels['Cut_Loss']:,.0f}", delta=f"{((levels['Cut_Loss']/harga_terakhir)-1)*100:.1f}%")
                with col_l4:
                    if levels["Take_Profit"]:
                        st.metric("Take Profit", f"Rp {levels['Take_Profit']:,.0f}", delta=f"{((levels['Take_Profit']/harga_terakhir)-1)*100:.1f}%")

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
                    if est_5_up: st.metric("Naik 5%", f"±{est_5_up} hari", f"{range_5_up[0]}-{range_5_up[1]} hari")
                    if est_10_up: st.metric("Naik 10%", f"±{est_10_up} hari", f"{range_10_up[0]}-{range_10_up[1]} hari")
                    if est_15_up: st.metric("Naik 15%", f"±{est_15_up} hari", f"{range_15_up[0]}-{range_15_up[1]} hari")
                with col_t2:
                    st.markdown("**Target Turun / Stop Loss**")
                    if est_5_down: st.metric("Turun 5%", f"±{est_5_down} hari", f"{range_5_down[0]}-{range_5_down[1]} hari")
                    if est_10_down: st.metric("Turun 10%", f"±{est_10_down} hari", f"{range_10_down[0]}-{range_10_down[1]} hari")
                    if est_15_down: st.metric("Turun 15%", f"±{est_15_down} hari", f"{range_15_down[0]}-{range_15_down[1]} hari")

            if berita:
                st.subheader("📰 Berita Terbaru")
                for b in berita:
                    st.markdown(f"- [{b['judul']}]({b['url']})")

            fig = go.Figure(data=[
                go.Candlestick(
                    x=data.index, open=data['Open'], high=data['High'],
                    low=data['Low'], close=data['Close'],
                    increasing_line_color='green', decreasing_line_color='red', name='Harga'
                ),
                go.Scatter(x=data.index, y=data['EMA20'], line=dict(color='blue', width=1.5), name='EMA 20'),
                go.Scatter(x=data.index, y=data['EMA50'], line=dict(color='orange', width=1.5), name='EMA 50'),
                go.Scatter(x=[data.index[0], data.index[-1]], y=[harga_tertinggi, harga_tertinggi],
                          line=dict(color='green', width=1, dash='dash'), name='High 1Y'),
                go.Scatter(x=[data.index[0], data.index[-1]], y=[harga_terendah, harga_terendah],
                          line=dict(color='red', width=1, dash='dash'), name='Low 1Y')
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
                st.dataframe(df_buy[['Saham', 'Harga', 'Perubahan', 'Volume', 'RSI', 'Pot_Buy', 'Cut_Loss', 'Take_Profit', 'Alasan']],
                            use_container_width=True, hide_index=True)
            else:
                st.info("Tidak ada saham BUY saat ini.")

            st.subheader("⚠️ WASPADA")
            df_waspada = df[df['Rekomendasi'] == 'WASPADA']
            if not df_waspada.empty:
                st.dataframe(df_waspada[['Saham', 'Harga', 'Perubahan', 'Volume', 'RSI', 'Cut_Loss', 'Take_Profit', 'Alasan']],
                            use_container_width=True, hide_index=True)

            st.subheader("🔴 SELL")
            df_sell = df[df['Rekomendasi'] == 'SELL']
            if not df_sell.empty:
                st.dataframe(df_sell[['Saham', 'Harga', 'Perubahan', 'Volume', 'RSI', 'Pot_Sell', 'Cut_Loss', 'Take_Profit', 'Alasan']],
                            use_container_width=True, hide_index=True)

            st.subheader("🟡 HOLD")
            df_hold = df[df['Rekomendasi'] == 'HOLD']
            if not df_hold.empty:
                st.dataframe(df_hold[['Saham', 'Harga', 'Perubahan', 'Volume', 'RSI', 'Pot_Buy', 'Pot_Sell', 'Cut_Loss', 'Take_Profit', 'Alasan']],
                            use_container_width=True, hide_index=True)

        progress_bar.empty()

st.caption("⚠️ Ini analisis teknikal sederhana. Bukan nasihat keuangan. Selalu cek fundamental & berita.")
