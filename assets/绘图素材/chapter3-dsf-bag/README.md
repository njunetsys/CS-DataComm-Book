# 第3章 - DSF/BAG架构配图

## 3.1 DSF双域架构图

### 图片说明
展示DSF（Disaggregated Scheduled Fabric）的双域架构设计，包括以太网域（Ethernet Domain）和交换结构域（Switching Fabric Domain）的分层结构和互联关系。

### Mermaid图表代码
```mermaid
flowchart TB
    subgraph SERVERS["🖥️ 服务器层"]
        direction LR
        S1["服务器1<br/>GPU/TPU/CPU"]
        S2["服务器2<br/>GPU/TPU/CPU"]
        S3["服务器N<br/>GPU/TPU/CPU"]
    end
    
    subgraph ETH_DOMAIN["🌐 以太网域 Ethernet Domain"]
        direction TB
        TOR1["ToR Switch<br/>Top of Rack"]
        AGGR1["聚合层<br/>Aggregation"]
        CORE1["核心层<br/>Core"]
    end
    
    subgraph FABRIC_DOMAIN["⚡ 交换结构域 Switching Fabric Domain"]
        direction TB
        IN["IN - Interface Node<br/>RDSW: Rack Direct Switch"]
        FN["FN - Fabric Node<br/>FDSW: Fabric Direct Switch"]
        IN_OUT["对外接口<br/>External Links"]
    end
    
    subgraph EXTERNAL["🌍 外部网络"]
        direction TB
        EXT1["数据中心互连<br/>DCI"]
        EXT2["互联网接入<br/>Internet"]
    end
    
    SERVERS -->|以太网| TOR1
    TOR1 --> AGGR1 --> CORE1
    CORE1 <-->|控制平面| IN
    SERVERS -->|高速链路| IN
    IN <-->|Fabric Links| FN
    FN --> IN_OUT --> EXTERNAL
    
    style ETH_DOMAIN fill:#e3f2fd
    style FABRIC_DOMAIN fill:#ffccbc
    style SERVERS fill:#c8e6c9
    style EXTERNAL fill:#fff9c4
```

### LaTeX引用代码
```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.95\textwidth]{chapter3/dsf-dual-domain.png}
    \caption{DSF双域架构示意图。以太网域提供传统网络服务，交换结构域提供超低延迟的调度 fabric，两者协同工作。}
    \label{fig:dsf-dual-domain}
\end{figure}
```

---

## 3.2 DSF组件图

### 图片说明
详细展示DSF架构中的核心组件：接口节点IN（Interface Node，使用RDSW）和Fabric节点FN（Fabric Node，使用FDSW）之间的互联关系和数据流向。

### Mermaid图表代码
```mermaid
flowchart TB
    subgraph SERVER["🖥️ 服务器节点"]
        direction TB
        NIC["NIC<br/>网络接口卡<br/>100G/200G/400G"]
        GPU["GPU/TPU<br/>计算加速器"]
    end
    
    subgraph IN["🔌 IN - Interface Node (RDSW)"]
        direction TB
        IN_PORTS["下行端口<br/>服务器连接<br/>64x400G"]
        IN_FABRIC["Fabric端口<br/>交换结构连接<br/>32x800G"]
        IN_CTRL["控制平面<br/>与以太网域交互"]
    end
    
    subgraph FN["⚡ FN - Fabric Node (FDSW)"]
        direction TB
        FN_PORTS["Fabric端口<br/>全互联<br/>64x800G"]
        FN_SCHED["调度引擎<br/>VOQ/信用机制"]
        FN_ROUTING["路由表<br/>快速转发"]
    end
    
    subgraph OTHER_IN["🔗 其他IN节点"]
        direction LR
        IN2["IN-2"]
        IN3["IN-3"]
        INN["IN-N"]
    end
    
    NIC -->|物理链路| IN_PORTS
    GPU -.->|DMA| NIC
    IN_PORTS --> IN_FABRIC --> FN_PORTS
    FN_PORTS <-->|全连接| OTHER_IN
    FN_SCHED --> FN_PORTS
    
    style IN fill:#e3f2fd
    style FN fill:#ffccbc
    style SERVER fill:#c8e6c9
    style OTHER_IN fill:#f3e5f5
```

### LaTeX引用代码
```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.95\textwidth]{chapter3/dsf-components.png}
    \caption{DSF核心组件架构。IN（RDSW）负责服务器接入，FN（FDSW）负责高速交换，通过VOQ调度实现无阻塞传输。}
    \label{fig:dsf-components}
\end{figure}
```

---

## 3.3 BAG架构拓扑图

### 图片说明
展示BAG（Backend Aggregation Group）架构的跨区域互联设计，包括超级脊层（Super-Spine）如何连接多个数据中心的DSF fabric。

