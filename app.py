import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import pandas_ta as ta
from main import analizar_quantum, obtener_universo
import random

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="QUANTUM TERMINAL PRO", page_icon="📊", layout="wide")

# 2. ESTILO CSS: DARK PREMIUM
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #05070a; }
    [data-testid="stMetric"] {
        background-color: #0f111a;
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 15px;
    }
    [data-testid="stMetricValue"] { color: #38bdf8 !important; font-weight: 700; }
    .stButton>button {
        background: linear-gradient(90deg, #2563eb 0%, #3b82f6 100%);
        color: white;
        border-radius: 8px;
        border: none;
        padding: 12px;
        font-weight: 600;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- MOTOR DE GRÁFICAS ---
def mostrar_grafica_top(ticker):
    try:
        df = yf.Ticker(ticker).history(period="6mo")
        if df.empty: return st.error(f"No hay datos para {ticker}")
        
        df.index = df.index.tz_localize(None)
        df.ta.rsi(length=14, append=True)
        df.ta.macd(append=True)
        df.ta.stoch(append=True)
        
        stoch_k, stoch_d = "STOCHk_14_3_3", "STOCHd_14_3_3"

        fig = make_subplots(
            rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.05, 
            row_heights=[0.5, 0.15, 0.15, 0.15],
            subplot_titles=(f"PRECIO: {ticker}", "RSI", "MACD", "ESTOCÁSTICO")
        )

        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Precio"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI_14'], name="RSI", line=dict(color='#a78bfa', width=2)), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD_12_26_9'], name="MACD", line=dict(color='#38bdf8')), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df[stoch_k], name="%K", line=dict(color='#fbbf24')), row=4, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df[stoch_d], name="%D", line=dict(color='#ffffff', dash='dot')), row=4, col=1)
        
        fig.update_layout(height=800, template="plotly_dark", paper_bgcolor='#05070a', plot_bgcolor='#05070a', xaxis_rangeslider_visible=False, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error en visualización: {e}")

# --- INTERFAZ ---
st.sidebar.title("💎 QUANTUM OPS")
mercado = st.sidebar.radio("MERCADO:", ["México (BMV)", "EE.UU. (S&P 500)"])
cod_mercado = "MEX" if "México" in mercado else "EEUU"
menu = st.sidebar.selectbox("VISTA:", ["Explorador", "Radar"])

st.title(f"🚀 Quantum Terminal - {mercado}")

if menu == "Explorador":
    def_t = "WALMEX.MX" if cod_mercado == "MEX" else "NVDA"
    ticker = st.text_input("Ticker:", def_t).upper()
    
    if st.button("ANALIZAR"):
        res = analizar_quantum(ticker, silencioso=False)
        if res:
            c1, c2, c3, c4 = st.columns(4)
            # EXPLICACIONES AL PASAR EL CURSOR (HELP)
            c1.metric("Confianza IA", f"{res['IA_Prob']:.1%}", 
                      help="Probabilidad matemática de que el precio mantenga tendencia alcista basada en Z-Score.")
            c2.metric("Quantum Score", f"{int(res['Q_Score'])} pts", 
                      help="Q-Score: Puntaje de 0 a 100 que combina IA, Opinión de Analistas y Volumen. >70 es señal fuerte.")
            c3.metric("Consenso Analistas", f"{res['Analistas']}", 
                      help="Promedio de recomendación (1=Compra Fuerte, 5=Venta).")
            c4.metric("Volumen Relativo", f"{res['Vol_Rel']:.2f}x", 
                      help="Mide cuánto dinero está entrando hoy comparado con los últimos 20 días. >1.5 indica interés institucional.")
            
            mostrar_grafica_top(ticker)

elif menu == "Radar":
    if st.button("ESCANEAR"):
        with st.spinner("Escaneando..."):
            universo = obtener_universo(cod_mercado)
            resultados = []
            muestra = random.sample(universo, min(len(universo), 20))
            for t in muestra:
                r = analizar_quantum(t, silencioso=True)
                if r: resultados.append(r)
            st.session_state['radar_results'] = pd.DataFrame(resultados).sort_values(by='Q_Score', ascending=False)

    if 'radar_results' in st.session_state:
        df = st.session_state['radar_results']
        st.dataframe(df[['Ticker', 'Precio', 'IA_Prob', 'Q_Score', 'Vol_Rel']], 
                     column_config={
                         "Precio": st.column_config.NumberColumn(format="$%.2f"),
                         "IA_Prob": st.column_config.ProgressColumn("Confianza IA", format="%.1%", min_value=0, max_value=1, help="Probabilidad de éxito según el modelo."),
                         "Q_Score": st.column_config.NumberColumn("Q-Score", format="%d pts", help="Puntaje de confluencia total."),
                         "Vol_Rel": st.column_config.NumberColumn("Volumen", format="%.2fx", help="Intensidad de la operación actual.")
                     }, use_container_width=True, hide_index=True)
        
        sel = st.selectbox("Graficar:", df['Ticker'].tolist())
        if sel: mostrar_grafica_top(sel)