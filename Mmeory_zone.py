import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch, Circle, Wedge
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
    'permanent': '#A3BE8C',     # Sage green for permanent
    'transient': '#D08770',     # Orange for transient
    'filling': '#EBCB8B',       # Yellow for filling
    'accent_blue': '#5E81AC',
    'accent_red': '#BF616A',
    'bg': '#FFFFFF',
    'line': '#4C566A',
    'pod_limit': '#BF616A'      # Red for pod limit line
}

# ============================================================================
# FUNCTION TO CREATE SINGLE FRAME
# ============================================================================
def create_frame(fig, fill_percentage, show_cleanup=False, batch_num=1):
    """Create a single frame showing the filling/clearing state"""
    fig.clear()
    
    # Main title
    fig.text(0.5, 0.96, 'spaCy Memory Zone: Transient Cache Lifecycle', 
             fontsize=42, ha='center', va='top', 
             color=COLORS['primary'], weight='600')
    
    if not show_cleanup:
        stage_text = f'Batch #{batch_num} Processing: {fill_percentage:.0f}% Transient Cache Filled'
        stage_color = COLORS['transient']
    else:
        stage_text = f'Batch #{batch_num} Complete: Transient Cache CLEARED ✓'
        stage_color = COLORS['permanent']
    
    fig.text(0.5, 0.92, stage_text, 
             fontsize=24, ha='center', va='top',
             color=stage_color, weight='500')
    
    # Create main axes
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    # ========== LEFT: VOCABULARY ==========
    vocab_x = 12
    
    # Title
    ax.text(vocab_x + 18, 82, 'VOCABULARY', fontsize=28, ha='center',
            color=COLORS['primary'], weight='700')
    
    # Permanent section (bottom - always stable)
    perm_vocab = FancyBboxPatch((vocab_x, 20), 36, 30,
                                boxstyle="round,pad=0.3",
                                edgecolor=COLORS['permanent'],
                                facecolor='#F0F9F4',
                                linewidth=4)
    ax.add_patch(perm_vocab)
    
    ax.text(vocab_x + 18, 42, 'PERMANENT', fontsize=16, ha='center',
            color=COLORS['permanent'], weight='700')
    ax.text(vocab_x + 18, 37, '1,456', fontsize=32, ha='center',
            color=COLORS['permanent'], weight='700')
    ax.text(vocab_x + 18, 32, 'entries', fontsize=14, ha='center',
            color=COLORS['primary'], weight='400')
    ax.text(vocab_x + 18, 26, 'Model Baseline', fontsize=12, ha='center',
            color=COLORS['primary'], weight='400', style='italic')
    
    # Transient section (top - fills and empties)
    trans_height = 28 * (fill_percentage / 100.0) if not show_cleanup else 0
    
    if trans_height > 0:
        trans_vocab = FancyBboxPatch((vocab_x, 52), 36, trans_height,
                                    boxstyle="round,pad=0.3",
                                    edgecolor=COLORS['transient'],
                                    facecolor='#FFF8E7',
                                    linewidth=4,
                                    linestyle='--',
                                    alpha=0.9)
        ax.add_patch(trans_vocab)
        
        # BATCH NUMBER INDICATOR - shown when filling
        batch_indicator = FancyBboxPatch((vocab_x - 10, 60), 8, 8,
                                        boxstyle="round,pad=0.3",
                                        edgecolor=COLORS['primary'],
                                        facecolor='white',
                                        linewidth=3)
        ax.add_patch(batch_indicator)
        
        ax.text(vocab_x - 6, 67, f'{batch_num}', fontsize=24, ha='center', va='center',
                color=COLORS['primary'], weight='700')
        ax.text(vocab_x - 6, 60.5, 'Batch', fontsize=10, ha='center', va='center',
                color=COLORS['primary'], weight='600')
        
        # Animated fill pattern
        fill_steps = int((trans_height / 2))
        for i in range(fill_steps):
            y_pos = 53 + (i * 2)
            if y_pos < 52 + trans_height - 1:
                fill_bar = Rectangle((vocab_x + 2, y_pos), 32, 1.5,
                                    facecolor=COLORS['filling'],
                                    edgecolor='none',
                                    alpha=0.6)
                ax.add_patch(fill_bar)
        
        # Show count
        mid_y = 52 + trans_height / 2
        ax.text(vocab_x + 18, mid_y + 3, 'TRANSIENT', fontsize=14, ha='center',
                color=COLORS['transient'], weight='700')
        
        new_entries = int(175289 * (fill_percentage / 100.0))
        ax.text(vocab_x + 18, mid_y - 2, f'{new_entries:,}', fontsize=20, ha='center',
                color=COLORS['transient'], weight='700')
        ax.text(vocab_x + 18, mid_y - 6, 'new entries', fontsize=11, ha='center',
                color=COLORS['primary'], weight='400')
    else:
        # Show empty transient slot
        empty_trans = FancyBboxPatch((vocab_x, 52), 36, 28,
                                    boxstyle="round,pad=0.3",
                                    edgecolor=COLORS['line'],
                                    facecolor='#F5F5F5',
                                    linewidth=2,
                                    linestyle=':',
                                    alpha=0.3)
        ax.add_patch(empty_trans)
        
        ax.text(vocab_x + 18, 66, 'TRANSIENT', fontsize=14, ha='center',
                color=COLORS['line'], weight='600', alpha=0.5)
        ax.text(vocab_x + 18, 61, '0', fontsize=28, ha='center',
                color=COLORS['line'], weight='700', alpha=0.5)
        ax.text(vocab_x + 18, 56, 'CLEARED', fontsize=12, ha='center',
                color=COLORS['permanent'], weight='700')
    
    # Total indicator
    total_vocab = 1456 + int(175289 * (fill_percentage / 100.0)) if not show_cleanup else 1456
    total_box = Rectangle((vocab_x - 2, 12), 40, 5,
                          facecolor=COLORS['accent_blue'] if total_vocab > 1456 else COLORS['permanent'],
                          edgecolor=COLORS['line'],
                          linewidth=2,
                          alpha=0.8)
    ax.add_patch(total_box)
    
    ax.text(vocab_x + 18, 14.5, f'TOTAL: {total_vocab:,}', fontsize=16, ha='center',
            color='white', weight='700')
    
    # ========== RIGHT: STRINGSTORE ==========
    string_x = 52
    
    # Title
    ax.text(string_x + 18, 82, 'STRINGSTORE', fontsize=28, ha='center',
            color=COLORS['primary'], weight='700')
    
    # Permanent section (bottom - always stable)
    perm_string = FancyBboxPatch((string_x, 20), 36, 30,
                                 boxstyle="round,pad=0.3",
                                 edgecolor=COLORS['permanent'],
                                 facecolor='#F0F9F4',
                                 linewidth=4)
    ax.add_patch(perm_string)
    
    ax.text(string_x + 18, 42, 'PERMANENT', fontsize=16, ha='center',
            color=COLORS['permanent'], weight='700')
    ax.text(string_x + 18, 37, '639,984', fontsize=28, ha='center',
            color=COLORS['permanent'], weight='700')
    ax.text(string_x + 18, 32, 'entries', fontsize=14, ha='center',
            color=COLORS['primary'], weight='400')
    ax.text(string_x + 18, 26, 'Model Baseline', fontsize=12, ha='center',
            color=COLORS['primary'], weight='400', style='italic')
    
    # Transient section (top - fills and empties)
    if trans_height > 0:
        trans_string = FancyBboxPatch((string_x, 52), 36, trans_height,
                                     boxstyle="round,pad=0.3",
                                     edgecolor=COLORS['transient'],
                                     facecolor='#FFF8E7',
                                     linewidth=4,
                                     linestyle='--',
                                     alpha=0.9)
        ax.add_patch(trans_string)
        
        # BATCH NUMBER INDICATOR - shown when filling (right side)
        batch_indicator_right = FancyBboxPatch((string_x + 38, 60), 8, 8,
                                              boxstyle="round,pad=0.3",
                                              edgecolor=COLORS['primary'],
                                              facecolor='white',
                                              linewidth=3)
        ax.add_patch(batch_indicator_right)
        
        ax.text(string_x + 42, 67, f'{batch_num}', fontsize=24, ha='center', va='center',
                color=COLORS['primary'], weight='700')
        ax.text(string_x + 42, 60.5, 'Batch', fontsize=10, ha='center', va='center',
                color=COLORS['primary'], weight='600')
        
        # Animated fill pattern
        for i in range(fill_steps):
            y_pos = 53 + (i * 2)
            if y_pos < 52 + trans_height - 1:
                fill_bar = Rectangle((string_x + 2, y_pos), 32, 1.5,
                                    facecolor=COLORS['filling'],
                                    edgecolor='none',
                                    alpha=0.6)
                ax.add_patch(fill_bar)
        
        # Show count
        mid_y = 52 + trans_height / 2
        ax.text(string_x + 18, mid_y + 3, 'TRANSIENT', fontsize=14, ha='center',
                color=COLORS['transient'], weight='700')
        
        new_string_entries = int(60515 * (fill_percentage / 100.0))
        ax.text(string_x + 18, mid_y - 2, f'{new_string_entries:,}', fontsize=20, ha='center',
                color=COLORS['transient'], weight='700')
        ax.text(string_x + 18, mid_y - 6, 'new entries', fontsize=11, ha='center',
                color=COLORS['primary'], weight='400')
    else:
        # Show empty transient slot
        empty_trans = FancyBboxPatch((string_x, 52), 36, 28,
                                    boxstyle="round,pad=0.3",
                                    edgecolor=COLORS['line'],
                                    facecolor='#F5F5F5',
                                    linewidth=2,
                                    linestyle=':',
                                    alpha=0.3)
        ax.add_patch(empty_trans)
        
        ax.text(string_x + 18, 66, 'TRANSIENT', fontsize=14, ha='center',
                color=COLORS['line'], weight='600', alpha=0.5)
        ax.text(string_x + 18, 61, '0', fontsize=28, ha='center',
                color=COLORS['line'], weight='700', alpha=0.5)
        ax.text(string_x + 18, 56, 'CLEARED', fontsize=12, ha='center',
                color=COLORS['permanent'], weight='700')
    
    # Total indicator
    total_string = 639984 + int(60515 * (fill_percentage / 100.0)) if not show_cleanup else 639984
    total_box2 = Rectangle((string_x - 2, 12), 40, 5,
                           facecolor=COLORS['accent_blue'] if total_string > 639984 else COLORS['permanent'],
                           edgecolor=COLORS['line'],
                           linewidth=2,
                           alpha=0.8)
    ax.add_patch(total_box2)
    
    ax.text(string_x + 18, 14.5, f'TOTAL: {total_string:,}', fontsize=16, ha='center',
            color='white', weight='700')
    
    # ========== BOTTOM: EXPLANATION ==========
    info_box = FancyBboxPatch((8, 2), 84, 7,
                              boxstyle="round,pad=0.4",
                              edgecolor=COLORS['accent_blue'],
                              facecolor='#EBF5FB',
                              linewidth=3)
    ax.add_patch(info_box)
    
    ax.text(50, 7.5, 'Memory Zone Mechanism', fontsize=20, ha='center',
            color=COLORS['primary'], weight='700')
    
    if not show_cleanup:
        ax.text(50, 5.3, '→ New transactions create TRANSIENT entries in both caches', 
                fontsize=14, ha='center', color=COLORS['primary'], weight='500')
        ax.text(50, 3.5, '→ PERMANENT baseline (1,456 | 639,984) remains untouched', 
                fontsize=14, ha='center', color=COLORS['permanent'], weight='500')
    else:
        ax.text(50, 5.3, '✓ Transaction complete → Memory Zone exits', 
                fontsize=14, ha='center', color=COLORS['permanent'], weight='600')
        ax.text(50, 3.5, '✓ Transient entries AUTO-CLEANED → Back to baseline!', 
                fontsize=14, ha='center', color=COLORS['permanent'], weight='600')

