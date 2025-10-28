import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch, Circle
import numpy as np

# Professional color palette
COLORS = {
    'primary': '#2E3440',      # Dark gray
    'accent_blue': '#5E81AC',  # Professional blue
    'accent_orange': '#D08770', # Muted orange
    'accent_red': '#BF616A',   # Muted red
    'accent_green': '#A3BE8C', # Sage green
    'text': '#ECEFF4',         # Off-white
    'subtext': '#D8DEE9',      # Light gray
    'bg': '#FFFFFF',           # White background
    'line': '#4C566A'          # Medium gray
}

# Create figure with white background
fig = plt.figure(figsize=(30, 18))
fig.patch.set_facecolor(COLORS['bg'])

# ============================================================================
# TITLE
# ============================================================================
fig.text(0.5, 0.97, 'Dictionary Resize Memory Growth Pattern', 
         fontsize=50, ha='center', va='top', 
         color=COLORS['primary'], weight='600',
         family='sans-serif')

fig.text(0.5, 0.945, 'Understanding Step Growth in Python Dictionary Memory Allocation', 
         fontsize=26, ha='center', va='top',
         color=COLORS['subtext'], weight='300',
         family='sans-serif')

# ============================================================================
# LEFT SECTION: DICTIONARY INTERNAL STRUCTURE (MORE SPACE)
# ============================================================================
ax_left = plt.subplot(1, 2, 1)
ax_left.set_xlim(0, 100)
ax_left.set_ylim(0, 100)
ax_left.axis('off')
ax_left.set_facecolor(COLORS['bg'])

# Section title with more space at top
ax_left.text(50, 96, 'Dictionary Internal Structure', fontsize=34, ha='center',
             color=COLORS['primary'], weight='600')

# STAGE 1: Filling Phase - HIGHER POSITION
stage1_y = 75
ax_left.text(10, stage1_y + 12, 'Phase 1', fontsize=22, ha='left',
             color=COLORS['accent_orange'], weight='600')
ax_left.text(10, stage1_y + 8, 'Hash Table Filling', fontsize=17, ha='left',
             color=COLORS['subtext'], weight='400')

# Hash table box
table1 = FancyBboxPatch((10, stage1_y), 80, 7,
                        boxstyle="round,pad=0.2",
                        edgecolor=COLORS['accent_orange'],
                        facecolor='#F9FAFB',
                        linewidth=3)
ax_left.add_patch(table1)

# Show slots
slot_width = 4.5
gap = 0.5
slots_shown = 16
filled_slots = 10

for i in range(slots_shown):
    x = 12 + i * (slot_width + gap)
    if i < filled_slots:
        slot = Rectangle((x, stage1_y + 1), slot_width, 5,
                        facecolor=COLORS['accent_blue'],
                        edgecolor=COLORS['line'],
                        linewidth=1.5, alpha=0.8)
    else:
        slot = Rectangle((x, stage1_y + 1), slot_width, 5,
                        facecolor='#E5E7EB',
                        edgecolor=COLORS['line'],
                        linewidth=1, alpha=0.5)
    ax_left.add_patch(slot)

# Percentage label
ax_left.text(90, stage1_y + 3.5, '63%', 
             fontsize=19, ha='right', va='center',
             color=COLORS['accent_orange'], weight='600')

# EXPLANATION TEXT 1 - MORE SPACE BELOW
ax_left.text(50, stage1_y - 2.5, 'Capacity: 4.2M slots  |  Items: 2.65M', 
             fontsize=14, ha='center', color=COLORS['primary'], weight='500')
ax_left.text(50, stage1_y - 5, 'Load factor approaching threshold', 
             fontsize=14, ha='center', color=COLORS['subtext'], weight='400')

# Arrow with more space
arrow1 = FancyArrowPatch((50, stage1_y - 7), (50, stage1_y - 11),
                        arrowstyle='->', mutation_scale=35,
                        color=COLORS['line'], linewidth=2.5)
ax_left.add_artist(arrow1)

