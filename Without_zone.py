import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch, Circle, Polygon
from matplotlib.animation import FuncAnimation, PillowWriter
import numpy as np

# ============================================================================
# CONFIGURATION - Adjust animation speed here
# ============================================================================
ANIMATION_SPEED = 150  # milliseconds per frame (higher = slower)
                       # Try: 100 (fast), 150 (medium), 200 (slow)

# Professional color palette
COLORS = {
    'primary': '#2E3440',
    'baseline': '#A3BE8C',      # Green for initial baseline
    'growing': '#D08770',       # Orange for growing cache
    'danger': '#BF616A',        # Red for danger zone
    'critical': '#8B0000',      # Dark red for critical
    'accent_blue': '#5E81AC',
    'bg': '#FFFFFF',
    'line': '#4C566A'
}

# ============================================================================
# FUNCTION TO CREATE SINGLE FRAME - WITHOUT MEMORY ZONE
# ============================================================================
def create_frame_without_zone(fig, transaction_num, vocab_size, string_size, pod_crashed=False):
    """Create a single frame showing the problem without memory zone"""
    fig.clear()
    
    # Main title
    if not pod_crashed:
        fig.text(0.5, 0.96, 'WITHOUT Memory Zone: Unbounded Growth Problem', 
                 fontsize=42, ha='center', va='top', 
                 color=COLORS['danger'], weight='600')
        
        stage_text = f'Transaction #{transaction_num:,} - All Entries Added PERMANENTLY'
        stage_color = COLORS['danger']
    else:
        fig.text(0.5, 0.96, 'WITHOUT Memory Zone: POD CRASHED! 💥', 
                 fontsize=42, ha='center', va='top', 
                 color=COLORS['critical'], weight='700')
        
        stage_text = 'Memory Limit Exceeded - Service Disruption'
        stage_color = COLORS['critical']
    
    fig.text(0.5, 0.92, stage_text, 
             fontsize=24, ha='center', va='top',
             color=stage_color, weight='500')
    
    # Create main axes
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    # Calculate fill percentage for visual
    vocab_fill_pct = min(100, ((vocab_size - 1456) / 175289) * 100)
    string_fill_pct = min(100, ((string_size - 639984) / 60515) * 100)
    
    # Determine color based on growth
    if vocab_size < 50000:
        vocab_color = COLORS['baseline']
        status = 'Normal'
    elif vocab_size < 100000:
        vocab_color = COLORS['growing']
        status = 'Growing'
    elif vocab_size < 150000:
        vocab_color = COLORS['danger']
        status = 'Warning'
    else:
        vocab_color = COLORS['critical']
        status = 'Critical'
    
    # ========== LEFT: VOCABULARY ==========
    vocab_x = 12
    
    # Title
    ax.text(vocab_x + 18, 82, 'VOCABULARY', fontsize=28, ha='center',
            color=COLORS['primary'], weight='700')
    
    # Single growing cache (no separation - everything permanent!)
    cache_height = 20 + (58 * (vocab_fill_pct / 100.0))
    
    vocab_box = FancyBboxPatch((vocab_x, 20), 36, cache_height,
                               boxstyle="round,pad=0.3",
                               edgecolor=vocab_color,
                               facecolor=vocab_color if not pod_crashed else COLORS['critical'],
                               linewidth=4,
                               alpha=0.7 if not pod_crashed else 0.9)
    ax.add_patch(vocab_box)
    
    # Show fill pattern
    if not pod_crashed:
        fill_steps = int((cache_height / 2.5))
        for i in range(fill_steps):
            y_pos = 21 + (i * 2.5)
            if y_pos < 20 + cache_height - 1:
                # Gradient effect - darker at bottom (older), lighter at top (newer)
                alpha_val = 0.3 + (i / fill_steps) * 0.5
                fill_bar = Rectangle((vocab_x + 2, y_pos), 32, 2,
                                    facecolor='#FFEB3B',  # Yellow for new entries
                                    edgecolor='none',
                                    alpha=alpha_val)
                ax.add_patch(fill_bar)
    
    # Show count and status
    mid_y = 20 + cache_height / 2
    if not pod_crashed:
        ax.text(vocab_x + 18, mid_y + 8, f'{vocab_size:,}', fontsize=28, ha='center',
                color='white', weight='700')
        ax.text(vocab_x + 18, mid_y + 3, 'entries', fontsize=14, ha='center',
                color='white', weight='500')
        
        growth = vocab_size - 1456
        ax.text(vocab_x + 18, mid_y - 3, f'+{growth:,}', fontsize=16, ha='center',
                color='white', weight='600', style='italic')
        ax.text(vocab_x + 18, mid_y - 7, 'NEVER CLEANED', fontsize=13, ha='center',
                color='white', weight='700',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.3))
    else:
        ax.text(vocab_x + 18, mid_y + 3, 'MEMORY', fontsize=20, ha='center',
                color='white', weight='700')
        ax.text(vocab_x + 18, mid_y - 3, 'EXHAUSTED', fontsize=20, ha='center',
                color='white', weight='700')
    
    # Status indicator
    status_box = Rectangle((vocab_x - 2, 12), 40, 5,
                          facecolor=vocab_color if not pod_crashed else COLORS['critical'],
                          edgecolor=COLORS['line'],
                          linewidth=2,
                          alpha=0.9)
    ax.add_patch(status_box)
    
    if not pod_crashed:
        ax.text(vocab_x + 18, 14.5, f'STATUS: {status.upper()}', fontsize=16, ha='center',
                color='white', weight='700')
    else:
        ax.text(vocab_x + 18, 14.5, 'CRASHED 💥', fontsize=18, ha='center',
                color='white', weight='700')
    
    # ========== RIGHT: STRINGSTORE ==========
    string_x = 52
    
    # Title
    ax.text(string_x + 18, 82, 'STRINGSTORE', fontsize=28, ha='center',
            color=COLORS['primary'], weight='700')
    
    # Single growing cache (no separation - everything permanent!)
    string_cache_height = 20 + (58 * (string_fill_pct / 100.0))
    
    string_box = FancyBboxPatch((string_x, 20), 36, string_cache_height,
                                boxstyle="round,pad=0.3",
                                edgecolor=vocab_color,
                                facecolor=vocab_color if not pod_crashed else COLORS['critical'],
                                linewidth=4,
                                alpha=0.7 if not pod_crashed else 0.9)
    ax.add_patch(string_box)
    
    # Show fill pattern
    if not pod_crashed:
        fill_steps = int((string_cache_height / 2.5))
        for i in range(fill_steps):
            y_pos = 21 + (i * 2.5)
            if y_pos < 20 + string_cache_height - 1:
                alpha_val = 0.3 + (i / fill_steps) * 0.5
                fill_bar = Rectangle((string_x + 2, y_pos), 32, 2,
                                    facecolor='#FFEB3B',
                                    edgecolor='none',
                                    alpha=alpha_val)
                ax.add_patch(fill_bar)
    
    # Show count and status
    mid_y = 20 + string_cache_height / 2
    if not pod_crashed:
        ax.text(string_x + 18, mid_y + 8, f'{string_size:,}', fontsize=28, ha='center',
                color='white', weight='700')
        ax.text(string_x + 18, mid_y + 3, 'entries', fontsize=14, ha='center',
                color='white', weight='500')
        
        growth = string_size - 639984
        ax.text(string_x + 18, mid_y - 3, f'+{growth:,}', fontsize=16, ha='center',
                color='white', weight='600', style='italic')
        ax.text(string_x + 18, mid_y - 7, 'NEVER CLEANED', fontsize=13, ha='center',
                color='white', weight='700',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.3))
    else:
        ax.text(string_x + 18, mid_y + 3, 'MEMORY', fontsize=20, ha='center',
                color='white', weight='700')
        ax.text(string_x + 18, mid_y - 3, 'EXHAUSTED', fontsize=20, ha='center',
                color='white', weight='700')
    
    # Status indicator
    status_box2 = Rectangle((string_x - 2, 12), 40, 5,
                           facecolor=vocab_color if not pod_crashed else COLORS['critical'],
                           edgecolor=COLORS['line'],
                           linewidth=2,
                           alpha=0.9)
    ax.add_patch(status_box2)
    
    if not pod_crashed:
        ax.text(string_x + 18, 14.5, f'STATUS: {status.upper()}', fontsize=16, ha='center',
                color='white', weight='700')
    else:
        ax.text(string_x + 18, 14.5, 'CRASHED 💥', fontsize=18, ha='center',
                color='white', weight='700')
    
    # ========== BOTTOM: EXPLANATION ==========
    if not pod_crashed:
        info_box = FancyBboxPatch((8, 2), 84, 7,
                                  boxstyle="round,pad=0.4",
                                  edgecolor=COLORS['danger'],
                                  facecolor='#FEF2F2',
                                  linewidth=3)
        ax.add_patch(info_box)
        
        ax.text(50, 7.5, '❌ The Problem: No Cleanup Mechanism', fontsize=20, ha='center',
                color=COLORS['danger'], weight='700')
        
        ax.text(50, 5.3, '→ Every unique token is added PERMANENTLY to main cache', 
                fontsize=14, ha='center', color=COLORS['primary'], weight='500')
        ax.text(50, 3.5, '→ No separation, no cleanup → Unbounded growth → Memory exhaustion → Pod crashes', 
                fontsize=14, ha='center', color=COLORS['danger'], weight='600')
    else:
        crash_box = FancyBboxPatch((8, 2), 84, 7,
                                   boxstyle="round,pad=0.4",
                                   edgecolor=COLORS['critical'],
                                   facecolor='#8B0000',
                                   linewidth=4)
        ax.add_patch(crash_box)
        
        ax.text(50, 7.5, '💥 POD CRASHED - SERVICE DISRUPTED', fontsize=22, ha='center',
                color='white', weight='700')
        
        ax.text(50, 5.3, 'Memory limit exceeded after continuous growth', 
                fontsize=15, ha='center', color='white', weight='600')
        ax.text(50, 3.5, '✓ Solution: Memory Zone separates transient from permanent and auto-cleans!', 
                fontsize=15, ha='center', color='#90EE90', weight='700')

