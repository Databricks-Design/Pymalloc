import re
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import numpy as np

def parse_svg_path_data(d_attribute):
    """
    Parse SVG path d attribute and extract all coordinate points.
    Handles M (moveto), L (lineto), and coordinate pairs.
    """
    # Remove extra whitespace
    d_attribute = re.sub(r'\s+', ' ', d_attribute.strip())
    
    points = []
    
    # Find all number pairs (x,y coordinates)
    # Matches patterns like: "100,106.16" or "100.765,106.16"
    coord_pattern = r'([\d.]+),([\d.]+)'
    matches = re.findall(coord_pattern, d_attribute)
    
    for x, y in matches:
        points.append((float(x), float(y)))
    
    if not points:
        # Try alternate parsing - space or command separated
        alt_pattern = r'([\d.]+)\s+([\d.]+)'
        matches = re.findall(alt_pattern, d_attribute)
        for x, y in matches:
            points.append((float(x), float(y)))
    
    return points

def extract_axis_labels_and_positions(soup):
    """
    Extract x-axis and y-axis labels with their exact positions from SVG
    Handles formats like "7 PM" and "286.16MB"
    """
    x_axis_data = []  # List of (position, label) tuples
    y_axis_data = []  # List of (position, label) tuples
    
    # Find all text elements in axis tick groups
    for g_elem in soup.find_all('g', class_=lambda x: x and 'recharts-cartesian-axis-tick' in x):
        # Get the text element
        text_elem = g_elem.find('text')
        if not text_elem:
            continue
        
        # Get tspan which contains the actual label
        tspan = text_elem.find('tspan')
        if not tspan:
            continue
        
        label = tspan.get_text(strip=True)
        
        # Get position from tspan or text element
        x_pos = tspan.get('x') or text_elem.get('x')
        y_pos = tspan.get('y') or text_elem.get('y')
        
        if not x_pos:
            continue
        
        x_pos = float(x_pos)
        y_pos = float(y_pos) if y_pos else 0
        
        # Determine if this is x-axis or y-axis based on label content
        # X-axis: contains time indicators (PM, AM, or colon for time)
        # Y-axis: contains MB or is just a number
        
        if 'MB' in label.upper() or re.match(r'^\d+\.?\d*$', label):
            # Y-axis label (memory)
            y_axis_data.append((y_pos, label))
        elif 'PM' in label.upper() or 'AM' in label.upper() or ':' in label:
            # X-axis label (time)
            x_axis_data.append((x_pos, label))
        else:
            # Try to determine by position
            # If x position is small (< 200), likely y-axis
            # If x position is large (> 200), likely x-axis
            if x_pos < 200:
                y_axis_data.append((y_pos, label))
            else:
                x_axis_data.append((x_pos, label))
    
    # Sort by position
    x_axis_data.sort(key=lambda x: x[0])
    y_axis_data.sort(key=lambda x: x[0])
    
    return x_axis_data, y_axis_data

def parse_memory_label(label):
    """
    Parse memory label like "286.16MB" or "500" and return value in MB
    """
    # Remove "MB" suffix if present
    label = label.upper().replace('MB', '').strip()
    
    try:
        return float(label)
    except:
        return None

def parse_time_label(label):
    """
    Parse time label like "7 PM", "6:30 PM", "12:00 AM" etc.
    Returns datetime object
    """
    base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    label = label.strip()
    
    # Check for colon format: "6:30 PM"
    time_match = re.search(r'(\d+):(\d+)', label)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
    else:
        # No colon, just hour: "7 PM"
        hour_match = re.search(r'(\d+)', label)
        if not hour_match:
            return None
        hour = int(hour_match.group(1))
        minute = 0
    
    # Check for PM/AM
    if 'PM' in label.upper():
        if hour != 12:
            hour += 12
    elif 'AM' in label.upper():
        if hour == 12:
            hour = 0
    
    return base_date.replace(hour=hour, minute=minute)

