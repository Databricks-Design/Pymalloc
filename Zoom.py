import re
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import numpy as np

def parse_svg_path(path_string):
    """Extract coordinates from SVG path string"""
    # Remove the 'M' (move to) command and split by 'L' (line to)
    path_string = path_string.strip()
    
    # Extract all coordinate pairs
    # Pattern matches numbers (including decimals) in pairs
    coords = re.findall(r'([\d.]+),([\d.]+)', path_string)
    
    x_coords = []
    y_coords = []
    
    for x, y in coords:
        x_coords.append(float(x))
        y_coords.append(float(y))
    
    return np.array(x_coords), np.array(y_coords)

def extract_memory_data(html_file):
    """Extract memory usage data from HTML file"""
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Find the memory usage path - looking for path with class containing "area" or similar
    memory_path = None
    
    # Try different selectors
    paths = soup.find_all('path')
    for path in paths:
        if path.get('d') and len(path.get('d', '')) > 100:  # Memory usage path should be long
            class_attr = path.get('class', [])
            if isinstance(class_attr, list):
                class_str = ' '.join(class_attr)
            else:
                class_str = class_attr
            
            # Look for area or curve patterns
            if 'area' in class_str.lower() or 'curve' in class_str.lower():
                memory_path = path.get('d')
                print(f"Found memory path with class: {class_str}")
                break
    
    if not memory_path:
        # If not found by class, take the longest path
        print("Trying to find longest path...")
        longest_path = max(paths, key=lambda p: len(p.get('d', '')))
        memory_path = longest_path.get('d')
    
    if not memory_path:
        raise ValueError("Could not find memory usage path in HTML")
    
    # Parse the path
    x_coords, y_coords = parse_svg_path(memory_path)
    
    # Extract time range from the HTML
    # Look for text elements or axis labels
    time_texts = []
    for text in soup.find_all('text'):
        text_content = text.get_text(strip=True)
        # Match time patterns like "6:30 PM", "18:30", etc.
        if re.search(r'\d+:\d+', text_content):
            time_texts.append(text_content)
    
    print(f"Found {len(time_texts)} time labels")
    print(f"Data points: {len(x_coords)}")
    
    return x_coords, y_coords, time_texts

def create_time_axis(x_coords, time_texts):
    """Create time axis from x coordinates and time labels"""
    # If we have time labels, use them to interpolate
    if len(time_texts) >= 2:
        # Parse first and last times
        print(f"Time range: {time_texts[0]} to {time_texts[-1]}")
        
        # Create a reference date (today)
        base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Try to parse times
        times = []
        for t in time_texts:
            # Extract time components
            time_match = re.search(r'(\d+):(\d+)', t)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                
                # Check for PM/AM
                if 'PM' in t.upper() or 'pm' in t:
                    if hour != 12:
                        hour += 12
                elif 'AM' in t.upper() or 'am' in t:
                    if hour == 12:
                        hour = 0
                
                times.append(base_date.replace(hour=hour, minute=minute))
        
        if len(times) >= 2:
            # Interpolate between start and end times
            start_time = times[0]
            end_time = times[-1]
            
            # If end time is before start time, add a day
            if end_time < start_time:
                end_time += timedelta(days=1)
            
            # Create time array
            time_range = (end_time - start_time).total_seconds()
            time_array = [start_time + timedelta(seconds=time_range * (x - x_coords.min()) / (x_coords.max() - x_coords.min())) 
                         for x in x_coords]
            
            return np.array(time_array)
    
    # Fallback: assume 1 hour span
    base_date = datetime.now().replace(hour=18, minute=0, second=0, microsecond=0)
    time_array = [base_date + timedelta(hours=(x - x_coords.min()) / (x_coords.max() - x_coords.min())) 
                 for x in x_coords]
    
    return np.array(time_array)

