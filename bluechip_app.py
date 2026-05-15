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
    "2y": "2 Tahun",
    "3y": "3 Tahun",
    "5y": "5 Tahun",
    "6y": "6 Tahun"
}

def hitung_rsi(data, periode=14):
    delta = data['Close'].diff()
    gain = delta.clip(lower=0).rolling(window=periode).mean()
    loss = -delta.clip(upper=0).rolling(window=periode).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def hitung_estimasi_waktu(data, target_persen):
    returns = data['Close'].pct_change().dropna()
    if len(returns) == 0:
        return None, None
    avg_return = returns.mean().item()
    std_return = returns.std().item()
    if abs(avg_return) < 0.0001:
        return None, None
    target_decimal = target_persen / 100
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
            harga_terendah_2th = data['Low'].min().item()
            jarak_dari_low = ((harga_terakhir - harga_terendah_2th) / harga_terendah_2th) * 100
            if rsi <= 35 and jarak_dari_low <= 8:
                rekomendasi = "BUY"
                alasan = f"Oversold RSI {rsi:.1f} + harga cuma {jarak_dari_low:.1f}% di atas low 2 tahun Rp {harga_terendah_2th:,.0f}. Area akumulasi."
                warna = "green"
            else:
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
            "Ticker": symbol,
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
        # Pakai session_state biar bisa di-set dari tab scan
        if 'saham_pilih' not in st.session_state:
            st.session_state.saham_pilih = "BBCA.JK"

        saham_pilih = st.selectbox(
            "Pilih Saham",
            options=list(saham_list.keys()),
            format_func=lambda x: f"{x.replace('.JK','')} - {saham_list[x]}",
            key="saham_pilih"
        )
    with col2:
        periode_pilih = st.selectbox(
            "Periode",
            options=list(periode_list.keys()),
            format_func=lambda x: periode_list[x],
            index=7,
            key="periode_pilih"
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

            # Bandingin harga Des 2019, Feb 2020, Sekarang
            try:
                harga_des2019 = data.loc[:'2019-12-31']['Close'].iloc[-1].item()
                harga_feb2020 = data.loc[:'2020-02-29']['Close'].iloc[-1].item()
                persen_2019_ke_feb2020 = ((harga_feb2020 - harga_des2019) / harga_des2019) * 100
                persen_feb2020_ke_sekarang = ((harga_terakhir - harga_feb2020) / harga_feb2020) * 100
                persen_2019_ke_sekarang = ((harga_terakhir - harga_des2019) / harga_des2019) * 100

                col_p1, col_p2, col_p3 = st.columns(3)
                with col_p1:
                    st.metric("Des 2019", f"Rp {harga_des2019:,.0f}")
                with col_p2:
                    st.metric("Feb 2020", f"Rp {harga_feb2020:,.0f}", f"{persen_2019_ke_feb2020:+.1f}%")
                with col_p3:
                    st.metric("Sekarang", f"Rp {harga_terakhir:,.0f}", f"{persen_feb2020_ke_sekarang:+.1f}%")
                st.caption(f"Perubahan Des 2019 → Sekarang: {persen_2019_ke_sekarang:+.1f}%")
                st.markdown("---")
            except:
                pass

            if harga_terakhir > ema20 and ema20 > ema50:
                if jarak
