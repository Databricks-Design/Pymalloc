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
    
    # Split by commands (M, L, etc.) but keep the coordinates
    # Pattern to match: M or L followed by coordinates
    points = []
    
    # Find all number pairs (x,y coordinates)
    # Matches patterns like: "100,106.16" or "100.765,106.16"
    coord_pattern = r'([\d.]+),([\d.]+)'
    matches = re.findall(coord_pattern, d_attribute)
    
    for x, y in matches:
        points.append((float(x), float(y)))
    
    if not points:
        # Try alternate parsing - space or command separated
        # Match: number space/command number
        alt_pattern = r'([\d.]+)\s+([\d.]+)'
        matches = re.findall(alt_pattern, d_attribute)
        for x, y in matches:
            points.append((float(x), float(y)))
    
    return points

def extract_axis_info(soup):
    """
    Extract x-axis and y-axis information from SVG text elements
    Uses the exact structure from recharts: 
    <g class="recharts-layer recharts-cartesian-axis-tick">
      <text orientation="bottom/left">
        <tspan>label</tspan>
      </text>
    </g>
    """
    axis_info = {
        'x_labels': [],
        'y_labels': [],
        'x_positions': [],
        'y_positions': []
    }
    
    # Find all axis tick groups
    tick_groups = soup.find_all('g', class_=lambda x: x and 'recharts-cartesian-axis-tick' in x)
    
    for tick_group in tick_groups:
        # Get the text element
        text_elem = tick_group.find('text')
        if not text_elem:
            continue
        
        # Check orientation to determine if x-axis or y-axis
        orientation = text_elem.get('orientation', '')
        
        # Get the tspan which contains the actual label
        tspan = text_elem.find('tspan')
        if not tspan:
            # Fallback to text content if no tspan
            label = text_elem.get_text(strip=True)
        else:
            label = tspan.get_text(strip=True)
        
        if not label:
            continue
        
        # Get positions from text element
        x_pos = text_elem.get('x')
        y_pos = text_elem.get('y')
        
        # Determine axis based on orientation attribute
        if orientation == 'bottom':
            # X-axis (time labels)
            axis_info['x_labels'].append(label)
            if x_pos:
                axis_info['x_positions'].append(float(x_pos))
        elif orientation == 'left' or orientation == 'right':
            # Y-axis (memory labels)
            axis_info['y_labels'].append(label)
            if y_pos:
                axis_info['y_positions'].append(float(y_pos))
        else:
            # Fallback: determine by content if no orientation
            # Time labels contain AM/PM or colon
            if re.search(r'\d+\s*(AM|PM|am|pm)', label) or re.search(r'\d+:\d+', label):
                axis_info['x_labels'].append(label)
                if x_pos:
                    axis_info['x_positions'].append(float(x_pos))
            # Memory labels contain MB/GB/KB or are plain numbers
            elif re.search(r'\d+\.?\d*\s*(MB|GB|KB|B|mb|gb|kb)', label, re.IGNORECASE) or re.match(r'^\d+(\.\d+)?$', label):
                axis_info['y_labels'].append(label)
                if y_pos:
                    axis_info['y_positions'].append(float(y_pos))
    
    return axis_info

def find_memory_usage_path(soup):
    """
    Find the Memory Usage path element from SVG
    """
    # Look for path with name="Memory Usage"
    memory_path = soup.find('path', attrs={'name': 'Memory Usage'})
    
    if memory_path:
        print("✓ Found path with name='Memory Usage'")
        return memory_path.get('d')
    
    # Look for path in recharts-layer with recharts-area class
    for g_elem in soup.find_all('g', class_=lambda x: x and 'recharts-area' in x):
        paths = g_elem.find_all('path', class_=lambda x: x and 'recharts-curve' in x)
        for path in paths:
            d_attr = path.get('d')
            if d_attr and len(d_attr) > 500:  # Memory path should be long
                print("✓ Found path in recharts-area layer")
                return d_attr
    
    # Fallback: find longest path with class containing 'curve' or 'area'
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
        # Sort by length and take longest
        candidate_paths.sort(reverse=True)
        print(f"✓ Found path with class: {candidate_paths[0][2]}")
        return candidate_paths[0][1]
    
    return None

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

