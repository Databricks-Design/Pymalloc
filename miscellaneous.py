def print_sample_outputs(output_folder: str):
    """
    Print sample transactions with their debatched outputs for verification.
    Shows: first 2 transactions + 2 transactions with empty string padding
    """
    print(f"\n--- Sample Outputs from {output_folder} ---")
    
    # Read the first output CSV file
    csv_files = sorted([f for f in os.listdir(output_folder) if f.startswith('output_part_')])
    if not csv_files:
        print("No output files found!")
        return
    
    first_csv = os.path.join(output_folder, csv_files[0])
    df = pd.read_csv(first_csv)
    
    # Print first 2 transactions
    print(f"\n{'#'*80}")
    print("FIRST 2 TRANSACTIONS")
    print(f"{'#'*80}")
    
    for idx in range(min(2, len(df))):
        row = df.iloc[idx]
        print(f"\n{'='*80}")
        print(f"Transaction ID: {row['transaction_id']}")
        print(f"{'='*80}")
        print(f"\nDescription: {row['description']}")
        print(f"Memo: {row['memo']}")
        print(f"\nDebatched Output JSON:")
        
        output_json = json.loads(row['outputs_json'])
        print(json.dumps(output_json, indent=2))
        print(f"\n{'='*80}")
    
    # Find transactions with empty strings in outputs
    print(f"\n{'#'*80}")
    print("TRANSACTIONS WITH EMPTY STRING PADDING (NULL VALUES)")
    print(f"{'#'*80}")
    
    samples_found = 0
    for idx, row in df.iterrows():
        if samples_found >= 2:
            break
            
        try:
            output_json = json.loads(row['outputs_json'])
            
            # Check if any output has empty strings
            has_empty = False
            for output in output_json.get('outputs', []):
                data = output.get('data', [])
                if '' in data:
                    has_empty = True
                    break
            
            if has_empty:
                print(f"\n{'='*80}")
                print(f"Transaction ID: {row['transaction_id']}")
                print(f"{'='*80}")
                print(f"\nDescription: {row['description']}")
                print(f"Memo: {row['memo']}")
                print(f"\nDebatched Output JSON (with empty strings):")
                print(json.dumps(output_json, indent=2))
                print(f"\n{'='*80}")
                samples_found += 1
                
        except Exception as e:
            continue
    
    if samples_found == 0:
        print("\nNo transactions with empty string padding found in sample.")


# Updated main() function with the new print_sample_outputs call:


    print_sample_outputs('output/api_1')
    
    
