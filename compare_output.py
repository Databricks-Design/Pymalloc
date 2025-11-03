import pandas as pd
import json
from typing import Any, Dict, List, Tuple
import os
from multiprocessing import Pool, cpu_count

def normalize_json(obj: Any) -> Any:
    """
    Recursively normalize JSON structure for order-independent comparison.
    Sorts dictionary keys and list elements for deterministic comparison.
    """
    if isinstance(obj, dict):
        return {k: normalize_json(v) for k, v in sorted(obj.items())}
    elif isinstance(obj, list):
        if obj and isinstance(obj[0], dict):
            return sorted([normalize_json(item) for item in obj], 
                         key=lambda x: json.dumps(x, sort_keys=True))
        return [normalize_json(item) for item in obj]
    else:
        return obj


def parse_outputs_json(value: Any) -> Dict:
    """
    Parse outputs_json column stored as JSON string.
    Returns parsed dictionary or empty dict if invalid.
    """
    if pd.isna(value) or value == '' or value == '{}':
        return {}
    
    if isinstance(value, str):
        try:
            return json.loads(value)
        except:
            return {}
    elif isinstance(value, dict):
        return value
    else:
        return {}


def find_differences(obj1: Any, obj2: Any, path: str = "root") -> List[str]:
    """
    Recursively find all differences between two objects.
    Works with any JSON structure without knowing schema in advance.
    Checks all keys, values, types, array lengths at all nesting levels.
    """
    differences = []
    
    if type(obj1) != type(obj2):
        differences.append(f"{path}: type(obj1)={type(obj1).__name__}, type(obj2)={type(obj2).__name__}")
        return differences
    
    if isinstance(obj1, dict):
        all_keys = set(obj1.keys()) | set(obj2.keys())
        
        for key in sorted(all_keys):
            new_path = f"{path}.{key}"
            
            if key not in obj1:
                differences.append(f"{new_path}: Key only in API_2")
            elif key not in obj2:
                differences.append(f"{new_path}: Key only in API_1")
            else:
                differences.extend(find_differences(obj1[key], obj2[key], new_path))
    
    elif isinstance(obj1, list):
        if len(obj1) != len(obj2):
            differences.append(f"{path}: Length mismatch - len(API_1)={len(obj1)}, len(API_2)={len(obj2)}")
        
        min_len = min(len(obj1), len(obj2))
        for i in range(min_len):
            new_path = f"{path}[{i}]"
            differences.extend(find_differences(obj1[i], obj2[i], new_path))
        
        if len(obj1) > len(obj2):
            for i in range(len(obj2), len(obj1)):
                differences.append(f"{path}[{i}]: Extra element in API_1")
        elif len(obj2) > len(obj1):
            for i in range(len(obj1), len(obj2)):
                differences.append(f"{path}[{i}]: Extra element in API_2")
    
    else:
        if obj1 != obj2:
            differences.append(f"{path}: API_1={repr(obj1)}, API_2={repr(obj2)}")
    
    return differences


def compare_outputs(output1: Dict, output2: Dict) -> Tuple[bool, str]:
    """
    Compare two output JSON objects using normalization first.
    Same approach as previous testing framework.
    Returns (is_match, detailed_comment)
    """
    norm1 = normalize_json(output1)
    norm2 = normalize_json(output2)
    
    if norm1 == norm2:
        return True, "MATCH"
    
    differences = find_differences(output1, output2)
    
    if not differences:
        differences = ["Structures differ but no specific difference detected"]
    
    comment = " | ".join(differences[:5])
    if len(differences) > 5:
        comment += f" | ... and {len(differences) - 5} more differences"
    
    return False, comment


def compare_single_row(args: Tuple[int, pd.Series, pd.Series]) -> Dict:
    """
    Compare a single transaction row.
    Designed for parallel processing with multiprocessing.
    """
    idx, row1, row2 = args
    
    output1 = parse_outputs_json(row1['outputs_json'])
    output2 = parse_outputs_json(row2['outputs_json'])
    
    is_match, comment = compare_outputs(output1, output2)
    
    return {
        'transaction_id': row1['transaction_id'],
        'description': row1['description'],
        'memo': row1['memo'],
        'api_1_output': row1['outputs_json'],
        'api_2_output': row2['outputs_json'],
        'match_status': "MATCH" if is_match else "MISMATCH",
        'comment': comment
    }


