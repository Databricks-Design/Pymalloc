
import os
import psutil
import gc
import uuid
import time
import pandas as pd
import matplotlib.pyplot as plt
import tracemalloc

def get_rss_mb():
    """Gets the current Resident Set Size (RSS) memory in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

# --- CONFIGURATION ---
TOTAL_BATCHES = 20000
BATCH_SIZE = 500
LOG_INTERVAL = 20
OUTPUT_FILENAME = 'python_memory_detailed_analysis.png'

# --- DATA COLLECTION LISTS ---
data_dict_cache = []

# --- SCRIPT START ---
print("Starting detailed memory analysis...")
gc.collect()
baseline_rss = get_rss_mb()
print(f"Baseline RSS: {baseline_rss:.2f} MB\n")

# Start memory tracing
tracemalloc.start()

# ======================================================================
# DETAILED SIMULATION: Dictionary Cache with Size Tracking
# ======================================================================
print("--- Running Detailed Simulation ---")
global_word_cache = {}

# Track for step detection
last_rss = baseline_rss
step_threshold_mb = 50  # Consider it a "step" if RSS jumps by more than this

for i in range(TOTAL_BATCHES):
    # Create new unique strings
    new_batch = [str(uuid.uuid4()) for _ in range(BATCH_SIZE)]
    
    # Add to cache
    for word in new_batch:
        if word not in global_word_cache:
            global_word_cache[word] = True
    
    # Log at intervals
    if i % LOG_INTERVAL == 0:
        rss_now = get_rss_mb()
        dict_size = len(global_word_cache)
        current_traced, peak_traced = tracemalloc.get_traced_memory()
        traced_mb = current_traced / (1024 * 1024)
        
        # Detect if this is a "step"
        rss_jump = rss_now - last_rss
        is_step = rss_jump > step_threshold_mb
        
        data_dict_cache.append({
            'batch_num': i,
            'rss_mb': rss_now,
            'dict_size': dict_size,
            'traced_mb': traced_mb,
            'rss_jump': rss_jump,
            'is_step': is_step
        })
        
        # Print detailed info for steps
        if is_step:
            print(f"🚀 STEP DETECTED at Batch {i}:")
            print(f"   RSS jumped by: {rss_jump:.2f} MB")
            print(f"   Dict size: {dict_size:,} items")
            print(f"   Traced memory: {traced_mb:.2f} MB")
            print(f"   RSS total: {rss_now:.2f} MB\n")
        elif i % (LOG_INTERVAL * 50) == 0:
            print(f"  Batch {i}/{TOTAL_BATCHES} - RSS: {rss_now:.2f} MB - Dict: {dict_size:,} items")
        
        last_rss = rss_now

print("\nSimulation complete. Generating analysis...\n")

# Stop tracing
tracemalloc.stop()

# ======================================================================
# ANALYSIS
# ======================================================================
df = pd.DataFrame(data_dict_cache)

# Find major steps
major_steps = df[df['is_step'] == True].copy()
print(f"Detected {len(major_steps)} major memory steps:\n")
for idx, row in major_steps.iterrows():
    print(f"Batch {row['batch_num']:5d}: "
          f"RSS +{row['rss_jump']:6.2f} MB → {row['rss_mb']:7.2f} MB total "
          f"(Dict: {row['dict_size']:,} items)")

# Calculate average bytes per item
if len(df) > 1:
    total_rss_growth = df['rss_mb'].iloc[-1] - df['rss_mb'].iloc[0]
    total_items = df['dict_size'].iloc[-1]
    bytes_per_item = (total_rss_growth * 1024 * 1024) / total_items
    print(f"\nAverage memory per cached item: {bytes_per_item:.1f} bytes")

# ======================================================================
# PLOTTING
# ======================================================================
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

# Plot 1: RSS Memory Usage
ax1.plot(df['batch_num'], df['rss_mb'], 'b-', linewidth=2, label='RSS Memory')
ax1.plot(df['batch_num'], df['traced_mb'], 'r--', linewidth=1.5, alpha=0.7, label='Traced Memory (Python View)')

# Annotate major steps
for idx, row in major_steps.iterrows():
    ax1.annotate(f"+{row['rss_jump']:.0f}MB\n{row['dict_size']:,} items",
                xy=(row['batch_num'], row['rss_mb']),
                xytext=(10, 10), textcoords='offset points',
                fontsize=8, color='red',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                arrowprops=dict(arrowstyle='->', color='red', lw=1.5))

ax1.set_title('Memory Usage with Step Annotations', fontsize=14, fontweight='bold')
ax1.set_xlabel('Batch Number', fontsize=12)
ax1.set_ylabel('Memory (MB)', fontsize=12)
ax1.legend(loc='upper left')
ax1.grid(True, linestyle='--', alpha=0.4)

# Plot 2: Dictionary Size vs Memory
ax2_twin = ax2.twinx()
ax2.plot(df['batch_num'], df['dict_size'], 'g-', linewidth=2, label='Dictionary Size')
ax2_twin.plot(df['batch_num'], df['rss_mb'], 'b-', linewidth=2, alpha=0.5, label='RSS Memory')

ax2.set_title('Dictionary Growth vs Memory Usage', fontsize=14, fontweight='bold')
ax2.set_xlabel('Batch Number', fontsize=12)
ax2.set_ylabel('Dictionary Size (items)', fontsize=12, color='g')
ax2_twin.set_ylabel('RSS Memory (MB)', fontsize=12, color='b')
ax2.tick_params(axis='y', labelcolor='g')
ax2_twin.tick_params(axis='y', labelcolor='b')
ax2.grid(True, linestyle='--', alpha=0.4)

# Combine legends
lines1, labels1 = ax2.get_legend_handles_labels()
lines2, labels2 = ax2_twin.get_legend_handles_labels()
ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

plt.tight_layout()
plt.savefig(OUTPUT_FILENAME, dpi=150)
print(f"\nDetailed graph saved as {OUTPUT_FILENAME}")

# Save data to CSV for further analysis
csv_filename = 'memory_analysis_data.csv'
df.to_csv(csv_filename, index=False)
print(f"Raw data saved as {csv_filename}")

plt.show()
