import psycopg2

def get_connection():
    return psycopg2.connect(
        dbname="sqlguard_db",
        user="diyamehta",
        password="",
        host="localhost",
        port="5432"
    )

def test_connection():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public';
        """)
        tables = cur.fetchall()
        print("✅ Connected! Tables found:")
        for t in tables:
            print(f"   → {t[0]}")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    test_connection()
    