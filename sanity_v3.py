import pandas as pd
import requests
import json
import time
from typing import Dict, List
import os

class APITester:
    """
    Tests API endpoints by sending batched requests.
    """
    
    def __init__(self, api_name: str, api_url: str, batch_size: int = 50):
        self.api_name = api_name
        self.api_url = api_url
        self.batch_size = batch_size
        self.headers = {'Content-Type': 'application/json'}
        
        self.all_results = []
        
    def build_tensor_payload(self, descriptions: List[str], memos: List[str]) -> Dict:
        """Build tensor-based payload for batch inference."""
        batch_size = len(descriptions)
        payload = {
            "inputs": [
                {
                    "name": "description",
                    "datatype": "BYTES",
                    "shape": [batch_size, 1],
                    "data": descriptions
                },
                {
                    "name": "memo",
                    "datatype": "BYTES",
                    "shape": [batch_size, 1],
                    "data": memos
                }
            ]
        }
        return payload
    
    def parse_tensor_response(self, response_json: Dict) -> List[Dict]:
        """
        De-batch the flattened tensor response into per-transaction JSON objects.
        If any output has entities: keep all values including empty strings for all outputs.
        If all outputs empty: use empty arrays for all outputs.
        """
        outputs = response_json.get('outputs', [])
        if not outputs:
            return []
        
        shape = outputs[0].get('shape', [])
        if len(shape) != 2:
            return []
        
        batch_size, max_entities = shape
        
        output_list = []
        for output in outputs:
            output_list.append({
                'name': output['name'],
                'datatype': output.get('datatype', 'BYTES'),
                'data': output['data']
            })
        
        results = []
        for i in range(batch_size):
            transaction_outputs = []
            
            # First pass: extract all data and check if transaction has any non-empty entities
            temp_data = []
            transaction_has_entities = False
            
            for output_info in output_list:
                transaction_data = []
                
                for j in range(max_entities):
                    idx = i * max_entities + j
                    value = output_info['data'][idx] if idx < len(output_info['data']) else ""
                    transaction_data.append(value)
                
                temp_data.append(transaction_data)
                
                # Check if this output has any non-empty value
                if any(val != "" for val in transaction_data):
                    transaction_has_entities = True
            
            # Second pass: build outputs based on whether transaction has entities
            for output_idx, output_info in enumerate(output_list):
                if transaction_has_entities:
                    # Keep all values including empty strings
                    data = temp_data[output_idx]
                else:
                    # All empty - use empty array
                    data = []
                
                transaction_outputs.append({
                    "name": output_info['name'],
                    "datatype": output_info['datatype'],
                    "shape": [1, len(data)],
                    "data": data
                })
            
            transaction_json = {
                "model_name": response_json.get('model_name', ''),
                "model_version": response_json.get('model_version', ''),
                "outputs": transaction_outputs
            }
            results.append(transaction_json)
        
        return results
    
    def send_batch_request(self, descriptions: List[str], memos: List[str]) -> tuple:
        """Send batch request to API and return parsed results with API timing."""
        payload = self.build_tensor_payload(descriptions, memos)
        
        try:
            api_start = time.time()
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            api_time = time.time() - api_start
            
            if response.status_code == 200:
                response_json = response.json()
                results = self.parse_tensor_response(response_json)
                return results, api_time, True, None
            else:
                return [], api_time, False, f"HTTP {response.status_code}"
                
        except Exception as e:
            return [], 0.0, False, str(e)
    
    def run_test(self, df: pd.DataFrame, output_folder: str, rows_per_file: int = 100000):
        """Run complete test on all transactions."""
        print(f"\n--- Running Test: {self.api_name} ---")
        
        test_start = time.time()
        
        batch_times = []
        batch_numbers = []
        memory_checks = []
        
        os.makedirs(output_folder, exist_ok=True)
        
        num_batches = len(df) // self.batch_size
        last_memory_check = time.time()
        
        file_counter = 1
        rows_in_current_file = 0
        current_file_results = []
        
        print(f"Total batches: {num_batches}")
        
        for batch_num in range(num_batches):
            start_idx = batch_num * self.batch_size
            end_idx = start_idx + self.batch_size
            batch_df = df.iloc[start_idx:end_idx]
            
            descriptions = batch_df['description'].fillna('').tolist()
            memos = batch_df['memo'].fillna('').tolist()
            
            results, api_time, success, error_msg = self.send_batch_request(descriptions, memos)
            
            for i, (_, row) in enumerate(batch_df.iterrows()):
                transaction_id = start_idx + i + 1
                output_json = json.dumps(results[i]) if i < len(results) else "{}"
                
                result_row = {
                    'transaction_id': transaction_id,
                    'description': row['description'],
                    'memo': row['memo'],
                    'outputs_json': output_json
                }
                
                current_file_results.append(result_row)
                rows_in_current_file += 1
                
                if rows_in_current_file >= rows_per_file:
                    output_csv = os.path.join(output_folder, f'output_part_{file_counter}.csv')
                    pd.DataFrame(current_file_results).to_csv(output_csv, index=False)
                    print(f"Saved: {output_csv}")
                    
                    file_counter += 1
                    rows_in_current_file = 0
                    current_file_results = []
            
            batch_times.append(api_time)
            batch_numbers.append(batch_num + 1)
            
            current_time = time.time()
            
            if current_time - last_memory_check >= 300:
                current_memory = float(input(f"Enter current memory after batch {batch_num + 1} (MB): "))
                memory_checks.append((batch_num + 1, current_memory))
                
                elapsed = current_time - test_start
                print(f"Batch {batch_num + 1}/{num_batches}: Memory={current_memory:.1f}MB, API Time={api_time:.2f}s")
                
                last_memory_check = current_time
            else:
                print(f"Processed batch {batch_num + 1}/{num_batches}", end='\r')
        
        if rows_in_current_file > 0:
            output_csv = os.path.join(output_folder, f'output_part_{file_counter}.csv')
            pd.DataFrame(current_file_results).to_csv(output_csv, index=False)
            print(f"\nSaved: {output_csv}")
        
        elapsed_time = time.time() - test_start
        avg_batch_time = sum(batch_times) / len(batch_times)
        
        print(f"\n--- Test Summary: {self.api_name} ---")
        print(f"Total batches: {num_batches}")
        print(f"Total elapsed time: {elapsed_time:.2f}s")
        print(f"Avg API time per batch: {avg_batch_time:.2f}s")
        print(f"\nMemory checks:")
        for batch, memory in memory_checks:
            print(f"  Batch {batch}: {memory:.1f} MB")
        
        return {
            'test_name': self.api_name,
            'batches': batch_numbers,
            'batch_times': batch_times,
            'elapsed_time': elapsed_time,
            'avg_batch_time': avg_batch_time,
            'memory_checks': memory_checks
        }


