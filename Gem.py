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
    (Handles <tspan> children, text labels like '286.10MB',
     and skips day labels like '11 FRI')
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

        # Check for day label (e.g., "11 FRI") and SKIP it
        if re.search(r'\d+\s+(FRI|SAT|SUN|MON|TUE|WED|THU)', text_content, re.IGNORECASE):
            continue # Skip this label

        # Check if it's a time label (for x-axis)
        # Now matches "8 PM" or "1:00 AM"
        if re.search(r'(\d+:\d+|\d+)\s*(AM|PM)', text_content, re.IGNORECASE) or \
           re.search(r'\d+:\d+', text_content):
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
            class_str = str(class_str)
        
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
    """
    base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Extract hour and minute
    time_match = re.search(r'(\d+):(\d+)', time_str)
    if not time_match:
        # Try parsing time like "8 PM" or "1 AM"
        time_match = re.search(r'(\d+)\s*(AM|PM)?', time_str, re.IGNORECASE)
        if time_match:
            hour = int(time_match.group(1))
            minute = 0
        else:
            return None # Cannot parse
    else:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))

    # Check for PM/AM in the full string
    is_pm = 'PM' in time_str.upper()
    is_am = 'AM' in time_str.upper()

    # Apply AM/PM logic
    if is_pm and hour != 12:
        hour += 12
    elif is_am and hour == 12: # 12 AM
        hour = 0
            
    if hour > 23: hour = hour % 24
 
    return base_date.replace(hour=hour, minute=minute)

# ===================================================================
# THIS IS THE CORRECTED FUNCTION
# ===================================================================
def create_time_array(x_coords, axis_info):
    """
    Create time array from x coordinates and axis labels
    """
    # Check if we have both labels and positions
    if not axis_info['x_labels'] or not axis_info['x_positions'] or \
       len(axis_info['x_labels']) < 2 or len(axis_info['x_positions']) < 2:
        
        print("⚠ Not enough x-axis labels or positions found, using default time range")
        base = datetime.now().replace(hour=18, minute=0, second=0, microsecond=0)
        duration = timedelta(hours=2)
        times = [base + duration * (x - x_coords.min()) / (x_coords.max() - x_coords.min()) 
                 for x in x_coords]
        return np.array(times)
    
    # --- NEW: Sort labels by their X-position ---
    # Zip positions and labels together
    paired_list = list(zip(axis_info['x_positions'], axis_info['x_labels']))
    # Sort by position (the first item in the tuple)
    paired_list.sort()
    # Unzip back into a sorted list of labels
    sorted_labels = [label for pos, label in paired_list]
    print(f"✓ Sorted time labels: {sorted_labels[:5]}... to ...{sorted_labels[-5:]}")
    # --- END NEW ---

    # Parse time labels from the *sorted* list
    times_parsed = []
    for label in sorted_labels:
        t = parse_time_label(label) # Uses new, robust parser
        if t:
            times_parsed.append(t)
    
    if len(times_parsed) < 2:
        print(f"⚠ Could not parse time labels ({sorted_labels}), using default")
        base = datetime.now().replace(hour=18, minute=0, second=0, microsecond=0)
        duration = timedelta(hours=2)
        times = [base + duration * (x - x_coords.min()) / (x_coords.max() - x_coords.min()) 
                 for x in x_coords]
        return np.array(times)

    # --- Logic for 24-HOUR 12-to-12 CYCLE ---
    # This loop detects midnight crossings (e.g., 11 PM -> 1 AM)
    # and adds 1 day to all subsequent labels.
    
    adjusted_times = []
    current_day_offset = 0
    last_hour = -1
    
    for time in times_parsed:
        current_hour = time.hour
        if last_hour != -1 and current_hour < last_hour:
             # e.g., current is 1 (1 AM) and last was 23 (11 PM)
            current_day_offset += 1 
            print(f"✓ Detected midnight crossing: {last_hour}:00 -> {current_hour}:00")
        
        adjusted_times.append(time + timedelta(days=current_day_offset))
        last_hour = current_hour
    
    times_parsed = adjusted_times # Overwrite with the corrected list
    # --- END NEW LOGIC ---
    
    
    # Interpolate times based on x coordinates
    start_time = times_parsed[0]
    end_time = times_parsed[-1]

    print(f"Time range: {start_time.strftime('%I:%M %p')} to {end_time.strftime('%I:%M %p')}")
    
    # Linear interpolation
    total_duration = (end_time - start_time).total_seconds()
    
    # Handle case where start/end are the same (e.g., 7PM to 7PM)
    # This was the cause of the bug
    if total_duration == 0 and len(times_parsed) > 1:
        print("⚠ Detected 0s duration with multiple labels. Forcing 24-hour cycle.")
        end_time += timedelta(days=1)
        total_duration = (end_time - start_time).total_seconds()
        print(f"✓ Corrected time range: {start_time.strftime('%I:%M %p')} to {end_time.strftime('%I:%M %p')}")
    
    # Ensure we don't divide by zero if all x_coords are the same
    x_range = x_coords.max() - x_coords.min()
    if x_range == 0:
        print("⚠ All X coordinates are identical. Cannot interpolate time.")
        print("✓ This may be a single data point (vertical line).")
        return np.array([start_time] * len(x_coords))

    times = [start_time + timedelta(seconds=total_duration * (x - x_coords.min()) / x_range) 
             for x in x_coords]
    
    return np.array(times)
# ===================================================================
# END OF CORRECTED FUNCTION
# ===================================================================

def create_memory_array(y_coords, axis_info):
    """
    Create memory array from y coordinates and axis labels
    """
    if not axis_info['y_labels'] or len(axis_info['y_labels']) < 2:
        # Normalize to 0-1000 MB range
        print("⚠ No y-axis labels found, normalizing to 0-1000 MB")
        y_normalized = (y_coords - y_coords.min()) / (y_coords.max() - y_coords.min())
        return y_normalized * 1000
    
    # Parse numeric labels
    y_values = []
    for label in axis_info['y_labels']:
        try:
            y_values.append(float(label))
        except:
            pass
    
    if len(y_values) < 2:
        print(f"⚠ Could not parse y-axis labels ({axis_info['y_labels']}), normalizing")
        y_normalized = (y_coords - y_coords.min()) / (y_coords.max() - y_coords.min())
        return y_normalized * 1000
    
    y_min = min(y_values)
    y_max = max(y_values)

    # Handle case where all labels are the same (e.g., ['0', '0'])
    if y_min == y_max:
        print(f"⚠ All Y-axis labels are the same value ({y_min}). Output will be constant.")
        return np.full(len(y_coords), y_min)

    
    print(f"Memory range: {y_min} to {y_max} MB")
    
    # Linear mapping
    # Ensure we don't divide by zero
    y_coord_range = y_coords.max() - y_coords.min()
    if y_coord_range == 0:
        print("⚠ All Y coordinates are identical. Cannot interpolate memory.")
        # Return the average of the min/max labels as a constant
        return np.full(len(y_coords), (y_min + y_max) / 2)

    y_normalized = (y_coords - y_coords.min()) / y_coord_range
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
    print(f"✓ Found {len(axis_info['x_labels'])} x-axis labels (Note: Skipped day annotations)")
    print(f"✓ Found {len(axis_info['y_labels'])} y-axis labels")
    
    if axis_info['x_labels']:
        print(f"  Time labels: {axis_info['x_labels'][:5]}...")
    if axis_info['y_labels']:
        print(f"  Memory labels: {axis_info['y_labels'][:5]}...")
    
    # Map coordinates
    print("\n🗺️  Mapping coordinates to values...")
    x_coords, y_coords = map_coordinates_to_values(points, axis_info, viewbox)
    
    # Create time and memory arrays
    time_array = create_time_array(x_coords, axis_info) # USES NEW FIXED FUNCTION
    memory_array = create_memory_array(y_coords, axis_info)
    
    print(f"✓ Data prepared: {len(time_array)} points")
    print(f"  Memory range: {memory_array.min():.2f} - {memory_array.max():.2f} MB")
    
    # --- Get min/max values from the *parsed labels* for setting axes ---
    y_labels_numeric = []
    for label in axis_info['y_labels']:
        try:
            y_labels_numeric.append(float(label))
        except:
            pass
            
    # Set Y-axis limits from labels, with 0 as a floor
    y_axis_min = min(y_labels_numeric) if y_labels_numeric else 0
    if y_axis_min > 0:
        y_axis_min = 0 # Always start Y-axis at 0 for memory graphs
        
    y_axis_max = max(y_labels_numeric) if y_labels_numeric else memory_array.max()
    y_axis_max = y_axis_max * 1.05 # Add 5% padding to the top
    
    # Set X-axis limits from data
    time_axis_min = time_array[0]
    time_axis_max = time_array[-1]
    
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
    
    # --- MODIFIED: Set axis limits based on parsed labels ---
    
    # Only set x-limits if they are different, otherwise Matplotlib warns
    if time_axis_min != time_axis_max:
        ax1.set_xlim(time_axis_min, time_axis_max)

    ax1.set_ylim(y_axis_min, y_axis_max) # e.g., 0 to 572.20 * 1.05
    # --- END MODIFIED ---
    
    # Format x-axis
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%I:%M %p'))
    
    # Auto-adjust locator based on time range
    total_seconds = (time_array[-1] - time_array[0]).total_seconds()
    
    # Only set a locator if there is a time duration
    if total_seconds > 0:
        if total_seconds <= 3600 * 3: # 3 hours
            ax1.xaxis.set_major_locator(mdates.MinuteLocator(interval=15))
        elif total_seconds <= 3600 * 12: # 12 hours
            ax1.xaxis.set_major_locator(mdates.HourLocator(interval=1))
        else: # More than 12 hours (like your 24hr graph)
            ax1.xaxis.set_major_locator(mdates.HourLocator(interval=2))
    else:
        # If no duration, just show the single time point
        ax1.set_xticks([time_axis_min])

    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    full_output = 'memory_usage_full.png'
    plt.savefig(full_output, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {full_output}")
    
    # Figure 2: Zoomed view (6:30 PM - 7:30 PM)
    fig2, ax2 = plt.subplots(figsize=(16, 6))
    
    # Determine the correct date for zoom
    base_date = time_array[0].replace(hour=0, minute=0, second=0, microsecond=0)
    zoom_start = base_date.replace(hour=18, minute=30)
    zoom_end = base_date.replace(hour=19, minute=30)

    # Handle midnight crossing for zoom
    if time_array[0].day != time_array[-1].day:
        if time_array[0].hour > 12 and time_array[-1].hour < 12: # e.g. starts at 8 PM, ends at 2 AM
             if zoom_start.hour < 12: # e.g. zoom is 2 AM
                 zoom_start += timedelta(days=1)
             if zoom_end.hour < 12:
                 zoom_end += timedelta(days=1)
    
    # If the whole graph is on the next day (e.g. 1 AM to 3 AM)
    if time_array[0].hour < 12 and zoom_start.hour > 12:
        zoom_start -= timedelta(days=1)
        zoom_end -= timedelta(days=1)
    
    # Handle the zoom window if the graph *starts* after the zoom end
    if time_array[0] > zoom_end:
         # Shift zoom window to be on the same day as the graph start
         days_diff = (time_array[0].date() - zoom_start.date()).days
         zoom_start += timedelta(days=days_diff)
         zoom_end += timedelta(days=days_diff)


    mask = (time_array >= zoom_start) & (time_array <= zoom_end)
    
    # Also check if the main time array has any duration
    if mask.any() and total_seconds > 0:
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
        ax2.set_ylim(y_axis_min, y_axis_max) # Also apply Y-axis limits to zoom plot

        print(f"✓ Zoomed view: {len(zoom_times)} points between 6:30-7:30 PM")
    else:
        # Give a more specific reason
        if total_seconds == 0:
            msg = "Skipping zoom: Main graph has no time duration."
        else:
            msg = f'No data in time range {zoom_start.strftime("%I:%M %p")} - {zoom_end.strftime("%I:%M %p")}'
        
        ax2.text(0.5, 0.5, msg, 
                 ha='center', va='center', transform=ax2.transAxes, fontsize=14, color='red')
        print(f"⚠ {msg}")
    
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
