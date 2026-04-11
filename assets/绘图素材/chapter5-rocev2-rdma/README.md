# 第5章 - RoCEv2/RDMA配图

## 5.1 RoCEv2 vs InfiniBand对比图

### 图片说明
对比展示RoCEv2（RDMA over Converged Ethernet v2）和InfiniBand两种RDMA技术在协议栈、部署方式和适用场景上的差异。

### Mermaid图表代码
```mermaid
flowchart TB
    subgraph APP["📱 应用层"]
        direction LR
        APP1["MPI<br/>消息传递"]
        APP2["NVMe-oF<br/>存储访问"]
        APP3["AI框架<br/>PyTorch/TensorFlow"]
    end
    
    subgraph VERBS["🔧 RDMA Verbs API"]
        direction TB
        VERBS_API["标准Verbs接口<br/>Send/Recv/Write/Read/Atomic"]
    end
    
    subgraph IB_STACK["🌀 InfiniBand协议栈"]
        direction TB
        IB_LINK["InfiniBand链路层<br/>原生RDMA支持"]
        IB_NET["IB网络层<br/>子网管理"]
        IB_TRANS["IB传输层<br/>可靠连接/不可靠数据报"]
    end
    
    subgraph ROCE_STACK["🌐 RoCEv2协议栈"]
        direction TB
        ROCE_ETH["以太网链路层<br/>标准以太网设备"]
        ROCE_IP["IP网络层<br/>路由可达"]
        ROCE_UDP["UDP传输层<br/>端口多路复用"]
        ROCE_IBGRH["IB Global Route Header<br/>RDMA扩展"]
    end
    
    subgraph DIFF["📊 关键差异对比"]
        direction TB
        D1["部署成本"]
        D1_IB["IB: 高<br/>专用设备"]
        D1_ROCE["RoCE: 中<br/>复用以太网"]
        
        D2["性能"]
        D2_IB["IB: 极高<br/>专用优化"]
        D2_ROCE["RoCE: 高<br/>接近IB"]
        
        D3["扩展性"]
        D3_IB["IB: 受限于子网<br/>SM管理"]
        D3_ROCE["RoCE: IP路由<br/>跨数据中心"]
        
        D4["拥塞控制"]
        D4_IB["IB: 信用机制<br/>ECN/PFC"]
        D4_ROCE["RoCE: DCQCN<br/>ECN+PFC"]
    end
    
    APP --> VERBS_API
    VERBS_API --> IB_TRANS & ROCE_IBGRH
    IB_TRANS --> IB_NET --> IB_LINK
    ROCE_IBGRH --> ROCE_UDP --> ROCE_IP --> ROCE_ETH
    
    D1 --> D1_IB & D1_ROCE
    D2 --> D2_IB & D2_ROCE
    D3 --> D3_IB & D3_ROCE
    D4 --> D4_IB & D4_ROCE
    
    style IB_STACK fill:#e3f2fd
    style ROCE_STACK fill:#ffccbc
    style APP fill:#c8e6c9
    style VERBS fill:#fff9c4
    style DIFF fill:#f3e5f5
```

### LaTeX引用代码
```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.95\textwidth]{chapter5/rocev2-vs-infiniband.png}
    \caption{RoCEv2与InfiniBand协议栈对比。两者共享Verbs API，但在网络层实现上有差异，RoCEv2更适合大规模数据中心部署。}
    \label{fig:roce-vs-ib}
\end{figure}
```

---

## 5.2 DCQCN拥塞控制流程图

### 图片说明
展示DCQCN（Data Center Quantized Congestion Notification）拥塞控制算法的工作流程，包括CNP（Congestion Notification Packet）的生成和传播机制。

### Mermaid图表代码
```mermaid
sequenceDiagram
    participant S as 发送端<br/>QP
    participant R as 接收端<br/>QP
    participant SW as 交换机<br/>ECN标记
    participant RNIC as RNIC<br/>CNP生成
    
    Note over S,RNIC: DCQCN拥塞控制流程
    
    rect rgb(200, 230, 255)
    Note right of S: 正常传输
    S->>SW: 数据包 (ECN Capable)
    SW->>R: 转发数据包
    R->>S: ACK确认
    end
    
    rect rgb(255, 200, 200)
    Note right of SW: 拥塞检测
    S->>SW: 数据包 (ECN=10)
    Note over SW: 队列长度 > 阈值<br/>设置ECN=11
    SW->>R: 数据包 (ECN=11)
    R->>RNIC: 检测到ECN标记
    end
    
    rect rgb(255, 255, 200)
    Note right of RNIC: CNP反馈
    RNIC->>S: CNP (Congestion Notification Packet)<br/>携带QP信息
    end
    
    rect rgb(200, 255, 200)
    Note right of S: 速率调整
    S->>S: α = (1-g)*α + g<br/>速率减少因子
    S->>S: Target_Rate = Current_Rate<br/>Current_Rate = Current_Rate * (1-α/2)
    Note over S: 发送速率降低<br/>缓解拥塞
    end
    
    rect rgb(230, 230, 255)
    Note right of S: 拥塞恢复
    S->>R: 继续发送(低速率)
    R->>S: ACK确认
    S->>S: 每个ACK增加速率<br/>Timer-based恢复
    S->>S: 逐步恢复至<br/>Target_Rate
    end
```

### LaTeX引用代码
```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.95\textwidth]{chapter5/dcqcn-congestion-control.png}
    \caption{DCQCN拥塞控制流程。交换机通过ECN标记拥塞，接收端生成CNP通知发送端，发送端采用量化的速率调整算法降低发送速率。}
    \label{fig:dcqcn-flow}
\end{figure}
```

