import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch
from matplotlib.animation import FuncAnimation, FFMpegWriter, PillowWriter
import numpy as np

# ============================================================================
# CONFIGURATION
# ============================================================================
ANIMATION_SPEED = 150  # milliseconds per frame
FPS = int(1000 / ANIMATION_SPEED)

# Professional color palette
COLORS = {
    'primary': '#2E3440',
    'permanent': '#A3BE8C',
    'transient': '#D08770',
    'filling': '#EBCB8B',
    'accent_blue': '#5E81AC',
    'accent_red': '#BF616A',
    'danger': '#BF616A',
    'critical': '#8B0000',
    'bg': '#FFFFFF',
    'line': '#4C566A'
}

# ============================================================================
# FRAME CREATION FUNCTIONS (SAME AS MP4 VERSION)
# ============================================================================

def create_frame_with_zone(fig, fill_percentage, show_cleanup=False, batch_num=1):
    """Create frame for WITH Memory Zone animation"""
    fig.clear()
    
    if not show_cleanup:
        stage_text = f'Batch #{batch_num} Processing: {fill_percentage:.0f}% Transient Filled'
        stage_color = COLORS['transient']
    else:
        stage_text = f'Batch #{batch_num} Complete: Transient CLEARED ✓'
        stage_color = COLORS['permanent']
    
    fig.text(0.5, 0.96, 'WITH Memory Zone: Controlled Cleanup', 
             fontsize=38, ha='center', va='top', 
             color=COLORS['permanent'], weight='700')
    
    fig.text(0.5, 0.91, stage_text, 
             fontsize=22, ha='center', va='top',
             color=stage_color, weight='600')
    
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 100)
    ax.set_ylim(-11, 90)
    ax.axis('off')
    
    # ========== LEFT: VOCABULARY ==========
    vocab_x = 12
    
    ax.text(vocab_x + 18, 78, 'VOCABULARY', fontsize=26, ha='center',
            color=COLORS['primary'], weight='700')
    
    perm_vocab = FancyBboxPatch((vocab_x, 10), 36, 30,
                                boxstyle="round,pad=0.3",
                                edgecolor=COLORS['permanent'],
                                facecolor='#F0F9F4',
                                linewidth=4)
    ax.add_patch(perm_vocab)
    
    ax.text(vocab_x + 18, 32, 'PERMANENT', fontsize=15, ha='center',
            color=COLORS['permanent'], weight='700')
    ax.text(vocab_x + 18, 27, '1,456', fontsize=28, ha='center',
            color=COLORS['permanent'], weight='700')
    ax.text(vocab_x + 18, 22, 'entries', fontsize=13, ha='center',
            color=COLORS['primary'], weight='400')
    ax.text(vocab_x + 18, 16, 'Model Baseline', fontsize=11, ha='center',
            color=COLORS['primary'], weight='400', style='italic')
    
    trans_height = 28 * (fill_percentage / 100.0) if not show_cleanup else 0
    
    if trans_height > 0:
        trans_vocab = FancyBboxPatch((vocab_x, 42), 36, trans_height,
                                    boxstyle="round,pad=0.3",
                                    edgecolor=COLORS['transient'],
                                    facecolor='#FFF8E7',
                                    linewidth=4,
                                    linestyle='--',
                                    alpha=0.9)
        ax.add_patch(trans_vocab)
        
        batch_indicator = FancyBboxPatch((vocab_x - 10, 48), 8, 12,
                                        boxstyle="round,pad=0.4",
                                        edgecolor=COLORS['primary'],
                                        facecolor='white',
                                        linewidth=3)
        ax.add_patch(batch_indicator)
        
        ax.text(vocab_x - 6, 56.5, f'{batch_num}', fontsize=24, ha='center', va='center',
                color=COLORS['primary'], weight='700')
        ax.text(vocab_x - 6, 50.5, 'Batch', fontsize=10, ha='center', va='center',
                color=COLORS['primary'], weight='600')
        
        fill_steps = int((trans_height / 2))
        for i in range(fill_steps):
            y_pos = 43 + (i * 2)
            if y_pos < 42 + trans_height - 1:
                fill_bar = Rectangle((vocab_x + 2, y_pos), 32, 1.5,
                                    facecolor=COLORS['filling'],
                                    edgecolor='none',
                                    alpha=0.6)
                ax.add_patch(fill_bar)
        
        mid_y = 42 + trans_height / 2
        ax.text(vocab_x + 18, mid_y + 3, 'TRANSIENT', fontsize=13, ha='center',
                color=COLORS['transient'], weight='700')
        
        new_entries = int(175289 * (fill_percentage / 100.0))
        ax.text(vocab_x + 18, mid_y - 2, f'{new_entries:,}', fontsize=18, ha='center',
                color=COLORS['transient'], weight='700')
        ax.text(vocab_x + 18, mid_y - 6, 'new entries', fontsize=10, ha='center',
                color=COLORS['primary'], weight='400')
    else:
        empty_trans = FancyBboxPatch((vocab_x, 42), 36, 28,
                                    boxstyle="round,pad=0.3",
                                    edgecolor=COLORS['line'],
                                    facecolor='#F5F5F5',
                                    linewidth=2,
                                    linestyle=':',
                                    alpha=0.3)
        ax.add_patch(empty_trans)
        
        ax.text(vocab_x + 18, 56, 'TRANSIENT', fontsize=13, ha='center',
                color=COLORS['line'], weight='600', alpha=0.5)
        ax.text(vocab_x + 18, 51, '0', fontsize=24, ha='center',
                color=COLORS['line'], weight='700', alpha=0.5)
        ax.text(vocab_x + 18, 46, 'CLEARED', fontsize=11, ha='center',
                color=COLORS['permanent'], weight='700')
    
    total_vocab = 1456 + int(175289 * (fill_percentage / 100.0)) if not show_cleanup else 1456
    total_box = Rectangle((vocab_x - 2, 2), 40, 5,
                          facecolor=COLORS['accent_blue'] if total_vocab > 1456 else COLORS['permanent'],
                          edgecolor=COLORS['line'],
                          linewidth=2,
                          alpha=0.8)
    ax.add_patch(total_box)
    
    ax.text(vocab_x + 18, 4.5, f'TOTAL: {total_vocab:,}', fontsize=14, ha='center',
            color='white', weight='700')
    
    # ========== RIGHT: STRINGSTORE ==========
    string_x = 52
    
    ax.text(string_x + 18, 78, 'STRINGSTORE', fontsize=26, ha='center',
            color=COLORS['primary'], weight='700')
    
    perm_string = FancyBboxPatch((string_x, 10), 36, 30,
                                 boxstyle="round,pad=0.3",
                                 edgecolor=COLORS['permanent'],
                                 facecolor='#F0F9F4',
                                 linewidth=4)
    ax.add_patch(perm_string)
    
    ax.text(string_x + 18, 32, 'PERMANENT', fontsize=15, ha='center',
            color=COLORS['permanent'], weight='700')
    ax.text(string_x + 18, 27, '639,984', fontsize=25, ha='center',
            color=COLORS['permanent'], weight='700')
    ax.text(string_x + 18, 22, 'entries', fontsize=13, ha='center',
            color=COLORS['primary'], weight='400')
    ax.text(string_x + 18, 16, 'Model Baseline', fontsize=11, ha='center',
            color=COLORS['primary'], weight='400', style='italic')
    
    if trans_height > 0:
        trans_string = FancyBboxPatch((string_x, 42), 36, trans_height,
                                     boxstyle="round,pad=0.3",
                                     edgecolor=COLORS['transient'],
                                     facecolor='#FFF8E7',
                                     linewidth=4,
                                     linestyle='--',
                                     alpha=0.9)
        ax.add_patch(trans_string)
        
        batch_indicator_right = FancyBboxPatch((string_x + 38, 48), 8, 12,
                                              boxstyle="round,pad=0.4",
                                              edgecolor=COLORS['primary'],
                                              facecolor='white',
                                              linewidth=3)
        ax.add_patch(batch_indicator_right)
        
        ax.text(string_x + 42, 56.5, f'{batch_num}', fontsize=24, ha='center', va='center',
                color=COLORS['primary'], weight='700')
        ax.text(string_x + 42, 50.5, 'Batch', fontsize=10, ha='center', va='center',
                color=COLORS['primary'], weight='600')
        
        for i in range(fill_steps):
            y_pos = 43 + (i * 2)
            if y_pos < 42 + trans_height - 1:
                fill_bar = Rectangle((string_x + 2, y_pos), 32, 1.5,
                                    facecolor=COLORS['filling'],
                                    edgecolor='none',
                                    alpha=0.6)
                ax.add_patch(fill_bar)
        
        mid_y = 42 + trans_height / 2
        ax.text(string_x + 18, mid_y + 3, 'TRANSIENT', fontsize=13, ha='center',
                color=COLORS['transient'], weight='700')
        
        new_string_entries = int(60515 * (fill_percentage / 100.0))
        ax.text(string_x + 18, mid_y - 2, f'{new_string_entries:,}', fontsize=18, ha='center',
                color=COLORS['transient'], weight='700')
        ax.text(string_x + 18, mid_y - 6, 'new entries', fontsize=10, ha='center',
                color=COLORS['primary'], weight='400')
    else:
        empty_trans = FancyBboxPatch((string_x, 42), 36, 28,
                                    boxstyle="round,pad=0.3",
                                    edgecolor=COLORS['line'],
                                    facecolor='#F5F5F5',
                                    linewidth=2,
                                    linestyle=':',
                                    alpha=0.3)
        ax.add_patch(empty_trans)
        
        ax.text(string_x + 18, 56, 'TRANSIENT', fontsize=13, ha='center',
                color=COLORS['line'], weight='600', alpha=0.5)
        ax.text(string_x + 18, 51, '0', fontsize=24, ha='center',
                color=COLORS['line'], weight='700', alpha=0.5)
        ax.text(string_x + 18, 46, 'CLEARED', fontsize=11, ha='center',
                color=COLORS['permanent'], weight='700')
    
    total_string = 639984 + int(60515 * (fill_percentage / 100.0)) if not show_cleanup else 639984
    total_box2 = Rectangle((string_x - 2, 2), 40, 5,
                           facecolor=COLORS['accent_blue'] if total_string > 639984 else COLORS['permanent'],
                           edgecolor=COLORS['line'],
                           linewidth=2,
                           alpha=0.8)
    ax.add_patch(total_box2)
    
    ax.text(string_x + 18, 4.5, f'TOTAL: {total_string:,}', fontsize=14, ha='center',
            color='white', weight='700')
    
    # Bottom explanation
    info_box = FancyBboxPatch((8, -9), 84, 7,
                              boxstyle="round,pad=0.4",
                              edgecolor=COLORS['accent_blue'],
                              facecolor='#EBF5FB',
                              linewidth=3)
    ax.add_patch(info_box)
    
    ax.text(50, -3.5, 'Memory Zone Mechanism', fontsize=18, ha='center',
            color=COLORS['primary'], weight='700')
    
    if not show_cleanup:
        ax.text(50, -5.5, 'New transactions create TRANSIENT entries in both caches', 
                fontsize=13, ha='center', color=COLORS['primary'], weight='500')
        ax.text(50, -7.5, 'PERMANENT baseline (1,456 | 639,984) remains untouched', 
                fontsize=13, ha='center', color=COLORS['permanent'], weight='600')
    else:
        ax.text(50, -5.5, '✓ Transaction complete → Memory Zone exits', 
                fontsize=13, ha='center', color=COLORS['permanent'], weight='600')
        ax.text(50, -7.5, '✓ Transient entries AUTO-CLEANED → Back to baseline!', 
                fontsize=13, ha='center', color=COLORS['permanent'], weight='600')


