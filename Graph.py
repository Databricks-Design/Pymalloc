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
fig = plt.figure(figsize=(28, 16))
fig.patch.set_facecolor(COLORS['bg'])

# ============================================================================
# TITLE
# ============================================================================
fig.text(0.5, 0.96, 'Memory Allocation Pattern Analysis', 
         fontsize=48, ha='center', va='top', 
         color=COLORS['primary'], weight='600',
         family='sans-serif')

fig.text(0.5, 0.93, 'Understanding Step Growth in Python Memory Consumption', 
         fontsize=24, ha='center', va='top',
         color=COLORS['subtext'], weight='300',
         family='sans-serif')

# ============================================================================
# LEFT SECTION: MEMORY ARCHITECTURE
# ============================================================================
ax_left = plt.subplot(1, 2, 1)
ax_left.set_xlim(0, 100)
ax_left.set_ylim(0, 100)
ax_left.axis('off')
ax_left.set_facecolor(COLORS['bg'])

# Section title
ax_left.text(50, 94, 'Memory Structure', fontsize=32, ha='center',
             color=COLORS['primary'], weight='600')

# STAGE 1: Filling
stage1_y = 68
ax_left.text(10, stage1_y + 15, 'Phase 1', fontsize=20, ha='left',
             color=COLORS['accent_orange'], weight='600')
ax_left.text(10, stage1_y + 11, 'Arena Filling', fontsize=16, ha='left',
             color=COLORS['subtext'], weight='400')

# Clean arena box
arena1 = FancyBboxPatch((10, stage1_y), 80, 8,
                        boxstyle="round,pad=0.2",
                        edgecolor=COLORS['accent_orange'],
                        facecolor='#F9FAFB',
                        linewidth=3)
ax_left.add_patch(arena1)

# Minimalist pool representation
pool_width = 9
gap = 0.8
pools_shown = 8
filled = 3

for i in range(pools_shown):
    x = 12 + i * (pool_width + gap)
    if i < filled:
        pool = Rectangle((x, stage1_y + 1), pool_width, 6,
                        facecolor=COLORS['accent_blue'],
                        edgecolor=COLORS['line'],
                        linewidth=1.5, alpha=0.8)
    else:
        pool = Rectangle((x, stage1_y + 1), pool_width, 6,
                        facecolor='#E5E7EB',
                        edgecolor=COLORS['line'],
                        linewidth=1, alpha=0.5)
    ax_left.add_patch(pool)

# Clean label
ax_left.text(90, stage1_y + 4, f'{int(filled/pools_shown*100)}%', 
             fontsize=18, ha='right', va='center',
             color=COLORS['accent_orange'], weight='600')

# EXPLANATION TEXT 1
ax_left.text(50, stage1_y - 2, 'Python requests 256 KB from OS as Arena.', 
             fontsize=13, ha='center', color=COLORS['primary'], weight='400')
ax_left.text(50, stage1_y - 5, 'Internal blocks fill gradually without additional OS requests.', 
             fontsize=13, ha='center', color=COLORS['subtext'], weight='400')

# Spacious arrow
arrow1 = FancyArrowPatch((50, stage1_y - 8), (50, stage1_y - 14),
                        arrowstyle='->', mutation_scale=30,
                        color=COLORS['line'], linewidth=2)
ax_left.add_artist(arrow1)

# STAGE 2: Full
stage2_y = 42
ax_left.text(10, stage2_y + 15, 'Phase 2', fontsize=20, ha='left',
             color=COLORS['accent_red'], weight='600')
ax_left.text(10, stage2_y + 11, 'Arena Full', fontsize=16, ha='left',
             color=COLORS['subtext'], weight='400')

arena2 = FancyBboxPatch((10, stage2_y), 80, 8,
                        boxstyle="round,pad=0.2",
                        edgecolor=COLORS['accent_red'],
                        facecolor='#FEF2F2',
                        linewidth=3)
ax_left.add_patch(arena2)

# All pools filled
for i in range(pools_shown):
    x = 12 + i * (pool_width + gap)
    pool = Rectangle((x, stage2_y + 1), pool_width, 6,
                    facecolor=COLORS['accent_red'],
                    edgecolor=COLORS['line'],
                    linewidth=1.5, alpha=0.7)
    ax_left.add_patch(pool)

ax_left.text(90, stage2_y + 4, '100%', fontsize=18, ha='right', va='center',
             color=COLORS['accent_red'], weight='600')

# EXPLANATION TEXT 2
ax_left.text(50, stage2_y - 2, 'Arena capacity exhausted. All 256 KB allocated.', 
             fontsize=13, ha='center', color=COLORS['primary'], weight='400')