def print_sample_outputs(output_folder: str):
    """
    Print sample transactions with their debatched outputs for verification.
    Shows: 2 fully empty, 2 partial (with empty strings), 1 full (no empty strings).
    """
    print(f"\n--- Sample Outputs from {output_folder} ---")
    
    csv_files = sorted([f for f in os.listdir(output_folder) if f.startswith('output_part_')])
    if not csv_files:
        print("No output files found!")
        return
    
    first_csv = os.path.join(output_folder, csv_files[0])
    df = pd.read_csv(first_csv)
    
    fully_empty = []
    partial_empty = []
    full_no_empty = []
    
    for idx, row in df.iterrows():
        try:
            output_json = json.loads(row['outputs_json'])
            
            all_empty_arrays = True
            has_empty_strings = False
            has_non_empty = False
            
            for output in output_json.get('outputs', []):
                data = output.get('data', [])
                
                if len(data) == 0:
                    continue
                else:
                    all_empty_arrays = False
                    if "" in data:
                        has_empty_strings = True
                    if any(val != "" for val in data):
                        has_non_empty = True
            
            if all_empty_arrays:
                fully_empty.append((idx, row))
            elif has_empty_strings and has_non_empty:
                partial_empty.append((idx, row))
            elif has_non_empty and not has_empty_strings:
                full_no_empty.append((idx, row))
                
        except Exception as e:
            continue
    
    print(f"\n{'#'*80}")
    print("FULLY EMPTY TRANSACTIONS (all data arrays empty)")
    print(f"{'#'*80}")
    
    for i in range(min(2, len(fully_empty))):
        idx, row = fully_empty[i]
        print(f"\n{'='*80}")
        print(f"Transaction ID: {row['transaction_id']}")
        print(f"{'='*80}")
        print(f"\nDescription: {row['description']}")
        print(f"Memo: {row['memo']}")
        print(f"\nDebatched Output JSON:")
        
        output_json = json.loads(row['outputs_json'])
        print(json.dumps(output_json, indent=2))
        print(f"\n{'='*80}")
    
    print(f"\n{'#'*80}")
    print("PARTIAL TRANSACTIONS (has data with empty strings)")
    print(f"{'#'*80}")
    
    for i in range(min(2, len(partial_empty))):
        idx, row = partial_empty[i]
        print(f"\n{'='*80}")
        print(f"Transaction ID: {row['transaction_id']}")
        print(f"{'='*80}")
        print(f"\nDescription: {row['description']}")
        print(f"Memo: {row['memo']}")
        print(f"\nDebatched Output JSON:")
        
        output_json = json.loads(row['outputs_json'])
        print(json.dumps(output_json, indent=2))
        print(f"\n{'='*80}")
    
    print(f"\n{'#'*80}")
    print("FULL TRANSACTION (no empty strings)")
    print(f"{'#'*80}")
    
    if len(full_no_empty) > 0:
        idx, row = full_no_empty[0]
        print(f"\n{'='*80}")
        print(f"Transaction ID: {row['transaction_id']}")
        print(f"{'='*80}")
        print(f"\nDescription: {row['description']}")
        print(f"Memo: {row['memo']}")
        print(f"\nDebatched Output JSON:")
        
        output_json = json.loads(row['outputs_json'])
        print(json.dumps(output_json, indent=2))
        print(f"\n{'='*80}")
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Fully empty transactions found: {len(fully_empty)}")
    print(f"Partial transactions found: {len(partial_empty)}")
    print(f"Full transactions found: {len(full_no_empty)}")