def create_frame_without_zone(fig, transaction_num, vocab_size, string_size, pod_crashed=False):
    """Create frame for WITHOUT Memory Zone animation"""
    fig.clear()
    
    if not pod_crashed:
        fig.text(0.5, 0.96, 'WITHOUT Memory Zone: Unbounded Growth', 
                 fontsize=38, ha='center', va='top', 
                 color=COLORS['danger'], weight='700')
        
        stage_text = f'Transaction #{transaction_num:,} - All Entries Added PERMANENTLY'
        stage_color = COLORS['danger']
    else:
        fig.text(0.5, 0.96, 'WITHOUT Memory Zone: POD CRASHED! 💥', 
                 fontsize=38, ha='center', va='top', 
                 color=COLORS['critical'], weight='700')
        
        stage_text = 'Memory Limit Exceeded - Service Disruption'
        stage_color = COLORS['critical']
    
    fig.text(0.5, 0.91, stage_text, 
             fontsize=22, ha='center', va='top',
             color=stage_color, weight='600')
    
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 100)
    ax.set_ylim(-11, 90)
    ax.axis('off')
    
    vocab_fill_pct = min(100, ((vocab_size - 1456) / 175289) * 100)
    
    if vocab_size < 50000:
        vocab_color = COLORS['permanent']
        status = 'Normal'
    elif vocab_size < 100000:
        vocab_color = COLORS['transient']
        status = 'Growing'
    elif vocab_size < 150000:
        vocab_color = COLORS['danger']
        status = 'Warning'
    else:
        vocab_color = COLORS['critical']
        status = 'Critical'
    
    # ========== LEFT: VOCABULARY ==========
    vocab_x = 12
    
    ax.text(vocab_x + 18, 78, 'VOCABULARY', fontsize=26, ha='center',
            color=COLORS['primary'], weight='700')
    
    if not pod_crashed and transaction_num > 100:
        batch_num = min(5, int(transaction_num / 3000) + 1)
        
        batch_accum_box = FancyBboxPatch((vocab_x - 10, 50), 8, 10,
                                        boxstyle="round,pad=0.4",
                                        edgecolor=vocab_color,
                                        facecolor='white',
                                        linewidth=3)
        ax.add_patch(batch_accum_box)
        
        ax.text(vocab_x - 6, 57.5, f'{batch_num}', fontsize=22, ha='center', va='center',
                color=vocab_color, weight='700')
        
        ax.text(vocab_x - 6, 52, 'Batch', fontsize=9, ha='center', va='center',
                color=COLORS['primary'], weight='600')
    
    cache_height = 10 + (62 * (vocab_fill_pct / 100.0))
    
    vocab_box = FancyBboxPatch((vocab_x, 10), 36, cache_height,
                               boxstyle="round,pad=0.3",
                               edgecolor=vocab_color,
                               facecolor=vocab_color if not pod_crashed else COLORS['critical'],
                               linewidth=4,
                               alpha=0.7 if not pod_crashed else 0.9)
    ax.add_patch(vocab_box)
    
    if not pod_crashed:
        fill_steps = int((cache_height / 2.5))
        for i in range(fill_steps):
            y_pos = 11 + (i * 2.5)
            if y_pos < 10 + cache_height - 1:
                alpha_val = 0.3 + (i / fill_steps) * 0.5
                fill_bar = Rectangle((vocab_x + 2, y_pos), 32, 2,
                                    facecolor='#FFEB3B',
                                    edgecolor='none',
                                    alpha=alpha_val)
                ax.add_patch(fill_bar)
    
    mid_y = 10 + cache_height / 2
    if not pod_crashed:
        ax.text(vocab_x + 18, mid_y + 8, f'{vocab_size:,}', fontsize=25, ha='center',
                color='white', weight='700')
        ax.text(vocab_x + 18, mid_y + 3, 'entries', fontsize=13, ha='center',
                color='white', weight='500')
        
        growth = vocab_size - 1456
        ax.text(vocab_x + 18, mid_y - 3, f'+{growth:,}', fontsize=15, ha='center',
                color='white', weight='600', style='italic')
        ax.text(vocab_x + 18, mid_y - 7, 'NEVER CLEANED', fontsize=12, ha='center',
                color='white', weight='700',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.3))
    else:
        ax.text(vocab_x + 18, mid_y + 3, 'MEMORY', fontsize=18, ha='center',
                color='white', weight='700')
        ax.text(vocab_x + 18, mid_y - 3, 'EXHAUSTED', fontsize=18, ha='center',
                color='white', weight='700')
    
    status_box = Rectangle((vocab_x - 2, 2), 40, 5,
                          facecolor=vocab_color if not pod_crashed else COLORS['critical'],
                          edgecolor=COLORS['line'],
                          linewidth=2,
                          alpha=0.9)
    ax.add_patch(status_box)
    
    if not pod_crashed:
        ax.text(vocab_x + 18, 4.5, f'{status.upper()}', fontsize=14, ha='center',
                color='white', weight='700')
    else:
        ax.text(vocab_x + 18, 4.5, 'CRASHED 💥', fontsize=16, ha='center',
                color='white', weight='700')
    
    # ========== RIGHT: STRINGSTORE ==========
    string_x = 52
    
    ax.text(string_x + 18, 78, 'STRINGSTORE', fontsize=26, ha='center',
            color=COLORS['primary'], weight='700')
    
    if not pod_crashed and transaction_num > 100:
        batch_num = min(5, int(transaction_num / 3000) + 1)
        
        batch_accum_box_right = FancyBboxPatch((string_x + 38, 50), 8, 10,
                                              boxstyle="round,pad=0.4",
                                              edgecolor=vocab_color,
                                              facecolor='white',
                                              linewidth=3)
        ax.add_patch(batch_accum_box_right)
        
        ax.text(string_x + 42, 57.5, f'{batch_num}', fontsize=22, ha='center', va='center',
                color=vocab_color, weight='700')
        
        ax.text(string_x + 42, 52, 'Batch', fontsize=9, ha='center', va='center',
                color=COLORS['primary'], weight='600')
    
    string_fill_pct = min(100, ((string_size - 639984) / 60515) * 100)
    string_cache_height = 10 + (62 * (string_fill_pct / 100.0))
    
    string_box = FancyBboxPatch((string_x, 10), 36, string_cache_height,
                                boxstyle="round,pad=0.3",
                                edgecolor=vocab_color,
                                facecolor=vocab_color if not pod_crashed else COLORS['critical'],
                                linewidth=4,
                                alpha=0.7 if not pod_crashed else 0.9)
    ax.add_patch(string_box)
    
    if not pod_crashed:
        fill_steps = int((string_cache_height / 2.5))
        for i in range(fill_steps):
            y_pos = 11 + (i * 2.5)
            if y_pos < 10 + string_cache_height - 1:
                alpha_val = 0.3 + (i / fill_steps) * 0.5
                fill_bar = Rectangle((string_x + 2, y_pos), 32, 2,
                                    facecolor='#FFEB3B',
                                    edgecolor='none',
                                    alpha=alpha_val)
                ax.add_patch(fill_bar)
    
    mid_y = 10 + string_cache_height / 2
    if not pod_crashed:
        ax.text(string_x + 18, mid_y + 8, f'{string_size:,}', fontsize=25, ha='center',
                color='white', weight='700')
        ax.text(string_x + 18, mid_y + 3, 'entries', fontsize=13, ha='center',
                color='white', weight='500')
        
        growth = string_size - 639984
        ax.text(string_x + 18, mid_y - 3, f'+{growth:,}', fontsize=15, ha='center',
                color='white', weight='600', style='italic')
        ax.text(string_x + 18, mid_y - 7, 'NEVER CLEANED', fontsize=12, ha='center',
                color='white', weight='700',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.3))
    else:
        ax.text(string_x + 18, mid_y + 3, 'MEMORY', fontsize=18, ha='center',
                color='white', weight='700')
        ax.text(string_x + 18, mid_y - 3, 'EXHAUSTED', fontsize=18, ha='center',
                color='white', weight='700')
    
    status_box2 = Rectangle((string_x - 2, 2), 40, 5,
                           facecolor=vocab_color if not pod_crashed else COLORS['critical'],
                           edgecolor=COLORS['line'],
                           linewidth=2,
                           alpha=0.9)
    ax.add_patch(status_box2)
    
    if not pod_crashed:
        ax.text(string_x + 18, 4.5, f'{status.upper()}', fontsize=14, ha='center',
                color='white', weight='700')
    else:
        ax.text(string_x + 18, 4.5, 'CRASHED 💥', fontsize=16, ha='center',
                color='white', weight='700')
    
    # Bottom explanation
    if not pod_crashed:
        info_box = FancyBboxPatch((8, -9), 84, 7,
                                  boxstyle="round,pad=0.4",
                                  edgecolor=COLORS['danger'],
                                  facecolor='#FEF2F2',
                                  linewidth=3)
        ax.add_patch(info_box)
        
        ax.text(50, -3.5, '❌ The Problem: No Cleanup Mechanism', fontsize=18, ha='center',
                color=COLORS['danger'], weight='700')
        
        ax.text(50, -5.5, 'Every unique token is added PERMANENTLY to main cache', 
                fontsize=13, ha='center', color=COLORS['primary'], weight='500')
        ax.text(50, -7.5, 'No separation, no cleanup → Unbounded growth → Pod crashes', 
                fontsize=13, ha='center', color=COLORS['danger'], weight='600')
    else:
        crash_box = FancyBboxPatch((8, -9), 84, 7,
                                   boxstyle="round,pad=0.4",
                                   edgecolor=COLORS['critical'],
                                   facecolor='#8B0000',
                                   linewidth=4)
        ax.add_patch(crash_box)
        
        ax.text(50, -3.5, '💥 POD CRASHED - SERVICE DISRUPTED', fontsize=20, ha='center',
                color='white', weight='700')
        
        ax.text(50, -5.5, 'Memory limit exceeded after continuous growth', 
                fontsize=13, ha='center', color='white', weight='600')
        ax.text(50, -7.5, '✓ Solution: Memory Zone separates transient from permanent!', 
                fontsize=13, ha='center', color='#90EE90', weight='700')

