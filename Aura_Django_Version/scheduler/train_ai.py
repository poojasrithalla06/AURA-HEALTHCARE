import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

def train_model():
    # Generate Synthetic Medical Dataset
    # Features: Age, HeartRate, SystolicBP, BodyTemp, Steps
    # Target: 1 (High Risk), 0 (Low Risk)
    np.random.seed(42)
    data_size = 1000
    
    age = np.random.randint(20, 85, data_size)
    hr = np.random.randint(60, 110, data_size)
    sbp = np.random.randint(110, 180, data_size)
    temp = np.random.uniform(97.0, 103.0, data_size)
    steps = np.random.randint(1000, 15000, data_size)
    
    # Simple logic for risk score
    # High risk if age is old AND BP is high, or heart rate is very high/low
    risk = ((sbp > 140) & (age > 50)) | (hr > 100) | (temp > 101)
    target = risk.astype(int)
    
    df = pd.DataFrame({
        'age': age,
        'heart_rate': hr,
        'systolic_bp': sbp,
        'body_temp': temp,
        'steps': steps,
        'target': target
    })
    
    X = df.drop('target', axis=1)
    y = df['target']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    
    model = RandomForestClassifier(n_estimators=100)
    model.fit(X_train, y_train)
    
    # Ensure directory exists
    os.makedirs('scheduler/ml_models', exist_ok=True)
    joblib.dump(model, 'scheduler/ml_models/health_risk_model.pkl')
    print("Model trained and saved to scheduler/ml_models/health_risk_model.pkl")

if __name__ == "__main__":
    train_model()
