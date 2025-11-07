def extract_axis_info(soup):
    """
    Extract x-axis and y-axis information from SVG text elements
    (Updated to handle <tspan> children and text labels like '286.10MB')
    """
    axis_info = {
        'x_labels': [],
        'y_labels': [],
        'x_positions': [],
        'y_positions': []
    }
    
    # Find all text elements
    for text_elem in soup.find_all('text'):
        
        # Get position if available
        x_pos = text_elem.get('x')
        y_pos = text_elem.get('y')

        # Find the first <tspan> inside the <text> element
        tspan = text_elem.find('tspan')
        
        if tspan:
            text_content = tspan.get_text(strip=True)
        else:
            # Fallback if there's no tspan
            text_content = text_elem.get_text(strip=True)

        # Check if it's a time label (for x-axis)
        if re.search(r'\d+:\d+', text_content) or 'PM' in text_content or 'AM' in text_content:
            axis_info['x_labels'].append(text_content)
            if x_pos:
                axis_info['x_positions'].append(float(x_pos))
        
        # Check if it's a memory label (e.g., "286.10MB", "0B")
        elif re.search(r'(MB|GB|B)$', text_content, re.IGNORECASE):
            # Extract just the number part
            num_match = re.match(r'^([\d.]+)', text_content)
            if num_match:
                label_value = num_match.group(1) # This will be "286.10" or "0"
                axis_info['y_labels'].append(label_value)
                if y_pos:
                    axis_info['y_positions'].append(float(y_pos))
            
    return axis_info





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
