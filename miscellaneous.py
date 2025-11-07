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
