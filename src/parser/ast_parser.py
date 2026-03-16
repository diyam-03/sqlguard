import pglast
from pglast import parse_sql
import json

def parse_query(sql_query):
    """
    Takes a raw SQL string and returns parsed AST tuple.
    Returns None if query cannot be parsed.
    """
    try:
        parsed = parse_sql(sql_query)
        return parsed
    except Exception as e:
        return None

def get_ast_string(sql_query):
    """
    Returns string representation of AST for feature extraction.
    """
    try:
        parsed = parse_sql(sql_query)
        return str(parsed)
    except Exception as e:
        return None

def get_ast_nodes(sql_query):
    """
    Returns the parsed AST nodes for a query.
    """
    try:
        parsed = parse_sql(sql_query)
        return parsed
    except Exception as e:
        return None

def test_parser():
    queries = [
        ("SAFE", "SELECT * FROM users WHERE username = 'alice'"),
        ("MALICIOUS", "SELECT * FROM users WHERE username = '' OR '1'='1'"),
        ("UNION ATTACK", "SELECT id FROM users UNION SELECT id FROM admin"),
        ("COMMENT INJECT", "SELECT * FROM users WHERE id = 1 OR 1=1"),
    ]

    for label, query in queries:
        print("=" * 60)
        print(f"TEST — {label}:")
        print(f"Query: {query}")
        result = parse_query(query)
        if result:
            print("✅ Parsed successfully")
            ast_str = get_ast_string(query)
            print(f"AST preview: {ast_str[:300]}")
        else:
            print("❌ Parse failed")
        print()

if __name__ == "__main__":
    test_parser()