def map_coordinates_to_values(points, axis_info, viewbox):
    """
    Map SVG coordinates to actual data values using axis labels
    """
    if not points:
        return [], []
    
    x_coords = np.array([p[0] for p in points])
    y_coords = np.array([p[1] for p in points])
    
    print(f"X range: {x_coords.min():.2f} to {x_coords.max():.2f}")
    print(f"Y range: {y_coords.min():.2f} to {y_coords.max():.2f}")
    
    # Invert Y coordinates (SVG is top-down)
    if viewbox:
        y_coords = viewbox['height'] - y_coords
    else:
        y_coords = y_coords.max() - y_coords
    
    return x_coords, y_coords

def parse_time_label(time_str):
    """
    Parse time string to datetime object
    FIXED: Now handles "7 PM" format without colon
    """
    base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Extract hour and minute
    time_match = re.search(r'(\d+):(\d+)', time_str)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
    else:
        # No colon, just hour (like "7 PM")
        hour_match = re.search(r'(\d+)', time_str)
        if not hour_match:
            return None
        hour = int(hour_match.group(1))
        minute = 0
    
    # Check for PM/AM
    if 'PM' in time_str.upper() or 'pm' in time_str:
        if hour != 12:
            hour += 12
    elif 'AM' in time_str.upper() or 'am' in time_str:
        if hour == 12:
            hour = 0
    
    return base_date.replace(hour=hour, minute=minute)

def create_time_array(x_coords, axis_info):
    """
    Create time array from x coordinates and axis labels
    """
    if not axis_info['x_labels'] or len(axis_info['x_labels']) < 2:
        # Fallback to simple time range
        print("⚠ No time labels found, using default time range")
        base = datetime.now().replace(hour=18, minute=0, second=0, microsecond=0)
        duration = timedelta(hours=2)
        times = [base + duration * (x - x_coords.min()) / (x_coords.max() - x_coords.min()) 
                for x in x_coords]
        return np.array(times)
    
    # Parse time labels
    times_parsed = []
    for label in axis_info['x_labels']:
        t = parse_time_label(label)
        if t:
            times_parsed.append(t)
    
    if len(times_parsed) < 2:
        print("⚠ Could not parse time labels, using default")
        base = datetime.now().replace(hour=18, minute=0, second=0, microsecond=0)
        duration = timedelta(hours=2)
        times = [base + duration * (x - x_coords.min()) / (x_coords.max() - x_coords.min()) 
                for x in x_coords]
        return np.array(times)
    
    # Interpolate times based on x coordinates
    start_time = times_parsed[0]
    end_time = times_parsed[-1]
    
    # Handle midnight crossing
    if end_time < start_time:
        end_time += timedelta(days=1)
    
    print(f"Time range: {start_time.strftime('%I:%M %p')} to {end_time.strftime('%I:%M %p')}")
    
    # Linear interpolation
    total_duration = (end_time - start_time).total_seconds()
    times = [start_time + timedelta(seconds=total_duration * (x - x_coords.min()) / (x_coords.max() - x_coords.min())) 
            for x in x_coords]
    
    return np.array(times)

def create_memory_array(y_coords, axis_info):
    """
    Create memory array from y coordinates and axis labels
    FIXED: Now handles "286.10MB" format
    """
    if not axis_info['y_labels'] or len(axis_info['y_labels']) < 2:
        # Normalize to 0-1000 MB range
        print("⚠ No y-axis labels found, normalizing to 0-1000 MB")
        y_normalized = (y_coords - y_coords.min()) / (y_coords.max() - y_coords.min())
        return y_normalized * 1000
    
    # Parse numeric labels - FIXED: strip "MB", "GB", etc.
    y_values = []
    for label in axis_info['y_labels']:
        try:
            # Remove units (MB, GB, KB, B) and parse
            numeric_part = re.sub(r'[A-Za-z\s]+', '', label)
            value = float(numeric_part)
            
            # Convert to MB if needed
            if 'GB' in label.upper():
                value *= 1024
            elif 'KB' in label.upper():
                value /= 1024
            elif 'B' in label.upper() and 'MB' not in label.upper():
                value /= (1024 * 1024)
            
            y_values.append(value)
        except:
            pass
    
    if len(y_values) < 2:
        print("⚠ Could not parse y-axis labels, normalizing")
        y_normalized = (y_coords - y_coords.min()) / (y_coords.max() - y_coords.min())
        return y_normalized * 1000
    
    y_min = min(y_values)
    y_max = max(y_values)
    
    print(f"Memory range: {y_min:.2f} to {y_max:.2f} MB")
    
    # Linear mapping
    y_normalized = (y_coords - y_coords.min()) / (y_coords.max() - y_coords.min())
    memory = y_min + y_normalized * (y_max - y_min)
    
    return memory

