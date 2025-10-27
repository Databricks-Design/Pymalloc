import os
import psutil
import gc
import uuid
import time
import pandas as pd
import matplotlib.pyplot as plt

def get_rss_mb():
    """Gets the current Resident Set Size (RSS) memory in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

# --- CONFIGURATION ---
TOTAL_BATCHES = 20000  # Total number of batches to simulate
BATCH_SIZE = 500       # Number of new "unique words" per batch
LOG_INTERVAL = 20      # How often to write a data point
OUTPUT_FILENAME = 'python_memory_pattern_proof.png'

# --- DATA COLLECTION LISTS ---
data_dict_cache = []  # Simulates "Without Zone"
data_no_cache = []    # Simulates "With Zone"

# --- SCRIPT START ---
print("Starting memory simulation...")
gc.collect()  # Start from a clean slate
baseline_rss = get_rss_mb()
print(f"Baseline RSS: {baseline_rss:.2f} MB")

# ======================================================================
# SIMULATION 1: "Without Memory Zone" (Dictionary Cache)
# This simulates spaCy's 'Vocab' using a standard Python 'dict'.
# We expect this to show the "STEP-UP" pattern.
# ======================================================================
print("\n--- Running Simulation 1: Dictionary Cache (No spaCy) ---")
global_word_cache = {}

# Add baseline data point
data_dict_cache.append({'batch_num': 0, 'rss_mb': baseline_rss})

for i in range(TOTAL_BATCHES):
    # 1. Create new, unique strings (simulating new words)
    new_batch = [str(uuid.uuid4()) for _ in range(BATCH_SIZE)]
    
    # 2. Add them to the global cache (simulating 'nlp.vocab')
    for word in new_batch:
        if word not in global_word_cache:
            global_word_cache[word] = True # Add to cache
    
    # 3. Log data at intervals
    if i % LOG_INTERVAL == 0:
        rss_now = get_rss_mb()
        data_dict_cache.append({'batch_num': i, 'rss_mb': rss_now})
        
        if i % (LOG_INTERVAL * 20) == 0:
            print(f"  Batch {i}/{TOTAL_BATCHES}... RSS: {rss_now:.2f} MB")

print("Simulation 1 complete.")
del global_word_cache  # Clean up before next run
gc.collect()
time.sleep(2)  # Let OS stabilize

# ======================================================================
# SIMULATION 2: "With Memory Zone" (No Caching)
# This simulates your 'memory_zone' loop.
# We expect this to be a FLAT line.
# ======================================================================
print("\n--- Running Simulation 2: No Caching (No spaCy) ---")
baseline_rss_2 = get_rss_mb()
print(f"Starting RSS for Sim 2: {baseline_rss_2:.2f} MB")

# Add baseline data point
data_no_cache.append({'batch_num': 0, 'rss_mb': baseline_rss_2})

for i in range(TOTAL_BATCHES):
    # 1. Create new, unique strings
    temp_batch = [str(uuid.uuid4()) for _ in range(BATCH_SIZE)]
    
    # 2. DO NOT store them. They are "orphaned" at the end of the loop.
    del temp_batch
    
    # 3. Force garbage collection, cleaning up the "orphaned" batch.
    gc.collect() 
    
    # 4. Log data at intervals
    if i % LOG_INTERVAL == 0:
        rss_now = get_rss_mb()
        data_no_cache.append({'batch_num': i, 'rss_mb': rss_now})
        
        if i % (LOG_INTERVAL * 20) == 0:
            print(f"  Batch {i}/{TOTAL_BATCHES}... RSS: {rss_now:.2f} MB")

print("Simulation 2 complete.")
print("\nData generation finished. Now plotting...")

# ======================================================================
# PLOTTING PHASE
# ======================================================================
try:
    # Convert lists of dicts to DataFrames for easy plotting
    df_dict_cache = pd.DataFrame(data_dict_cache)
    df_no_cache = pd.DataFrame(data_no_cache)

    # Create the plot
    plt.figure(figsize=(14, 7))

    # Plot the "Dictionary Cache" (simulating 'Without Zone')
    plt.plot(
        df_dict_cache['batch_num'], 
        df_dict_cache['rss_mb'], 
        label='Without Memory Zone (Python Dict Cache)', 
        color='blue', 
        linewidth=2
    )

    # Plot the "No Caching" (simulating 'With Zone')
    plt.plot(
        df_no_cache['batch_num'], 
        df_no_cache['rss_mb'], 
        label='With Memory Zone (No Caching)', 
        color='green', 
        linewidth=2
    )

    # Fill the area between
    min_rss = df_no_cache['rss_mb'].min()
    plt.fill_between(
        df_dict_cache['batch_num'], 
        df_dict_cache['rss_mb'], 
        min_rss,  # Use a stable floor for fill
        color='yellow', 
        alpha=0.3,
        label='Memory Held by Cache'
    )

    # Style the graph
    plt.title('Python Memory Allocation Pattern (No spaCy)', fontsize=16)
    plt.xlabel('Batch Number', fontsize=12)
    plt.ylabel('Memory Usage (MB)', fontsize=12)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()

    # Save and show the graph
    plt.savefig(OUTPUT_FILENAME)
    print(f"\nGraph saved as {OUTPUT_FILENAME}")
    
    # Show the plot
    plt.show()

except Exception as e:
    print(f"\nAn error occurred during plotting: {e}")
    print("Please ensure matplotlib, pandas, and psutil are installed.")