# ============================================================================
# CREATE STATIC IMAGES (KEY FRAMES) - WITHOUT MEMORY ZONE
# ============================================================================

print("Creating static key frames for WITHOUT Memory Zone scenario...")

# Frame 1: Initial state
fig1 = plt.figure(figsize=(20, 12))
fig1.patch.set_facecolor(COLORS['bg'])
create_frame_without_zone(fig1, 100, 15000, 645000, pod_crashed=False)
plt.savefig('/mnt/user-data/outputs/spacy_without_zone_frame_1_start.png', 
            dpi=300, bbox_inches='tight', facecolor=COLORS['bg'])
print("✅ Frame 1: Initial state (small growth)")

# Frame 2: Growing
fig2 = plt.figure(figsize=(20, 12))
fig2.patch.set_facecolor(COLORS['bg'])
create_frame_without_zone(fig2, 5000, 75000, 670000, pod_crashed=False)
plt.savefig('/mnt/user-data/outputs/spacy_without_zone_frame_2_growing.png', 
            dpi=300, bbox_inches='tight', facecolor=COLORS['bg'])
print("✅ Frame 2: Growing (medium)")

# Frame 3: Warning
fig3 = plt.figure(figsize=(20, 12))
fig3.patch.set_facecolor(COLORS['bg'])
create_frame_without_zone(fig3, 10000, 130000, 685000, pod_crashed=False)
plt.savefig('/mnt/user-data/outputs/spacy_without_zone_frame_3_warning.png', 
            dpi=300, bbox_inches='tight', facecolor=COLORS['bg'])
