import yfinance as yf
import pandas as pd
import numpy as np
import warnings
import random
from indicators import calc_zscore, calc_market_context, calc_volatility
from model import train_zscore_model

warnings.filterwarnings('ignore')

def obtener_universo(mercado="EEUU"):
    """Obtiene tickers según el mercado seleccionado."""
    if mercado == "MEX":
        return [
            "WALMEX.MX", "AMXB.MX", "GFNORTEO.MX", "GMEXICOB.MX", "FEMSAUBD.MX", 
            "CEMEXCPO.MX", "TLEVISACPO.MX", "ASURB.MX", "GAPB.MX", "ALPEKA.MX",
            "BBAJIOO.MX", "AC.MX", "GRUMAB.MX", "PINFRA.MX", "OMAB.MX", "LABB.MX"
        ]
    else:
        try:
            sp500 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
            return [t.replace('.', '-') for t in sp500['Symbol'].tolist()]
        except:
            return ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META"]

def analizar_quantum(ticker, silencioso=True):
    """Analizador con fix de zona horaria y soporte para BMV."""
    try:
        t_obj = yf.Ticker(ticker)
        hist = t_obj.history(period="2y", interval="1d")
        spy = yf.download("SPY", period="2y", interval="1d", progress=False)
        
        if hist.empty or spy.empty: return None

        # Limpieza de zona horaria para evitar error de join
        hist.index = hist.index.tz_localize(None)
        spy.index = spy.index.tz_localize(None)
        
        # Sincronización de datos
        combined = pd.concat([hist['Close'], spy['Close']], axis=1, join='inner')
        combined.columns = ['Ticker_Close', 'SPY_Close']
        
        precio_hist = combined['Ticker_Close']
        precio_spy = combined['SPY_Close']
        
        # Datos Fundamentales
        info = t_obj.info
        rec_analistas = info.get('recommendationMean', 3.0)
        
        # Volumen Relativo
        vol_hoy = hist['Volume'].reindex(combined.index).iloc[-1]
        vol_prom = hist['Volume'].reindex(combined.index).iloc[-21:-1].mean()
        vol_rel = vol_hoy / vol_prom if vol_prom > 0 else 0
        
        # IA Quant
        df = pd.DataFrame(index=combined.index)
        df['Close'] = precio_hist
        df['Z_Score'] = calc_zscore(precio_hist)
        df['Relative_Strength'] = calc_market_context(precio_hist, precio_spy)
        df['Volatility'] = calc_volatility(precio_hist)
        df = df.dropna()

        model, scaler, acc = train_zscore_model(df)
        last_row = df.iloc[[-1]][['Z_Score', 'Relative_Strength', 'Volatility']]
        last_row_scaled = scaler.transform(last_row)
        prob = model.predict_proba(last_row_scaled)[0][1]

        # Puntaje Cuántico (0-100)
        score_q = (prob * 50) + ((5 - rec_analistas) * 10) + (min(vol_rel, 2) * 10)
        
        return {
            'Ticker': ticker,
            'Precio': round(float(precio_hist.iloc[-1]), 2),
            'IA_Prob': prob,
            'IA_Acc': acc,
            'Q_Score': round(score_q, 2),
            'Analistas': round(rec_analistas, 2),
            'Vol_Rel': vol_rel
        }
    except Exception as e:
        if not silencioso: print(f"Error en {ticker}: {e}")
        return None