import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle
import numpy as np

# 设置中文字体支持
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(1, 1, figsize=(14, 10))
ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.axis('off')

# 标题
ax.text(7, 9.5, 'AI Training Cluster Network Architecture', fontsize=16, fontweight='bold', ha='center')

# 颜色定义
colors = {
    'gpu': '#FF6B6B',
    'rds': '#4ECDC4', 
    'fds': '#45B7D1',
    'bag': '#96CEB4',
    'edge': '#FFEAA7',
    'storage': '#DDA0DD'
}

# L1 Zone - 左侧
for i in range(4):
    x = 0.5 + i * 1.5
    # GPU Rack
    gpu_rect = FancyBboxPatch((x, 2), 1.2, 1.2, boxstyle="round,pad=0.05", 
                               facecolor=colors['gpu'], edgecolor='black', linewidth=1)
    ax.add_patch(gpu_rect)
    ax.text(x + 0.6, 2.6, f'GPU\nRack {i+1}', ha='center', va='center', fontsize=7, fontweight='bold')
    
    # RDSW
    rds_rect = FancyBboxPatch((x, 4), 1.2, 0.8, boxstyle="round,pad=0.05",
                               facecolor=colors['rds'], edgecolor='black', linewidth=1)
    ax.add_patch(rds_rect)
    ax.text(x + 0.6, 4.4, 'RDSW', ha='center', va='center', fontsize=7, fontweight='bold')
    
    # 连接线
    ax.arrow(x + 0.6, 3.2, 0, 0.6, head_width=0.1, head_length=0.1, fc='black', ec='black')

# FDSW Layer
for i in range(3):
    x = 1.0 + i * 1.8
    fds_rect = FancyBboxPatch((x, 5.5), 1.2, 0.8, boxstyle="round,pad=0.05",
                               facecolor=colors['fds'], edgecolor='black', linewidth=1)
    ax.add_patch(fds_rect)
    ax.text(x + 0.6, 5.9, f'FDSW {i+1}', ha='center', va='center', fontsize=7, fontweight='bold')

# L2 Zone - 右侧
for i in range(4):
    x = 8.5 + i * 1.2
    gpu_rect = FancyBboxPatch((x, 2), 1, 1.2, boxstyle="round,pad=0.05",
                               facecolor=colors['gpu'], edgecolor='black', linewidth=1)
    ax.add_patch(gpu_rect)
    ax.text(x + 0.5, 2.6, f'G{i+5}', ha='center', va='center', fontsize=7, fontweight='bold')

# L2 SDSW
for i in range(2):
    x = 8.5 + i * 2.5
    sds_rect = FancyBboxPatch((x, 4), 1.2, 0.8, boxstyle="round,pad=0.05",
                               facecolor='#95E1D3', edgecolor='black', linewidth=1)
    ax.add_patch(sds_rect)
    ax.text(x + 0.6, 4.4, 'SDSW', ha='center', va='center', fontsize=7, fontweight='bold')

# BAG Layer
bag_rect = FancyBboxPatch((4, 7), 6, 1.2, boxstyle="round,pad=0.05",
                           facecolor=colors['bag'], edgecolor='black', linewidth=2)
ax.add_patch(bag_rect)
ax.text(7, 7.6, 'BAG - Backend Aggregation Gateway (Super Spine)', ha='center', va='center', 
        fontsize=10, fontweight='bold')

# Edge PoD
edge_rect = FancyBboxPatch((5.5, 5.5), 3, 0.8, boxstyle="round,pad=0.05",
                            facecolor=colors['edge'], edgecolor='black', linewidth=1)
ax.add_patch(edge_rect)
ax.text(7, 5.9, 'Edge PoD (EDSW)', ha='center', va='center', fontsize=9, fontweight='bold')

# 连接箭头
# L1 to FDSW
ax.annotate('', xy=(1.6, 5.5), xytext=(1.2, 4.8), arrowprops=dict(arrowstyle='->', color='gray', lw=1))
ax.annotate('', xy=(3.4, 5.5), xytext=(2.1, 4.8), arrowprops=dict(arrowstyle='->', color='gray', lw=1))
ax.annotate('', xy=(5.2, 5.5), xytext=(5.4, 4.8), arrowprops=dict(arrowstyle='->', color='gray', lw=1))

# FDSW to Edge
ax.annotate('', xy=(5.5, 6.3), xytext=(4.3, 6.3), arrowprops=dict(arrowstyle='->', color='gray', lw=1))
ax.annotate('', xy=(8.5, 6.3), xytext=(6.8, 6.3), arrowprops=dict(arrowstyle='->', color='gray', lw=1))

# Edge to BAG
ax.annotate('', xy=(7, 7), xytext=(7, 6.3), arrowprops=dict(arrowstyle='->', color='black', lw=2))

# L1 to L2
ax.annotate('', xy=(8.5, 3.5), xytext=(6.2, 4), arrowprops=dict(arrowstyle='->', color='blue', lw=1.5, ls='--'))

# 标签
ax.text(3, 1.3, 'DSF L1 Zone\n(~4,500 GPUs)', ha='center', fontsize=9, style='italic', color='gray')
ax.text(10.5, 1.3, 'DSF L2 Zone\n(~18,000 GPUs)', ha='center', fontsize=9, style='italic', color='gray')
ax.text(11.5, 7.6, 'Inter-Region\nConnectivity', ha='center', fontsize=8, style='italic', color='gray')

# 图例
legend_items = [
    (colors['gpu'], 'GPU Rack'),
    (colors['rds'], 'RDSW (Interface Node)'),
    (colors['fds'], 'FDSW (Fabric Node)'),
    (colors['bag'], 'BAG (Super Spine)'),
    (colors['edge'], 'Edge PoD'),
]
for i, (color, label) in enumerate(legend_items):
    rect = Rectangle((11.5, 4.5 - i*0.5), 0.3, 0.3, facecolor=color, edgecolor='black')
    ax.add_patch(rect)
    ax.text(12, 4.65 - i*0.5, label, fontsize=8, va='center')

plt.tight_layout()
plt.savefig('/root/.openclaw/workspace/book-project/assets/重构配图/ch06/fig1_ai_cluster_architecture.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

print("Figure 1: AI Cluster Architecture saved!")
