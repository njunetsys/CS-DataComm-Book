import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch
import numpy as np

fig, axes = plt.subplots(1, 3, figsize=(16, 8))

colors = {
    'gpu': '#FF6B6B',
    'rds': '#4ECDC4', 
    'fds': '#45B7D1',
    'sds': '#96CEB4',
    'edge': '#FFEAA7',
    'bag': '#DDA0DD'
}

# ==================== L1 Level ====================
ax = axes[0]
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis('off')
ax.set_title('Level 1: Single AI Zone\n(~4,500 GPUs)', fontsize=12, fontweight='bold', pad=20)

# GPU机架
for row in range(3):
    for col in range(4):
        x = 1 + col * 1.8
        y = 1.5 + row * 1.5
        gpu = FancyBboxPatch((x, y), 1.2, 1, boxstyle="round,pad=0.05",
                              facecolor=colors['gpu'], edgecolor='black', linewidth=1)
        ax.add_patch(gpu)
        ax.text(x + 0.6, y + 0.5, 'GPU', ha='center', va='center', fontsize=7)

# RDSW层
for i in range(4):
    x = 1 + i * 1.8
    rds = FancyBboxPatch((x, 6), 1.2, 0.8, boxstyle="round,pad=0.05",
                          facecolor=colors['rds'], edgecolor='black', linewidth=1.5)
    ax.add_patch(rds)
    ax.text(x + 0.6, 6.4, f'RDSW{i+1}', ha='center', va='center', fontsize=7, fontweight='bold')

# FDSW层
for i in range(3):
    x = 1.4 + i * 2.2
    fds = FancyBboxPatch((x, 7.5), 1.4, 0.8, boxstyle="round,pad=0.05",
                          facecolor=colors['fds'], edgecolor='black', linewidth=1.5)
    ax.add_patch(fds)
    ax.text(x + 0.7, 7.9, f'FDSW{i+1}', ha='center', va='center', fontsize=8, fontweight='bold')

# 连接
for i in range(4):
    for j in range(3):
        x1 = 1.6 + i * 1.8
        x2 = 2.1 + j * 2.2
        ax.plot([x1, x2], [6.8, 7.5], 'k-', lw=0.5, alpha=0.3)

ax.text(5, 0.8, 'Two network planes for redundancy', ha='center', fontsize=9, style='italic', color='gray')

# ==================== L2 Level ====================
ax = axes[1]
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis('off')
ax.set_title('Level 2: Four L1 Zones Interconnected\n(~18,000 GPUs)', fontsize=12, fontweight='bold', pad=20)

# 四个L1区域
l1_positions = [(2, 6), (6, 6), (2, 2), (6, 2)]
for i, (x, y) in enumerate(l1_positions):
    l1 = FancyBboxPatch((x, y), 2.5, 2, boxstyle="round,pad=0.1",
                         facecolor=colors['rds'], edgecolor='black', linewidth=2, alpha=0.6)
    ax.add_patch(l1)
    ax.text(x + 1.25, y + 1, f'L1 Zone {i+1}', ha='center', va='center', fontsize=9, fontweight='bold')

# SDSW层
sds_positions = [(2.5, 4.5), (5.5, 4.5), (2.5, 5.5), (5.5, 5.5)]
for i, (x, y) in enumerate(sds_positions[:4]):
    sds = FancyBboxPatch((x, y), 1.5, 0.7, boxstyle="round,pad=0.05",
                          facecolor=colors['sds'], edgecolor='black', linewidth=1.5)
    ax.add_patch(sds)
    ax.text(x + 0.75, y + 0.35, f'SDSW{i+1}', ha='center', va='center', fontsize=8, fontweight='bold')

# 连接线 (Spine层连接)
for x1, y1 in l1_positions:
    for x2, y2 in [(2.5, 4.5), (5.5, 4.5)]:
        cx = x1 + 1.25
        cy = y1 + 2
        ax.plot([cx, x2 + 0.75], [cy, y2], 'b-', lw=0.8, alpha=0.4)

ax.text(5, 0.8, 'Non-blocking spine topology', ha='center', fontsize=9, style='italic', color='gray')

# ==================== L3 Level ====================
ax = axes[2]
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis('off')
ax.set_title('Level 3: Five L2 Zones via Super Spine\n(Up to 100,000+ GPUs)', fontsize=12, fontweight='bold', pad=20)

# 五个L2区域围绕中心
angles = np.linspace(0, 2*np.pi, 6)[:-1]
radius = 3
center = (5, 5)

for i, angle in enumerate(angles):
    x = center[0] + radius * np.cos(angle) - 0.8
    y = center[1] + radius * np.sin(angle) - 0.5
    
    l2 = FancyBboxPatch((x, y), 1.6, 1, boxstyle="round,pad=0.05",
                         facecolor=colors['sds'], edgecolor='black', linewidth=1.5)
    ax.add_patch(l2)
    ax.text(x + 0.8, y + 0.5, f'L2-{i+1}', ha='center', va='center', fontsize=8, fontweight='bold')
    
    # Edge PoD
    edge_x = center[0] + (radius - 1) * np.cos(angle) - 0.5
    edge_y = center[1] + (radius - 1) * np.sin(angle) - 0.3
    edge = FancyBboxPatch((edge_x, edge_y), 1, 0.6, boxstyle="round,pad=0.03",
                           facecolor=colors['edge'], edgecolor='black', linewidth=1)
    ax.add_patch(edge)
    ax.text(edge_x + 0.5, edge_y + 0.3, 'Edge', ha='center', va='center', fontsize=6)

# BAG超级脊层
bag = FancyBboxPatch((center[0]-1.2, center[1]-0.6), 2.4, 1.2, boxstyle="round,pad=0.1",
                      facecolor=colors['bag'], edgecolor='black', linewidth=3)
ax.add_patch(bag)
ax.text(center[0], center[1], 'BAG\nSuper Spine', ha='center', va='center', fontsize=10, fontweight='bold')

ax.text(5, 0.8, '4.5:1 oversubscription at L3', ha='center', fontsize=9, style='italic', color='gray')

plt.tight_layout()
plt.savefig('/root/.openclaw/workspace/book-project/assets/重构配图/ch06/fig3_dsf_three_tiers.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

print("Figure 3: DSF Three Tiers saved!")
