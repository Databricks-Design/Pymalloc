import pandas as pd
import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import os

class APITester:
    """
    Tests API endpoints by sending batched requests and tracking performance metrics.
    Processes transactions in batches and collects timing, success rate, and response data.
    """
    
    def __init__(self, api_name: str, api_url: str, batch_size: int = 50):
        self.api_name = api_name
        self.api_url = api_url
        self.batch_size = batch_size
        self.headers = {'Content-Type': 'application/json'}
        
        self.batch_times = []
        self.api_response_times = []
        self.http_status_codes = []
        self.success_flags = []
        self.entities_per_batch = []
        
        self.all_results = []
        
    def build_tensor_payload(self, descriptions: List[str], memos: List[str]) -> Dict:
        """
        Build tensor-based payload for batch inference.
        Shape dimensions represent [batch_size, sequence_length].
        """
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
        Converts flattened array structure back to individual transaction results.
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
        """
        Send batch request to API and return parsed results with timing.
        Returns: (results_list, api_response_time, http_status, success, error_msg)
        """
        payload = self.build_tensor_payload(descriptions, memos)
        
        try:
            request_start = time.time()
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            api_time = time.time() - request_start
            
            status_code = response.status_code
            
            if status_code == 200:
                response_json = response.json()
                results = self.parse_tensor_response(response_json)
                return results, api_time, status_code, True, None
            else:
                return [], api_time, status_code, False, f"HTTP {status_code}"
                
        except Exception as e:
            return [], 0, 0, False, str(e)
    
    def run_test(self, df: pd.DataFrame, output_folder: str):
        """
        Run complete test on all transactions.
        Process in batches, track metrics, save results.
        """
        print(f"\n=== Running Test: {self.api_name} ===")
        print(f"Total transactions: {len(df)}")
        print(f"Batch size: {self.batch_size}")
        print(f"Total batches: {len(df) // self.batch_size}")
        
        os.makedirs(output_folder, exist_ok=True)
        
        print("\n--- Infrastructure Metrics (Baseline) ---")
        baseline_cpu = float(input("Enter baseline CPU usage (0.0-1.0): "))
        baseline_memory = float(input("Enter baseline memory (MB): "))
        
        test_start = time.time()
        num_batches = len(df) // self.batch_size
        last_print_time = time.time()
        
        for batch_num in range(num_batches):
            batch_start = time.time()
            
            start_idx = batch_num * self.batch_size
            end_idx = start_idx + self.batch_size
            batch_df = df.iloc[start_idx:end_idx]
            
            descriptions = batch_df['description'].fillna('').tolist()
            memos = batch_df['memo'].fillna('').tolist()
            
            results, api_time, status_code, success, error_msg = self.send_batch_request(
                descriptions, memos
            )
            
            for i, (_, row) in enumerate(batch_df.iterrows()):
                transaction_id = start_idx + i + 1
                output_json = json.dumps(results[i]) if i < len(results) else "{}"
                
                self.all_results.append({
                    'transaction_id': transaction_id,
                    'description': row['description'],
                    'memo': row['memo'],
                    'outputs_json': output_json
                })
            
            batch_time = time.time() - batch_start
            self.batch_times.append(batch_time)
            self.api_response_times.append(api_time)
            self.http_status_codes.append(status_code)
            self.success_flags.append(success)
            
            total_entities = sum(
                len(r['outputs'][0]['data']) if r.get('outputs') else 0 
                for r in results
            )
            self.entities_per_batch.append(total_entities)
            
            current_time = time.time()
            if current_time - last_print_time >= 300:
                elapsed = current_time - test_start
                progress = (batch_num + 1) / num_batches * 100
                print(f"[{elapsed/60:.1f} min] Batch {batch_num + 1}/{num_batches} "
                      f"({progress:.1f}%) - Last batch: {batch_time:.2f}s")
                last_print_time = current_time
        
        test_end = time.time()
        total_elapsed = test_end - test_start
        
        print("\n--- Infrastructure Metrics (Final) ---")
        final_cpu = float(input("Enter final CPU usage (0.0-1.0): "))
        final_memory = float(input("Enter final memory (MB): "))
        
        results_df = pd.DataFrame(self.all_results)
        output_csv = os.path.join(output_folder, 'output_part_1.csv')
        results_df.to_csv(output_csv, index=False)
        print(f"\nResults saved: {output_csv}")
        
        successful_batches = sum(self.success_flags)
        success_rate = (successful_batches / len(self.success_flags)) * 100
        
        summary = {
            'test_name': self.api_name,
            'api_endpoint': self.api_url,
            'test_start_time': datetime.fromtimestamp(test_start).isoformat(),
            'test_end_time': datetime.fromtimestamp(test_end).isoformat(),
            
            'batch_size': self.batch_size,
            'total_batches': num_batches,
            'total_transactions': len(df),
            
            'batches': list(range(1, num_batches + 1)),
            'batch_times': self.batch_times,
            'api_response_times': self.api_response_times,
            'http_status_codes': self.http_status_codes,
            'success_flags': self.success_flags,
            'entities_per_batch': self.entities_per_batch,
            
            'total_elapsed_time': total_elapsed,
            'avg_batch_time': sum(self.batch_times) / len(self.batch_times),
            'avg_api_response_time': sum(self.api_response_times) / len(self.api_response_times),
            'min_batch_time': min(self.batch_times),
            'max_batch_time': max(self.batch_times),
            
            'successful_batches': successful_batches,
            'failed_batches': num_batches - successful_batches,
            'success_rate': success_rate,
            
            'throughput_tps': len(df) / total_elapsed,
            'throughput_bps': num_batches / total_elapsed,
            
            'infrastructure': {
                'baseline_cpu': baseline_cpu,
                'final_cpu': final_cpu,
                'cpu_increase': final_cpu - baseline_cpu,
                'baseline_memory_mb': baseline_memory,
                'final_memory_mb': final_memory,
                'memory_increase_mb': final_memory - baseline_memory
            }
        }
        
        results_json_path = os.path.join(output_folder, 'results.json')
        with open(results_json_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"Metrics saved: {results_json_path}")
        
        print(f"\n=== Test Complete: {self.api_name} ===")
        print(f"Total time: {total_elapsed:.2f}s ({total_elapsed/60:.1f} min)")
        print(f"Avg batch time: {summary['avg_batch_time']:.2f}s")
        print(f"Avg API response time: {summary['avg_api_response_time']:.2f}s")
        print(f"Success rate: {success_rate:.1f}%")
        print(f"Throughput: {summary['throughput_tps']:.2f} transactions/sec")
        print(f"CPU increase: {summary['infrastructure']['cpu_increase']:.2f}")
        print(f"Memory increase: {summary['infrastructure']['memory_increase_mb']:.1f} MB")
        
        return summary


def main():
    
    INPUT_CSV = 'input_data.csv'
    API_1_URL = 'PLACEHOLDER_API_1_URL'
    API_2_URL = 'PLACEHOLDER_API_2_URL'
    BATCH_SIZE = 50
    
    print("Loading data...")
    df = pd.read_csv(INPUT_CSV, usecols=['description', 'memo'])
    print(f"Loaded {len(df)} transactions")
    
    if len(df) > 100000:
        df = df.head(100000)
        print(f"Limited to {len(df)} transactions")
    
    print("\n" + "="*60)
    print("TESTING API 1")
    print("="*60)
    api1_tester = APITester('api_1', API_1_URL, BATCH_SIZE)
    api1_summary = api1_tester.run_test(df, 'output/api_1')
    
    print("\n" + "="*60)
    print("Cooldown period: 2 minutes...")
    print("="*60)
    time.sleep(120)
    
    print("\n" + "="*60)
    print("TESTING API 2")
    print("="*60)
    api2_tester = APITester('api_2', API_2_URL, BATCH_SIZE)
    api2_summary = api2_tester.run_test(df, 'output/api_2')
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETE")
    print("="*60)
    print("\nRun compare_output.py to analyze differences between APIs")


if __name__ == "__main__":
    main()
