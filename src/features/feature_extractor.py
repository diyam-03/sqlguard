import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.parser.ast_parser import parse_query, get_ast_string

def extract_features(sql_query):
    """
    Extracts 35 structural features from a SQL query's AST.
    Returns a dictionary of features.
    """
    features = {}
    
    # Get raw query string for text-based features
    query_str = str(sql_query).lower()
    
    # Get AST
    ast = parse_query(sql_query)
    ast_str = get_ast_string(sql_query) or ""
    ast_str_lower = ast_str.lower()
    
    # ── FEATURE GROUP 1: Boolean & Logical Structure ──
    features['or_branch_count'] = ast_str_lower.count('or_expr')
    features['and_branch_count'] = ast_str_lower.count('and_expr')
    features['not_expr_count'] = ast_str_lower.count('not_expr')
    features['bool_expr_count'] = ast_str_lower.count('boolexpr')
    
    # ── FEATURE GROUP 2: UNION & Set Operations ──
    features['union_select_flag'] = int('setop_union' in ast_str_lower)
    features['intersect_flag'] = int('setop_intersect' in ast_str_lower)
    features['except_flag'] = int('setop_except' in ast_str_lower)
    
    # ── FEATURE GROUP 3: Tautology Detection ──
    features['tautology_score'] = _detect_tautology(ast_str_lower)
    features['always_true_flag'] = int(
        ("'1'='1'" in query_str) or 
        ('1=1' in query_str) or 
        ("'a'='a'" in query_str) or
        ("'x'='x'" in query_str)
    )
    
    # ── FEATURE GROUP 4: Comment Injection ──
    features['comment_inject_flag'] = int(
        '--' in query_str or 
        '#' in query_str or 
        '/*' in query_str
    )
    
    # ── FEATURE GROUP 5: Stacked Queries ──
    features['stacked_query_flag'] = int(';' in query_str)
    features['multiple_statements'] = query_str.count(';')
    
    # ── FEATURE GROUP 6: Subquery Analysis ──
    features['subquery_count'] = ast_str_lower.count('sublink')
    features['nested_select_flag'] = int(ast_str_lower.count('selectstmt') > 1)
    
    # ── FEATURE GROUP 7: Function Calls ──
    features['function_call_count'] = ast_str_lower.count('funcname')
    features['char_encoding_flag'] = int('char(' in query_str)
    features['sleep_flag'] = int('sleep' in query_str or 'benchmark' in query_str)
    features['version_flag'] = int('version()' in query_str or '@@version' in query_str)
    
    # ── FEATURE GROUP 8: Keyword Density ──
    sql_keywords = [
        'select', 'insert', 'update', 'delete', 'drop', 'create',
        'union', 'where', 'from', 'join', 'having', 'group', 'order',
        'exec', 'execute', 'cast', 'convert', 'declare', 'table'
    ]
    words = query_str.split()
    total_words = max(len(words), 1)
    keyword_count = sum(1 for w in words if w in sql_keywords)
    features['keyword_density'] = round(keyword_count / total_words, 4)
    features['total_token_count'] = total_words
    features['sql_keyword_count'] = keyword_count
    
    # ── FEATURE GROUP 9: String Literal Analysis ──
    features['string_literal_count'] = ast_str_lower.count('sval=')
    features['numeric_literal_count'] = ast_str_lower.count('ival=')
    features['empty_string_flag'] = int("sval=''" in ast_str_lower)
    
    # ── FEATURE GROUP 10: Query Structure ──
    features['has_where_clause'] = int('whereclause' in ast_str_lower)
    features['has_order_by'] = int('sortclause' in ast_str_lower)
    features['has_group_by'] = int('groupclause' in ast_str_lower)
    features['has_having'] = int('havingclause' in ast_str_lower)
    features['has_limit'] = int('limitcount' in ast_str_lower)
    features['column_ref_count'] = ast_str_lower.count('columnref')
    features['target_list_count'] = ast_str_lower.count('restarget')
    
    # ── FEATURE GROUP 11: Dangerous Operations ──
    features['drop_flag'] = int('drop' in query_str)
    features['truncate_flag'] = int('truncate' in query_str)
    features['exec_flag'] = int('exec' in query_str or 'execute' in query_str)
    features['xp_cmdshell_flag'] = int('xp_cmdshell' in query_str)
    
    return features

def _detect_tautology(ast_str_lower):
    """
    Returns a tautology score between 0 and 1.
    """
    score = 0.0
    if 'or_expr' in ast_str_lower:
        score += 0.4
    if "sval='1'" in ast_str_lower and ast_str_lower.count("sval='1'") >= 2:
        score += 0.3
    if "ival=1" in ast_str_lower and 'or_expr' in ast_str_lower:
        score += 0.3
    return round(min(score, 1.0), 4)

def test_features():
    queries = [
        ("SAFE", "SELECT * FROM users WHERE username = 'alice'"),
        ("MALICIOUS", "SELECT * FROM users WHERE username = '' OR '1'='1'"),
        ("UNION ATTACK", "SELECT id FROM users UNION SELECT id FROM admin"),
        ("COMMENT INJECT", "SELECT * FROM users WHERE id = 1 OR 1=1"),
        ("STACKED", "SELECT * FROM users; DROP TABLE users;"),
    ]

    for label, query in queries:
        print("=" * 60)
        print(f"{label}: {query}")
        features = extract_features(query)
        print(f"Total features: {len(features)}")
        # Print only non-zero features
        non_zero = {k: v for k, v in features.items() if v != 0}
        print(f"Non-zero features: {non_zero}")
        print()

if __name__ == "__main__":
    test_features()