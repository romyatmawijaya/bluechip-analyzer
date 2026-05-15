import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Saham Scanner v2", layout="wide")
st.title("📊 Scanner Saham BUY & SELL v2")
st.caption("Mode Longgar - biar ada hasil buat test kolom baru")

DAFTAR_SAHAM = [
    "BBCA.JK", "BBRI.JK", "BMRI.JK", "TLKM.JK", "ASII.JK",
    "UNVR.JK", "ICBP.JK", "KLBF.JK", "INDF.JK", "GOTO.JK"
]

periode_list = {"1 Bulan": "1mo", "3 Bulan": "3mo", "6 Bulan": "6mo", "1 Tahun": "1y"}
periode_scan = st.selectbox("Pilih Periode Data", list(periode_list.keys()), index=2)

@st.cache_data
def cek_saham(ticker, periode):
    try:
        saham = yf.Ticker(ticker)
        hist = saham.history(period=periode, interval="1d")
        if len(hist) < 30:
            return None
        
        harga = hist['Close'].iloc[-1]
        support = hist['Low'].rolling(20).min().iloc[-1]
        resistance = hist['High'].rolling(20).max().iloc[-1]
        sma20 = hist['Close'].rolling(20).mean()
        sma50 = hist['Close'].rolling(50).mean()
        avg_vol = hist['Volume'].rolling(20).mean().iloc[-1]
        vol = hist['Volume'].iloc[-1]
        
        # Hitung ATR buat estimasi
        high_low = hist['High'] - hist['Low']
        high_close = np.abs(hist['High'] - hist['Close'].shift())
        low_close = np.abs(hist['Low'] - hist['Close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(14).mean().iloc[-1]
        avg_move_pct = (atr / harga) * 100 if harga > 0 else 1
        
        # Estimasi hari
        estimasi_normal = max(1, int(round(2 / avg_move_pct)))
        estimasi_minus5 = max(1, int(round(5 / avg_move_pct)))
        estimasi_minus10 = max(1, int(round(10 / avg_move_pct)))
        
        # KRITERIA LONGGAR - biar gampang ada hasil
        # Cukup harga > sma20 dan volume naik 1.2x
        if (harga > sma20.iloc[-1] and vol > avg_vol * 1.2):
            return {
                "Saham": ticker.replace(".JK", ""),
                "Harga": round(harga, 2),
                "TP": round(resistance, 2),
                "SL": round(support, 2),
                "Potensial Buy": round(harga, 2),
                "Buy -5%": round(harga * 0.95, 2),
                "Buy -10%": round(harga * 0.90, 2),
                "Est TP": f"{estimasi_normal}h",
                "Est -5%": f"{estimasi_minus5}h",
                "Est -10%": f"{estimasi_minus10}h"
            }
        
        # KRITERIA SELL LONGGAR
        elif (harga < sma20.iloc[-1] and vol > avg_vol * 1.2):
            return {
                "Saham": ticker.replace(".JK", ""),
                "Harga": round(harga, 2),
                "TP": round(support, 2),
                "SL": round(resistance, 2),
                "Potensial Buy": "-",
                "Buy -5%": "-",
                "Buy -10%": "-",
                "Est TP": "-",
                "Est -5%": "-",
                "Est -10%": "-"
            }
    except Exception as e:
        return None
    return None

if st.button("🔍 Scan Sekarang"):
    with st.spinner("Scan saham..."):
        hasil = []
        for saham in DAFTAR_SAHAM:
            data = cek_saham(saham, periode_list[periode_scan])
            if data:
                hasil.append(data)
        
        if hasil:
            df = pd.DataFrame(hasil)
            df_buy = df[df['Potensial Buy'] != "-"]
            df_sell = df[df['Potensial Buy'] == "-"]
            
            if not df_buy.empty:
                st.subheader("🟢 Rekomendasi BUY")
                st.dataframe(df_buy, use_container_width=True)
            
            if not df_sell.empty:
                st.subheader("🔴 Rekomendasi SELL")
                st.dataframe(df_sell, use_container_width=True)
        else:
            st.warning("Masih kosong. Coba ganti periode ke 1 Bulan atau tambah saham di DAFTAR_SAHAM")

st.markdown("---")
st.caption("Catatan: Ini mode longgar buat test. Jangan dipake buat trading beneran ya.")
