"""
Test execution of all 19 analytical queries against local database.
"""
from db import execute_query, QUERIES_MYSQL

def test_all_queries():
    print(f"Testing execution of {len(QUERIES_MYSQL)} analytical queries...")
    success_count = 0
    for key in sorted(QUERIES_MYSQL.keys()):
        params = ("TCS",) if key == "q5_moving_average" else None
        res = execute_query(key, params)
        if res.get("status") == "success":
            data_len = len(res.get("data", []))
            print(f"  [PASS] {key} -> returned {data_len} rows (source: {res.get('source')})")
            success_count += 1
        else:
            print(f"  [FAIL] {key} -> {res.get('error')}")

    print(f"\nCompleted: {success_count}/{len(QUERIES_MYSQL)} queries succeeded.")

if __name__ == "__main__":
    test_all_queries()
