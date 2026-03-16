import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, classification_report
import xgboost as xgb
import pickle
import time

from src.features.feature_extractor import extract_features
from src.db_connect import get_connection

def load_data_from_db():
    """
    Loads all queries and labels from training_dataset table.
    """
    print("Loading data from database...")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT sample_query, label 
        FROM training_dataset 
        ORDER BY dataset_id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    print(f"✅ Loaded {len(rows)} queries from database")
    return rows

def build_feature_matrix(rows):
    """
    Extracts features from all queries and builds X, y matrices.
    """
    print("Extracting features from all queries...")
    X = []
    y = []
    failed = 0

    for i, (query, label) in enumerate(rows):
        if i % 5000 == 0:
            print(f"  Processing {i}/{len(rows)}...")
        try:
            features = extract_features(query)
            X.append(list(features.values()))
            y.append(1 if label else 0)
        except Exception as e:
            failed += 1

    print(f"✅ Features extracted. Failed: {failed}")
    return np.array(X), np.array(y)

def train_xgboost(X_train, X_test, y_train, y_test):
    """
    Trains XGBoost classifier and returns metrics.
    """
    print("\nTraining XGBoost...")
    start = time.time()
    
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        use_label_encoder=False,
        eval_metric='logloss',
        random_state=42
    )
    model.fit(X_train, y_train)
    
    latency = (time.time() - start) * 1000
    y_pred = model.predict(X_test)
    
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    
    print(f"✅ XGBoost Results:")
    print(f"   Accuracy:  {acc:.4f} ({acc*100:.2f}%)")
    print(f"   F1 Score:  {f1:.4f}")
    print(f"   Train time: {latency:.2f}ms")
    print(f"\nDetailed Report:")
    print(classification_report(y_test, y_pred, 
          target_names=['Safe', 'Malicious']))
    
    return model, acc, f1

def train_random_forest(X_train, X_test, y_train, y_test):
    """
    Trains Random Forest classifier and returns metrics.
    """
    print("\nTraining Random Forest...")
    start = time.time()
    
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    
    latency = (time.time() - start) * 1000
    y_pred = model.predict(X_test)
    
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    
    print(f"✅ Random Forest Results:")
    print(f"   Accuracy:  {acc:.4f} ({acc*100:.2f}%)")
    print(f"   F1 Score:  {f1:.4f}")
    print(f"   Train time: {latency:.2f}ms")
    print(f"\nDetailed Report:")
    print(classification_report(y_test, y_pred,
          target_names=['Safe', 'Malicious']))
    
    return model, acc, f1

def save_model(model, name):
    """
    Saves trained model to models/ folder.
    """
    path = f"models/{name}.pkl"
    with open(path, 'wb') as f:
        pickle.dump(model, f)
    print(f"✅ Model saved to {path}")

if __name__ == "__main__":
    # Load data
    rows = load_data_from_db()
    
    # Build feature matrix
    X, y = build_feature_matrix(rows)
    print(f"\nFeature matrix shape: {X.shape}")
    print(f"Label distribution: {np.bincount(y)}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\nTrain size: {len(X_train)}, Test size: {len(X_test)}")
    
    # Train models
    xgb_model, xgb_acc, xgb_f1 = train_xgboost(
        X_train, X_test, y_train, y_test
    )
    rf_model, rf_acc, rf_f1 = train_random_forest(
        X_train, X_test, y_train, y_test
    )
    
    # Save models
    save_model(xgb_model, 'xgboost_v1')
    save_model(rf_model, 'random_forest_v1')
    
    # Final comparison
    print("\n" + "=" * 60)
    print("MODEL COMPARISON:")
    print(f"{'Model':<20} {'Accuracy':<12} {'F1 Score'}")
    print("-" * 45)
    print(f"{'XGBoost':<20} {xgb_acc*100:.2f}%{'':<6} {xgb_f1:.4f}")
    print(f"{'Random Forest':<20} {rf_acc*100:.2f}%{'':<6} {rf_f1:.4f}")