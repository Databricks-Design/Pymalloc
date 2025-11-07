def print_sample_outputs(output_folder: str, num_samples: int = 2):
    """
    Print sample transactions with their debatched outputs for verification.
    """
    print(f"\n--- Sample Outputs from {output_folder} ---")
    
    # Read the first output CSV file
    csv_files = sorted([f for f in os.listdir(output_folder) if f.startswith('output_part_')])
    if not csv_files:
        print("No output files found!")
        return
    
    first_csv = os.path.join(output_folder, csv_files[0])
    df = pd.read_csv(first_csv, nrows=num_samples)
    
    for idx, row in df.iterrows():
        print(f"\n{'='*80}")
        print(f"Transaction ID: {row['transaction_id']}")
        print(f"{'='*80}")
        print(f"\nDescription: {row['description']}")
        print(f"Memo: {row['memo']}")
        print(f"\nDebatched Output JSON:")
        
        # Parse and pretty print the JSON
        output_json = json.loads(row['outputs_json'])
        print(json.dumps(output_json, indent=2))
        print(f"\n{'='*80}")


# Add this at the end of main() function, before the final print statements:

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
    
    # Print sample outputs from API 1
    print_sample_outputs('output/api_1', num_samples=2)
    
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
    
    # Print sample outputs from API 2
    print_sample_outputs('output/api_2', num_samples=2)
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETE")
    print("="*60)
    print("\nRun compare_output.py to analyze differences between APIs")
