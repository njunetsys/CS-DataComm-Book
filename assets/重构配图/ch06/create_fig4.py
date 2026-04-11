import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, FancyArrowPatch
import numpy as np

fig, ax = plt.subplots(1, 1, figsize=(14, 10))
ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.axis('off')

# 标题
ax.text(7, 9.5, 'Desync Debug Workflow for AI Training', fontsize=16, fontweight='bold', ha='center')

# 颜色
colors = {
    'problem': '#E74C3C',
    'detect': '#F39C12',
    'analyze': '#3498DB',
    'locate': '#2ECC71',
    'fix': '#9B59B6'
}

# ==================== 阶段1: 问题发生 ====================
stage1_y = 7.5
ax.text(1, stage1_y + 0.8, '1. Training Stalled', fontsize=11, fontweight='bold', color=colors['problem'])

# 绘制多个GPU
for i in range(5):
    x = 1 + i * 1.2
    gpu = FancyBboxPatch((x, stage1_y - 0.3), 0.8, 0.6, boxstyle="round,pad=0.05",
                          facecolor='#3498DB', edgecolor='black', linewidth=1)
    ax.add_patch(gpu)
    ax.text(x + 0.4, stage1_y, f'GPU{i+1}', ha='center', va='center', fontsize=7)

# 其中GPU3出现问题
problem_gpu = FancyBboxPatch((3.4, stage1_y - 0.3), 0.8, 0.6, boxstyle="round,pad=0.05",
                              facecolor=colors['problem'], edgecolor='black', linewidth=2)
ax.add_patch(problem_gpu)
ax.text(3.8, stage1_y, 'GPU3', ha='center', va='center', fontsize=7, color='white', fontweight='bold')

# 同步障碍
barrier = FancyBboxPatch((0.8, stage1_y - 0.8), 5.2, 0.3, boxstyle="round,pad=0.05",
                          facecolor='#95A5A6', edgecolor='black', linewidth=1)
ax.add_patch(barrier)
ax.text(3.4, stage1_y - 0.65, 'AllReduce Sync Barrier', ha='center', va='center', fontsize=8, style='italic')

# 说明
ax.text(3.4, stage1_y - 1.3, 'Training job hangs due to straggler GPU', ha='center', fontsize=9, 
        style='italic', color=colors['problem'])

# ==================== 阶段2: 检测 ====================
stage2_y = 5.5
ax.text(1, stage2_y + 0.8, '2. Desync Detection', fontsize=11, fontweight='bold', color=colors['detect'])

# 检测框
detect_box = FancyBboxPatch((1, stage2_y - 0.4), 4.5, 1, boxstyle="round,pad=0.1",
                             facecolor=colors['detect'], edgecolor='black', linewidth=2)
ax.add_patch(detect_box)

detect_text = """• Monitor collective communication timing
• Detect sync point deviation 
• Trigger desync debug capture
• Log timestamps from all ranks"""
ax.text(3.25, stage2_y + 0.1, detect_text, ha='center', va='center', fontsize=8)

# ==================== 阶段3: 分析 ====================
stage3_y = 3.5
ax.text(8, stage3_y + 0.8, '3. Distributed Analysis', fontsize=11, fontweight='bold', color=colors['analyze'])

# 分析框
analyze_box = FancyBboxPatch((8, stage3_y - 0.4), 4.5, 1.2, boxstyle="round,pad=0.1",
                              facecolor=colors['analyze'], edgecolor='black', linewidth=2)
ax.add_patch(analyze_box)

analyze_text = """• Collect traces from all ranks
• Build global timeline view
• Identify outlier nodes
• Correlate with network events
• Check hardware health metrics"""
ax.text(10.25, stage3_y + 0.2, analyze_text, ha='center', va='center', fontsize=8)

# ==================== 阶段4: 定位 ====================
stage4_y = 1.5
ax.text(1, stage4_y + 1.3, '4. Straggler Location', fontsize=11, fontweight='bold', color=colors['locate'])

# 层次化定位流程
levels = [
    ('Cluster Level', 8.5, 0.4),
    ('Rack Level', 5, 0.35),
    ('Server Level', 2.5, 0.3),
    ('GPU Level', 1, 0.25)
]

for i, (label, width, height) in enumerate(levels):
    x = 1
    y = stage4_y + 0.8 - i * 0.4
    rect = FancyBboxPatch((x, y), width, height, boxstyle="round,pad=0.02",
                           facecolor=colors['locate'], edgecolor='black', linewidth=1, alpha=0.7 + i*0.08)
    ax.add_patch(rect)
    ax.text(x + width/2, y + height/2, label, ha='center', va='center', fontsize=8 - i*0.3)

# ==================== 阶段5: 修复 ====================
stage5_y = 1.5
ax.text(8, stage5_y + 1.3, '5. Resolution', fontsize=11, fontweight='bold', color=colors['fix'])

fix_box = FancyBboxPatch((8, stage5_y - 0.2), 4.5, 1.2, boxstyle="round,pad=0.1",
                          facecolor=colors['fix'], edgecolor='black', linewidth=2)
ax.add_patch(fix_box)

fix_text = """• Isolate problematic GPU
• Migrate to spare capacity
• Restart from checkpoint
• Update health database
• Continue training"""
ax.text(10.25, stage5_y + 0.4, fix_text, ha='center', va='center', fontsize=8)

# 箭头连接
# 阶段1 -> 阶段2
ax.annotate('', xy=(3.25, 5.1), xytext=(3.25, 6.2),
            arrowprops=dict(arrowstyle='->', color='black', lw=2))

# 阶段2 -> 阶段3
ax.annotate('', xy=(8, 5.5), xytext=(5.5, 5.5),
            arrowprops=dict(arrowstyle='->', color='black', lw=2))

# 阶段3 -> 阶段4
ax.annotate('', xy=(3.5, 2.9), xytext=(8, 3.5),
            arrowprops=dict(arrowstyle='->', color='black', lw=2, connectionstyle='arc3,rad=-0.3'))

# 阶段3 -> 阶段5
ax.annotate('', xy=(8, 2.5), xytext=(10.25, 3.1),
            arrowprops=dict(arrowstyle='->', color='black', lw=2))

# Flight Recorder 说明
flight_box = FancyBboxPatch((7.5, 8.5), 5.5, 0.8, boxstyle="round,pad=0.05",
                             facecolor='wheat', edgecolor='orange', linewidth=1)
ax.add_patch(flight_box)
ax.text(10.25, 8.9, 'Flight Recorder: Captures collective communication history', 
        ha='center', va='center', fontsize=9, style='italic')
ax.text(10.25, 8.6, 'for post-mortem analysis of distributed training issues', 
        ha='center', va='center', fontsize=9, style='italic')

plt.tight_layout()
plt.savefig('/root/.openclaw/workspace/book-project/assets/重构配图/ch06/fig4_desync_debug_workflow.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

print("Figure 4: Desync Debug Workflow saved!")