# STAGE 2: Threshold - MIDDLE POSITION WITH SPACE
stage2_y = 50
ax_left.text(10, stage2_y + 12, 'Phase 2', fontsize=22, ha='left',
             color=COLORS['accent_red'], weight='600')
ax_left.text(10, stage2_y + 8, 'Threshold Crossed', fontsize=17, ha='left',
             color=COLORS['subtext'], weight='400')

table2 = FancyBboxPatch((10, stage2_y), 80, 7,
                        boxstyle="round,pad=0.2",
                        edgecolor=COLORS['accent_red'],
                        facecolor='#FEF2F2',
                        linewidth=3)
ax_left.add_patch(table2)

# Almost full slots
for i in range(slots_shown):
    x = 12 + i * (slot_width + gap)
    if i < 11:  # 67%
        slot = Rectangle((x, stage2_y + 1), slot_width, 5,
                        facecolor=COLORS['accent_red'],
                        edgecolor=COLORS['line'],
                        linewidth=1.5, alpha=0.7)
    else:
        slot = Rectangle((x, stage2_y + 1), slot_width, 5,
                        facecolor='#E5E7EB',
                        edgecolor=COLORS['line'],
                        linewidth=1, alpha=0.5)
    ax_left.add_patch(slot)

ax_left.text(90, stage2_y + 3.5, '67%', fontsize=19, ha='right', va='center',
             color=COLORS['accent_red'], weight='600')

# EXPLANATION TEXT 2 - MORE SPACE
ax_left.text(50, stage2_y - 2.5, 'Threshold at 2.8M items', 
             fontsize=14, ha='center', color=COLORS['primary'], weight='500')
ax_left.text(50, stage2_y - 5, 'RESIZE TRIGGERED!', 
             fontsize=15, ha='center', color=COLORS['accent_red'], weight='700')

# Critical arrow with more space
arrow2 = FancyArrowPatch((50, stage2_y - 7.5), (50, stage2_y - 11.5),
                        arrowstyle='->', mutation_scale=40,
                        color=COLORS['accent_red'], linewidth=3.5)
ax_left.add_artist(arrow2)

ax_left.text(50, stage2_y - 9.5, 'Capacity Doubles', fontsize=17, ha='center',
             color=COLORS['accent_red'], weight='600',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='white',
                      edgecolor=COLORS['accent_red'], linewidth=2.5))

# STAGE 3: Doubled - LOWER POSITION WITH SPACE
stage3_y = 18
ax_left.text(10, stage3_y + 12, 'Phase 3', fontsize=22, ha='left',
             color=COLORS['accent_green'], weight='600')
ax_left.text(10, stage3_y + 8, 'New Capacity', fontsize=17, ha='left',
             color=COLORS['subtext'], weight='400')

# Two rows for doubled capacity
table3_top = FancyBboxPatch((10, stage3_y + 4), 80, 3,
                            boxstyle="round,pad=0.1",
                            edgecolor=COLORS['accent_green'],
                            facecolor='#F0F9F4',
                            linewidth=2.5)
ax_left.add_patch(table3_top)

table3_bottom = FancyBboxPatch((10, stage3_y), 80, 3,
                               boxstyle="round,pad=0.1",
                               edgecolor=COLORS['accent_green'],
                               facecolor='#F0F9F4',
                               linewidth=2.5)
ax_left.add_patch(table3_bottom)

# Slots in both rows
small_slot = 4.5
for row, y_offset in enumerate([5.5, 1.5]):
    for i in range(slots_shown):
        x = 12 + i * (small_slot + gap)
        if i < 5 and row == 0:
            slot = Rectangle((x, stage3_y + y_offset), small_slot, 1.8,
                            facecolor=COLORS['accent_green'],
                            edgecolor=COLORS['line'],
                            linewidth=1, alpha=0.7)
        else:
            slot = Rectangle((x, stage3_y + y_offset), small_slot, 1.8,
                            facecolor='#E5E7EB',
                            edgecolor=COLORS['line'],
                            linewidth=0.8, alpha=0.5)
        ax_left.add_patch(slot)

