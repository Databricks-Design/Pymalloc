import re
import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from bs4 import BeautifulSoup
import numpy as np
import sys
import traceback

def find_graph_data_in_scripts(soup):
    """
    Searches <script> tags for embedded JSON data for the graph.
    """
    print("🔍 Searching <script> tags for embedded graph data...")
    
    # This regex looks for a JS variable assignment (e.g., data = [...]) 
    # that contains a large JSON array of objects.
    # We look for "Memory Usage" since we know that's the name of the plot.
    
    data_regex = re.compile(r'(\[.*?\{.*?"Memory Usage".*?\}\s*?,\s*?\{.*?\}_.*?\])', re.DOTALL | re.MULTILINE)
    
    all_scripts = soup.find_all('script')
    
    for script in all_scripts:
        if script.string:
            match = data_regex.search(script.string)
            if match:
                data_string = match.group(1)
                print(f"✓ Found potential JSON data string! (Length: {len(data_string)})")
                
                # Clean up the string (it might be part of a JS var, e.g., "data = [...]")
                # This finds the first '[' and the last ']'
                json_start = data_string.find('[')
                json_end = data_string.rfind(']')
                
                if json_start != -1 and json_end != -1:
                    data_string = data_string[json_start : json_end + 1]
                    
                    try:
                        # Try to parse it as JSON
                        data = json.loads(data_string)
                        print(f"✓ Successfully parsed JSON with {len(data)} data points!")
                        return data
                    except json.JSONDecodeError as e:
                        print(f"⚠ Found string, but failed to parse as JSON: {e}")
                        
    print("✗ Could not find any embedded JSON data in <script> tags.")
    return None

def plot_from_json_data(data):
    """
    Plots the graph from the extracted JSON data.
    """
    if not data or len(data) < 2:
        print("✗ No data to plot.")
        return

    # --- We need to figure out the keys ---
    first_point = data[0]
    print(f"🔍 Inspecting first data point keys: {first_point.keys()}")

    # --- Guesses for the key names ---
    time_key = None
    memory_key = None

    for key in first_point.keys():
        if "time" in key.lower() or "date" in key.lower() or "epoch" in key.lower() or "ts" in key.lower():
            time_key = key
    
    # The name of the path was "Memory Usage"
    if "Memory Usage" in first_point:
        memory_key = "Memory Usage"
    else: # Fallback
        for key in first_point.keys():
             if "memory" in key.lower() or "usage" in key.lower():
                memory_key = key
            
    if not time_key or not memory_key:
        print(f"✗ Could not automatically determine 'time' and 'memory' keys from: {first_point.keys()}")
        print("Please inspect the keys and modify the script.")
        return

    print(f"✓ Using '{time_key}' for time and '{memory_key}' for memory.")

    # --- Extract data ---
    time_array_raw = []
    memory_array = []
    
    for point in data:
        # Check that the keys exist and the value is a number
        if point.get(time_key) is not None and point.get(memory_key) is not None:
            try:
                time_array_raw.append(float(point[time_key]))
                memory_array.append(float(point[memory_key]))
            except (ValueError, TypeError):
                # Skip points with non-numeric data
                pass

    if not time_array_raw or not memory_array:
        print("✗ Failed to extract numeric data. Are the values numbers?")
        return
        
    print(f"✓ Extracted {len(memory_array)} data points.")
    
    # --- Convert time ---
    # We need to guess the format. Is it seconds? Milliseconds?
    time_array = []
    
    # A common check: if the number is huge, it's probably milliseconds
    if np.mean(time_array_raw) > 1_000_000_000_000: # 1 trillion (e.g., 1678886400000)
        print("✓ Detected time as MILLISECONDS.")
        time_array = [datetime.fromtimestamp(t / 1000.0) for t in time_array_raw]
    else: # e.g., 1678886400
        print("✓ Detected time as SECONDS.")
        time_array = [datetime.fromtimestamp(t) for t in time_array_raw]

    # --- Plot the data ---
    print("\n📈 Creating graphs...")
    fig1, ax1 = plt.subplots(figsize=(16, 6))
    
    ax1.fill_between(time_array, memory_array, alpha=0.5, color='#E57373', label='Memory Usage')
    ax1.plot(time_array, memory_array, color='#C62828', linewidth=1.5)
    ax1.set_xlabel('Time', fontsize=13, fontweight='bold')
    ax1.set_ylabel('Memory Usage (MB)', fontsize=13, fontweight='bold')
    ax1.set_title('Memory Usage - Full Timeline (from JSON data)', fontsize=15, fontweight='bold', pad=20)
    ax1.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
    ax1.legend(loc='upper right', fontsize=11)
    
    # Format x-axis
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%I:%M %p'))
    total_seconds = (time_array[-1] - time_array[0]).total_seconds()
    if total_seconds > 0:
        if total_seconds <= 3600 * 3: ax1.xaxis.set_major_locator(mdates.MinuteLocator(interval=15))
        elif total_seconds <= 3600 * 12: ax1.xaxis.set_major_locator(mdates.HourLocator(interval=1))
        else: ax1.xaxis.set_major_locator(mdates.HourLocator(interval=2))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    full_output = 'memory_usage_full_from_json.png'
    plt.savefig(full_output, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {full_output}")
    
    plt.show()

def main_json_extractor(html_file):
    """
    Main function to find, extract, and plot graph data from <script> tags.
    """
    print("\n" + "="*70)
    print("GRAPH JSON DATA EXTRACTOR")
    print("="*70)
    
    try:
        print(f"\n📂 Reading: {html_file}")
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        print("✓ HTML parsed successfully")

        # Find the data
        graph_data = find_graph_data_in_scripts(soup)
        
        if graph_data:
            # Plot the data
            plot_from_json_data(graph_data)
        else:
            print("✗ Could not find any embedded JSON data.")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        traceback.print_exc()

# Main execution
if __name__ == "__main__":
    if len(sys.argv) > 1:
        html_file = sys.argv[1]
    else:
        html_file = input("Enter path to HTML file: ").strip()
    
    main_json_extractor(html_file)
