#!/usr/bin/env python3

import os
import pandas as pd
import json
from typing import Any, Dict, List, Tuple
import glob
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp

warnings.filterwarnings('ignore')

# ============================================================================
# SHARED UTILITY FUNCTIONS
# ============================================================================

def normalize_json(obj: Any) -> Any:
    """
    Recursively normalize JSON structure for comparison.
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


def parse_json_field(value: Any) -> Any:
    """
    Parse JSON field which can be string or already parsed.
    Returns the parsed object (dict, list, or None).
    """
    if pd.isna(value) or value == '' or value in ['{}', '[]']:
        return None
    
    if isinstance(value, str):
        try:
            return json.loads(value)
        except:
            return None
    else:
        return value


# ============================================================================
# PER-TRANSACTION COMPARISON FUNCTIONS
# ============================================================================

def parse_outputs_json(value: Any) -> Dict:
    """
    Parse outputs_json column which can be string or dict.
    """
    if pd.isna(value) or value == '' or value == '{}':
        return {}
    
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except:
            return {}
    elif isinstance(value, dict):
        return value
    else:
        return {}


def compare_outputs(output1: Dict, output2: Dict) -> Tuple[bool, str]:
    """
    Compare two outputs_json values.
    Returns: (is_match, comment)
    """
    norm1 = normalize_json(output1)
    norm2 = normalize_json(output2)
    
    if norm1 == norm2:
        return True, "MATCH"
    
    comments = []
    
    def find_diff(obj1, obj2, path="root"):
        diffs = []
        
        if type(obj1) != type(obj2):
            diffs.append(f"{path}: type mismatch")
            return diffs
        
        if isinstance(obj1, dict):
            all_keys = set(obj1.keys()) | set(obj2.keys())
            for key in sorted(all_keys):
                if key not in obj1:
                    diffs.append(f"{path}.{key}: only in api_2")
                elif key not in obj2:
                    diffs.append(f"{path}.{key}: only in api_1")
                else:
                    diffs.extend(find_diff(obj1[key], obj2[key], f"{path}.{key}"))
        
        elif isinstance(obj1, list):
            if len(obj1) != len(obj2):
                diffs.append(f"{path}: length mismatch (api_1={len(obj1)}, api_2={len(obj2)})")
            
            for i in range(min(len(obj1), len(obj2))):
                diffs.extend(find_diff(obj1[i], obj2[i], f"{path}[{i}]"))
            
            if len(obj1) > len(obj2):
                for i in range(len(obj2), len(obj1)):
                    diffs.append(f"{path}[{i}]: extra in api_1")
            elif len(obj2) > len(obj1):
                for i in range(len(obj1), len(obj2)):
                    diffs.append(f"{path}[{i}]: extra in api_2")
        
        else:
            if obj1 != obj2:
                diffs.append(f"{path}: api_1={repr(obj1)}, api_2={repr(obj2)}")
        
        return diffs
    
    comments = find_diff(output1, output2)
    
    return False, " | ".join(comments[:5]) if comments else "Structure mismatch"


def verify_same_input_data_transaction(df_api1: pd.DataFrame, df_api2: pd.DataFrame) -> Tuple[bool, str]:
    """
    Verify that both dataframes contain the same input data (transaction level).
    """
    if len(df_api1) != len(df_api2):
        return False, f"Different number of rows: api_1={len(df_api1)}, api_2={len(df_api2)}"
    
    if 'transaction_id' in df_api1.columns and 'transaction_id' in df_api2.columns:
        ids_match = (df_api1['transaction_id'].astype(str) == df_api2['transaction_id'].astype(str)).all()
        if not ids_match:
            return False, "Transaction IDs don't match - files may not be aligned"
    
    if 'description' in df_api1.columns and 'description' in df_api2.columns:
        desc_match = (df_api1['description'].astype(str) == df_api2['description'].astype(str)).all()
        if not desc_match:
            return False, "Descriptions don't match - files may not be aligned"
    
    return True, "Input data verified as identical"


def compare_csv_files(file_pair: Tuple[str, str, int]) -> Tuple[pd.DataFrame, int, Dict]:
    """
    Compare two CSV files and return comparison dataframe (transaction level).
    """
    api1_csv, api2_csv, part_num = file_pair
    
    print(f"  [Part {part_num}] Starting comparison...")
    
    df_api1 = pd.read_csv(api1_csv, keep_default_na=False, low_memory=False, dtype={'outputs_json': str})
    df_api2 = pd.read_csv(api2_csv, keep_default_na=False, low_memory=False, dtype={'outputs_json': str})
    
    is_same, verification_msg = verify_same_input_data_transaction(df_api1, df_api2)
    
    comparison_data = []
    
    for idx in range(max(len(df_api1), len(df_api2))):
        if idx >= len(df_api1):
            row_id = df_api2.iloc[idx]['transaction_id']
            row_desc = df_api2.iloc[idx]['description']
            comparison_data.append({
                'transaction_id': row_id,
                'description': row_desc,
                'memo': df_api2.iloc[idx]['memo'],
                'api_1_output': "MISSING ROW",
                'api_2_output': str(df_api2.iloc[idx].get('outputs_json', '')),
                'match_status': 'DATA_MISMATCH',
                'comment': "Row exists only in api_2"
            })
        elif idx >= len(df_api2):
            row_id = df_api1.iloc[idx]['transaction_id']
            row_desc = df_api1.iloc[idx]['description']
            comparison_data.append({
                'transaction_id': row_id,
                'description': row_desc,
                'memo': df_api1.iloc[idx]['memo'],
                'api_1_output': str(df_api1.iloc[idx].get('outputs_json', '')),
                'api_2_output': "MISSING ROW",
                'match_status': 'DATA_MISMATCH',
                'comment': "Row exists only in api_1"
            })
        else:
            row_api1 = df_api1.iloc[idx]
            row_api2 = df_api2.iloc[idx]
            
            row_id_api1 = str(row_api1['transaction_id'])
            row_id_api2 = str(row_api2['transaction_id'])
            row_desc_api1 = str(row_api1['description'])
            row_desc_api2 = str(row_api2['description'])
            
            if row_id_api1 != row_id_api2 or row_desc_api1 != row_desc_api2:
                comparison_data.append({
                    'transaction_id': f"api_1={row_id_api1}, api_2={row_id_api2}",
                    'description': row_desc_api1,
                    'memo': row_api1['memo'],
                    'api_1_output': "N/A",
                    'api_2_output': "N/A",
                    'match_status': 'DATA_MISMATCH',
                    'comment': "Input data doesn't match - rows are not aligned!"
                })
                continue
            
            output_api1_raw = row_api1.get('outputs_json', '')
            output_api2_raw = row_api2.get('outputs_json', '')
            
            output_api1 = parse_outputs_json(output_api1_raw)
            output_api2 = parse_outputs_json(output_api2_raw)
            
            is_match, comment = compare_outputs(output_api1, output_api2)
            
            output_api1_str = str(output_api1_raw) if output_api1_raw else "{}"
            output_api2_str = str(output_api2_raw) if output_api2_raw else "{}"
            
            comparison_data.append({
                'transaction_id': row_id_api1,
                'description': row_desc_api1,
                'memo': row_api1['memo'],
                'api_1_output': output_api1_str,
                'api_2_output': output_api2_str,
                'match_status': 'MATCH' if is_match else 'MISMATCH',
                'comment': comment
            })
    
    comparison_df = pd.DataFrame(comparison_data)
    
    stats = {
        'matches': (comparison_df['match_status'] == 'MATCH').sum(),
        'mismatches': (comparison_df['match_status'] == 'MISMATCH').sum(),
        'data_mismatches': (comparison_df['match_status'] == 'DATA_MISMATCH').sum(),
        'verification': verification_msg
    }
    
    print(f"  [Part {part_num}] Complete - Matches: {stats['matches']}, Mismatches: {stats['mismatches']}")
    
    return comparison_df, part_num, stats


def compare_all_parts(output_dir: str, use_multiprocessing: bool = True):
    """
    Compare all CSV parts between api_1 and api_2 folders (transaction level).
    """
    api1_folder = os.path.join(output_dir, "api_1")
    api2_folder = os.path.join(output_dir, "api_2")
    comparison_folder = os.path.join(output_dir, "comparison")
    
    os.makedirs(comparison_folder, exist_ok=True)
    
    api1_files = sorted(glob.glob(os.path.join(api1_folder, "output_part_*.csv")))
    api2_files = sorted(glob.glob(os.path.join(api2_folder, "output_part_*.csv")))
    
    if not api1_files:
        print("ERROR: No CSV files found in api_1 folder!")
        return None
    
    if not api2_files:
        print("ERROR: No CSV files found in api_2 folder!")
        return None
    
    print(f"\nFound {len(api1_files)} files in api_1")
    print(f"Found {len(api2_files)} files in api_2")
    
    if len(api1_files) != len(api2_files):
        print(f"⚠️ WARNING: Different number of CSV files!")
    
    num_pairs = min(len(api1_files), len(api2_files))
    
    file_pairs = [
        (api1_files[i], api2_files[i], i+1)
        for i in range(num_pairs)
    ]
    
    print(f"\n{'='*80}")
    if use_multiprocessing:
        num_workers = max(1, int(mp.cpu_count() * 0.75))
        print(f"Using multiprocessing with {num_workers} workers")
        print(f"Processing {num_pairs} file pairs in parallel...")
        print(f"{'='*80}\n")
        
        all_comparisons = {}
        all_stats = {}
        
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            future_to_part = {executor.submit(compare_csv_files, pair): pair[2] 
                             for pair in file_pairs}
            
            for future in as_completed(future_to_part):
                part_num = future_to_part[future]
                try:
                    comparison_df, part_num, stats = future.result()
                    all_comparisons[part_num] = comparison_df
                    all_stats[part_num] = stats
                    
                except Exception as exc:
                    print(f"  [Part {part_num}] Generated an exception: {exc}")
    else:
        print("Using sequential processing...")
        print(f"{'='*80}\n")
        
        all_comparisons = {}
        all_stats = {}
        
        for pair in file_pairs:
            comparison_df, part_num, stats = compare_csv_files(pair)
            all_comparisons[part_num] = comparison_df
            all_stats[part_num] = stats
    
    print(f"\n{'='*80}")
    print("Combining all comparisons...")
    
    ordered_comparisons = [all_comparisons[i] for i in sorted(all_comparisons.keys())]
    combined_df = pd.concat(ordered_comparisons, ignore_index=True)
    
    combined_file = os.path.join(comparison_folder, "combined_comparison.csv")
    combined_df.to_csv(combined_file, index=False)
    print(f"✓ Saved combined comparison: {combined_file}")
    
    total_matches = sum(stats['matches'] for stats in all_stats.values())
    total_mismatches = sum(stats['mismatches'] for stats in all_stats.values())
    total_data_mismatches = sum(stats['data_mismatches'] for stats in all_stats.values())
    
    mismatches_df = combined_df[combined_df['match_status'].isin(['MISMATCH', 'DATA_MISMATCH'])]
    if len(mismatches_df) > 0:
        mismatches_file = os.path.join(comparison_folder, "mismatch_only.csv")
        mismatches_df.to_csv(mismatches_file, index=False)
        print(f"✓ Saved mismatches only: {mismatches_file}")
    
    print(f"\n{'='*80}")
    print("PER-TRANSACTION COMPARISON SUMMARY")
    print(f"{'='*80}")
    print(f"Total Rows Compared: {len(combined_df)}")
    print(f"Total Matches: {total_matches} ({total_matches/len(combined_df)*100:.2f}%)")
    print(f"Total Mismatches: {total_mismatches} ({total_mismatches/len(combined_df)*100:.2f}%)")
    
    if total_data_mismatches > 0:
        print(f"⚠️ Data Alignment Issues: {total_data_mismatches} ({total_data_mismatches/len(combined_df)*100:.2f}%)")
    
    if total_mismatches > 0:
        print(f"\n✓ Review '{mismatches_file}' to see all {total_mismatches + total_data_mismatches} issues")
    else:
        print("\n🎉 PERFECT MATCH! All outputs are identical between api_1 and api_2!")
    
    summary_file = os.path.join(comparison_folder, "comparison_summary.txt")
    with open(summary_file, 'w') as f:
        f.write("="*80 + "\n")
        f.write("PER-TRANSACTION OUTPUT COMPARISON SUMMARY REPORT\n")
        f.write("="*80 + "\n\n")
        f.write(f"Total Rows Compared: {len(combined_df)}\n")
        f.write(f"Total Matches: {total_matches} ({total_matches/len(combined_df)*100:.2f}%)\n")
        f.write(f"Total Output Mismatches: {total_mismatches} ({total_mismatches/len(combined_df)*100:.2f}%)\n")
        f.write(f"Total Data Alignment Issues: {total_data_mismatches} ({total_data_mismatches/len(combined_df)*100:.2f}%)\n\n")
        
        if total_mismatches > 0:
            f.write("Top 20 Mismatch Reasons:\n")
            f.write("-"*80 + "\n")
            mismatch_df = combined_df[combined_df['match_status'] == 'MISMATCH']
            if len(mismatch_df) > 0:
                mismatch_reasons = mismatch_df['comment'].value_counts().head(20)
                for reason, count in mismatch_reasons.items():
                    f.write(f"  {count:6d}x - {str(reason)[:200]}\n")
        
        if total_data_mismatches > 0:
            f.write("\n⚠️ CRITICAL: Data alignment issues detected!\n")
            f.write("This suggests the input data in both tests may not be identical.\n")
    
    print(f"\n✓ Saved summary report: {summary_file}")
    print(f"\n{'='*80}")
    
    return {
        'total_matches': total_matches,
        'total_mismatches': total_mismatches,
        'total_data_mismatches': total_data_mismatches,
        'total_rows': len(combined_df)
    }


# ============================================================================
# BATCHED COMPARISON FUNCTIONS
# ============================================================================

def compare_json_arrays(arr1: List, arr2: List, field_name: str) -> Tuple[bool, str]:
    """
    Compare two JSON arrays (for descriptions_json or memos_json).
    Returns: (is_match, comment)
    """
    if arr1 is None and arr2 is None:
        return True, "Both empty"
    
    if arr1 is None or arr2 is None:
        return False, f"{field_name}: one is empty, other is not"
    
    if len(arr1) != len(arr2):
        return False, f"{field_name}: length mismatch (api_1={len(arr1)}, api_2={len(arr2)})"
    
    for i, (item1, item2) in enumerate(zip(arr1, arr2)):
        if str(item1) != str(item2):
            return False, f"{field_name}[{i}]: api_1={repr(item1)}, api_2={repr(item2)}"
    
    return True, "Match"


def compare_api_responses(response1: Dict, response2: Dict) -> Tuple[bool, str]:
    """
    Compare two api_response_json values.
    Returns: (is_match, comment)
    """
    if response1 is None and response2 is None:
        return True, "MATCH"
    
    if response1 is None or response2 is None:
        return False, "One response is empty, other is not"
    
    norm1 = normalize_json(response1)
    norm2 = normalize_json(response2)
    
    if norm1 == norm2:
        return True, "MATCH"
    
    def find_diff(obj1, obj2, path="root"):
        diffs = []
        
        if type(obj1) != type(obj2):
            diffs.append(f"{path}: type mismatch")
            return diffs
        
        if isinstance(obj1, dict):
            all_keys = set(obj1.keys()) | set(obj2.keys())
            for key in sorted(all_keys):
                if key not in obj1:
                    diffs.append(f"{path}.{key}: only in api_2")
                elif key not in obj2:
                    diffs.append(f"{path}.{key}: only in api_1")
                else:
                    diffs.extend(find_diff(obj1[key], obj2[key], f"{path}.{key}"))
        
        elif isinstance(obj1, list):
            if len(obj1) != len(obj2):
                diffs.append(f"{path}: length mismatch (api_1={len(obj1)}, api_2={len(obj2)})")
            
            for i in range(min(len(obj1), len(obj2))):
                diffs.extend(find_diff(obj1[i], obj2[i], f"{path}[{i}]"))
            
            if len(obj1) > len(obj2):
                for i in range(len(obj2), len(obj1)):
                    diffs.append(f"{path}[{i}]: extra in api_1")
            elif len(obj2) > len(obj1):
                for i in range(len(obj1), len(obj2)):
                    diffs.append(f"{path}[{i}]: extra in api_2")
        
        else:
            if obj1 != obj2:
                diffs.append(f"{path}: api_1={repr(obj1)}, api_2={repr(obj2)}")
        
        return diffs
    
    comments = find_diff(response1, response2)
    
    return False, " | ".join(comments[:5]) if comments else "Structure mismatch"


def verify_same_input_data_batch(df_api1: pd.DataFrame, df_api2: pd.DataFrame) -> Tuple[bool, str]:
    """
    Verify that both dataframes contain the same batch input data.
    """
    if len(df_api1) != len(df_api2):
        return False, f"Different number of batches: api_1={len(df_api1)}, api_2={len(df_api2)}"
    
    if 'batch_id' in df_api1.columns and 'batch_id' in df_api2.columns:
        ids_match = (df_api1['batch_id'].astype(str) == df_api2['batch_id'].astype(str)).all()
        if not ids_match:
            return False, "Batch IDs don't match - files may not be aligned"
    
    for idx in range(len(df_api1)):
        desc1 = parse_json_field(df_api1.iloc[idx]['descriptions_json'])
        desc2 = parse_json_field(df_api2.iloc[idx]['descriptions_json'])
        
        if desc1 != desc2:
            return False, f"descriptions_json don't match at batch {idx+1}"
    
    for idx in range(len(df_api1)):
        memo1 = parse_json_field(df_api1.iloc[idx]['memos_json'])
        memo2 = parse_json_field(df_api2.iloc[idx]['memos_json'])
        
        if memo1 != memo2:
            return False, f"memos_json don't match at batch {idx+1}"
    
    return True, "Input data verified as identical"


def compare_batched_csv(api1_csv: str, api2_csv: str) -> Tuple[pd.DataFrame, Dict]:
    """
    Compare two batched_output.csv files and return comparison dataframe.
    """
    print(f"  Starting batched output comparison...")
    
    df_api1 = pd.read_csv(api1_csv, keep_default_na=False, low_memory=False, 
                         dtype={'descriptions_json': str, 'memos_json': str, 'api_response_json': str})
    df_api2 = pd.read_csv(api2_csv, keep_default_na=False, low_memory=False,
                         dtype={'descriptions_json': str, 'memos_json': str, 'api_response_json': str})
    
    is_same, verification_msg = verify_same_input_data_batch(df_api1, df_api2)
    
    comparison_data = []
    
    for idx in range(max(len(df_api1), len(df_api2))):
        if idx >= len(df_api1):
            batch_id = df_api2.iloc[idx]['batch_id']
            comparison_data.append({
                'batch_id': batch_id,
                'descriptions_match': 'MISSING_BATCH',
                'memos_match': 'MISSING_BATCH',
                'api_response_match': 'DATA_MISMATCH',
                'comment': "Batch exists only in api_2"
            })
        elif idx >= len(df_api2):
            batch_id = df_api1.iloc[idx]['batch_id']
            comparison_data.append({
                'batch_id': batch_id,
                'descriptions_match': 'MISSING_BATCH',
                'memos_match': 'MISSING_BATCH',
                'api_response_match': 'DATA_MISMATCH',
                'comment': "Batch exists only in api_1"
            })
        else:
            row_api1 = df_api1.iloc[idx]
            row_api2 = df_api2.iloc[idx]
            
            batch_id_api1 = str(row_api1['batch_id'])
            batch_id_api2 = str(row_api2['batch_id'])
            
            if batch_id_api1 != batch_id_api2:
                comparison_data.append({
                    'batch_id': f"api_1={batch_id_api1}, api_2={batch_id_api2}",
                    'descriptions_match': 'DATA_MISMATCH',
                    'memos_match': 'DATA_MISMATCH',
                    'api_response_match': 'DATA_MISMATCH',
                    'comment': "Batch IDs don't match - batches are not aligned!"
                })
                continue
            
            descriptions1 = parse_json_field(row_api1['descriptions_json'])
            descriptions2 = parse_json_field(row_api2['descriptions_json'])
            memos1 = parse_json_field(row_api1['memos_json'])
            memos2 = parse_json_field(row_api2['memos_json'])
            
            desc_match, desc_comment = compare_json_arrays(descriptions1, descriptions2, "descriptions_json")
            memo_match, memo_comment = compare_json_arrays(memos1, memos2, "memos_json")
            
            response1 = parse_json_field(row_api1['api_response_json'])
            response2 = parse_json_field(row_api2['api_response_json'])
            
            resp_match, resp_comment = compare_api_responses(response1, response2)
            
            if not desc_match or not memo_match:
                overall_status = 'DATA_MISMATCH'
                overall_comment = f"Input mismatch: {desc_comment}; {memo_comment}"
            elif not resp_match:
                overall_status = 'MISMATCH'
                overall_comment = resp_comment
            else:
                overall_status = 'MATCH'
                overall_comment = 'All fields match'
            
            comparison_data.append({
                'batch_id': batch_id_api1,
                'descriptions_match': 'MATCH' if desc_match else 'MISMATCH',
                'memos_match': 'MATCH' if memo_match else 'MISMATCH',
                'api_response_match': 'MATCH' if resp_match else 'MISMATCH',
                'comment': overall_comment
            })
    
    comparison_df = pd.DataFrame(comparison_data)
    
    match_conditions = (comparison_df['api_response_match'] == 'MATCH') & \
                      (comparison_df['descriptions_match'] == 'MATCH') & \
                      (comparison_df['memos_match'] == 'MATCH')
    
    comparison_df['match_status'] = match_conditions.apply(lambda x: 'MATCH' if x else 'MISMATCH')
    
    data_mismatch_conditions = (comparison_df['descriptions_match'].isin(['MISMATCH', 'MISSING_BATCH', 'DATA_MISMATCH'])) | \
                               (comparison_df['memos_match'].isin(['MISMATCH', 'MISSING_BATCH', 'DATA_MISMATCH']))
    comparison_df.loc[data_mismatch_conditions, 'match_status'] = 'DATA_MISMATCH'
    
    stats = {
        'matches': (comparison_df['match_status'] == 'MATCH').sum(),
        'mismatches': (comparison_df['match_status'] == 'MISMATCH').sum(),
        'data_mismatches': (comparison_df['match_status'] == 'DATA_MISMATCH').sum(),
        'verification': verification_msg
    }
    
    print(f"  Complete - Matches: {stats['matches']}, Mismatches: {stats['mismatches']}, Data Issues: {stats['data_mismatches']}")
    
    return comparison_df, stats


def compare_batched_outputs(output_dir: str):
    """
    Compare batched_output.csv files between api_1 and api_2 folders.
    """
    api1_file = os.path.join(output_dir, "api_1", "batched_output.csv")
    api2_file = os.path.join(output_dir, "api_2", "batched_output.csv")
    comparison_folder = os.path.join(output_dir, "batched_comparison")
    
    os.makedirs(comparison_folder, exist_ok=True)
    
    if not os.path.exists(api1_file):
        print(f"⚠️ WARNING: File not found - {api1_file}")
        print("   Skipping batched output comparison...")
        return None
    
    if not os.path.exists(api2_file):
        print(f"⚠️ WARNING: File not found - {api2_file}")
        print("   Skipping batched output comparison...")
        return None
    
    print(f"\n{'='*80}")
    print(f"Comparing batched outputs...")
    print(f"{'='*80}\n")
    
    comparison_df, stats = compare_batched_csv(api1_file, api2_file)
    
    print(f"\n{'='*80}")
    print("Saving batched comparison results...")
    
    combined_file = os.path.join(comparison_folder, "batched_combined_comparison.csv")
    comparison_df.to_csv(combined_file, index=False)
    print(f"✓ Saved combined comparison: {combined_file}")
    
    mismatches_df = comparison_df[comparison_df['match_status'].isin(['MISMATCH', 'DATA_MISMATCH'])]
    if len(mismatches_df) > 0:
        mismatches_file = os.path.join(comparison_folder, "batched_mismatch_only.csv")
        mismatches_df.to_csv(mismatches_file, index=False)
        print(f"✓ Saved mismatches only: {mismatches_file}")
    
    total_batches = len(comparison_df)
    total_matches = stats['matches']
    total_mismatches = stats['mismatches']
    total_data_mismatches = stats['data_mismatches']
    
    print(f"\n{'='*80}")
    print("BATCHED OUTPUT COMPARISON SUMMARY")
    print(f"{'='*80}")
    print(f"Total Batches Compared: {total_batches}")
    print(f"Total Matches: {total_matches} ({total_matches/total_batches*100:.2f}%)")
    print(f"API Response Mismatches: {total_mismatches} ({total_mismatches/total_batches*100:.2f}%)")
    
    if total_data_mismatches > 0:
        print(f"⚠️ Input Data Alignment Issues: {total_data_mismatches} ({total_data_mismatches/total_batches*100:.2f}%)")
    
    if total_mismatches > 0 or total_data_mismatches > 0:
        print(f"\n✓ Review '{mismatches_file}' to see all {total_mismatches + total_data_mismatches} issues")
    else:
        print("\n🎉 PERFECT MATCH! All batched outputs are identical between api_1 and api_2!")
    
    summary_file = os.path.join(comparison_folder, "batched_comparison_summary.txt")
    with open(summary_file, 'w') as f:
        f.write("="*80 + "\n")
        f.write("BATCHED OUTPUT COMPARISON SUMMARY REPORT\n")
        f.write("="*80 + "\n\n")
        f.write(f"Total Batches Compared: {total_batches}\n")
        f.write(f"Total Matches: {total_matches} ({total_matches/total_batches*100:.2f}%)\n")
        f.write(f"API Response Mismatches: {total_mismatches} ({total_mismatches/total_batches*100:.2f}%)\n")
        f.write(f"Input Data Alignment Issues: {total_data_mismatches} ({total_data_mismatches/total_batches*100:.2f}%)\n\n")
        
        f.write(f"Verification Status: {stats['verification']}\n\n")
        
        if total_mismatches > 0:
            f.write("Top 20 Mismatch Reasons:\n")
            f.write("-"*80 + "\n")
            mismatch_df = comparison_df[comparison_df['match_status'] == 'MISMATCH']
            if len(mismatch_df) > 0:
                mismatch_reasons = mismatch_df['comment'].value_counts().head(20)
                for reason, count in mismatch_reasons.items():
                    f.write(f"  {count:6d}x - {str(reason)[:200]}\n")
        
        if total_data_mismatches > 0:
            f.write("\n⚠️ CRITICAL: Input data alignment issues detected!\n")
            f.write("This suggests the batched inputs in both tests may not be identical.\n")
    
    print(f"\n✓ Saved summary report: {summary_file}")
    print(f"\n{'='*80}")
    
    return {
        'total_matches': total_matches,
        'total_mismatches': total_mismatches,
        'total_data_mismatches': total_data_mismatches,
        'total_batches': total_batches
    }


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    OUTPUT_DIR = "./output"
    USE_MULTIPROCESSING = True
    
    if not os.path.exists(OUTPUT_DIR):
        print(f"ERROR: Output directory '{OUTPUT_DIR}' not found!")
        return
    
    print("\n" + "="*80)
    print("STARTING OUTPUT COMPARISON")
    print("="*80)
    
    # Part 1: Compare per-transaction outputs
    print("\n📊 PART 1: PER-TRANSACTION OUTPUT COMPARISON")
    transaction_results = compare_all_parts(OUTPUT_DIR, use_multiprocessing=USE_MULTIPROCESSING)
    
    # Part 2: Compare batched outputs
    print("\n📦 PART 2: BATCHED OUTPUT COMPARISON")
    batched_results = compare_batched_outputs(OUTPUT_DIR)
    
    # Final Summary
    print("\n" + "="*80)
    print("OVERALL COMPARISON SUMMARY")
    print("="*80)
    
    if transaction_results:
        print(f"\n✓ Per-Transaction Comparison:")
        print(f"  - Total Rows: {transaction_results['total_rows']}")
        print(f"  - Matches: {transaction_results['total_matches']} ({transaction_results['total_matches']/transaction_results['total_rows']*100:.2f}%)")
        if transaction_results['total_mismatches'] > 0:
            print(f"  - Mismatches: {transaction_results['total_mismatches']}")
    
    if batched_results:
        print(f"\n✓ Batched Comparison:")
        print(f"  - Total Batches: {batched_results['total_batches']}")
        print(f"  - Matches: {batched_results['total_matches']} ({batched_results['total_matches']/batched_results['total_batches']*100:.2f}%)")
        if batched_results['total_mismatches'] > 0:
            print(f"  - Mismatches: {batched_results['total_mismatches']}")
    
    print("\n✓ Comparison complete!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
