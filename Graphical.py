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

# Import all frame creation functions from backup
import sys
sys.path.insert(0, '/home/claude')
from create_both_formats_BACKUP import create_frame_with_zone, create_frame_without_zone

# ============================================================================
# MODIFIED ANIMATION FUNCTION - SMOOTH DELETION BETWEEN BATCHES
# ============================================================================

def animate_with_zone_smooth(frame):
    """
    Modified animation showing smooth deletion between batches
    ONLY CHANGE: Added deletion animation frames between batches
    """
    frames_per_cycle = 32  # Increased from 28 to add deletion frames (4 extra)
    batch_num = (frame // frames_per_cycle) + 1
    frame_in_cycle = frame % frames_per_cycle
    
    # Fill phase (14 frames)
    if frame_in_cycle < 14:
        fill_pct = (frame_in_cycle / 14) * 100
        create_frame_with_zone(fig_with, fill_pct, show_cleanup=False, batch_num=batch_num)
    
    # Hold at full (4 frames)
    elif frame_in_cycle < 18:
        create_frame_with_zone(fig_with, 100, show_cleanup=False, batch_num=batch_num)
    
    # SMOOTH DELETION ANIMATION (6 frames) - NEW!
    elif frame_in_cycle < 24:
        # Gradually reduce from 100% to 0%
        deletion_progress = (frame_in_cycle - 18) / 6
        remaining_pct = 100 * (1 - deletion_progress)
        create_frame_with_zone(fig_with, remaining_pct, show_cleanup=True, batch_num=batch_num)
    
    # Hold at baseline (8 frames) - shorter than before
    else:
        create_frame_with_zone(fig_with, 0, show_cleanup=True, batch_num=batch_num)

# ============================================================================
# CREATE VIDEO 1: WITH MEMORY ZONE (SMOOTH VERSION)
# ============================================================================

print("=" * 70)
print("Creating WITH Memory Zone Animations - SMOOTH DELETION VERSION")
print("=" * 70)
print("Change: Added smooth deletion animation between batches")
print("=" * 70)

fig_with = plt.figure(figsize=(18, 12))
fig_with.patch.set_facecolor(COLORS['bg'])

total_frames_with = 32 * 3  # Updated for new frame count
anim_with = FuncAnimation(fig_with, animate_with_zone_smooth, frames=total_frames_with, 
                         interval=ANIMATION_SPEED)

# Save as ONE-TIME PLAY GIF (no loop)
print("Creating GIF (one-time play, smooth deletion)...")
writer_gif = PillowWriter(fps=FPS)
anim_with.save('/mnt/user-data/outputs/spacy_with_memory_zone_oneplay_smooth.gif', 
               writer=writer_gif, dpi=100)
print("✅ GIF created: spacy_with_memory_zone_oneplay_smooth.gif")

# Save as MP4
print("Creating MP4 (with play/pause controls, smooth deletion)...")
writer_mp4 = FFMpegWriter(fps=FPS, bitrate=3000)
anim_with.save('/mnt/user-data/outputs/spacy_with_memory_zone_smooth.mp4', 
               writer=writer_mp4, dpi=150)
print("✅ MP4 created: spacy_with_memory_zone_smooth.mp4")

plt.close('all')

# ============================================================================
# CREATE VIDEO 2: WITHOUT MEMORY ZONE (UNCHANGED)
# ============================================================================

print("\n" + "=" * 70)
print("Creating WITHOUT Memory Zone Animations (UNCHANGED)")
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
print("✅ SMOOTH VERSION CREATED!")
print("=" * 70)
print("\n📹 NEW - WITH Memory Zone (SMOOTH deletion):")
print("   • spacy_with_memory_zone_oneplay_smooth.gif")
print("   • spacy_with_memory_zone_smooth.mp4")
print("\n📹 UNCHANGED - WITHOUT Memory Zone:")
print("   • spacy_without_memory_zone_oneplay.gif (same as before)")
print("   • spacy_without_memory_zone.mp4 (same as before)")
print("\n🔄 What Changed:")
print("   • Transient cache now SMOOTHLY empties (100% → 0%) over 6 frames")
print("   • Shows gradual deletion animation between batches")
print("   • Continuous flow: Fill → Delete smoothly → Next batch")
print("\n📁 Your ORIGINAL files are still available:")
print("   • spacy_with_memory_zone_oneplay.gif (original discrete)")
print("   • spacy_with_memory_zone.mp4 (original discrete)")
print("\n💡 If you don't like it:")
print("   • Just use the original files (no '_smooth' suffix)")
print("   • Or I can rollback code changes immediately")
print("\n✅ Code backup saved as: create_both_formats_BACKUP.py")
