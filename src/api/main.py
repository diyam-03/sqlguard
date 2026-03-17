from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.ml.inference import predict
from src.db_connect import get_connection
import psycopg2.extras
from datetime import datetime

app = FastAPI(
    title="SQLGuard API",
    description="DBMS-Native SQL Injection Detection System",
    version="1.0.0"
)

# Allow React frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── PYDANTIC MODELS ───

class QueryInput(BaseModel):
    sql_query: str
    user_id: Optional[int] = 1
    session_id: Optional[str] = "default"

class UserCreate(BaseModel):
    username: str
    role: Optional[str] = "viewer"
    ip_address: Optional[str] = None

class UserUpdate(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class AlertUpdate(BaseModel):
    resolved: bool
    notes: Optional[str] = None

# ─── ROOT ───

@app.get("/")
def root():
    return {
        "system": "SQLGuard",
        "version": "1.0.0",
        "status": "running",
        "description": "DBMS-Native SQL Injection Detection System"
    }

# ─── DETECTION ENDPOINT ───

@app.post("/detect")
def detect_injection(query_input: QueryInput):
    """
    Main detection endpoint.
    Submits a SQL query for injection analysis.
    Returns verdict, confidence, risk level and latency.
    """
    result = predict(query_input.sql_query)
    
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # Save raw query
        cur.execute("""
            INSERT INTO raw_query 
            (user_id, raw_sql_text, query_type, session_id, db_name)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING query_id
        """, (
            query_input.user_id,
            query_input.sql_query,
            query_input.sql_query.strip().split()[0].upper(),
            query_input.session_id,
            "sqlguard_db"
        ))
        query_id = cur.fetchone()[0]

        # Save features
        features = result['features']
        cur.execute("""
            INSERT INTO ast_features
            (query_id, tree_depth, node_count, or_branch_count,
             tautology_score, keyword_density, union_select_flag,
             comment_inject_flag, stacked_query_flag, feature_vector)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING feature_id
        """, (
            query_id,
            features.get('total_token_count', 0),
            features.get('sql_keyword_count', 0),
            features.get('or_branch_count', 0),
            features.get('tautology_score', 0),
            features.get('keyword_density', 0),
            bool(features.get('union_select_flag', 0)),
            bool(features.get('comment_inject_flag', 0)),
            bool(features.get('stacked_query_flag', 0)),
            psycopg2.extras.Json(features)
        ))
        feature_id = cur.fetchone()[0]

        # Save prediction
        cur.execute("""
            INSERT INTO ml_prediction
            (feature_id, model_id, is_malicious, confidence_score,
             risk_level, decision, latency_ms)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING prediction_id
        """, (
            feature_id,
            1,
            result['is_malicious'],
            result['confidence'],
            result['risk_level'],
            result['decision'],
            result['latency_ms']
        ))
        prediction_id = cur.fetchone()[0]

        # Save alert if malicious
        if result['is_malicious']:
            cur.execute("""
                INSERT INTO alert_log
                (prediction_id, user_id, alert_type, severity)
                VALUES (%s, %s, %s, %s)
            """, (
                prediction_id,
                query_input.user_id,
                result.get('risk_level', 'HIGH'),
                result.get('risk_level', 'HIGH')
            ))

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

    return {
        "query_id": query_id,
        "prediction_id": prediction_id,
        "query": query_input.sql_query,
        "is_malicious": result['is_malicious'],
        "confidence": result['confidence'],
        "risk_level": result['risk_level'],
        "decision": result['decision'],
        "latency_ms": result['latency_ms']
    }

# ─── QUERIES CRUD ───

@app.get("/queries")
def get_queries(limit: int = 50, offset: int = 0):
    """Get all queries with pagination."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT r.*, p.is_malicious, p.confidence_score, 
               p.risk_level, p.decision
        FROM raw_query r
        LEFT JOIN ast_features f ON r.query_id = f.query_id
        LEFT JOIN ml_prediction p ON f.feature_id = p.feature_id
        ORDER BY r.timestamp DESC
        LIMIT %s OFFSET %s
    """, (limit, offset))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {"queries": [dict(r) for r in rows], "total": len(rows)}

@app.get("/queries/{query_id}")
def get_query(query_id: int):
    """Get a specific query by ID."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT r.*, p.is_malicious, p.confidence_score,
               p.risk_level, p.decision, f.feature_vector
        FROM raw_query r
        LEFT JOIN ast_features f ON r.query_id = f.query_id
        LEFT JOIN ml_prediction p ON f.feature_id = p.feature_id
        WHERE r.query_id = %s
    """, (query_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Query not found")
    return dict(row)

@app.put("/queries/{query_id}")
def update_query(query_id: int, session_id: str):
    """Update query session ID."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE raw_query SET session_id = %s WHERE query_id = %s
    """, (session_id, query_id))
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Query updated", "query_id": query_id}