def plot_memory_usage(html_file, output_full='memory_usage_full.png', 
                      output_zoom='memory_usage_zoomed.png'):
    """Plot memory usage graphs"""
    
    # Extract data
    x_coords, y_coords, time_texts = extract_memory_data(html_file)
    
    # Invert y-axis (SVG coordinates are top-down)
    y_coords = y_coords.max() - y_coords
    
    # Normalize y to reasonable memory values (MB or GB)
    # Assuming the graph shows memory in MB
    y_memory = (y_coords - y_coords.min()) / (y_coords.max() - y_coords.min()) * 1000  # Scale to 0-1000 MB
    
    # Create time axis
    time_array = create_time_axis(x_coords, time_texts)
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # Plot 1: Full timeline
    ax1.fill_between(time_array, y_memory, alpha=0.6, color='#E57373', label='Memory Usage')
    ax1.plot(time_array, y_memory, color='#C62828', linewidth=1.5)
    ax1.set_xlabel('Time', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Memory Usage (MB)', fontsize=12, fontweight='bold')
    ax1.set_title('Memory Usage - Full Timeline', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.legend(loc='upper right')
    
    # Format x-axis for time
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%I:%M %p'))
    ax1.xaxis.set_major_locator(mdates.MinuteLocator(interval=15))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Plot 2: Zoomed view (6:30 PM - 7:30 PM)
    # Create mask for time range
    zoom_start = datetime.now().replace(hour=18, minute=30, second=0, microsecond=0)
    zoom_end = datetime.now().replace(hour=19, minute=30, second=0, microsecond=0)
    
    # Adjust if times span midnight
    if time_array[-1] < time_array[0]:
        zoom_end += timedelta(days=1)
    
    mask = (time_array >= zoom_start) & (time_array <= zoom_end)
    
    if mask.any():
        zoom_times = time_array[mask]
        zoom_memory = y_memory[mask]
        
        ax2.fill_between(zoom_times, zoom_memory, alpha=0.6, color='#E57373', label='Memory Usage')
        ax2.plot(zoom_times, zoom_memory, color='#C62828', linewidth=2)
        ax2.set_xlabel('Time', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Memory Usage (MB)', fontsize=12, fontweight='bold')
        ax2.set_title('Memory Usage - Magnified View (6:30 PM - 7:30 PM)', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3, linestyle='--')
        ax2.legend(loc='upper right')
        
        # Format x-axis for zoomed view with more granularity
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%I:%M:%S %p'))
        ax2.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Set x-axis limits explicitly
        ax2.set_xlim(zoom_start, zoom_end)
    else:
        ax2.text(0.5, 0.5, 'No data in specified time range (6:30 PM - 7:30 PM)', 
                ha='center', va='center', transform=ax2.transAxes, fontsize=12)
    
    plt.tight_layout()
    plt.savefig(output_full, dpi=300, bbox_inches='tight')
    print(f"\nFull graph saved to: {output_full}")
    
    # Create separate zoomed figure
    fig2, ax3 = plt.subplots(1, 1, figsize=(14, 6))
    
    if mask.any():
        ax3.fill_between(zoom_times, zoom_memory, alpha=0.6, color='#E57373', label='Memory Usage')
        ax3.plot(zoom_times, zoom_memory, color='#C62828', linewidth=2, marker='o', markersize=3)
        ax3.set_xlabel('Time', fontsize=12, fontweight='bold')
        ax3.set_ylabel('Memory Usage (MB)', fontsize=12, fontweight='bold')
        ax3.set_title('Memory Usage - Magnified View (6:30 PM - 7:30 PM)', fontsize=14, fontweight='bold')
        ax3.grid(True, alpha=0.3, linestyle='--')
        ax3.legend(loc='upper right')
        
        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%I:%M:%S %p'))
        ax3.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
        plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        ax3.set_xlim(zoom_start, zoom_end)
    
    plt.tight_layout()
    plt.savefig(output_zoom, dpi=300, bbox_inches='tight')
    print(f"Zoomed graph saved to: {output_zoom}")
    
    plt.show()
    
    return time_array, y_memory

# Main execution
if __name__ == "__main__":
    # Specify your HTML file path
    html_file = input("Enter the path to your HTML file: ").strip()
    
    print(f"\nProcessing: {html_file}")
    print("="*60)
    
    try:
        time_data, memory_data = plot_memory_usage(html_file)
        print("\n✓ Successfully created memory usage graphs!")
        print(f"  - Data points: {len(time_data)}")
        print(f"  - Memory range: {memory_data.min():.2f} - {memory_data.max():.2f} MB")
        print(f"  - Time range: {time_data[0].strftime('%I:%M %p')} - {time_data[-1].strftime('%I:%M %p')}")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