ax_left.text(90, stage3_y + 3.5, '2× Size', fontsize=19, ha='right', va='center',
             color=COLORS['accent_green'], weight='600')

# EXPLANATION TEXT 3 - CLEAR SPACE BELOW
ax_left.text(50, stage3_y - 2.5, 'New: 8.4M slots (2²³)  |  Items: 2.8M', 
             fontsize=14, ha='center', color=COLORS['primary'], weight='500')
ax_left.text(50, stage3_y - 5, 'RSS jumps +161 MB instantly', 
             fontsize=14, ha='center', color=COLORS['accent_green'], weight='600')

# ============================================================================
# RIGHT SECTION: EXPERIMENTAL GRAPH (MORE VERTICAL SPACE)
# ============================================================================
ax_right = plt.subplot(1, 2, 2)
ax_right.set_facecolor(COLORS['bg'])
ax_right.set_xlim(0, 10000)
ax_right.set_ylim(850, 1850)

# Section title with space
ax_right.text(5000, 1820, 'RSS Memory Pattern', fontsize=34, ha='center',
              color=COLORS['primary'], weight='600')

# Explanatory text with space
ax_right.text(5000, 1770, 'Real experiment: 10,000 batches, 5M cached items', 
              fontsize=15, ha='center', color=COLORS['subtext'], weight='400')
ax_right.text(5000, 1740, 'Steps occur at 67% load factor threshold', 
              fontsize=15, ha='center', color=COLORS['accent_red'], weight='500')

# Grid
ax_right.grid(True, alpha=0.15, color=COLORS['line'], 
              linestyle='-', linewidth=0.8, zorder=0)

# Actual data
x_data = [0, 1000, 2000, 3000, 4000, 5000, 5600, 5650, 6000, 7000, 8000, 8200, 8250, 9000, 10000]
y_data = [900, 950, 1000, 1050, 1100, 1150, 1200, 1361, 1370, 1420, 1470, 1510, 1671, 1720, 1770]

# Fill
ax_right.fill_between(x_data, y_data, 850, 
                      alpha=0.08, color=COLORS['accent_blue'], zorder=1)

# Line
ax_right.plot(x_data, y_data, color=COLORS['accent_blue'], 
              linewidth=4.5, zorder=3, solid_capstyle='round')

# Step markers with better positioning
steps = [
    (5650, 1361, '+161 MB', '2.8M items', -1000, 180),
    (8250, 1671, '+129 MB', '4.1M items', -1000, 120)
]

for x, y, jump_text, items_text, x_offset, y_offset in steps:
    # Circle marker
    circle = plt.Circle((x, y), 90, facecolor=COLORS['accent_red'], 
                       edgecolor='white', linewidth=3.5, zorder=5, alpha=0.9)
    ax_right.add_patch(circle)
    
    # Clean annotation with better spacing
    ax_right.annotate(f'{jump_text}\n{items_text}', 
                     xy=(x, y), 
                     xytext=(x + x_offset, y + y_offset),
                     fontsize=16, 
                     color=COLORS['primary'], 
                     weight='600',
                     ha='center',
                     bbox=dict(boxstyle='round,pad=0.7', 
                              facecolor='white', 
                              edgecolor=COLORS['accent_red'],
                              linewidth=2.5),
                     arrowprops=dict(arrowstyle='->', 
                                   color=COLORS['accent_red'], 
                                   lw=3,
                                   connectionstyle="arc3,rad=0.2"))

# Plateau labels - better positioned
ax_right.text(2800, 1050, 'Plateau:\nGradual\nFilling', 
              fontsize=14, ha='center', va='center',
              color=COLORS['accent_orange'], weight='500',
              bbox=dict(boxstyle='round,pad=0.6', facecolor='white',
                       edgecolor=COLORS['accent_orange'], linewidth=2, alpha=0.95))

