import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle
import numpy as np

# 设置中文字体
plt.rcParams['font.size'] = 12

# 图1: PUE计算公式和优化路径图
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# 左图：PUE计算公式
ax1.set_xlim(0, 10)
ax1.set_ylim(0, 10)
ax1.axis('off')
ax1.set_title('PUE (Power Usage Effectiveness) Formula', fontsize=14, fontweight='bold', pad=20)

# PUE公式
formula_text = r'$PUE = \frac{Total\ Facility\ Power}{IT\ Equipment\ Power}$'
ax1.text(5, 8, formula_text, fontsize=18, ha='center', va='center', 
         bbox=dict(boxstyle='round,pad=0.5', facecolor='#E3F2FD', edgecolor='#1976D2', linewidth=2))

# 分解公式
breakdown = r'$PUE = 1 + \frac{Cooling + Power\ Loss + Lighting}{IT\ Power}$'
ax1.text(5, 5.5, breakdown, fontsize=14, ha='center', va='center',
         bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFF3E0', edgecolor='#F57C00', linewidth=1.5))

# 理想值说明
ax1.text(5, 3.5, 'Ideal PUE ≈ 1.0', fontsize=12, ha='center', va='center', color='#2E7D32', fontweight='bold')
ax1.text(5, 2.8, 'Traditional DC: 1.5-2.0', fontsize=11, ha='center', va='center', color='#C62828')
ax1.text(5, 2.2, 'Meta Fleet Average: 1.10', fontsize=11, ha='center', va='center', color='#1565C0', fontweight='bold')

# 右图：PUE优化路径时间线
ax2.set_xlim(0, 10)
ax2.set_ylim(0, 10)
ax2.axis('off')
ax2.set_title('PUE Optimization Journey', fontsize=14, fontweight='bold', pad=20)

# 时间线数据
milestones = [
    (2010, 'Traditional Cooling', 1.8, '#EF5350'),
    (2014, 'Free Cooling', 1.4, '#FFA726'),
    (2018, 'StatePoint Liquid', 1.15, '#66BB6A'),
    (2022, 'Direct Chip Liquid', 1.08, '#42A5F5'),
    (2024, 'Immersion Cooling', 1.03, '#7E57C2')
]

y_pos = 8.5
for year, tech, pue, color in milestones:
    # 年份
    ax2.text(1, y_pos, str(year), fontsize=11, ha='center', va='center', fontweight='bold')
    # 技术名称
    ax2.text(3.5, y_pos, tech, fontsize=11, ha='left', va='center')
    # PUE值
    circle = Circle((7, y_pos), 0.4, color=color, zorder=3)
    ax2.add_patch(circle)
    ax2.text(7, y_pos, f'{pue}', fontsize=10, ha='center', va='center', color='white', fontweight='bold')
    
    if y_pos > 2:
        ax2.annotate('', xy=(7, y_pos-0.8), xytext=(7, y_pos-0.5),
                    arrowprops=dict(arrowstyle='->', color='gray', lw=1.5))
    y_pos -= 1.5

# 添加趋势线
ax2.text(8.5, 8.5, 'PUE', fontsize=10, ha='center', va='center', fontweight='bold')
ax2.set_xlim(-0.5, 10)

plt.tight_layout()
plt.savefig('/root/.openclaw/workspace/book-project/assets/重构配图/ch07/pue_formula_optimization.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

print("图1: PUE计算公式和优化路径图 - 完成")