---

## 5.3 RDMA数据传输路径图

### 图片说明
展示RDMA（Remote Direct Memory Access）的三种传输操作（Send/Recv、Write、Read）的数据路径，以及与传统TCP/IP的对比。

### Mermaid图表代码
```mermaid
flowchart TB
    subgraph TRADITIONAL["🔴 传统TCP/IP传输"]
        direction TB
        T_APP["应用程序<br/>数据拷贝"]
        T_BUF["Socket Buffer<br/>内核空间拷贝"]
        T_TCP["TCP/IP协议栈<br/>处理开销"]
        T_NIC["网卡<br/>DMA传输"]
        T_NET["网络"]
        
        T_APP -->|内存拷贝| T_BUF -->|协议处理| T_TCP -->|DMA| T_NIC --> T_NET
    end
    
    subgraph RDMA_SEND["🟢 RDMA Send/Recv"]
        direction TB
        S_APP["发送应用<br/>Post Send"]
        S_QP["发送队列<br/>Send Queue"]
        S_NIC["RNIC<br/>DMA读取本地内存"]
        S_NET["网络传输"]
        R_NIC["接收RNIC<br/>DMA写入远程内存"]
        R_CQ["完成队列<br/>Completion Queue"]
        R_APP["接收应用<br/>Get Completion"]
        
        S_APP --> S_QP --> S_NIC --> S_NET --> R_NIC --> R_CQ --> R_APP
    end
    
    subgraph RDMA_WRITE["🔵 RDMA Write (One-sided)"]
        direction TB
        W_APP["发送应用<br/>准备数据"]
        W_REG["内存注册<br/>MR: Memory Region"]
        W_RKEY["R_Key交换<br/>远程访问密钥"]
        W_OP["Post RDMA Write<br/>指定远程地址"]
        W_NIC["RNIC直接写入<br/>远程内存"]
        W_ACK["ACK确认<br/>可选完成通知"]
        
        W_APP --> W_REG --> W_RKEY --> W_OP --> W_NIC --> W_ACK
    end
    
    subgraph RDMA_READ["🟣 RDMA Read (One-sided)"]
        direction TB
        RD_APP["读取应用<br/>Post RDMA Read"]
        RD_ADDR["远程地址<br/>+ R_Key"]
        RD_NIC["RNIC直接读取<br/>远程内存"]
        RD_LOCAL["本地内存<br/>数据存放"]
        RD_COMP["完成通知<br/>数据可用"]
        
        RD_APP --> RD_ADDR --> RD_NIC --> RD_LOCAL --> RD_COMP
    end
    
    style TRADITIONAL fill:#ffccbc
    style RDMA_SEND fill:#c8e6c9
    style RDMA_WRITE fill:#e3f2fd
    style RDMA_READ fill:#f3e5f5
```

### LaTeX引用代码
```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.95\textwidth]{chapter5/rdma-data-path.png}
    \caption{RDMA数据传输路径对比。传统TCP/IP需要多次内存拷贝和内核介入，RDMA通过内核旁路实现零拷贝传输，大幅降低延迟和CPU开销。}
    \label{fig:rdma-path}
\end{figure}
```

---

## 5.4 负载均衡技术演进图

### 图片说明
展示数据中心网络负载均衡技术的演进历程，从传统的ECMP到现代的Packet Spraying、Conga、Letflow等技术。

### Mermaid图表代码
```mermaid
timeline
    title 数据中心负载均衡技术演进
    
    section 2010-2013
        ECMP : 等价多路径路由
             : 基于流的哈希
             : 大象流问题
             : 无法适应链路不均
    
    section 2014-2016
        MPTCP : 多路径TCP
              : 子流级负载均衡
              : 需要端侧修改
              : 部署复杂
        
        CONGA : 数据中心网络拥塞感知
              : Leaf-Spine架构优化
              : 分布式流量调度
              : 需专用硬件支持
    
    section 2017-2019
        HULA : 利用链路状态的自适应
             : 每跳可编程
             : 快速收敛
             : 状态开销较大
        
        Letflow : 基于let时间的流切片
                : 减少交换机状态
                : 低开销高效果
                : 适应突发流量
    
    section 2020-2024
        Packet Spraying : 包级喷洒
                        : 极致负载均衡
                        : 需乱序重排
                        : 现代交换机支持
        
        P4可编程 : 自定义负载均衡
                : 应用感知调度
                : 灵活策略部署
                : 硬件可编程
```

### LaTeX引用代码
```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.95\textwidth]{chapter5/load-balancing-evolution.png}
    \caption{数据中心负载均衡技术演进时间线。从基于流的ECMP到包级喷洒，负载均衡粒度不断细化，适应AI训练等大带宽需求场景。}
    \label{fig:lb-evolution}
\end{figure}
```

---

## 本章配图清单

| 序号 | 图号 | 图名 | 文件路径 |
|------|------|------|----------|
| 5.1 | Fig 5.1 | RoCEv2与InfiniBand对比 | chapter5/rocev2-vs-infiniband.png |
| 5.2 | Fig 5.2 | DCQCN拥塞控制流程 | chapter5/dcqcn-congestion-control.png |
| 5.3 | Fig 5.3 | RDMA数据传输路径 | chapter5/rdma-data-path.png |
| 5.4 | Fig 5.4 | 负载均衡技术演进 | chapter5/load-balancing-evolution.png |
