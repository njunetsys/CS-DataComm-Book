# Noteleaf

讲义生产与质检工具链。机器只定位，裁决归人。

纯 Python 标准库实现，无需安装任何第三方包，Python 3.8+ 开箱即用。

## 是什么

Noteleaf 是一条人机分工的质检链，把讲义生产拆成六段流水线：

```
ASSET → ANCHOR → WRITE → GATE → REVIEW → DELIVER
素材     认知锚    写作     门禁    审稿      交付
```

机器负责可复现的定位与核对（有没有、过不过、命中在哪一行），人负责裁决与创作。教学结构检查永久 WARN 不 BLOCK，防「合规稿」KPI 游戏。

## 目录结构

```
tools/
  lf/                 13 个工具模块
  check_chain.py      GATE 门禁编排器
CloudComputing/framework/
  spec/               流水线单一真源（spec_v0.1.0.json）
  contracts/          意图契约（含模板与 part4 实例）
  vocab/              封闭术语词表（锁版本）
  prefs/              写作偏好声明
  anchors/            通用写作规则（ANCHOR_RULES.html）
  k1/                 素材获取种子表
  inputs/part4/       示例素材（FatTree / Jupiter 论文 Markdown）
工具手册_Noteleaf.html   完整手册（组件设计 + 使用 + 扩展操作）
```

## 快速开始

所有命令在仓库根目录运行。

```bash
# 自检（改完工具先跑这个）
python3 tools/lf/intent_ga.py --selfcheck
python3 tools/lf/lecture_lint.py --selfcheck

# 机械痕迹体检（破折号 / 画外音 / 空锚文本 / 图引用）
python3 tools/lf/lecture_lint.py <讲义.html>

# 结构与忠实度体检（标题 / 图 / 术语 / 示例）
python3 tools/lf/rubric_check.py <讲义.html>

# 从素材抽概念顺序 → 提案讲述顺序（机器只提案，裁决归人）
python3 tools/lf/logic_order.py EXTRACT CloudComputing/framework/inputs/part4
python3 tools/lf/logic_order.py PROPOSE CloudComputing/framework/inputs/part4 \
    --section 1.2 --current "传统三层架构,STP,CLOS,Fat-Tree,Leaf-Spine,Jupiter"

# 意图契约核对（四要素 + 讲述顺序）
python3 tools/lf/intent_ga.py CHECK  CloudComputing/framework/contracts/part4_s12.contract.json <讲义.html> --section-id s12
python3 tools/lf/intent_ga.py ORDER  CloudComputing/framework/contracts/part4_s12.contract.json <讲义.html> --section-id s12

# 全链验证（六段流水线）
python3 tools/lf/pipeline_run.py --lecture <讲ID> --html <讲义.html> --json
```

## 组件一览

| 模块 | 角色 | 一句话 |
|---|---|---|
| pipeline_run | 编排 | 六段流水线唯一入口，共享文档上下文 |
| k1_acquire | K1 素材获取 | 论文 / 厂商数字卡 / 教材 / 知乎线索，落工单 |
| doc_read | K2 解析 | 按格式选解析器，保结构、算指纹、统计可复核信号 |
| asset_score | K2 评估 | 五维评分（源头 / 机制 / 可核对 / 时效 / 许可），透明可复核 |
| prefs | K3 偏好 | 声明式供料排序，只影响排序不改正文 |
| preflight | O2 前置门禁 | 写作前硬前置：偏好已声明 + 认知锚就位 |
| check_chain | GATE 门禁 | 红线 / 自包含 / 外链 / 图序，FAIL=0 才过 |
| lecture_lint | 机械体检 | L1-L8 确定性定位，不裁决不改写 |
| rubric_check | G2 评测 | PresentBench 式原子项，二分判定 + 局部证据 |
| intent_ga | 意图契约 | 四要素 CHECK + 逻辑顺序 ORDER，双层判据防空壳 |
| logic_order | 逻辑顺序 | EXTRACT / PROPOSE / CONFIRM，材料自带逻辑 |
| memory | M2 记忆 | 三层记忆，只记显式声明与已闭环结论 |
| doc_slice | 切片 | 按章切带行号纯文本，供文件交接省 token |
| spec | 真源 | 读 spec 并校验，段序漂移即 FAIL |

## 文档

完整手册见 [`工具手册_Noteleaf.html`](工具手册_Noteleaf.html)（单文件自包含，浏览器直接打开），含：

- 17 节：设计哲学、六段流水线、13 个组件逐个详解（方法 + 判据 + CLI + 实测校准记录）
- **§15 扩展操作**：如何添加知识点（加一节 / 加检查规则 / 加素材来源 / 改流水线）
- 典型工作流与排错表

## 设计原则

1. **spec 单一真源**：段序、能力归属、门禁名都写在 spec，不硬编码。
2. **机器只定位，裁决归人**：检查只报「有/没有、过/不过、在哪一行」。
3. **append-only 台账**：素材、工单、决策只追加，同名冲突报错不覆盖。
4. **显式意图**：写作前必须声明偏好与契约，缺项即拦。
5. **纠错转检查**：同一个错只纠正一次，然后写成 lint 规则。

## 许可

内部教学工具。示例素材（FatTree / Jupiter 论文 Markdown）版权归原作者与 ACM 所有，仅作研究学习参考。
