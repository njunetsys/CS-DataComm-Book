import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, Wedge, FancyArrowPatch
import numpy as np

fig, ax = plt.subplots(figsize=(14, 10))

ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.axis('off')
ax.set_title('Renewable Energy Architecture for Data Centers', fontsize=16, fontweight='bold', pad=20)

# 太阳能农场
solar = Rectangle((0.5, 6), 3, 3, facecolor='#FFF9C4', edgecolor='#FBC02D', linewidth=2)
ax.add_patch(solar)
ax.text(2, 8.8, '☀️ Solar Farm', fontsize=11, ha='center', fontweight='bold')

# 太阳能板示意
for i in range(3):
    for j in range(4):
        panel = Rectangle((0.8+i*0.8, 6.3+j*0.6), 0.6, 0.4, 
                         facecolor='#FFC107', edgecolor='#F57F17', linewidth=0.5)
        ax.add_patch(panel)

# 风电场
wind_x = 5
for i in range(3):
    x = wind_x + i * 1.2
    # 塔筒
    ax.plot([x, x], [6, 7.5], color='#607D8B', linewidth=3)
    # 叶片
    ax.text(x, 7.8, '⚡', fontsize=20, ha='center', va='center')
    
ax.text(wind_x + 1.2, 8.8, '💨 Wind Farm', fontsize=11, ha='center', fontweight='bold')

# 储能系统
battery = FancyBboxPatch((9.5, 6.5), 2, 2, boxstyle="round,pad=0.1",
                         facecolor='#E3F2FD', edgecolor='#1976D2', linewidth=2)
ax.add_patch(battery)
ax.text(10.5, 8.1, '🔋 Energy', fontsize=10, ha='center', fontweight='bold')
ax.text(10.5, 7.6, 'Storage', fontsize=10, ha='center', fontweight='bold')
ax.text(10.5, 7.1, '(ESS)', fontsize=9, ha='center', color='#1565C0')
ax.text(10.5, 6.7, 'Grid Scale', fontsize=8, ha='center', color='#546E7A')

# 电网连接
ax.plot([3.5, 5, 8.5, 9.5], [7.5, 7.5, 7.5, 7.5], 'k-', linewidth=2, alpha=0.3)
ax.plot([10.5, 10.5], [6.5, 5.2], 'k-', linewidth=2, alpha=0.3)

# 数据中心图标
dc = FancyBboxPatch((8, 2.5), 5, 2.5, boxstyle="round,pad=0.1",
                     facecolor='#E8EAF6', edgecolor='#3F51B5', linewidth=2)
ax.add_patch(dc)

# 数据中心内部
ax.text(10.5, 4.5, '🏢 Data Center', fontsize=11, ha='center', fontweight='bold')

# 服务器机架
for i in range(4):
    rack = Rectangle((8.5+i*1, 2.8), 0.6, 1.2, facecolor='#C5CAE9', edgecolor='#3949AB', linewidth=1)
    ax.add_patch(rack)
    # 服务器LED
    for j in range(3):
        ax.plot(8.8+i*1, 3.1+j*0.3, 'o', markersize=2, color='#4CAF50')

# 连接箭头
ax.annotate('', xy=(8.5, 5), xytext=(7.5, 6.5),
           arrowprops=dict(arrowstyle='->', color='#4CAF50', lw=2))

# 智能控制系统
control = FancyBboxPatch((0.5, 2.5), 3, 2.5, boxstyle="round,pad=0.1",
                          facecolor='#F3E5F5', edgecolor='#9C27B0', linewidth=2)
ax.add_patch(control)
ax.text(2, 4.5, '🤖 AI Control', fontsize=10, ha='center', fontweight='bold')
ax.text(2, 4.0, 'System', fontsize=10, ha='center', fontweight='bold')
ax.text(2, 3.3, '• Load balancing', fontsize=8, ha='center')
ax.text(2, 2.9, '• Demand response', fontsize=8, ha='center')

# 控制连接
ax.annotate('', xy=(8, 3.5), xytext=(3.5, 3.5),
           arrowprops=dict(arrowstyle='->', color='#9C27B0', lw=2))

# 挑战框
challenges = FancyBboxPatch((4, 0.3), 6, 1.5, boxstyle="round,pad=0.1",
                             facecolor='#FFEBEE', edgecolor='#E53935', linewidth=1)
ax.add_patch(challenges)
ax.text(7, 1.5, '⚠️ Key Challenge: Intermittency Management', fontsize=10, ha='center', fontweight='bold', color='#C62828')
ax.text(7, 0.9, 'Solar: Day only | Wind: Weather dependent | Solution: Storage + Smart Grid + Hybrid', 
        fontsize=9, ha='center', color='#37474F')

# Meta数据标注
ax.text(13.5, 0.5, 'Meta: 15GW+\nClean Energy\nPortfolio', fontsize=9, ha='center', va='center',
        bbox=dict(boxstyle='round', facecolor='#E8F5E9', edgecolor='#4CAF50'))

plt.tight_layout()
plt.savefig('/root/.openclaw/workspace/book-project/assets/重构配图/ch07/renewable_energy_architecture.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

print("图5: 可再生能源应用架构图 - 完成")