# ============================================================================
# CREATE STATIC IMAGES (KEY FRAMES)
# ============================================================================

print("Creating static key frames...")

# Frame 1: Empty (baseline)
fig1 = plt.figure(figsize=(20, 12))
fig1.patch.set_facecolor(COLORS['bg'])
create_frame(fig1, 0, show_cleanup=False, batch_num=1)
plt.savefig('/mnt/user-data/outputs/spacy_frame_1_baseline.png', 
            dpi=300, bbox_inches='tight', facecolor=COLORS['bg'])
print("✅ Frame 1: Baseline (0% filled)")

# Frame 2: Partially filled
fig2 = plt.figure(figsize=(20, 12))
fig2.patch.set_facecolor(COLORS['bg'])
create_frame(fig2, 50, show_cleanup=False, batch_num=1)
plt.savefig('/mnt/user-data/outputs/spacy_frame_2_filling.png', 
            dpi=300, bbox_inches='tight', facecolor=COLORS['bg'])
print("✅ Frame 2: Processing (50% filled)")

# Frame 3: Fully filled
fig3 = plt.figure(figsize=(20, 12))
fig3.patch.set_facecolor(COLORS['bg'])
create_frame(fig3, 100, show_cleanup=False, batch_num=1)
plt.savefig('/mnt/user-data/outputs/spacy_frame_3_full.png', 
            dpi=300, bbox_inches='tight', facecolor=COLORS['bg'])
