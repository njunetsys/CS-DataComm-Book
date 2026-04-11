import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, Arrow
import numpy as np

fig, ax = plt.subplots(1, 1, figsize=(14, 9))
ax.set_xlim(0, 14)
ax.set_ylim(0, 9)
ax.axis('off')

# 标题
ax.text(7, 8.5, 'BAG Cross-Regional Interconnection Topology', fontsize=16, fontweight='bold', ha='center')

# 颜色定义
colors = {
    'dc1': '#FF6B6B',
    'dc2': '#4ECDC4', 
    'dc3': '#45B7D1',
    'dc4': '#96CEB4',
    'dc5': '#FFEAA7',
    'bag': '#DDA0DD',
    'connection': '#95A5A6'
}

# 5个数据中心
positions = [
    (1.5, 4, 'DC-1\n(Building A)', colors['dc1']),
    (4.5, 6.5, 'DC-2\n(Building B)', colors['dc2']),
    (7, 7.5, 'DC-3\n(Building C)', colors['dc3']),
    (9.5, 6.5, 'DC-4\n(Building D)', colors['dc4']),
    (12, 4, 'DC-5\n(Building E)', colors['dc5']),
]

# 绘制数据中心框
for x, y, label, color in positions:
    # 数据中心外框
    dc_rect = FancyBboxPatch((x-1, y-1.5), 2, 2.5, boxstyle="round,pad=0.1",
                              facecolor=color, edgecolor='black', linewidth=2, alpha=0.7)
    ax.add_patch(dc_rect)
    ax.text(x, y + 0.5, label, ha='center', va='center', fontsize=10, fontweight='bold')
    
    # L2区域内部
    l2_rect = FancyBboxPatch((x-0.8, y-1), 1.6, 1.2, boxstyle="round,pad=0.05",
                              facecolor='white', edgecolor='black', linewidth=1)
    ax.add_patch(l2_rect)
    ax.text(x, y - 0.4, 'DSF L2 Zone', ha='center', va='center', fontsize=8)

# BAG中心节点
bag_x, bag_y = 7, 4
bag_rect = FancyBboxPatch((bag_x-1.5, bag_y-0.8), 3, 1.6, boxstyle="round,pad=0.1",
                           facecolor=colors['bag'], edgecolor='black', linewidth=3)
ax.add_patch(bag_rect)
ax.text(bag_x, bag_y + 0.3, 'BAG Super Spine', ha='center', va='center', fontsize=12, fontweight='bold')
ax.text(bag_x, bag_y - 0.2, 'Centralized Aggregation Layer', ha='center', va='center', fontsize=9, style='italic')

# 连接线和标注
# Planar Topology (solid lines)
for i, (x, y, label, color) in enumerate(positions):
    # 连接到BAG中心的实线 - 平面拓扑
    ax.annotate('', xy=(bag_x - 1.2 + i * 0.6, bag_y + 0.8), 
                xytext=(x, y - 1.5),
                arrowprops=dict(arrowstyle='->', color='#3498DB', lw=2))

# Spread Topology (dashed lines showing diversity)
for i, (x, y, label, color) in enumerate(positions[:3]):
    ax.plot([x, bag_x - 1], [y - 1.5, bag_y - 0.8], 'g--', lw=1.5, alpha=0.5)

# 图例说明
legend_y = 1.5
ax.add_patch(Rectangle((0.5, legend_y), 0.4, 0.3, facecolor='#3498DB', edgecolor='black'))
ax.text(1.1, legend_y + 0.15, 'Planar Topology (One-to-One)', fontsize=9, va='center')

ax.add_patch(Rectangle((4.5, legend_y), 0.4, 0.3, facecolor='green', edgecolor='black', alpha=0.5))
ax.text(5.1, legend_y + 0.15, 'Spread Topology (Path Diversity)', fontsize=9, va='center')

ax.add_patch(Rectangle((9, legend_y), 0.4, 0.3, facecolor=colors['bag'], edgecolor='black'))
ax.text(9.6, legend_y + 0.15, 'BAG Super Spine (Jericho3)', fontsize=9, va='center')

# 关键指标
metrics_text = """Key Metrics:
• Inter-BAG Capacity: 16-48 Pbps per region pair
• Typical Oversubscription: 4.5:1 (L2 to BAG)
• BAG-to-BAG: Variable based on regional needs
• Distance: Within latency constraints
• Security: MACsec encryption for BAG-to-BAG"""
ax.text(7, 0.8, metrics_text, ha='center', va='center', fontsize=9, 
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

plt.tight_layout()
plt.savefig('/root/.openclaw/workspace/book-project/assets/重构配图/ch06/fig2_bag_topology.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

print("Figure 2: BAG Topology saved!")