print("✅ Frame 3: Warning (high growth)")

# Frame 4: Critical before crash
fig4 = plt.figure(figsize=(20, 12))
fig4.patch.set_facecolor(COLORS['bg'])
create_frame_without_zone(fig4, 15000, 176745, 700499, pod_crashed=False)
plt.savefig('/mnt/user-data/outputs/spacy_without_zone_frame_4_critical.png', 
            dpi=300, bbox_inches='tight', facecolor=COLORS['bg'])
print("✅ Frame 4: Critical (about to crash)")

# Frame 5: Crashed
fig5 = plt.figure(figsize=(20, 12))
fig5.patch.set_facecolor(COLORS['bg'])
create_frame_without_zone(fig5, 15500, 176745, 700499, pod_crashed=True)
plt.savefig('/mnt/user-data/outputs/spacy_without_zone_frame_5_crashed.png', 
            dpi=300, bbox_inches='tight', facecolor=COLORS['bg'])
print("✅ Frame 5: Pod crashed!")

plt.close('all')

# ============================================================================
# CREATE ANIMATED GIF - WITHOUT MEMORY ZONE
# ============================================================================

print(f"\nCreating animated GIF (speed: {ANIMATION_SPEED}ms per frame)...")

fig_anim = plt.figure(figsize=(20, 12))
fig_anim.patch.set_facecolor(COLORS['bg'])