def extract_viewbox_dimensions(soup):
    """
    Extract SVG viewBox to understand coordinate system
    """
    svg = soup.find('svg')
    if svg:
        viewbox = svg.get('viewBox')
        if viewbox:
            dims = [float(x) for x in viewbox.split()]
            return {
                'min_x': dims[0],
                'min_y': dims[1],
                'width': dims[2],
                'height': dims[3]
            }
    return None

def find_memory_usage_path(soup):
    """
    Find the Memory Usage path element from SVG
    """
    # Look for path with name="Memory Usage"
    memory_path = soup.find('path', attrs={'name': 'Memory Usage'})
    
    if memory_path:
        print("✓ Found path with name='Memory Usage'")
        return memory_path.get('d')
    
    # Look for path in recharts-area layer
    for g_elem in soup.find_all('g', class_=lambda x: x and 'recharts-area' in x):
        paths = g_elem.find_all('path', class_=lambda x: x and 'recharts-curve' in x)
        for path in paths:
            d_attr = path.get('d')
            if d_attr and len(d_attr) > 500:  # Memory path should be long
                print("✓ Found path in recharts-area layer")
                return d_attr
    
    # Fallback: find longest path
    all_paths = soup.find_all('path')
    candidate_paths = []
    
    for path in all_paths:
        d_attr = path.get('d')
        class_attr = path.get('class', [])
        if isinstance(class_attr, list):
            class_str = ' '.join(class_attr)
        else:
            class_str = str(class_attr)
        
        if d_attr and len(d_attr) > 500:
            if 'curve' in class_str.lower() or 'area' in class_str.lower():
                candidate_paths.append((len(d_attr), d_attr, class_str))
    
    if candidate_paths:
        candidate_paths.sort(reverse=True)
        print(f"✓ Found path with class: {candidate_paths[0][2]}")
        return candidate_paths[0][1]
    
    return None

