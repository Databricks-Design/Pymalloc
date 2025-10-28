

import os
import psutil
import gc
import uuid
import sys
import pandas as pd
import matplotlib.pyplot as plt

def get_rss_mb():
    """Gets the current Resident Set Size (RSS) memory in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

# --- CONFIGURATION ---
TOTAL_BATCHES = 10000
BATCH_SIZE = 500
LOG_INTERVAL = 20

# --- DATA COLLECTION ---
data = []

# --- START ---
print("="*70)
print("OBSERVING: WHAT CAUSES MEMORY STEPS?")
print("="*70)
gc.collect()
baseline_rss = get_rss_mb()
print(f"\nBaseline RSS: {baseline_rss:.2f} MB\n")
print("Tracking dictionary size and actual memory usage...")
print("We'll analyze the pattern AFTER collecting data.\n")

global_word_cache = {}

for i in range(TOTAL_BATCHES):
    # Add items to dictionary
    new_batch = [str(uuid.uuid4()) for _ in range(BATCH_SIZE)]
    for word in new_batch:
        if word not in global_word_cache:
            global_word_cache[word] = True
    
    # Log at intervals
    if i % LOG_INTERVAL == 0:
        rss_now = get_rss_mb()
        dict_size = len(global_word_cache)
        dict_actual_bytes = sys.getsizeof(global_word_cache)
        
        data.append({
            'batch_num': i,
            'rss_mb': rss_now,
            'dict_size': dict_size,
            'dict_bytes': dict_actual_bytes
        })
        
        if i % (LOG_INTERVAL * 50) == 0:
            print(f"Batch {i:5d} - RSS: {rss_now:7.2f} MB - Dict items: {dict_size:,}")

print("\n" + "="*70)
print("DATA COLLECTION COMPLETE")
print("="*70)

# --- ANALYSIS ---
df = pd.DataFrame(data)

# Calculate RSS changes
df['rss_change_mb'] = df['rss_mb'].diff()

# Calculate dict size changes
df['items_added'] = df['dict_size'].diff()

# Calculate bytes per new item
df['bytes_per_item'] = (df['rss_change_mb'] * 1024 * 1024) / df['items_added']

# Detect significant jumps (using statistical method, not manual threshold)
mean_change = df['rss_change_mb'].mean()
std_change = df['rss_change_mb'].std()
significant_threshold = mean_change + (2 * std_change)  # 2 standard deviations above mean

df['is_significant_jump'] = df['rss_change_mb'] > significant_threshold

# Find the jumps
jumps = df[df['is_significant_jump'] == True].copy()

print(f"\nSTATISTICAL ANALYSIS:")
print(f"  Mean RSS change per interval: {mean_change:.2f} MB")
print(f"  Std deviation: {std_change:.2f} MB")
print(f"  Significant jump threshold (mean + 2*std): {significant_threshold:.2f} MB")
print(f"  Number of significant jumps detected: {len(jumps)}")

if len(jumps) > 0:
    print(f"\n{'='*70}")
    print("SIGNIFICANT MEMORY JUMPS DETECTED:")
    print(f"{'='*70}")
    
    for idx, row in jumps.iterrows():
        print(f"\nJump at Batch {row['batch_num']}:")
        print(f"  ├─ RSS jumped: +{row['rss_change_mb']:.2f} MB")
        print(f"  ├─ Dictionary size at jump: {row['dict_size']:,} items")
        print(f"  ├─ Dict sys.getsizeof(): {row['dict_bytes']:,} bytes ({row['dict_bytes']/(1024*1024):.2f} MB)")
        print(f"  └─ Bytes per item at this jump: {row['bytes_per_item']:.0f} bytes/item")
    
    # Analyze pattern in jump dictionary sizes
    print(f"\n{'='*70}")
    print("PATTERN ANALYSIS:")
    print(f"{'='*70}")
    
    jump_sizes = jumps['dict_size'].tolist()
    print(f"\nDictionary sizes when jumps occurred:")
    for i, size in enumerate(jump_sizes, 1):
        print(f"  Jump {i}: {size:,} items")
    
    # Check if there's a pattern (powers of 2, fibonacci, etc.)
    print(f"\nChecking for patterns...")
    
    # Check ratios between consecutive jumps
    if len(jump_sizes) > 1:
        print(f"\nRatios between jump sizes:")
        for i in range(1, len(jump_sizes)):
            ratio = jump_sizes[i] / jump_sizes[i-1]
            print(f"  Jump {i+1} / Jump {i} = {ratio:.2f}x")
    
    # Check if sizes relate to powers of 2
    print(f"\nRelation to powers of 2:")
    for i, size in enumerate(jump_sizes, 1):
        # Find nearest power of 2
        import math
        log2_val = math.log2(size) if size > 0 else 0
        nearest_power = 2 ** round(log2_val)
        ratio_to_power = size / nearest_power
        print(f"  Jump {i} at {size:,} items ≈ {ratio_to_power:.2f} × 2^{round(log2_val):.0f} ({nearest_power:,})")

# --- PLOTTING ---
print(f"\n{'='*70}")
print("GENERATING VISUALIZATION")
print(f"{'='*70}\n")

fig, axes = plt.subplots(3, 1, figsize=(14, 12))

# Plot 1: RSS Memory with Jump Markers
axes[0].plot(df['batch_num'], df['rss_mb'], 'b-', linewidth=2.5, label='RSS Memory')

if len(jumps) > 0:
    for idx, row in jumps.iterrows():
        axes[0].axvline(x=row['batch_num'], color='red', linestyle='--', alpha=0.7, linewidth=2)
        axes[0].scatter(row['batch_num'], row['rss_mb'], color='red', s=100, zorder=5)
        axes[0].annotate(f"+{row['rss_change_mb']:.0f}MB\n{row['dict_size']:,} items",
                        xy=(row['batch_num'], row['rss_mb']),
                        xytext=(10, 10), textcoords='offset points',
                        fontsize=8, color='red', fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.4', facecolor='yellow', alpha=0.8),
                        arrowprops=dict(arrowstyle='->', color='red', lw=2))

axes[0].set_title('RSS Memory - Where Do Steps Occur?', fontsize=14, fontweight='bold')
axes[0].set_xlabel('Batch Number', fontsize=11)
axes[0].set_ylabel('RSS (MB)', fontsize=11)
axes[0].legend(loc='upper left')
axes[0].grid(True, linestyle='--', alpha=0.4)

# Plot 2: Dictionary Size
axes[1].plot(df['batch_num'], df['dict_size'], 'g-', linewidth=2.5, label='Dictionary Size')

if len(jumps) > 0:
    for idx, row in jumps.iterrows():
        axes[1].axvline(x=row['batch_num'], color='red', linestyle='--', alpha=0.7, linewidth=2)
        axes[1].scatter(row['batch_num'], row['dict_size'], color='red', s=100, zorder=5)

axes[1].set_title('Dictionary Size - Linear Growth', fontsize=14, fontweight='bold')
axes[1].set_xlabel('Batch Number', fontsize=11)
axes[1].set_ylabel('Number of Items', fontsize=11)
axes[1].legend(loc='upper left')
axes[1].grid(True, linestyle='--', alpha=0.4)

# Plot 3: RSS Change Rate (shows jumps clearly)
axes[2].plot(df['batch_num'], df['rss_change_mb'], 'purple', linewidth=2, label='RSS Change per Interval')
axes[2].axhline(y=significant_threshold, color='red', linestyle='--', linewidth=2, 
                label=f'Significant Jump Threshold ({significant_threshold:.1f} MB)')
axes[2].fill_between(df['batch_num'], 0, df['rss_change_mb'], 
                      where=(df['rss_change_mb'] > 0), alpha=0.3, color='purple')

if len(jumps) > 0:
    axes[2].scatter(jumps['batch_num'], jumps['rss_change_mb'], color='red', s=100, zorder=5)

axes[2].set_title('RSS Change Rate - Identifying Jumps', fontsize=14, fontweight='bold')
axes[2].set_xlabel('Batch Number', fontsize=11)
axes[2].set_ylabel('RSS Change (MB)', fontsize=11)
axes[2].legend(loc='upper right')
axes[2].grid(True, linestyle='--', alpha=0.4)

plt.tight_layout()
plt.savefig('observed_memory_pattern.png', dpi=150, bbox_inches='tight')
print(f"✅ Visualization saved as 'observed_memory_pattern.png'\n")

df.to_csv('observed_memory_data.csv', index=False)
print(f"✅ Data saved as 'observed_memory_data.csv'\n")

print("="*70)
print("EXPERIMENT COMPLETE")
print("="*70)
print("\nNow YOU analyze: Do the jump points follow a pattern?")
print("Do they occur at specific dictionary sizes?")
print("What's the ratio between jump points?")
print("="*70)

plt.show()
