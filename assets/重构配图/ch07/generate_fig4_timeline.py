import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch, Circle
import numpy as np

fig, ax = plt.subplots(figsize=(16, 9))

ax.set_xlim(0, 16)
ax.set_ylim(0, 10)
ax.axis('off')
ax.set_title("Meta's Sustainability Journey (2011-2024)", fontsize=16, fontweight='bold', pad=20)

# 时间线数据 - 分三个阶段
phases = [
    {
        'name': 'Foundation\n(2011-2015)',
        'x': 3,
        'color': '#90CAF9',
        'events': [
            ('2011', 'First GHG\nInventory', 7.5),
            ('2013', 'Open Compute\nProject', 5.5),
            ('2014', '50% Renewables\nGoal', 3.5)
        ]
    },
    {
        'name': 'Acceleration\n(2016-2020)',
        'x': 8,
        'color': '#81C784',
        'events': [
            ('2018', '100% Renewable\nEnergy Target', 7.5),
            ('2018', 'StatePoint\nLiquid Cooling', 5.5),
            ('2020', 'Net Zero\n2030 Commitment', 3.5)
        ]
    },
    {
        'name': 'Execution\n(2021-2024)',
        'x': 13,
        'color': '#FFCC80',
        'events': [
            ('2021', 'RL Cooling\nOptimization', 7.5),
            ('2022', '15GW Clean\nEnergy Portfolio', 5.5),
            ('2024', 'Design for\nSustainability', 3.5)
        ]
    }
]

# 绘制阶段背景
for phase in phases:
    x = phase['x']
    color = phase['color']
    
    # 阶段背景
    bg = FancyBboxPatch((x-2.3, 2.5), 4.6, 6, boxstyle="round,pad=0.1",
                         facecolor=color, alpha=0.2, edgecolor=color, linewidth=2)
    ax.add_patch(bg)
    
    # 阶段标题
    ax.text(x, 8.8, phase['name'], fontsize=11, ha='center', va='center', fontweight='bold')
    
    # 事件
    for year, event, y in phase['events']:
        # 年份圆圈
        circle = Circle((x-1.2, y), 0.35, facecolor=color, edgecolor='white', linewidth=2, zorder=3)
        ax.add_patch(circle)
        ax.text(x-1.2, y, year, fontsize=8, ha='center', va='center', fontweight='bold')
        
        # 事件描述
        ax.text(x+0.3, y, event, fontsize=9, ha='left', va='center')
        
        # 连接线
        ax.plot([x-0.8, x-0.1], [y, y], color=color, linewidth=1.5)

# 阶段间箭头
ax.annotate('', xy=(5.5, 5.5), xytext=(5.2, 5.5),
           arrowprops=dict(arrowstyle='->', color='#78909C', lw=3))
ax.annotate('', xy=(10.5, 5.5), xytext=(10.2, 5.5),
           arrowprops=dict(arrowstyle='->', color='#78909C', lw=3))

# 底部关键数据
stats_box = FancyBboxPatch((1, 0.3), 14, 1.8, boxstyle="round,pad=0.05",
                            facecolor='#F5F5F5', edgecolor='#9E9E9E', linewidth=1)
ax.add_patch(stats_box)

stats = [
    ('15GW+', 'Clean Energy'),
    ('1.10', 'Fleet Average PUE'),
    ('100%', 'Renewable Matched'),
    ('Net Zero', 'by 2030'),
    ('Water+', 'by 2030')
]

x_pos = 2
for value, label in stats:
    ax.text(x_pos, 1.5, value, fontsize=14, ha='center', va='center', fontweight='bold', color='#1565C0')
    ax.text(x_pos, 0.8, label, fontsize=9, ha='center', va='center', color='#616161')
    x_pos += 3

# 时间线主线
ax.plot([1, 15], [2.3, 2.3], color='#BDBDBD', linewidth=1, alpha=0.5)

plt.tight_layout()
plt.savefig('/root/.openclaw/workspace/book-project/assets/重构配图/ch07/meta_sustainability_timeline.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

print("图4: Meta可持续发展时间线 - 完成")