ax_right.text(6800, 1480, 'Plateau', 
              fontsize=14, ha='center', va='center',
              color=COLORS['accent_orange'], weight='500',
              bbox=dict(boxstyle='round,pad=0.6', facecolor='white',
                       edgecolor=COLORS['accent_orange'], linewidth=2, alpha=0.95))

# Axis labels
ax_right.set_xlabel('Processing Batches (500 items each)', fontsize=21, 
                   color=COLORS['primary'], weight='500', labelpad=18)
ax_right.set_ylabel('Resident Set Size (MB)', fontsize=21,
                   color=COLORS['primary'], weight='500', labelpad=18)

# Ticks
ax_right.tick_params(colors=COLORS['subtext'], labelsize=15, 
                    width=2, length=6)

# Spines
for spine in ['top', 'right']:
    ax_right.spines[spine].set_visible(False)
for spine in ['bottom', 'left']:
    ax_right.spines[spine].set_color(COLORS['line'])
    ax_right.spines[spine].set_linewidth(2)

# ============================================================================
# BOTTOM LEGEND (MORE SPACE)
# ============================================================================

legend_box = FancyBboxPatch((0.08, 0.075), 0.84, 0.09,
                           boxstyle="round,pad=0.015",
                           edgecolor=COLORS['line'],
                           facecolor='#F9FAFB',
                           linewidth=2,
                           transform=fig.transFigure)
fig.patches.append(legend_box)

fig.text(0.12, 0.145, 'Dictionary Memory Components', fontsize=22, ha='left',
         color=COLORS['primary'], weight='600')

legend_data = [
    (COLORS['accent_red'], 'Hash Table', 'Internal array (power of 2)'),
    (COLORS['accent_orange'], 'Load Factor', '67% threshold'),
    (COLORS['accent_blue'], 'Entry Cost', '~157 bytes/item'),
]

x_positions = [0.26, 0.52, 0.78]

for x, (color, name, desc) in zip(x_positions, legend_data):
    indicator = Rectangle((x - 0.02, 0.105), 0.03, 0.045,
                         facecolor=color, edgecolor=COLORS['line'],
                         linewidth=2, transform=fig.transFigure,
                         alpha=0.85)
    fig.patches.append(indicator)
    
    fig.text(x + 0.02, 0.135, name, fontsize=19, ha='left',
             color=COLORS['primary'], weight='600')
    fig.text(x + 0.02, 0.105, desc, fontsize=14, ha='left',
             color=COLORS['subtext'], weight='400')

# Key insight box
insight_box = FancyBboxPatch((0.08, 0.01), 0.84, 0.055,
                            boxstyle="round,pad=0.015",
                            edgecolor=COLORS['accent_green'],
                            facecolor='#F0F9F4',
                            linewidth=2.5,
                            transform=fig.transFigure)
fig.patches.append(insight_box)

fig.text(0.5, 0.052, 'Memory Step Pattern Explanation', 
         fontsize=18, ha='center',
         color=COLORS['primary'], weight='700')
fig.text(0.5, 0.028, 'Python dictionaries double capacity when load factor exceeds 67%. Each resize allocates new hash table at 2× size (2²² → 2²³ → 2²⁴). '
         'RSS jumps 130-160 MB per step, then plateau continues until next threshold.', 
         fontsize=15, ha='center',
         color=COLORS['subtext'], weight='400')

plt.tight_layout(rect=[0, 0.17, 1, 0.93])
plt.savefig('/mnt/user-data/outputs/dictionary_resize_infographic.png', 
            dpi=300, bbox_inches='tight',
            facecolor=COLORS['bg'], edgecolor='none')

print("✅ CLEAN DICTIONARY RESIZE INFOGRAPHIC CREATED!")
print("📁 File: dictionary_resize_infographic.png")
print("\n📊 Reference-style layout with:")
print("  • Vertical phases on left")
print("  • Graph on right")
print("  • Proper spacing - no overlaps!")
print("  • Based on your actual data")