def map_svg_to_data_coordinates(points, x_axis_data, y_axis_data, viewbox):
    """
    Map SVG path coordinates to actual data values using axis labels
    Returns: (time_array, memory_array)
    """
    if not points:
        return [], []
    
    x_coords = np.array([p[0] for p in points])
    y_coords = np.array([p[1] for p in points])
    
    print(f"\n📍 SVG Coordinate Ranges:")
    print(f"   X: {x_coords.min():.2f} to {x_coords.max():.2f}")
    print(f"   Y: {y_coords.min():.2f} to {y_coords.max():.2f}")
    
    # ===== Process X-axis (Time) =====
    if not x_axis_data or len(x_axis_data) < 2:
        print("⚠ Warning: No x-axis labels found, using default time range")
        base = datetime.now().replace(hour=18, minute=0, second=0, microsecond=0)
        duration = timedelta(hours=2)
        time_array = np.array([base + duration * (x - x_coords.min()) / (x_coords.max() - x_coords.min()) 
                               for x in x_coords])
    else:
        print(f"\n⏰ X-axis (Time) labels found: {len(x_axis_data)}")
        for pos, label in x_axis_data[:5]:
            print(f"   Position {pos:.2f}: '{label}'")
        if len(x_axis_data) > 5:
            print(f"   ... and {len(x_axis_data) - 5} more")
        
        # Parse time labels
        time_values = []
        positions = []
        for pos, label in x_axis_data:
            parsed_time = parse_time_label(label)
            if parsed_time:
                positions.append(pos)
                time_values.append(parsed_time)
        
        if len(time_values) < 2:
            print("⚠ Warning: Could not parse time labels, using default")
            base = datetime.now().replace(hour=18, minute=0, second=0, microsecond=0)
            duration = timedelta(hours=2)
            time_array = np.array([base + duration * (x - x_coords.min()) / (x_coords.max() - x_coords.min()) 
                                   for x in x_coords])
        else:
            # Handle midnight crossing
            if time_values[-1] < time_values[0]:
                for i in range(1, len(time_values)):
                    if time_values[i] < time_values[i-1]:
                        time_values[i] += timedelta(days=1)
            
            positions = np.array(positions)
            time_seconds = np.array([(t - time_values[0]).total_seconds() for t in time_values])
            
            # Interpolate for all x coordinates
            time_interp = np.interp(x_coords, positions, time_seconds)
            time_array = np.array([time_values[0] + timedelta(seconds=s) for s in time_interp])
            
            print(f"   ✓ Time range: {time_values[0].strftime('%I:%M %p')} to {time_values[-1].strftime('%I:%M %p')}")
    
    # ===== Process Y-axis (Memory) =====
    # SVG Y coordinates are inverted (top = 0), so we need to flip them
    if viewbox:
        y_coords_flipped = viewbox['height'] - y_coords
    else:
        y_coords_flipped = y_coords.max() - y_coords
    
    if not y_axis_data or len(y_axis_data) < 2:
        print("⚠ Warning: No y-axis labels found, normalizing to 0-1000 MB")
        y_normalized = (y_coords_flipped - y_coords_flipped.min()) / (y_coords_flipped.max() - y_coords_flipped.min())
        memory_array = y_normalized * 1000
    else:
        print(f"\n💾 Y-axis (Memory) labels found: {len(y_axis_data)}")
        for pos, label in y_axis_data[:5]:
            print(f"   Position {pos:.2f}: '{label}'")
        if len(y_axis_data) > 5:
            print(f"   ... and {len(y_axis_data) - 5} more")
        
        # Parse memory labels
        memory_values = []
        positions = []
        for pos, label in y_axis_data:
            parsed_mem = parse_memory_label(label)
            if parsed_mem is not None:
                # Y positions in SVG are also inverted
                if viewbox:
                    pos_flipped = viewbox['height'] - pos
                else:
                    # Use the max y position from the data
                    max_y_pos = max([p[0] for p in y_axis_data])
                    pos_flipped = max_y_pos - pos
                positions.append(pos_flipped)
                memory_values.append(parsed_mem)
        
        if len(memory_values) < 2:
            print("⚠ Warning: Could not parse memory labels, normalizing")
            y_normalized = (y_coords_flipped - y_coords_flipped.min()) / (y_coords_flipped.max() - y_coords_flipped.min())
            memory_array = y_normalized * 1000
        else:
            positions = np.array(positions)
            memory_values = np.array(memory_values)
            
            # Interpolate for all y coordinates
            memory_array = np.interp(y_coords_flipped, positions, memory_values)
            
            print(f"   ✓ Memory range: {memory_values.min():.2f} MB to {memory_values.max():.2f} MB")
    
    return time_array, memory_array