ax_left.text(50, stage2_y - 5, 'Application requires additional memory.', 
             fontsize=13, ha='center', color=COLORS['accent_red'], weight='500')

# Critical arrow
arrow2 = FancyArrowPatch((50, stage2_y - 8), (50, stage2_y - 14),
                        arrowstyle='->', mutation_scale=35,
                        color=COLORS['accent_red'], linewidth=3)
ax_left.add_artist(arrow2)

ax_left.text(50, stage2_y - 11, 'OS Memory Request', fontsize=16, ha='center',
             color=COLORS['accent_red'], weight='600',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                      edgecolor=COLORS['accent_red'], linewidth=2))

# STAGE 3: New allocation
stage3_y = 16
ax_left.text(10, stage3_y + 15, 'Phase 3', fontsize=20, ha='left',
             color=COLORS['accent_green'], weight='600')
ax_left.text(10, stage3_y + 11, 'New Arena Allocated', fontsize=16, ha='left',
             color=COLORS['subtext'], weight='400')

arena3 = FancyBboxPatch((10, stage3_y), 80, 8,
                        boxstyle="round,pad=0.2",
                        edgecolor=COLORS['accent_green'],
                        facecolor='#F0F9F4',
                        linewidth=3)
ax_left.add_patch(arena3)

# Few pools
for i in range(pools_shown):
    x = 12 + i * (pool_width + gap)
    if i < 1:
        pool = Rectangle((x, stage3_y + 1), pool_width, 6,
                        facecolor=COLORS['accent_green'],
                        edgecolor=COLORS['line'],
                        linewidth=1.5, alpha=0.7)
    else:
        pool = Rectangle((x, stage3_y + 1), pool_width, 6,
                        facecolor='#E5E7EB',
                        edgecolor=COLORS['line'],
                        linewidth=1, alpha=0.5)
    ax_left.add_patch(pool)

ax_left.text(90, stage3_y + 4, '+256 KB', fontsize=18, ha='right', va='center',
             color=COLORS['accent_green'], weight='600')

# EXPLANATION TEXT 3
ax_left.text(50, stage3_y - 2, 'OS allocates new 256 KB arena.', 
             fontsize=13, ha='center', color=COLORS['primary'], weight='400')
ax_left.text(50, stage3_y - 5, 'RSS increases by 256 KB, creating visible step in graph.', 
             fontsize=13, ha='center', color=COLORS['accent_green'], weight='500')

# ============================================================================
# RIGHT SECTION: GRAPH
# ============================================================================
ax_right = plt.subplot(1, 2, 2)
ax_right.set_facecolor(COLORS['bg'])
ax_right.set_xlim(0, 100)
ax_right.set_ylim(600, 1300)

# Section title
ax_right.text(50, 1280, 'RSS Memory Pattern', fontsize=32, ha='center',
              color=COLORS['primary'], weight='600')

# Graph explanation
ax_right.text(50, 1250, 'RSS remains stable during internal allocation (plateau).', 
              fontsize=14, ha='center', color=COLORS['subtext'], weight='400')
ax_right.text(50, 1230, 'Step occurs when OS allocates new 256 KB arena.', 
              fontsize=14, ha='center', color=COLORS['accent_red'], weight='500')

# Professional grid
ax_right.grid(True, alpha=0.15, color=COLORS['line'], 
              linestyle='-', linewidth=0.8, zorder=0)

# Clean step data
x_data = [0, 25, 35, 35.2, 55, 65, 65.2, 85, 95]
y_data = [650, 700, 745, 1001, 1040, 1085, 1341, 1380, 1420]

# Subtle fill
ax_right.fill_between(x_data, y_data, 600, 
                      alpha=0.08, color=COLORS['accent_blue'], zorder=1)

# Clean line
ax_right.plot(x_data, y_data, color=COLORS['accent_blue'], 
              linewidth=4, zorder=3, solid_capstyle='round')

# Professional step markers
steps = [(35.2, 1001), (65.2, 1341)]
for i, (x, y) in enumerate(steps):
    # Clean circle
    circle = plt.Circle((x, y), 18, facecolor=COLORS['accent_red'], 
                       edgecolor='white', linewidth=3, zorder=5, alpha=0.9)
    ax_right.add_patch(circle)
    
    # Clean annotation
    ax_right.annotate('+256 KB\nArena', xy=(x, y), xytext=(x - 15, y + 100),
                     fontsize=15, color=COLORS['primary'], weight='600',
                     ha='center',
                     bbox=dict(boxstyle='round,pad=0.6', 
                              facecolor='white', 
                              edgecolor=COLORS['accent_red'],
                              linewidth=2),
                     arrowprops=dict(arrowstyle='->', 
                                   color=COLORS['accent_red'], 
                                   lw=2.5,
                                   connectionstyle="arc3,rad=0.2"))

