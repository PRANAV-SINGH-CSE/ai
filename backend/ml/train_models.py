import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

# Create dummy user performance data
# Columns: accuracy, avg_time, attempts, difficulty_score -> label: is_weak (0 or 1)
def generate_synthetic_performance_data(n_samples=1000):
    np.random.seed(42)
    accuracy = np.random.uniform(0, 1, n_samples)
    avg_time = np.random.uniform(30, 300, n_samples)
    attempts = np.random.randint(1, 50, n_samples)
    difficulty_score = np.random.uniform(1, 5, n_samples)
    
    # Logic for is_weak
    # Weak if accuracy < 0.5 or (accuracy < 0.7 and avg_time > 200)
    is_weak = ((accuracy < 0.5) | ((accuracy < 0.7) & (avg_time > 180))).astype(int)
    
    df = pd.DataFrame({
        'accuracy': accuracy,
        'avg_time': avg_time,
        'attempts': attempts,
        'difficulty_score': difficulty_score,
        'is_weak': is_weak
    })
    return df

def train_weakness_model():
    print("Training Weakness Detection Model...")
    df = generate_synthetic_performance_data()
    X = df.drop('is_weak', axis=1)
    y = df['is_weak']
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    joblib.dump(model, 'backend/ml/weakness_model.pkl')
    print("Model saved to backend/ml/weakness_model.pkl")

def train_recommendation_model():
    print("Training Recommendation Model...")
    # This is a simplified version: Predict next difficulty level based on current stats
    # Columns: current_accuracy, current_avg_time -> label: recommended_difficulty (1-5)
    n_samples = 1000
    acc = np.random.uniform(0, 1, n_samples)
    time = np.random.uniform(30, 300, n_samples)
    
    # Target: 5 if acc > 0.9, 4 if acc > 0.7, 3 if acc > 0.5, 2 if acc > 0.3, else 1
    rec_diff = []
    for a in acc:
        if a > 0.85: rec_diff.append(5)
        elif a > 0.7: rec_diff.append(4)
        elif a > 0.5: rec_diff.append(3)
        elif a > 0.3: rec_diff.append(2)
        else: rec_diff.append(1)
        
    df = pd.DataFrame({
        'accuracy': acc,
        'avg_time': time,
        'recommended_difficulty': rec_diff
    })
    
    X = df.drop('recommended_difficulty', axis=1)
    y = df['recommended_difficulty']
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    joblib.dump(model, 'backend/ml/recommendation_model.pkl')
    print("Model saved to backend/ml/recommendation_model.pkl")

if __name__ == "__main__":
    if not os.path.exists('backend/ml'):
        os.makedirs('backend/ml')
    train_weakness_model()
    train_recommendation_model()
