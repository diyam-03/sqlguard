import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.parser.ast_parser import parse_query, get_ast_string

def extract_text_features(sql_query):
    """
    Text-based features that work even when AST parsing fails.
    """
    q = str(sql_query).lower()
    
    features = {}
    features['has_or_keyword'] = int(' or ' in q)
    features['has_union_keyword'] = int('union' in q)
    features['has_select_keyword'] = int('select' in q)
    features['has_drop_keyword'] = int('drop' in q)
    features['has_insert_keyword'] = int('insert' in q)
    features['has_delete_keyword'] = int('delete' in q)
    features['has_exec_keyword'] = int('exec' in q or 'execute' in q)
    features['has_sleep'] = int('sleep' in q or 'pg_sleep' in q)
    features['has_comment'] = int('--' in q or '#' in q or '/*' in q)
    features['has_semicolon'] = int(';' in q)
    features['has_single_quote'] = int("'" in q)
    features['has_double_quote'] = int('"' in q)
    features['has_tautology'] = int(
        '1=1' in q.replace(' ', '') or 
        "'a'='a'" in q or
        "'1'='1'" in q or
        '1 = 1' in q
    )
    features['has_char_func'] = int('char(' in q)
    features['has_load_file'] = int('load_file' in q)
    features['has_into_outfile'] = int('into outfile' in q)
    features['has_information_schema'] = int('information_schema' in q)
    features['has_sys_tables'] = int('sys.' in q or 'sysobjects' in q or 'syscolumns' in q)
    features['query_length'] = len(q)
    features['special_char_ratio'] = round(
        sum(1 for c in q if c in "';\"()=<>!@#$%^&*") / max(len(q), 1), 4
    )
    
    return features

def extract_features(sql_query):
    """
    Extracts features from a SQL query combining AST and text analysis.
    Returns a dictionary of features.
    """
    # Get text features first — always works
    text_features = extract_text_features(sql_query)
    
    # Get AST features — works for valid SQL
    query_str = str(sql_query).lower()
    ast = parse_query(sql_query)
    ast_str = get_ast_string(sql_query) or ""
    ast_str_lower = ast_str.lower()

    ast_features = {}

    # ── FEATURE GROUP 1: Boolean & Logical Structure ──
    ast_features['or_branch_count'] = ast_str_lower.count('or_expr')
    ast_features['and_branch_count'] = ast_str_lower.count('and_expr')
    ast_features['not_expr_count'] = ast_str_lower.count('not_expr')
    ast_features['bool_expr_count'] = ast_str_lower.count('boolexpr')

    # ── FEATURE GROUP 2: UNION & Set Operations ──
    ast_features['union_select_flag'] = int('setop_union' in ast_str_lower)
    ast_features['intersect_flag'] = int('setop_intersect' in ast_str_lower)
    ast_features['except_flag'] = int('setop_except' in ast_str_lower)

    # ── FEATURE GROUP 3: Tautology Detection ──
    ast_features['tautology_score'] = _detect_tautology(ast_str_lower)
    ast_features['always_true_flag'] = int(
        ("'1'='1'" in query_str) or
        ('1=1' in query_str) or
        ("'a'='a'" in query_str) or
        ("'x'='x'" in query_str)
    )

    # ── FEATURE GROUP 4: Comment Injection ──
    ast_features['comment_inject_flag'] = int(
        '--' in query_str or
        '#' in query_str or
        '/*' in query_str
    )

    # ── FEATURE GROUP 5: Stacked Queries ──
    ast_features['stacked_query_flag'] = int(';' in query_str)
    ast_features['multiple_statements'] = query_str.count(';')

    # ── FEATURE GROUP 6: Subquery Analysis ──
    ast_features['subquery_count'] = ast_str_lower.count('sublink')
    ast_features['nested_select_flag'] = int(ast_str_lower.count('selectstmt') > 1)

    # ── FEATURE GROUP 7: Function Calls ──
    ast_features['function_call_count'] = ast_str_lower.count('funcname')
    ast_features['char_encoding_flag'] = int('char(' in query_str)
    ast_features['sleep_flag'] = int('sleep' in query_str or 'benchmark' in query_str)
    ast_features['version_flag'] = int('version()' in query_str or '@@version' in query_str)

    # ── FEATURE GROUP 8: Keyword Density ──
    sql_keywords = [
        'select', 'insert', 'update', 'delete', 'drop', 'create',
        'union', 'where', 'from', 'join', 'having', 'group', 'order',
        'exec', 'execute', 'cast', 'convert', 'declare', 'table'
    ]
    words = query_str.split()
    total_words = max(len(words), 1)
    keyword_count = sum(1 for w in words if w in sql_keywords)
    ast_features['keyword_density'] = round(keyword_count / total_words, 4)
    ast_features['total_token_count'] = total_words
    ast_features['sql_keyword_count'] = keyword_count

    # ── FEATURE GROUP 9: String Literal Analysis ──
    ast_features['string_literal_count'] = ast_str_lower.count('sval=')
    ast_features['numeric_literal_count'] = ast_str_lower.count('ival=')
    ast_features['empty_string_flag'] = int("sval=''" in ast_str_lower)

    # ── FEATURE GROUP 10: Query Structure ──
    ast_features['has_where_clause'] = int('whereclause' in ast_str_lower)
    ast_features['has_order_by'] = int('sortclause' in ast_str_lower)
    ast_features['has_group_by'] = int('groupclause' in ast_str_lower)
    ast_features['has_having'] = int('havingclause' in ast_str_lower)
    ast_features['has_limit'] = int('limitcount' in ast_str_lower)
    ast_features['column_ref_count'] = ast_str_lower.count('columnref')
    ast_features['target_list_count'] = ast_str_lower.count('restarget')

    # ── FEATURE GROUP 11: Dangerous Operations ──
    ast_features['drop_flag'] = int('drop' in query_str)
    ast_features['truncate_flag'] = int('truncate' in query_str)
    ast_features['exec_flag'] = int('exec' in query_str or 'execute' in query_str)
    ast_features['xp_cmdshell_flag'] = int('xp_cmdshell' in query_str)

    # Combine both feature sets
    combined = {**text_features, **ast_features}
    return combined

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