print("✅ Frame 3: Maximum (100% filled)")

# Frame 4: Cleaned
fig4 = plt.figure(figsize=(20, 12))
fig4.patch.set_facecolor(COLORS['bg'])
create_frame(fig4, 0, show_cleanup=True, batch_num=1)
plt.savefig('/mnt/user-data/outputs/spacy_frame_4_cleaned.png', 
            dpi=300, bbox_inches='tight', facecolor=COLORS['bg'])
print("✅ Frame 4: Cleaned (back to baseline)")

plt.close('all')

# ============================================================================
# CREATE ANIMATED GIF
# ============================================================================

print("\nCreating animated GIF...")

fig_anim = plt.figure(figsize=(20, 12))
fig_anim.patch.set_facecolor(COLORS['bg'])

def animate(frame):
    """Animation function for each frame - shows multiple batch cycles"""
    
    # Define cycle: each batch goes through fill -> hold -> cleanup -> hold -> next batch
    frames_per_cycle = 28  # Frames for one complete batch cycle
    
    # Calculate which batch we're in
    batch_num = (frame // frames_per_cycle) + 1
    frame_in_cycle = frame % frames_per_cycle
    
    # Filling phase: 0-100%
    if frame_in_cycle < 14:
        fill_pct = (frame_in_cycle / 14) * 100
        create_frame(fig_anim, fill_pct, show_cleanup=False, batch_num=batch_num)
    # Hold at full
    elif frame_in_cycle < 18:
        create_frame(fig_anim, 100, show_cleanup=False, batch_num=batch_num)
    # Cleanup phase
    elif frame_in_cycle < 20:
        create_frame(fig_anim, 0, show_cleanup=True, batch_num=batch_num)
    # Hold at baseline
    else:
        create_frame(fig_anim, 0, show_cleanup=True, batch_num=batch_num)

# Create animation - show 3 complete batch cycles
total_frames = 28 * 3  # 3 batches
anim = FuncAnimation(fig_anim, animate, frames=total_frames, 
                     interval=ANIMATION_SPEED, repeat=True)

# Save as GIF
writer = PillowWriter(fps=int(1000/ANIMATION_SPEED))
anim.save('/mnt/user-data/outputs/spacy_memory_zone_animation.gif', 
          writer=writer, dpi=100)

print("✅ Animated GIF created")

plt.close('all')

print("\n" + "="*70)
print("✅ ALL FILES CREATED SUCCESSFULLY!")
print("="*70)
print(f"\n⚙️  Animation Speed: {ANIMATION_SPEED}ms per frame")
print("   (Edit ANIMATION_SPEED variable at top of code to adjust)")
print("\n📁 Static Frames (High Resolution - 300 DPI):")
print("   1. spacy_frame_1_baseline.png - Empty baseline state")
print("   2. spacy_frame_2_filling.png - Mid-processing (50%)")
print("   3. spacy_frame_3_full.png - Fully loaded (100%)")
print("   4. spacy_frame_4_cleaned.png - After cleanup")
print("\n🎬 Animated Version:")
print("   • spacy_memory_zone_animation.gif - Shows 3 batch cycles")
print("\n💡 The animation shows:")
print("   → Batch #1: Fill → Process → Clean → Baseline")
print("   → Batch #2: Fill → Process → Clean → Baseline")
print("   → Batch #3: Fill → Process → Clean → Baseline")
print("   → Permanent baseline (1,456 | 639,984) stays constant")
print("   → Transient cache fills and clears with each batch")
print("   → Memory stays stable - no unbounded growth!")