def verify_input_alignment(df1: pd.DataFrame, df2: pd.DataFrame) -> Tuple[bool, str]:
    """
    Verify that both dataframes have identical input data.
    Critical for ensuring fair comparison.
    """
    if len(df1) != len(df2):
        return False, f"Row count mismatch: api_1={len(df1)}, api_2={len(df2)}"
    
    if not df1['transaction_id'].equals(df2['transaction_id']):
        return False, "Transaction IDs do not match"
    
    desc_mismatch = (df1['description'] != df2['description']).sum()
    if desc_mismatch > 0:
        return False, f"{desc_mismatch} descriptions do not match"
    
    memo_mismatch = (df1['memo'].fillna('') != df2['memo'].fillna('')).sum()
    if memo_mismatch > 0:
        return False, f"{memo_mismatch} memos do not match"
    
    return True, "Input data aligned correctly"


def compare_csv_files():
    """
    Main comparison function with multiprocessing support.
    Loads both API outputs and performs parallel row-by-row comparison.
    """
    print("=== Starting Output Comparison ===\n")
    
    api1_csv = 'output/api_1/output_part_1.csv'
    api2_csv = 'output/api_2/output_part_1.csv'
    
    print("Loading output files...")
    df1 = pd.read_csv(api1_csv, dtype={'outputs_json': str})
    df2 = pd.read_csv(api2_csv, dtype={'outputs_json': str})
    
    print(f"API 1: {len(df1)} transactions")
    print(f"API 2: {len(df2)} transactions")
    
    print("\nVerifying input data alignment...")
    aligned, align_msg = verify_input_alignment(df1, df2)
    print(f"Alignment check: {align_msg}")
    
    if not aligned:
        print("\nERROR: Input data not aligned. Cannot proceed with comparison.")
        return
    
    print("\nComparing outputs with multiprocessing...")
    total_rows = len(df1)
    
    args_list = [
        (i, df1.iloc[i], df2.iloc[i])
        for i in range(total_rows)
    ]
    
    num_processes = min(cpu_count(), 8)
    print(f"Using {num_processes} processes")
    
    with Pool(processes=num_processes) as pool:
        comparison_results = []
        chunk_size = 1000
        
        for i in range(0, len(args_list), chunk_size):
            chunk = args_list[i:i+chunk_size]
            chunk_results = pool.map(compare_single_row, chunk)
            comparison_results.extend(chunk_results)
            
            progress = min(i + chunk_size, total_rows)
            print(f"Progress: {progress}/{total_rows} ({progress/total_rows*100:.1f}%)")
    
    comparison_df = pd.DataFrame(comparison_results)
    
    match_count = (comparison_df['match_status'] == 'MATCH').sum()
    mismatch_count = (comparison_df['match_status'] == 'MISMATCH').sum()
    
    os.makedirs('output/comparison', exist_ok=True)
    
    combined_path = 'output/comparison/combined_comparison.csv'
    comparison_df.to_csv(combined_path, index=False)
    print(f"\nSaved: {combined_path}")
    
    mismatch_df = comparison_df[comparison_df['match_status'] == 'MISMATCH']
    mismatch_path = 'output/comparison/mismatch_only.csv'
    mismatch_df.to_csv(mismatch_path, index=False)
    print(f"Saved: {mismatch_path}")
    
    match_percentage = (match_count / total_rows) * 100
    
    summary_text = f"""
=== COMPARISON SUMMARY ===

Total Transactions: {total_rows}
Matches: {match_count} ({match_percentage:.2f}%)
Mismatches: {mismatch_count} ({100 - match_percentage:.2f}%)

Input Data Alignment: {align_msg}

Comparison Method: Normalized deep comparison (schema-independent)
- Checks all keys at all levels
- Checks all values recursively
- Checks all array lengths
- Checks all types
- Works with any JSON structure

Files Generated:
- {combined_path}
- {mismatch_path}

Status: {"PASS - All outputs match" if mismatch_count == 0 else f"FAIL - {mismatch_count} mismatches found"}
"""
    
    summary_path = 'output/comparison/comparison_summary.txt'
    with open(summary_path, 'w') as f:
        f.write(summary_text)
    print(f"Saved: {summary_path}")
    
    print(summary_text)
    
    if mismatch_count > 0:
        print("\n=== Sample Mismatches (first 5) ===")
        for i, row in mismatch_df.head(5).iterrows():
            print(f"\nTransaction {row['transaction_id']}:")
            print(f"  Description: {row['description'][:60]}...")
            print(f"  Differences: {row['comment'][:150]}...")


if __name__ == "__main__":
    compare_csv_files()
