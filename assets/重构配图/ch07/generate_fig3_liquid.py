import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, FancyArrowPatch, Polygon
import numpy as np

fig, axes = plt.subplots(1, 3, figsize=(15, 8))

def draw_server(ax, title, color, cooling_type):
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    ax.set_title(title, fontsize=12, fontweight='bold', pad=10, color=color)
    
    # 机架外框
    rack = Rectangle((2, 1), 6, 8, linewidth=2, edgecolor='#37474F', facecolor='#ECEFF1')
    ax.add_patch(rack)
    
    if cooling_type == 'air':
        # 服务器单元
        for i in range(4):
            y = 2 + i * 1.8
            server = Rectangle((2.5, y), 5, 1.5, facecolor='#FFCCBC', edgecolor='#FF7043', linewidth=1)
            ax.add_patch(server)
            # CPU/GPU
            ax.add_patch(Circle((4.5, y+0.75), 0.3, facecolor='#FF5722', edgecolor='#BF360C'))
            ax.add_patch(Circle((5.5, y+0.75), 0.3, facecolor='#FF5722', edgecolor='#BF360C'))
            # 风扇
            ax.plot([7.5], [y+0.75], 'o', markersize=8, color='#1976D2')
        
        # 冷风进入
        for i in range(3):
            ax.annotate('', xy=(3+i*2, 1.5), xytext=(3+i*2, 0.5),
                       arrowprops=dict(arrowstyle='->', color='#4FC3F7', lw=2))
        ax.text(5, 0.2, 'Cold Air In', fontsize=9, ha='center', color='#0288D1')
        
        # 热风排出
        for i in range(3):
            ax.annotate('', xy=(3+i*2, 9.5), xytext=(3+i*2, 8.5),
                       arrowprops=dict(arrowstyle='->', color='#FF7043', lw=2))
        ax.text(5, 9.8, 'Hot Air Out', fontsize=9, ha='center', color='#D84315')
        
    elif cooling_type == 'cold_plate':
        # 服务器单元
        for i in range(4):
            y = 2 + i * 1.8
            server = Rectangle((2.5, y), 5, 1.5, facecolor='#BBDEFB', edgecolor='#2196F3', linewidth=1)
            ax.add_patch(server)
            # CPU/GPU with cold plate
            ax.add_patch(Circle((4.5, y+0.75), 0.35, facecolor='#1565C0', edgecolor='#0D47A1'))
            ax.add_patch(Circle((5.5, y+0.75), 0.35, facecolor='#1565C0', edgecolor='#0D47A1'))
            # 冷板标记
            ax.text(4.5, y+0.75, 'CP', fontsize=7, ha='center', va='center', color='white', fontweight='bold')
            ax.text(5.5, y+0.75, 'CP', fontsize=7, ha='center', va='center', color='white', fontweight='bold')
        
        # 冷却液管道
        ax.plot([1.5, 2.5], [5, 5], color='#00BCD4', linewidth=4)
        ax.plot([7.5, 8.5], [5, 5], color='#00BCD4', linewidth=4)
        ax.text(1, 5, 'In', fontsize=9, ha='center', va='center', color='#00ACC1', fontweight='bold')
        ax.text(9, 5, 'Out', fontsize=9, ha='center', va='center', color='#FF5722', fontweight='bold')
        
        # 管道连接示意
        ax.annotate('', xy=(1.5, 5.3), xytext=(1.5, 4.7),
                   arrowprops=dict(arrowstyle='->', color='#00BCD4', lw=2))
        ax.annotate('', xy=(8.5, 4.7), xytext=(8.5, 5.3),
                   arrowprops=dict(arrowstyle='->', color='#FF5722', lw=2))
        
    elif cooling_type == 'immersion':
        # 液体填充
        liquid = Rectangle((2.1, 1.1), 5.8, 7.8, facecolor='#81C784', alpha=0.3, edgecolor='none')
        ax.add_patch(liquid)
        
        # 浸没的服务器
        for i in range(4):
            y = 2 + i * 1.8
            server = Rectangle((2.5, y), 5, 1.5, facecolor='#C8E6C9', edgecolor='#4CAF50', linewidth=1)
            ax.add_patch(server)
            # CPU/GPU直接接触液体
            ax.add_patch(Circle((4.5, y+0.75), 0.35, facecolor='#2E7D32', edgecolor='#1B5E20'))
            ax.add_patch(Circle((5.5, y+0.75), 0.35, facecolor='#2E7D32', edgecolor='#1B5E20'))
        
        # 液体液位线
        ax.plot([2, 8], [8.5, 8.5], '--', color='#4CAF50', linewidth=2)
        ax.text(7, 8.8, 'Dielectric Fluid', fontsize=9, ha='center', color='#2E7D32')
        
        # 冷凝器连接
        ax.plot([8.5, 9.5], [5.5, 6.5], color='#FF9800', linewidth=3)
        ax.plot([8.5, 9.5], [4.5, 3.5], color='#00BCD4', linewidth=3)
        ax.text(9.8, 6.8, 'Vapor', fontsize=8, ha='left', color='#FF9800')
        ax.text(9.8, 3.2, 'Liquid', fontsize=8, ha='left', color='#00BCD4')

# 绘制三种冷却方式
draw_server(axes[0], 'Air Cooling', '#FF7043', 'air')
draw_server(axes[1], 'Direct-to-Chip Liquid', '#2196F3', 'cold_plate')
draw_server(axes[2], 'Immersion Cooling', '#4CAF50', 'immersion')

plt.suptitle('Liquid Cooling Architecture Comparison', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('/root/.openclaw/workspace/book-project/assets/重构配图/ch07/liquid_cooling_comparison.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

print("图3: 液冷技术架构对比图 - 完成")