def main():
    
    INPUT_CSV = 'input_data.csv'
    API_1_URL = 'PLACEHOLDER_API_1_URL'
    API_2_URL = 'PLACEHOLDER_API_2_URL'
    BATCH_SIZE = 50
    ROWS_PER_FILE = 100000
    
    print("Loading data...")
    df = pd.read_csv(INPUT_CSV, usecols=['description', 'memo'])
    print(f"Loaded {len(df)} transactions")
    
    print("\n" + "="*60)
    print("TESTING API 1")
    print("="*60)
    api1_tester = APITester('api_1', API_1_URL, BATCH_SIZE)
    api1_summary = api1_tester.run_test(df, 'output/api_1', ROWS_PER_FILE)
    
    results_json_path = os.path.join('output/api_1', 'results.json')
    with open(results_json_path, 'w') as f:
        json.dump(api1_summary, f, indent=2)
    print(f"Metrics saved: {results_json_path}")
    
    print_sample_outputs('output/api_1')
    
    print("\n" + "="*60)
    print("Cooldown period: 2 minutes...")
    print("="*60)
    time.sleep(120)
    
    print("\n" + "="*60)
    print("TESTING API 2")
    print("="*60)
    api2_tester = APITester('api_2', API_2_URL, BATCH_SIZE)
    api2_summary = api2_tester.run_test(df, 'output/api_2', ROWS_PER_FILE)
    
    results_json_path = os.path.join('output/api_2', 'results.json')
    with open(results_json_path, 'w') as f:
        json.dump(api2_summary, f, indent=2)
    print(f"Metrics saved: {results_json_path}")
    
    print_sample_outputs('output/api_2')
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETE")
    print("="*60)
    print("\nRun compare_output.py to analyze differences between APIs")


if __name__ == "__main__":
    main()
