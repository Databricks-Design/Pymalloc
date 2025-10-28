import json
import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

# Load results
OUTPUT_DIR = "./output"
without_json_path = os.path.join(OUTPUT_DIR, "without_zone", "test_results.json")
with_json_path = os.path.join(OUTPUT_DIR, "with_zone", "test_results.json")

with open(without_json_path, 'r') as f:
    results_without = json.load(f)

with open(with_json_path, 'r') as f:
    results_with = json.load(f)

def detect_steps(memory_data, batches, threshold_mb=10):
    """
    Detect significant memory steps/jumps
    threshold_mb: Minimum jump size to consider (default 10 MB)
    """
    # Calculate differences between consecutive measurements
    memory_diff = np.diff(memory_data)
    
    # Find peaks in the differences (jumps)
    # Use prominence to find significant jumps
    peaks, properties = find_peaks(memory_diff, prominence=threshold_mb)
    
    steps = []
    for i, peak_idx in enumerate(peaks):
        batch_num = batches[peak_idx]
        memory_before = memory_data[peak_idx]
        memory_after = memory_data[peak_idx + 1]
        jump_size = memory_after - memory_before
        
        steps.append({
            'step_num': i + 1,
            'batch': batch_num,
            'memory_before': memory_before,
            'memory_after': memory_after,
            'jump_mb': jump_size
        })
    
    return steps

def analyze_scenario(results, name):
    """Analyze one scenario (with or without zone)"""
    print("="*80)
    print(f"📊 {name}")
    print("="*80)
    
    batches = results['batches']
    memory_data = results['memory_mb']
    vocab_data = results['vocab_size']
    string_store_data = results['string_store_size']
    
    # Detect steps with 10 MB threshold
    steps = detect_steps(memory_data, batches, threshold_mb=10)
    
    if not steps:
        print("❌ No significant memory steps detected (threshold: 10 MB)\n")
        return steps, batches, memory_data, vocab_data, string_store_data
    
    print(f"✅ Detected {len(steps)} significant memory step(s):\n")
    
    total_jump = 0
    for step in steps:
        print(f"  Step {step['step_num']}:")
        print(f"    ├─ Batch: {step['batch']}")
        print(f"    ├─ Memory: {step['memory_before']:.1f} → {step['memory_after']:.1f} MB")
        print(f"    └─ Jump: +{step['jump_mb']:.1f} MB")
        print()
        total_jump += step['jump_mb']
    
    print(f"  Total memory jumps: +{total_jump:.1f} MB")
    
    # Check if vocab/string_store also jumped at these points
    print(f"\n  Checking vocab & string_store at step points:")
    for step in steps:
        batch_idx = batches.index(step['batch'])
        vocab_before = vocab_data[batch_idx] if batch_idx > 0 else vocab_data[0]
        vocab_after = vocab_data[batch_idx + 1] if batch_idx + 1 < len(vocab_data) else vocab_data[-1]
        
        string_before = string_store_data[batch_idx] if batch_idx > 0 else string_store_data[0]
        string_after = string_store_data[batch_idx + 1] if batch_idx + 1 < len(string_store_data) else string_store_data[-1]
        
        print(f"\n    Step {step['step_num']} (Batch {step['batch']}):")
        print(f"      Vocab: {vocab_before:,} → {vocab_after:,} (Δ: {vocab_after - vocab_before:,})")
        print(f"      String Store: {string_before:,} → {string_after:,} (Δ: {string_after - string_before:,})")
    
    print("\n")
    
    return steps, batches, memory_data, vocab_data, string_store_data

# Analyze both scenarios
print("\n")
steps_without, batches_w, mem_w, vocab_w, str_w = analyze_scenario(results_without, "WITHOUT MEMORY ZONE")
steps_with, batches_wz, mem_wz, vocab_wz, str_wz = analyze_scenario(results_with, "WITH MEMORY ZONE")

# Create visualization
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10))

# Plot 1: WITHOUT ZONE
ax1.plot(batches_w, mem_w, 'b-', linewidth=2.5, label='RSS Memory', alpha=0.8)

for step in steps_without:
    batch_idx = batches_w.index(step['batch'])
    ax1.axvline(x=step['batch'], color='red', linestyle='--', linewidth=2, alpha=0.7)
    ax1.annotate(f"Step {step['step_num']}\n+{step['jump_mb']:.0f} MB",
                xy=(step['batch'], step['memory_after']),
                xytext=(10, 10), textcoords='offset points',
                fontsize=10, color='red', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.8),
                arrowprops=dict(arrowstyle='->', color='red', lw=2))

ax1.set_title('WITHOUT MEMORY ZONE - RSS Steps Detection', fontsize=14, fontweight='bold')
ax1.set_xlabel('Batch Number', fontsize=12)
ax1.set_ylabel('Memory (MB)', fontsize=12)
ax1.legend(fontsize=11)
ax1.grid(True, linestyle='--', alpha=0.4)

# Plot 2: WITH ZONE
ax2.plot(batches_wz, mem_wz, 'g-', linewidth=2.5, label='RSS Memory', alpha=0.8)

for step in steps_with:
    batch_idx = batches_wz.index(step['batch'])
    ax2.axvline(x=step['batch'], color='red', linestyle='--', linewidth=2, alpha=0.7)
    ax2.annotate(f"Step {step['step_num']}\n+{step['jump_mb']:.0f} MB",
                xy=(step['batch'], step['memory_after']),
                xytext=(10, 10), textcoords='offset points',
                fontsize=10, color='red', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.8),
                arrowprops=dict(arrowstyle='->', color='red', lw=2))

ax2.set_title('WITH MEMORY ZONE - RSS Steps Detection', fontsize=14, fontweight='bold')
ax2.set_xlabel('Batch Number', fontsize=12)
ax2.set_ylabel('Memory (MB)', fontsize=12)
ax2.legend(fontsize=11)
ax2.grid(True, linestyle='--', alpha=0.4)

plt.tight_layout()
plt.savefig('rss_steps_detection.png', dpi=150, bbox_inches='tight')
print("="*80)
print("✅ Visualization saved as 'rss_steps_detection.png'")
print("="*80)

# Comparison summary
print("\n" + "="*80)
print("📊 COMPARISON SUMMARY")
print("="*80)
print(f"WITHOUT Zone: {len(steps_without)} step(s)")
print(f"WITH Zone:    {len(steps_with)} step(s)")

if steps_without and steps_with:
    total_jumps_without = sum(s['jump_mb'] for s in steps_without)
    total_jumps_with = sum(s['jump_mb'] for s in steps_with)
    print(f"\nTotal RSS jumps:")
    print(f"  WITHOUT Zone: +{total_jumps_without:.1f} MB")
    print(f"  WITH Zone:    +{total_jumps_with:.1f} MB")
    print(f"  Difference:   {total_jumps_without - total_jumps_with:.1f} MB")

print("="*80 + "\n")

plt.show()