# ============================================================================
# CREATE VIDEO 1: WITH MEMORY ZONE
# ============================================================================

print("=" * 70)
print("Creating WITH Memory Zone Animations (GIF + MP4)")
print("=" * 70)

fig_with = plt.figure(figsize=(18, 12))
fig_with.patch.set_facecolor(COLORS['bg'])

def animate_with_zone(frame):
    frames_per_cycle = 28
    batch_num = (frame // frames_per_cycle) + 1
    frame_in_cycle = frame % frames_per_cycle
    
    if frame_in_cycle < 14:
        fill_pct = (frame_in_cycle / 14) * 100
        create_frame_with_zone(fig_with, fill_pct, show_cleanup=False, batch_num=batch_num)
    elif frame_in_cycle < 18:
        create_frame_with_zone(fig_with, 100, show_cleanup=False, batch_num=batch_num)
    elif frame_in_cycle < 20:
        create_frame_with_zone(fig_with, 0, show_cleanup=True, batch_num=batch_num)
    else:
        create_frame_with_zone(fig_with, 0, show_cleanup=True, batch_num=batch_num)

total_frames_with = 28 * 3
anim_with = FuncAnimation(fig_with, animate_with_zone, frames=total_frames_with, 
                         interval=ANIMATION_SPEED)

# Save as ONE-TIME PLAY GIF (no loop)
print("Creating GIF (one-time play, no loop)...")
writer_gif = PillowWriter(fps=FPS)
anim_with.save('/mnt/user-data/outputs/spacy_with_memory_zone_oneplay.gif', 
               writer=writer_gif, dpi=100)
print("✅ GIF created: spacy_with_memory_zone_oneplay.gif")

# Save as MP4
print("Creating MP4 (with play/pause controls)...")
writer_mp4 = FFMpegWriter(fps=FPS, bitrate=3000)
anim_with.save('/mnt/user-data/outputs/spacy_with_memory_zone.mp4', 
               writer=writer_mp4, dpi=150)
print("✅ MP4 created: spacy_with_memory_zone.mp4")

plt.close('all')

# ============================================================================
# CREATE VIDEO 2: WITHOUT MEMORY ZONE
# ============================================================================

print("\n" + "=" * 70)
print("Creating WITHOUT Memory Zone Animations (GIF + MP4)")
print("=" * 70)

fig_without = plt.figure(figsize=(18, 12))
fig_without.patch.set_facecolor(COLORS['bg'])

def animate_without_zone(frame):
    vocab_growth_rate = 175289 / 60
    string_growth_rate = 60515 / 60
    
    if frame < 60:
        transaction = int(100 + frame * 250)
        vocab = int(1456 + (frame * vocab_growth_rate))
        string = int(639984 + (frame * string_growth_rate))
        create_frame_without_zone(fig_without, transaction, vocab, string, pod_crashed=False)
    elif frame < 70:
        create_frame_without_zone(fig_without, 15000, 176745, 700499, pod_crashed=False)
    else:
        create_frame_without_zone(fig_without, 15500, 176745, 700499, pod_crashed=True)

total_frames_without = 80
anim_without = FuncAnimation(fig_without, animate_without_zone, frames=total_frames_without, 
                            interval=ANIMATION_SPEED)

# Save as ONE-TIME PLAY GIF (no loop)
print("Creating GIF (one-time play, no loop)...")
writer_gif2 = PillowWriter(fps=FPS)
anim_without.save('/mnt/user-data/outputs/spacy_without_memory_zone_oneplay.gif', 
                  writer=writer_gif2, dpi=100)
print("✅ GIF created: spacy_without_memory_zone_oneplay.gif")

# Save as MP4
print("Creating MP4 (with play/pause controls)...")
writer_mp4_2 = FFMpegWriter(fps=FPS, bitrate=3000)
anim_without.save('/mnt/user-data/outputs/spacy_without_memory_zone.mp4', 
                  writer=writer_mp4_2, dpi=150)
print("✅ MP4 created: spacy_without_memory_zone.mp4")

plt.close('all')

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "=" * 70)
print("✅ ALL ANIMATIONS CREATED SUCCESSFULLY!")
print("=" * 70)
print("\n📹 WITH Memory Zone (Solution):")
print("   • spacy_with_memory_zone_oneplay.gif - One-time play GIF")
print("   • spacy_with_memory_zone.mp4 - MP4 with play/pause controls")
print("\n📹 WITHOUT Memory Zone (Problem):")
print("   • spacy_without_memory_zone_oneplay.gif - One-time play GIF")
print("   • spacy_without_memory_zone.mp4 - MP4 with play/pause controls")
print("\n💡 GIF Format:")
print("   • Plays automatically ONCE when loaded")
print("   • Stops at the end (no loop)")
print("   • Click to restart (browser dependent)")
print("\n💡 MP4 Format:")
print("   • Full play/pause/stop controls")
print("   • Better quality and smaller file size")
print("   • Perfect for presentations with manual control")
print("\n🎯 Use GIF for: Web pages, emails, auto-play scenarios")
print("🎯 Use MP4 for: Presentations, manual control needed")