### Mermaid图表代码
```mermaid
flowchart TB
    subgraph DC1["🏢 数据中心 1"]
        direction TB
        D1_DSF["DSF Fabric"]
        D1_IN1["IN-1"]
        D1_IN2["IN-2"]
        D1_INN["IN-N"]
        D1_DSF --> D1_IN1 & D1_IN2 & D1_INN
    end
    
    subgraph DC2["🏢 数据中心 2"]
        direction TB
        D2_DSF["DSF Fabric"]
        D2_IN1["IN-1"]
        D2_IN2["IN-2"]
        D2_INN["IN-N"]
        D2_DSF --> D2_IN1 & D2_IN2 & D2_INN
    end
    
    subgraph DC3["🏢 数据中心 3"]
        direction TB
        D3_DSF["DSF Fabric"]
        D3_IN1["IN-1"]
        D3_IN2["IN-2"]
        D3_INN["IN-N"]
        D3_DSF --> D3_IN1 & D3_IN2 & D3_INN
    end
    
    subgraph BAG["🌐 BAG - Backend Aggregation Group"]
        direction TB
        SS1["Super-Spine-1<br/>超级脊层节点"]
        SS2["Super-Spine-2<br/>超级脊层节点"]
        SS3["Super-Spine-N<br/>超级脊层节点"]
    end
    
    D1_IN1 & D1_IN2 & D1_INN -->|长距链路| BAG
    D2_IN1 & D2_IN2 & D2_INN -->|长距链路| BAG
    D3_IN1 & D3_IN2 & D3_INN -->|长距链路| BAG
    
    style DC1 fill:#e3f2fd
    style DC2 fill:#e8f5e9
    style DC3 fill:#fff3e0
    style BAG fill:#ffccbc
```

### LaTeX引用代码
```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.95\textwidth]{chapter3/bag-topology.png}
    \caption{BAG跨区域互联架构。多个数据中心的DSF通过BAG超级脊层互联，形成大规模AI训练网络。}
    \label{fig:bag-topology}
\end{figure}
```

---

## 3.4 包喷洒示意图

### 图片说明
展示DSF架构中的包喷洒（Packet Spraying）技术，包括数据包如何在多条路径上分布传输以实现负载均衡。

### Mermaid图表代码
```mermaid
flowchart LR
    subgraph SOURCE["📤 源节点"]
        direction TB
        FLOW["数据流<br/>Flow ABC"]
        PKT1["包1"]
        PKT2["包2"]
        PKT3["包3"]
        PKT4["包4"]
        FLOW --> PKT1 & PKT2 & PKT3 & PKT4
    end
    
    subgraph SPRAY["🎯 包喷洒引擎"]
        direction TB
        HASH["负载均衡器<br/>Flowlet/Packet spraying"]
        PATH1["路径1"]
        PATH2["路径2"]
        PATH3["路径3"]
        HASH --> PATH1 & PATH2 & PATH3
    end
    
    subgraph NETWORK["🌐 多路径网络"]
        direction TB
        LINK1["链路1<br/>延迟: 2μs"]
        LINK2["链路2<br/>延迟: 3μs"]
        LINK3["链路3<br/>延迟: 2.5μs"]
    end
    
    subgraph REORDER["🔄 重排序缓冲"]
        direction TB
        BUF["VOQ缓冲区<br/>按序重组"]
    end
    
    subgraph DEST["📥 目的节点"]
        direction TB
        RECV["接收队列<br/>有序数据流"]
    end
    
    PKT1 --> HASH --> PATH1 --> LINK1 --> BUF
    PKT2 --> HASH --> PATH2 --> LINK2 --> BUF
    PKT3 --> HASH --> PATH3 --> LINK3 --> BUF
    PKT4 --> HASH --> PATH1 --> LINK1 --> BUF
    BUF --> RECV
    
    style SOURCE fill:#c8e6c9
    style SPRAY fill:#fff9c4
    style NETWORK fill:#e3f2fd
    style REORDER fill:#ffccbc
    style DEST fill:#f3e5f5
```

### LaTeX引用代码
```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.95\textwidth]{chapter3/packet-spraying.png}
    \caption{包喷洒技术示意图。通过将数据流分散到多条路径传输，提高网络利用率和避免拥塞，接收端通过VOQ缓冲区重排序。}
    \label{fig:packet-spraying}
\end{figure}
```

---

## 本章配图清单

| 序号 | 图号 | 图名 | 文件路径 |
|------|------|------|----------|
| 3.1 | Fig 3.1 | DSF双域架构示意图 | chapter3/dsf-dual-domain.png |
| 3.2 | Fig 3.2 | DSF核心组件架构 | chapter3/dsf-components.png |
| 3.3 | Fig 3.3 | BAG跨区域互联架构 | chapter3/bag-topology.png |
| 3.4 | Fig 3.4 | 包喷洒技术示意图 | chapter3/packet-spraying.png |