@app.delete("/queries/{query_id}")
def delete_query(query_id: int):
    """Delete a query record."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM raw_query WHERE query_id = %s", (query_id,))
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Query deleted", "query_id": query_id}

# ─── USERS CRUD ───

@app.post("/users")
def create_user(user: UserCreate):
    """Create a new user."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (username, role, ip_address)
        VALUES (%s, %s, %s)
        RETURNING user_id
    """, (user.username, user.role, user.ip_address))
    user_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "User created", "user_id": user_id}

@app.get("/users")
def get_users():
    """Get all users."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM users ORDER BY created_at DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {"users": [dict(r) for r in rows]}

@app.get("/users/{user_id}")
def get_user(user_id: int):
    """Get a specific user."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(row)

@app.put("/users/{user_id}")
def update_user(user_id: int, user: UserUpdate):
    """Update a user."""
    conn = get_connection()
    cur = conn.cursor()
    if user.username:
        cur.execute(
            "UPDATE users SET username = %s WHERE user_id = %s",
            (user.username, user_id)
        )
    if user.role:
        cur.execute(
            "UPDATE users SET role = %s WHERE user_id = %s",
            (user.role, user_id)
        )
    if user.is_active is not None:
        cur.execute(
            "UPDATE users SET is_active = %s WHERE user_id = %s",
            (user.is_active, user_id)
        )
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "User updated", "user_id": user_id}

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    """Delete a user."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "User deleted", "user_id": user_id}

# ─── ALERTS ───

@app.get("/alerts")
def get_alerts(limit: int = 50):
    """Get all alerts."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT a.*, r.raw_sql_text, p.confidence_score, p.risk_level
        FROM alert_log a
        JOIN ml_prediction p ON a.prediction_id = p.prediction_id
        JOIN ast_features f ON p.feature_id = f.feature_id
        JOIN raw_query r ON f.query_id = r.query_id
        ORDER BY a.alert_id DESC
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {"alerts": [dict(r) for r in rows]}

@app.put("/alerts/{alert_id}")
def resolve_alert(alert_id: int, update: AlertUpdate):
    """Resolve an alert."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE alert_log 
        SET notified_admin = %s, resolved_at = NOW(), notes = %s
        WHERE alert_id = %s
    """, (update.resolved, update.notes, alert_id))
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Alert updated", "alert_id": alert_id}

# ─── STATS FOR DASHBOARD ───

@app.get("/stats")
def get_stats():
    """Dashboard statistics."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM raw_query")
    total_queries = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*) FROM ml_prediction WHERE is_malicious = true
    """)
    total_blocked = cur.fetchone()[0]

    cur.execute("""
        SELECT AVG(confidence_score) FROM ml_prediction 
        WHERE is_malicious = true
    """)
    avg_confidence = cur.fetchone()[0] or 0

    cur.execute("""
        SELECT AVG(latency_ms) FROM ml_prediction
    """)
    avg_latency = cur.fetchone()[0] or 0

    cur.close()
    conn.close()

    return {
        "total_queries": total_queries,
        "total_blocked": total_blocked,
        "total_allowed": total_queries - total_blocked,
        "block_rate": round(total_blocked / max(total_queries, 1) * 100, 2),
        "avg_confidence": round(float(avg_confidence) * 100, 2),
        "avg_latency_ms": round(float(avg_latency), 3)
    }

@app.get("/stats/trends")
def get_trends():
    """Attack trends over time for line chart."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT 
            DATE(r.timestamp) as date,
            COUNT(*) as total_queries,
            SUM(CASE WHEN p.is_malicious THEN 1 ELSE 0 END) as blocked
        FROM raw_query r
        LEFT JOIN ast_features f ON r.query_id = f.query_id
        LEFT JOIN ml_prediction p ON f.feature_id = p.feature_id
        GROUP BY DATE(r.timestamp)
        ORDER BY date DESC
        LIMIT 30
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {"trends": [dict(r) for r in rows]}

@app.get("/stats/distribution")
def get_distribution():
    """Attack type distribution for donut chart."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT 
            p.risk_level,
            COUNT(*) as count
        FROM ml_prediction p
        WHERE p.is_malicious = true
        GROUP BY p.risk_level
        ORDER BY count DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {"distribution": [dict(r) for r in rows]}

@app.get("/models")
def get_models():
    """Get model registry."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM model_registry ORDER BY model_id DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {"models": [dict(r) for r in rows]}