# Plateau labels
ax_right.text(15, 675, 'Plateau:\nInternal\nAllocation', 
              fontsize=13, ha='center', va='center',
              color=COLORS['accent_orange'], weight='500',
              bbox=dict(boxstyle='round,pad=0.5', facecolor='white',
                       edgecolor=COLORS['accent_orange'], linewidth=1.5, alpha=0.9))

ax_right.text(50, 1020, 'Plateau', 
              fontsize=13, ha='center', va='center',
              color=COLORS['accent_orange'], weight='500',
              bbox=dict(boxstyle='round,pad=0.5', facecolor='white',
                       edgecolor=COLORS['accent_orange'], linewidth=1.5, alpha=0.9))

# Clean axis labels
ax_right.set_xlabel('Processing Batches', fontsize=20, 
                   color=COLORS['primary'], weight='500', labelpad=15)
ax_right.set_ylabel('Resident Set Size (MB)', fontsize=20,
                   color=COLORS['primary'], weight='500', labelpad=15)

# Clean ticks
ax_right.tick_params(colors=COLORS['subtext'], labelsize=14, 
                    width=1.5, length=5)

# Clean spines
for spine in ['top', 'right']:
    ax_right.spines[spine].set_visible(False)
for spine in ['bottom', 'left']:
    ax_right.spines[spine].set_color(COLORS['line'])
    ax_right.spines[spine].set_linewidth(1.5)

# ============================================================================
# LEGEND (Bottom - Clean & Spacious)
# ============================================================================

# Legend background
legend_box = FancyBboxPatch((0.08, 0.06), 0.84, 0.08,
                           boxstyle="round,pad=0.01",
                           edgecolor=COLORS['line'],
                           facecolor='#F9FAFB',
                           linewidth=1.5,
                           transform=fig.transFigure)
fig.patches.append(legend_box)

# Legend title
fig.text(0.12, 0.125, 'Component Hierarchy', fontsize=20, ha='left',
         color=COLORS['primary'], weight='600')

# Clean legend items
legend_data = [
    (COLORS['accent_red'], 'Arena', '256 KB block from OS'),
    (COLORS['accent_orange'], 'Pool', '4 KB segment (64 per arena)'),
    (COLORS['accent_blue'], 'Block', '8-512 bytes (stores objects)'),
]

x_positions = [0.25, 0.50, 0.75]

for x, (color, name, desc) in zip(x_positions, legend_data):
    # Clean indicator
    indicator = Rectangle((x - 0.015, 0.095), 0.025, 0.04,
                         facecolor=color, edgecolor=COLORS['line'],
                         linewidth=1.5, transform=fig.transFigure,
                         alpha=0.8)
    fig.patches.append(indicator)
    
    # Clean text
    fig.text(x + 0.02, 0.12, name, fontsize=18, ha='left',
             color=COLORS['primary'], weight='600')
    fig.text(x + 0.02, 0.09, desc, fontsize=13, ha='left',
             color=COLORS['subtext'], weight='400')

# Key insight box (comprehensive explanation)
insight_box = FancyBboxPatch((0.08, 0.01), 0.84, 0.045,
                            boxstyle="round,pad=0.01",
                            edgecolor=COLORS['accent_green'],
                            facecolor='#F0F9F4',
                            linewidth=2,
                            transform=fig.transFigure)
fig.patches.append(insight_box)

fig.text(0.5, 0.04, 'Memory Step Pattern Explanation', 
         fontsize=16, ha='center',
         color=COLORS['primary'], weight='600')
fig.text(0.5, 0.02, 'Python allocates memory in 256 KB chunks (arenas) from the operating system. Each step in the graph represents one arena allocation. Plateau phases show internal memory reuse within existing arenas.', 
         fontsize=14, ha='center',
         color=COLORS['subtext'], weight='400')

plt.tight_layout(rect=[0, 0.15, 1, 0.91])
plt.savefig('/mnt/user-data/outputs/FINAL_PROFESSIONAL_DIAGRAM.png', 
            dpi=300, bbox_inches='tight',
            facecolor=COLORS['bg'], edgecolor='none')

print("✅ FINAL PROFESSIONAL DIAGRAM CREATED!")
print("📁 File: FINAL_PROFESSIONAL_DIAGRAM.png")
print("\n📊 Includes:")
print("  • Detailed phase explanations")
print("  • Graph interpretation text")
print("  • Comprehensive legend")
print("  • Executive summary at bottom")
