import numpy as np
import pandas as pd

def calc_zscore(series, window=20):
    """Calcula cuántas desviaciones estándar se aleja el precio de su media móvil."""
    rolling_mean = series.rolling(window=window).mean()
    rolling_std = series.rolling(window=window).std()
    z_score = (series - rolling_mean) / rolling_std
    return z_score

def calc_market_context(ticker_price, spy_price):
    """Calcula la fuerza relativa de la acción frente al mercado (SPY)."""
    stock_ret = ticker_price.pct_change(5) # Retorno 1 semana
    spy_ret = spy_price.pct_change(5)
    relative_strength = stock_ret - spy_ret
    return relative_strength

def calc_volatility(series, window=10):
    """Calcula la volatilidad logarítmica (más estable para modelos)."""
    return np.log(series / series.shift(1)).rolling(window).std()