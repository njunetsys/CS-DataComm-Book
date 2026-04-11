import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, FancyArrowPatch, Polygon
import numpy as np

fig, axes = plt.subplots(1, 2, figsize=(14, 7))

# ==================== 大象流示意 ====================
ax = axes[0]
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis('off')
ax.set_title('Elephant Flows in AI Training', fontsize=13, fontweight='bold', pad=20)

# 高速公路车道
colors_road = ['#E8E8E8', '#D0D0D0', '#E8E8E8', '#D0D0D0']
for i, color in enumerate(colors_road):
    y = 2 + i * 1.8
    road = Rectangle((0.5, y), 9, 1.6, facecolor=color, edgecolor='gray', linewidth=0.5)
    ax.add_patch(road)

# 车道标签
labels = ['Link 1', 'Link 2', 'Link 3', 'Link 4']
for i, label in enumerate(labels):
    ax.text(0.2, 2.8 + i * 1.8, label, ha='center', va='center', fontsize=8, rotation=90)

# 大象流 - 超大流量块
# Link 1 - 多个大象流堆积 (拥塞)
for i in range(3):
    elephant = FancyBboxPatch((1 + i * 2.5, 2.2), 2, 1.2, boxstyle="round,pad=0.05",
                               facecolor='#E74C3C', edgecolor='darkred', linewidth=2)
    ax.add_patch(elephant)
    ax.text(2 + i * 2.5, 2.8, f'AllReduce\n{100+i*20}GB', ha='center', va='center', fontsize=6, color='white', fontweight='bold')

# Link 2 - 一个大象流
elephant2 = FancyBboxPatch((1.5, 4), 5, 1.2, boxstyle="round,pad=0.05",
                            facecolor='#E74C3C', edgecolor='darkred', linewidth=2)
ax.add_patch(elephant2)
ax.text(4, 4.6, 'Gradient Sync (500GB)', ha='center', va='center', fontsize=8, color='white', fontweight='bold')

# Link 3 - 空
elephant3_text = ax.text(5, 5.8, 'EMPTY', ha='center', va='center', fontsize=12, 
                          color='green', style='italic', alpha=0.5)

# Link 4 - 一个大象流
elephant4 = FancyBboxPatch((2, 7.6), 4, 1.2, boxstyle="round,pad=0.05",
                            facecolor='#E74C3C', edgecolor='darkred', linewidth=2)
ax.add_patch(elephant4)
ax.text(4, 8.2, 'Model Checkpoint (300GB)', ha='center', va='center', fontsize=8, color='white', fontweight='bold')

# 拥塞指示
ax.text(5, 1.3, 'Hash Collision → Link 1 Overloaded (Congestion)', ha='center', fontsize=9, color='red', fontweight='bold')
ax.text(5, 0.8, 'Traditional ECMP fails with elephant flows', ha='center', fontsize=8, style='italic', color='gray')

# ==================== 老鼠流 vs 大象流对比 ====================
ax = axes[1]
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis('off')
ax.set_title('Elephant Flows vs Mice Flows', fontsize=13, fontweight='bold', pad=20)

# 传统云计算 - 老鼠流
ax.text(2.5, 9, 'Traditional Cloud\n(Mice Flows)', ha='center', fontsize=11, fontweight='bold', color='#3498DB')

# 老鼠流可视化 - 小数据包
np.random.seed(42)
for i in range(50):
    x = np.random.uniform(0.5, 4.5)
    y = np.random.uniform(5.5, 8.5)
    size = np.random.uniform(0.08, 0.15)
    mouse = Circle((x, y), size, facecolor='#3498DB', edgecolor='darkblue', linewidth=0.5, alpha=0.7)
    ax.add_patch(mouse)

# 老鼠流特征
mice_features = """Characteristics:
• Many small flows
• Short duration
• High entropy
• ECMP works well
• Bursty traffic"""
ax.text(2.5, 4.5, mice_features, ha='center', va='top', fontsize=8,
        bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))

# AI训练 - 大象流
ax.text(7.5, 9, 'AI Training\n(Elephant Flows)', ha='center', fontsize=11, fontweight='bold', color='#E74C3C')

# 大象流可视化 - 大流量块
for i in range(5):
    x = 5.5 + (i % 3) * 1.5
    y = 6.5 + (i // 3) * 1.5
    elephant = FancyBboxPatch((x, y), 1.2, 1, boxstyle="round,pad=0.05",
                               facecolor='#E74C3C', edgecolor='darkred', linewidth=2)
    ax.add_patch(elephant)
    sizes = ['10GB', '50GB', '100GB', '200GB', '500GB']
    ax.text(x + 0.6, y + 0.5, sizes[i], ha='center', va='center', fontsize=7, color='white', fontweight='bold')

# 大象流特征
elephant_features = """Characteristics:
• Few huge flows
• Long duration (seconds~minutes)
• Low entropy
• ECMP fails (hash collision)
• Synchronous patterns"""
ax.text(7.5, 4.5, elephant_features, ha='center', va='top', fontsize=8,
        bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.3))

# 关键洞察
insight_box = FancyBboxPatch((1, 0.5), 8, 1.2, boxstyle="round,pad=0.1",
                              facecolor='wheat', edgecolor='orange', linewidth=2)
ax.add_patch(insight_box)
ax.text(5, 1.1, 'Key Insight: AI training creates \u201celephant flows\u201d that break traditional load balancing.', 
        ha='center', va='center', fontsize=10, fontweight='bold')
ax.text(5, 0.75, 'Need: Cell-based packet spraying (DSF) instead of flow-based ECMP', 
        ha='center', va='center', fontsize=9, style='italic')

plt.tight_layout()
plt.savefig('/root/.openclaw/workspace/book-project/assets/重构配图/ch06/fig5_elephant_vs_mice_flows.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

print("Figure 5: Elephant vs Mice Flows saved!")
