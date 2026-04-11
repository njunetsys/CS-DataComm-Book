# 书籍配图素材总索引

本目录包含书籍新增章节的所有配图素材，使用Mermaid语法编写，可转换为各种格式的图片。

## 目录结构

```
book-project/assets/绘图素材/
├── chapter3-dsf-bag/          # 第3章 - DSF/BAG架构配图
├── chapter4-p4-dpu-cxl/       # 第4章 - P4/DPU/CXL配图
├── chapter5-rocev2-rdma/      # 第5章 - RoCEv2/RDMA配图
├── chapter6-ai-network/       # 第6章 - AI训练网络配图
├── chapter7-green-computing/  # 第7章 - 绿色计算配图
├── README.md                  # 本文件
└── latex-references.tex       # LaTeX图片引用汇总
```

## 章节配图清单

### 第3章 - DSF/BAG架构配图

| 图号 | 图名 | 关键内容 |
|------|------|----------|
| Fig 3.1 | DSF双域架构示意图 | 以太网域与交换结构域的分层设计 |
| Fig 3.2 | DSF核心组件架构 | IN(RDSW)和FN(FDSW)的互联关系 |
| Fig 3.3 | BAG跨区域互联架构 | 超级脊层连接多数据中心 |
| Fig 3.4 | 包喷洒技术示意图 | 多路径传输和负载均衡 |

### 第4章 - P4/DPU/CXL配图

| 图号 | 图名 | 关键内容 |
|------|------|----------|
| Fig 4.1 | P4可编程数据平面架构 | 解析器、匹配-动作表、控制流 |
| Fig 4.2 | DPU架构与异构计算协作 | CPU/DPU/GPU协作关系 |
| Fig 4.3 | CXL内存扩展架构 | CXL三种设备类型和协议栈 |
| Fig 4.4 | eBPF+Cilium数据路径 | 内核各层hook点和数据包处理流程 |

### 第5章 - RoCEv2/RDMA配图

| 图号 | 图名 | 关键内容 |
|------|------|----------|
| Fig 5.1 | RoCEv2与InfiniBand对比 | 协议栈差异和部署考量 |
| Fig 5.2 | DCQCN拥塞控制流程 | CNP生成和速率调整机制 |
| Fig 5.3 | RDMA数据传输路径 | Send/Write/Read三种操作对比 |
| Fig 5.4 | 负载均衡技术演进 | ECMP到Packet Spraying的发展历程 |

### 第6章 - AI训练网络配图

| 图号 | 图名 | 关键内容 |
|------|------|----------|
| Fig 6.1 | BAG跨区域互联拓扑 | 多区域数据中心互联架构 |
| Fig 6.2 | DSF三级扩展架构 | L1/L2/L3三级扩展能力 |
| Fig 6.3 | AI训练集群网络架构全景 | 前端/后端网络分离设计 |
| Fig 6.4 | 性能优化工具链 | 监控-分析-优化-自动化闭环 |

### 第7章 - 绿色计算配图

| 图号 | 图名 | 关键内容 |
|------|------|----------|
| Fig 7.1 | 数据中心PUE优化示意图 | PUE计算和优化方向 |
| Fig 7.2 | 液冷技术架构对比图 | 冷板式vs浸没式液冷 |
| Fig 7.3 | 可再生能源应用架构 | 太阳能、风能、储能系统 |
| Fig 7.4 | Meta可持续发展时间线 | 2011-2024里程碑事件 |

## 使用方法

### 1. 转换为图片

#### 使用Mermaid CLI
```bash
# 安装Mermaid CLI
npm install -g @mermaid-js/mermaid-cli

# 转换单个图表
mmdc -i input.mmd -o output.png

# 批量转换
for f in */*.mmd; do mmdc -i "$f" -o "${f%.mmd}.png"; done
```

#### 使用在线工具
- [Mermaid Live Editor](https://mermaid.live/)
- [Mermaid.ink](https://mermaid.ink/)

### 2. 嵌入LaTeX文档

所有图片已提供LaTeX引用代码，直接复制到文档中即可。示例：

```latex
\usepackage{graphicx}
\usepackage{float}

% 在正文中引用
如图~\ref{fig:dsf-dual-domain}所示，DSF采用双域架构...

% 图片插入代码
\begin{figure}[H]
    \centering
    \includegraphics[width=0.9\textwidth]{chapter3/dsf-dual-domain.png}
    \caption{DSF双域架构示意图。以太网域提供传统网络服务，交换结构域提供超低延迟的调度fabric。}
    \label{fig:dsf-dual-domain}
\end{figure}
```

### 3. 修改和定制

所有图表使用Mermaid语法，可直接编辑修改：
- 修改节点文字：直接编辑引号内内容
- 调整颜色：修改`fill:#颜色代码`
- 调整布局：修改`direction TB/LR/RL/BT`

## 配色方案

| 用途 | 颜色代码 | 说明 |
|------|----------|------|
| 核心组件 | `#e3f2fd` | 浅蓝色 |
| 网络/连接 | `#ffccbc` | 浅橙色 |
| 计算/处理 | `#c8e6c9` | 浅绿色 |
| 存储/数据 | `#fff9c4` | 浅黄色 |
| 控制/管理 | `#f3e5f5` | 浅紫色 |
| 背景/辅助 | `#e1f5fe` | 天蓝色 |

## 版本信息

- 创建日期：2026-03-21
- Mermaid版本：10.x
- 共包含：20幅架构图
- 覆盖章节：第3、4、5、6、7章
