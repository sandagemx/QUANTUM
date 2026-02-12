from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score

def train_zscore_model(df):
    # Seleccionamos las columnas que creamos en indicators
    features = ['Z_Score', 'Relative_Strength', 'Volatility']
    X = df[features]
    
    # Target: ¿Subirá más del 2% en 10 días?
    y = (df['Close'].shift(-10) / df['Close'] > 1.02).astype(int)
    
    # Limpieza de NAs generados por los indicadores y el shift
    valid_idx = y.dropna().index
    X = X.loc[valid_idx].dropna()
    y = y.loc[X.index]

    # Split temporal (80% tren, 20% test)
    split = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    # Escalado
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Modelo RandomForest (Excelente para manejar Z-Scores)
    model = RandomForestClassifier(n_estimators=100, max_depth=4, random_state=42)
    model.fit(X_train_scaled, y_train)
    
    acc = accuracy_score(y_test, model.predict(X_test_scaled))
    return model, scaler, acc