def plot_memory_graphs(html_file):
    """
    Main function to extract and plot memory usage
    """
    print("\n" + "="*70)
    print("MEMORY USAGE GRAPH EXTRACTOR")
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
    
    # Extract axis information
    print("\n📏 Extracting axis information...")
    axis_info = extract_axis_info(soup)
    print(f"✓ Found {len(axis_info['x_labels'])} x-axis labels")
    print(f"✓ Found {len(axis_info['y_labels'])} y-axis labels")
    
    if axis_info['x_labels']:
        print(f"  Time labels: {axis_info['x_labels'][:5]}...")
    if axis_info['y_labels']:
        print(f"  Memory labels: {axis_info['y_labels'][:5]}...")
    
    # Map coordinates
    print("\n🗺️  Mapping coordinates to values...")
    x_coords, y_coords = map_coordinates_to_values(points, axis_info, viewbox)
    
    # Create time and memory arrays
    time_array = create_time_array(x_coords, axis_info)
    memory_array = create_memory_array(y_coords, axis_info)
    
    print(f"✓ Data prepared: {len(time_array)} points")
    print(f"  Memory range: {memory_array.min():.2f} - {memory_array.max():.2f} MB")
    
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
    
    # Figure 2: Zoomed view (6:30 PM - 7:30 PM)
    fig2, ax2 = plt.subplots(figsize=(16, 6))
    
    zoom_start = datetime.now().replace(hour=18, minute=30, second=0, microsecond=0)
    zoom_end = datetime.now().replace(hour=19, minute=30, second=0, microsecond=0)
    
    # Handle midnight crossing
    if time_array[-1] < time_array[0]:
        zoom_end += timedelta(days=1)
    
    mask = (time_array >= zoom_start) & (time_array <= zoom_end)
    
    if mask.any():
        zoom_times = time_array[mask]
        zoom_memory = memory_array[mask]
        
        ax2.fill_between(zoom_times, zoom_memory, alpha=0.5, color='#E57373', label='Memory Usage')
        ax2.plot(zoom_times, zoom_memory, color='#C62828', linewidth=2, marker='o', 
                markersize=4, markevery=max(1, len(zoom_times)//50))
        ax2.set_xlabel('Time', fontsize=13, fontweight='bold')
        ax2.set_ylabel('Memory Usage (MB)', fontsize=13, fontweight='bold')
        ax2.set_title('Memory Usage - Magnified View (6:30 PM - 7:30 PM)', 
                     fontsize=15, fontweight='bold', pad=20)
        ax2.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
        ax2.legend(loc='upper right', fontsize=11)
        
        # More granular time labels
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%I:%M %p'))
        ax2.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        ax2.set_xlim(zoom_start, zoom_end)
        
        print(f"✓ Zoomed view: {len(zoom_times)} points between 6:30-7:30 PM")
    else:
        ax2.text(0.5, 0.5, 'No data in time range 6:30 PM - 7:30 PM', 
                ha='center', va='center', transform=ax2.transAxes, fontsize=14, color='red')
        print("⚠ No data points in 6:30-7:30 PM range")
    
    plt.tight_layout()
    zoom_output = 'memory_usage_zoomed.png'
    plt.savefig(zoom_output, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {zoom_output}")
    
    plt.show()
    
    print("\n" + "="*70)
    print("✅ COMPLETE!")
    print("="*70)
    print(f"📊 Total data points: {len(points)}")
    print(f"📈 Graphs saved to current directory")
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