def animate_without_zone(frame):
    """Animation function showing continuous growth without cleanup"""
    
    # Growth rate per frame
    vocab_growth_rate = 175289 / 60  # Grow to max in 60 frames
    string_growth_rate = 60515 / 60
    
    if frame < 60:
        # Continuous growth phase
        transaction = int(100 + frame * 250)
        vocab = int(1456 + (frame * vocab_growth_rate))
        string = int(639984 + (frame * string_growth_rate))
        create_frame_without_zone(fig_anim, transaction, vocab, string, pod_crashed=False)
    
    elif frame < 70:
        # Hold at critical
        create_frame_without_zone(fig_anim, 15000, 176745, 700499, pod_crashed=False)
    
    else:
        # Crashed state
        create_frame_without_zone(fig_anim, 15500, 176745, 700499, pod_crashed=True)

# Create animation
total_frames = 80
anim = FuncAnimation(fig_anim, animate_without_zone, frames=total_frames, 
                     interval=ANIMATION_SPEED, repeat=True)

# Save as GIF
writer = PillowWriter(fps=int(1000/ANIMATION_SPEED))
anim.save('/mnt/user-data/outputs/spacy_without_memory_zone_problem.gif', 
          writer=writer, dpi=100)

print("✅ Animated GIF created (WITHOUT Memory Zone)")

plt.close('all')

print("\n" + "="*70)
print("✅ ALL FILES CREATED SUCCESSFULLY!")
print("="*70)
print(f"\n⚙️  Animation Speed: {ANIMATION_SPEED}ms per frame")
print("   (Edit ANIMATION_SPEED variable in code to adjust)")
print("\n📁 Static Frames (High Resolution - 300 DPI):")
print("   1. spacy_without_zone_frame_1_start.png - Initial small growth")
print("   2. spacy_without_zone_frame_2_growing.png - Medium growth")
print("   3. spacy_without_zone_frame_3_warning.png - Warning level")
print("   4. spacy_without_zone_frame_4_critical.png - Critical state")
print("   5. spacy_without_zone_frame_5_crashed.png - Pod crashed!")
print("\n🎬 Animated Version:")
print("   • spacy_without_memory_zone_problem.gif - Continuous growth to crash")
print("\n💡 This animation shows THE PROBLEM:")
print("   ❌ No separation between permanent and transient")
print("   ❌ All entries added directly to main cache")
print("   ❌ Never cleaned - continuous unbounded growth")
print("   ❌ Eventually hits memory limit → Pod crashes")
print("   ✓ Memory Zone solves this by separating and cleaning transient entries!")
