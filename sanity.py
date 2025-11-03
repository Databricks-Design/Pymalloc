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
        Parse tensor response and de-flatten to per-transaction JSON objects.
        """
        outputs = response_json.get('outputs', [])
        if not outputs:
            return []
        
        shape = outputs[0].get('shape', [])
        if len(shape) != 2:
            return []
        
        batch_size, max_entities = shape
        
        output_dict = {}
        for output in outputs:
            name = output['name']
            data = output['data']
            output_dict[name] = data
        
        results = []
        for i in range(batch_size):
            transaction_outputs = []
            
            for output_name, data_array in output_dict.items():
                transaction_data = []
                
                for j in range(max_entities):
                    idx = i * max_entities + j
                    value = data_array[idx] if idx < len(data_array) else ""
                    
                    if value != "":
                        transaction_data.append(value)
                
                transaction_outputs.append({
                    "name": output_name,
                    "data": transaction_data
                })
            
            transaction_json = {
                "model_name": response_json.get('model_name', ''),
                "model_version": response_json.get('model_version', ''),
                "outputs": transaction_outputs
            }
            results.append(transaction_json)
        
        return results
    
    def send_batch_request(self, descriptions: List[str], memos: List[str]) -> tuple:
        """Send batch request to API and return parsed results."""
        payload = self.build_tensor_payload(descriptions, memos)
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                response_json = response.json()
                results = self.parse_tensor_response(response_json)
                return results, True, None
            else:
                return [], False, f"HTTP {response.status_code}"
                
        except Exception as e:
            return [], False, str(e)
    
    def run_test(self, df: pd.DataFrame, output_folder: str, rows_per_file: int = 100000):
        """Run complete test on all transactions."""
        print(f"\n--- Running Test: {self.api_name} ---")
        
        # Get baseline memory
        baseline_memory = float(input("Enter baseline memory (MB): "))
        print(f"Baseline memory: {baseline_memory:.1f} MB")
        
        test_start = time.time()
        
        batch_times = []
        batch_numbers = []
        
        # Track memory checks for printing
        memory_checks = [(0, baseline_memory)]  # (batch_number, memory)
        
        os.makedirs(output_folder, exist_ok=True)
        
        num_batches = len(df) // self.batch_size
        last_memory_check = time.time()
        
        file_counter = 1
        rows_in_current_file = 0
        current_file_results = []
        
        print(f"Total batches: {num_batches}")
        
        for batch_num in range(num_batches):
            batch_start = time.time()
            
            start_idx = batch_num * self.batch_size
            end_idx = start_idx + self.batch_size
            batch_df = df.iloc[start_idx:end_idx]
            
            descriptions = batch_df['description'].fillna('').tolist()
            memos = batch_df['memo'].fillna('').tolist()
            
            results, success, error_msg = self.send_batch_request(descriptions, memos)
            
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
            
            batch_time = time.time() - batch_start
            batch_times.append(batch_time)
            batch_numbers.append(batch_num + 1)
            
            current_time = time.time()
            
            # Check memory every 5 minutes
            if current_time - last_memory_check >= 300:
                current_memory = float(input(f"Enter current memory after batch {batch_num + 1} (MB): "))
                memory_checks.append((batch_num + 1, current_memory))
                
                elapsed = current_time - test_start
                print(f"Batch {batch_num + 1}/{num_batches}: Memory={current_memory:.1f}MB, Time={batch_time:.2f}s")
                
                last_memory_check = current_time
            else:
                print(f"Processed batch {batch_num + 1}/{num_batches}", end='\r')
        
        if rows_in_current_file > 0:
            output_csv = os.path.join(output_folder, f'output_part_{file_counter}.csv')
            pd.DataFrame(current_file_results).to_csv(output_csv, index=False)
            print(f"\nSaved: {output_csv}")
        
        # Get final memory
        final_memory = float(input("\nEnter final memory (MB): "))
        memory_checks.append((num_batches, final_memory))
        
        elapsed_time = time.time() - test_start
        avg_batch_time = sum(batch_times) / len(batch_times)
        
        # Print summary
        print(f"\n--- Test Summary: {self.api_name} ---")
        print(f"Total batches: {num_batches}")
        print(f"Total elapsed time: {elapsed_time:.2f}s")
        print(f"Avg batch time: {avg_batch_time:.2f}s")
        print(f"\nMemory checks:")
        for batch, memory in memory_checks:
            print(f"  Batch {batch}: {memory:.1f} MB")
        
        return {
            'test_name': self.api_name,
            'batches': batch_numbers,
            'batch_times': batch_times,
            'elapsed_time': elapsed_time,
            'avg_batch_time': avg_batch_time
        }


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
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETE")
    print("="*60)
    print("\nRun compare_output.py to analyze differences between APIs")


if __name__ == "__main__":
    main()
