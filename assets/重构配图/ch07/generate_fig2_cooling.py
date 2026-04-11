import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch, Circle
import numpy as np

# 图2: 冷却技术演进图：风冷→冷板→浸没式
fig, ax = plt.subplots(1, 1, figsize=(14, 8))

ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.axis('off')
ax.set_title('Evolution of Data Center Cooling Technologies', fontsize=16, fontweight='bold', pad=20)

# 三个阶段的技术
stages = [
    {
        'title': 'Air Cooling\n(Traditional)',
        'x': 2,
        'color': '#FF7043',
        'density': '<15 kW/rack',
        'pue': 'PUE: 1.5-2.0',
        'features': ['Standard AC units', 'CRAC/CRAH systems', 'Raised floor design'],
        'icon': '💨'
    },
    {
        'title': 'Direct-to-Chip\nLiquid Cooling',
        'x': 7,
        'color': '#29B6F6',
        'density': '30-50 kW/rack',
        'pue': 'PUE: 1.05-1.15',
        'features': ['Cold plates on CPU/GPU', 'Coolant circulation', 'Hybrid air+liquid'],
        'icon': '❄️'
    },
    {
        'title': 'Immersion\nCooling',
        'x': 12,
        'color': '#66BB6A',
        'density': '>100 kW/rack',
        'pue': 'PUE: 1.02-1.08',
        'features': ['Full immersion', 'Dielectric fluid', 'Zero water usage'],
        'icon': '🌊'
    }
]

for stage in stages:
    x = stage['x']
    color = stage['color']
    
    # 主框
    box = FancyBboxPatch((x-1.3, 4), 2.6, 5, boxstyle="round,pad=0.1", 
                          facecolor=color, alpha=0.2, edgecolor=color, linewidth=2)
    ax.add_patch(box)
    
    # 标题
    ax.text(x, 8.5, stage['icon'], fontsize=24, ha='center', va='center')
    ax.text(x, 7.8, stage['title'], fontsize=11, ha='center', va='center', fontweight='bold')
    
    # 密度
    ax.text(x, 6.8, stage['density'], fontsize=10, ha='center', va='center', 
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # PUE
    ax.text(x, 6.2, stage['pue'], fontsize=9, ha='center', va='center', color=color, fontweight='bold')
    
    # 特性列表
    y_feat = 5.4
    for feat in stage['features']:
        ax.text(x, y_feat, f'• {feat}', fontsize=8, ha='center', va='center')
        y_feat -= 0.4

# 箭头连接
arrow1 = FancyArrowPatch((3.5, 6.5), (5.5, 6.5), 
                         arrowstyle='->', mutation_scale=20, linewidth=2, color='#78909C')
ax.add_patch(arrow1)
ax.text(4.5, 6.8, 'AI Era', fontsize=9, ha='center', va='center', color='#546E7A', fontweight='bold')

arrow2 = FancyArrowPatch((8.5, 6.5), (10.5, 6.5), 
                         arrowstyle='->', mutation_scale=20, linewidth=2, color='#78909C')
ax.add_patch(arrow2)
ax.text(9.5, 6.8, 'Future', fontsize=9, ha='center', va='center', color='#546E7A', fontweight='bold')

# 时间线
ax.text(2, 3.2, '2010s', fontsize=10, ha='center', va='center', color='#757575')
ax.text(7, 3.2, '2020s', fontsize=10, ha='center', va='center', color='#757575')
ax.text(12, 3.2, '2030s', fontsize=10, ha='center', va='center', color='#757575')

ax.plot([2, 12], [2.8, 2.8], 'k-', linewidth=2, alpha=0.3)
for x in [2, 7, 12]:
    ax.plot(x, 2.8, 'o', markersize=10, color='white', markeredgecolor='#546E7A', markeredgewidth=2)

# 底部说明
ax.text(7, 1.5, 'Driven by AI training power density: from 5kW to 100kW+ per rack', 
        fontsize=10, ha='center', va='center', style='italic', color='#455A64')

ax.set_xlim(-0.5, 14.5)
plt.tight_layout()
plt.savefig('/root/.openclaw/workspace/book-project/assets/重构配图/ch07/cooling_evolution.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

print("图2: 冷却技术演进图 - 完成")