def plot_memory_graphs(html_file):
    """
    Main function to extract and plot memory usage with correct axis mapping
    """
    print("\n" + "="*70)
    print("MEMORY USAGE GRAPH EXTRACTOR (FIXED VERSION)")
    print("="*70)
    
    # Read HTML file
    print(f"\n📂 Reading: {html_file}")
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    print("✓ HTML parsed successfully")
    
    # Extract viewBox
    viewbox = extract_viewbox_dimensions(soup)
    if viewbox:
        print(f"✓ ViewBox: {viewbox['width']}x{viewbox['height']}")
    
    # Extract axis labels and positions
    print("\n🔍 Extracting axis labels from HTML...")
    x_axis_data, y_axis_data = extract_axis_labels_and_positions(soup)
    
    if not x_axis_data:
        print("⚠ No x-axis labels found!")
    if not y_axis_data:
        print("⚠ No y-axis labels found!")
    
    # Find Memory Usage path
    print("\n🔍 Searching for Memory Usage path...")
    d_attribute = find_memory_usage_path(soup)
    
    if not d_attribute:
        print("✗ Could not find Memory Usage path!")
        return
    
    print(f"✓ Path data length: {len(d_attribute)} characters")
    
    # Parse path data
    print("\n📊 Parsing coordinate points...")
    points = parse_svg_path_data(d_attribute)
    print(f"✓ Extracted {len(points)} coordinate points")
    
    if len(points) < 10:
        print("✗ Not enough points found!")
        return
    
    # Map coordinates to actual values
    print("\n🗺️  Mapping SVG coordinates to data values...")
    time_array, memory_array = map_svg_to_data_coordinates(points, x_axis_data, y_axis_data, viewbox)
    
    if len(time_array) == 0 or len(memory_array) == 0:
        print("✗ Failed to map coordinates!")
        return
    
    print(f"\n✓ Data prepared: {len(time_array)} points")
    print(f"  Memory range: {memory_array.min():.2f} - {memory_array.max():.2f} MB")
    print(f"  Time range: {time_array[0].strftime('%I:%M %p')} - {time_array[-1].strftime('%I:%M %p')}")
    
    # Create plots
    print("\n📈 Creating graphs...")
    
    # Figure 1: Full timeline
    fig1, ax1 = plt.subplots(figsize=(16, 6))
    
    ax1.fill_between(time_array, memory_array, alpha=0.5, color='#E57373', label='Memory Usage')
    ax1.plot(time_array, memory_array, color='#C62828', linewidth=1.5)
    ax1.set_xlabel('Time', fontsize=13, fontweight='bold')
    ax1.set_ylabel('Memory Usage (MB)', fontsize=13, fontweight='bold')
    ax1.set_title('Memory Usage - Full Timeline', fontsize=15, fontweight='bold', pad=20)
    ax1.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
    ax1.legend(loc='upper right', fontsize=11)
    
    # Format x-axis
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%I:%M %p'))
    ax1.xaxis.set_major_locator(mdates.MinuteLocator(interval=15))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    full_output = 'memory_usage_full.png'
    plt.savefig(full_output, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {full_output}")
    
    # Figure 2: Zoomed view (middle hour)
    fig2, ax2 = plt.subplots(figsize=(16, 6))
    
    # Calculate zoom range (middle hour of data)
    total_duration = (time_array[-1] - time_array[0]).total_seconds()
    zoom_start = time_array[0] + timedelta(seconds=total_duration * 0.25)
    zoom_end = time_array[0] + timedelta(seconds=total_duration * 0.75)
    
    mask = (time_array >= zoom_start) & (time_array <= zoom_end)
    
    if mask.any():
        zoom_times = time_array[mask]
        zoom_memory = memory_array[mask]
        
        ax2.fill_between(zoom_times, zoom_memory, alpha=0.5, color='#E57373', label='Memory Usage')
        ax2.plot(zoom_times, zoom_memory, color='#C62828', linewidth=2, marker='o', 
                markersize=4, markevery=max(1, len(zoom_times)//50))
        ax2.set_xlabel('Time', fontsize=13, fontweight='bold')
        ax2.set_ylabel('Memory Usage (MB)', fontsize=13, fontweight='bold')
        ax2.set_title(f'Memory Usage - Magnified View ({zoom_start.strftime("%I:%M %p")} - {zoom_end.strftime("%I:%M %p")})', 
                     fontsize=15, fontweight='bold', pad=20)
        ax2.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
        ax2.legend(loc='upper right', fontsize=11)
        
        # More granular time labels
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%I:%M %p'))
        ax2.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        ax2.set_xlim(zoom_start, zoom_end)
        
        print(f"✓ Zoomed view: {len(zoom_times)} points")
    else:
        ax2.text(0.5, 0.5, 'No data in zoom range', 
                ha='center', va='center', transform=ax2.transAxes, fontsize=14, color='red')
        print("⚠ No data points in zoom range")
    
    plt.tight_layout()
    zoom_output = 'memory_usage_zoomed.png'
    plt.savefig(zoom_output, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {zoom_output}")
    
    plt.show()
    
    print("\n" + "="*70)
    print("✅ COMPLETE!")
    print("="*70)
    print(f"📊 Total data points: {len(points)}")
    print(f"📈 Graphs saved:")
    print(f"   - {full_output}")
    print(f"   - {zoom_output}")
    print("="*70 + "\n")

# Main execution
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        html_file = sys.argv[1]
    else:
        html_file = input("Enter path to HTML file: ").strip()
    
    try:
        plot_memory_graphs(html_file)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
