import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import pickle
import time
import numpy as np
from src.features.feature_extractor import extract_features

# Load models once when module is imported
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../models')
print(f"Looking for models in: {BASE_DIR}")

def load_model(model_name):
    path = os.path.join(BASE_DIR, f"{model_name}.pkl")
    with open(path, 'rb') as f:
        return pickle.load(f)

# Load both models
xgb_model = load_model('xgboost_v1')
rf_model = load_model('random_forest_v1')

def predict(sql_query, model='xgboost'):
    """
    Takes a raw SQL query and returns prediction.
    
    Returns dict with:
    - is_malicious: True/False
    - confidence: 0.0 to 1.0
    - risk_level: LOW / MEDIUM / HIGH / CRITICAL
    - decision: ALLOW / BLOCK
    - latency_ms: inference time
    - features: extracted features
    """
    start = time.time()
    
    # Step 1 — Extract features
    features = extract_features(sql_query)
    feature_vector = np.array(list(features.values())).reshape(1, -1)
    
    # Step 2 — Run model
    if model == 'xgboost':
        m = xgb_model
    else:
        m = rf_model
    
    prediction = m.predict(feature_vector)[0]
    confidence = float(m.predict_proba(feature_vector)[0][prediction])
    
    # Step 3 — Calculate latency
    latency_ms = round((time.time() - start) * 1000, 3)
    
    # Step 4 — Determine risk level
    is_malicious = bool(prediction == 1)
    if not is_malicious:
        risk_level = "LOW"
    elif confidence < 0.7:
        risk_level = "MEDIUM"
    elif confidence < 0.9:
        risk_level = "HIGH"
    else:
        risk_level = "CRITICAL"
    
    decision = "BLOCK" if is_malicious else "ALLOW"
    
    return {
        "query": sql_query,
        "is_malicious": is_malicious,
        "confidence": round(confidence, 4),
        "risk_level": risk_level,
        "decision": decision,
        "latency_ms": latency_ms,
        "features": features
    }

def test_inference():
    queries = [
        ("SAFE", "SELECT * FROM users WHERE username = 'alice'"),
        ("SAFE", "SELECT id, email FROM customers WHERE id = 42"),
        ("MALICIOUS", "SELECT * FROM users WHERE username = '' OR '1'='1'"),
        ("MALICIOUS", "SELECT id FROM users UNION SELECT id FROM admin"),
        ("MALICIOUS", "SELECT * FROM users; DROP TABLE users;"),
        ("MALICIOUS", "SELECT * FROM users WHERE id = 1 OR 1=1"),
    ]
    
    print("=" * 70)
    print("SQLGUARD INFERENCE ENGINE TEST")
    print("=" * 70)
    
    correct = 0
    for true_label, query in queries:
        result = predict(query)
        predicted = "MALICIOUS" if result['is_malicious'] else "SAFE"
        is_correct = predicted == true_label
        if is_correct:
            correct += 1
        
        status = "✅" if is_correct else "❌"
        print(f"\n{status} {true_label} → predicted: {predicted}")
        print(f"   Query: {query[:60]}...")
        print(f"   Confidence: {result['confidence']*100:.1f}%")
        print(f"   Risk Level: {result['risk_level']}")
        print(f"   Decision: {result['decision']}")
        print(f"   Latency: {result['latency_ms']}ms")
    
    print("\n" + "=" * 70)
    print(f"Correct: {correct}/{len(queries)} ({correct/len(queries)*100:.1f}%)")
    print("=" * 70)

if __name__ == "__main__":
    test_inference()