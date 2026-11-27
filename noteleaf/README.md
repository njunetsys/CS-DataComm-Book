# Noteleaf

讲义生产与质检工具链。机器只定位，裁决归人。

纯 Python 标准库实现，无需安装任何第三方包，Python 3.8+ 开箱即用。所有命令在仓库根目录运行。

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
工具手册_Noteleaf.html   完整手册（19 节：组件设计 + 方法论 + 数据格式 + 扩展操作）
```

## 快速开始

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

| 模块 | 角色 | 一句话 | 主要输出 |
|---|---|---|---|
| pipeline_run | 编排 | 六段流水线唯一入口，共享文档上下文 | 摘要 JSON + `review/<讲ID>_pipeline_full.json` |
| k1_acquire | K1 素材获取 | 论文 / 厂商数字卡 / 教材 / 知乎线索，落工单 | `k1/tickets.jsonl` 追加、三态分级与缺口清单 |
| doc_read | K2 解析 | 按格式选解析器，保结构、算指纹、统计可复核信号 | 结构统计 JSON，`--save` 落 parsed.md |
| asset_score | K2 评估 | 五维评分（源头 / 机制 / 可核对 / 时效 / 许可），透明可复核 | `asset_ledger.jsonl` 追加评估卡 |
| prefs | K3 偏好 | 声明式供料排序，只影响排序不改正文 | `prefs/<讲ID>_prefs.json`、供料排序表 |
| preflight | O2 前置门禁 | 写作前硬前置：偏好已声明 + 认知锚就位 | 三道门判定 + 补齐命令 |
| check_chain | GATE 门禁 | 红线 / 自包含 / 外链 / 图序，FAIL=0 才过 | 六种门逐门结果，退出码 0/1 |
| lecture_lint | 机械体检 | L1-L8 确定性定位，不裁决不改写 | 逐条命中（文件/行号/级别） |
| rubric_check | G2 评测 | PresentBench 式原子项，二分判定 + 局部证据 | R1-R7 判定 + 待回源清单 |
| intent_ga | 意图契约 | 四要素 CHECK + 逻辑顺序 ORDER，双层判据防空壳 | 要素落点 / 逆序对 / 缺失锚 |
| logic_order | 逻辑顺序 | EXTRACT / PROPOSE / CONFIRM，材料自带逻辑 | 候选顺序打分；CONFIRM 写契约 order_anchors |
| memory | M2 记忆 | 三层记忆，只记显式声明与已闭环结论 | `memory/` 画像与决策 |
| doc_slice | 切片 | 按章切带行号纯文本，供文件交接省 token | chapters/*.txt + manifest |
| spec | 真源 | 读 spec 并校验，段序漂移即 FAIL | spec 回读与校验结果 |

## 数据文件格式（扩展时照此填）

| 文件 | 关键字段 |
|---|---|
| `spec/spec_v0.1.0.json` | `pipeline[]` 段序数组 {id, name, abilities, gate}；段序漂移即 FAIL |
| `contracts/*.contract.json` | contract_id（讲::节）/ section_id（与 HTML 节 id 一致）/ objectives（读者能+可测动词）/ known_terms_ref（名@版本）/ required_elements（what/why/how/cost）/ order_anchors（CONFIRM 写入，ORDER 只读这个）/ version+changelog |
| `vocab/*_known_terms.json` | terms[] + version（追加术语必须 +1）+ changelog |
| `prefs/<讲ID>_prefs.json` | dimensions[]（应用/原理/机制/架构多选）+ audience/level（可选） |
| `inputs/<part>/manifest.json` | materials[] 每项 {id, title, venue, md 相对路径} |
| `inputs/<part>/concept_map.json` | 每概念 {pats:[标题正则], prereq:[先修]}；pats 收紧防泛词；`_` 开头键被忽略 |
| `k1/paper_seeds.json` | 论文种子表（why_background + capability_signal 锚） |
| `k1/tickets.jsonl` | 工单台账 append-only；name+kind+urn 冲突报错不覆盖 |
| `asset_ledger.jsonl` | 素材评估卡：name/layer/src/mechanism/cite/recency/score；条目不可变 |

## 典型工作流

**修订一讲**：构建新稿 → `lecture_lint`（FAIL 清零）→ `pipeline_run --json`（全链含契约）→ 交付。

**给一节上逻辑契约**：marker 抽素材（禁 pdftotext）→ 写 concept_map → EXTRACT → PROPOSE → 作者选定 → CONFIRM 写契约 → ORDER 回读验证。此后 pipeline REVIEW 自动盯顺序。

**添加一个知识点**：完整六步见手册 §17（备素材 → 登记 manifest → 锁词表 → 定顺序 → 写契约 → 组稿过门禁）。

**独立审稿**：`doc_slice` 切片交接 → `rubric_check --export-json` 导待回源清单 → 审稿人全新上下文五动作 → `memory.py LINK_REVIEW` 闭环。

## 常见问题

| 问题 | 答案 |
|---|---|
| ORDER 报 missing？ | 锚词与正文实际写法不一致（如 Leaf-Spine vs Spine-Leaf）；grep 正文确认后改契约 |
| EXTRACT 概念顺序乱？ | 概念表泛词误命中，收紧 pats；确认素材是 marker 抽的而非 pdftotext（双栏混排） |
| RAGFlow 发现层不可用？ | `k1/ragflow.json` 含密钥未随包发布；缺失时自动跳过发现层并提示，不报错 |
| pipeline CONTEXT FAIL？ | 运行中文件被别处改动（doc_stable 检出）；重跑或查并行 agent |
| 讲义允许厂商名吗？ | 允许（讲义体例）；教材相反全禁。两套稿件不互套 |
| 教学结构检查会拦我吗？ | 不会，永久 WARN 不 BLOCK；只有红线类（破折号/外链/自包含）才 FAIL |

## 文档

完整手册见 [`工具手册_Noteleaf.html`](工具手册_Noteleaf.html)（单文件自包含，浏览器直接打开），19 节：

- §1-2 设计哲学 + 六段流水线能力模型
- §3-14 十三个组件逐个详解（方法 + 判据 + CLI + 实测校准记录）
- §15 配套写作方法论（cloud-lecture-writing 与 book-production 两个 skill 的精华：启动铁律 / 事实核查 / 机械清理 / 七条硬门禁 / 六条红线 / 五动作审稿）
- §16 数据文件格式速查
- §17 扩展操作：如何添加知识点（加一节六步 / 加检查规则 / 加素材来源 / 改流水线）
- §18 典型工作流 · §19 排错表

## 设计原则

1. **spec 单一真源**：段序、能力归属、门禁名都写在 spec，不硬编码。
2. **机器只定位，裁决归人**：检查只报「有/没有、过/不过、在哪一行」。
3. **append-only 台账**：素材、工单、决策只追加，同名冲突报错不覆盖。
4. **显式意图**：写作前必须声明偏好与契约，缺项即拦。
5. **纠错转检查**：同一个错只纠正一次，然后写成 lint 规则。

## 许可

内部教学工具。示例素材（FatTree / Jupiter 论文 Markdown）版权归原作者与 ACM 所有，仅作研究学习参考。
