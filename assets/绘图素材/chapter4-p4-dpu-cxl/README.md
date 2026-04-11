# 第4章 - P4/DPU/CXL配图

## 4.1 P4可编程数据平面架构图

### 图片说明
展示P4（Programming Protocol-independent Packet Processors）语言定义的编程数据平面架构，包括解析器、匹配-动作表、控制流和反解析器等核心组件。

### Mermaid图表代码
```mermaid
flowchart LR
    subgraph INGRESS["📥 入站处理"]
        direction TB
        PARSER["📝 解析器 Parser<br/>识别包头字段<br/>提取关键信息"]
        
        subgraph MA_TABLES["🎯 匹配-动作表 Match-Action"]
            direction TB
            T1["表1: L2转发<br/>匹配: MAC地址<br/>动作: 转发/泛洪"]
            T2["表2: L3路由<br/>匹配: IP前缀<br/>动作: 下一跳/丢弃"]
            T3["表3: ACL<br/>匹配: 五元组<br/>动作: 允许/拒绝"]
            T4["表4: 自定义<br/>用户定义逻辑"]
        end
        
        CONTROL["🎮 控制流 Control Flow<br/>定义表处理顺序"]
        DEPARSER["✍️ 反解析器 Deparser<br/>重组数据包"]
    end
    
    subgraph EGRESS["📤 出站处理"]
        direction TB
        E_PIPE["出站流水线<br/>队列调度<br/>拥塞控制"]
        E_BUFF["缓冲区管理<br/>优先级队列"]
    end
    
    subgraph P4C["🔧 P4编译器"]
        direction TB
        P4CODE["P4源代码<br/>用户定义逻辑"]
        FRONTEND["前端<br/>语法分析"]
        MIDEND["中端<br/>优化转换"]
        BACKEND["后端<br/>目标代码生成"]
    end
    
    PARSER --> CONTROL
    CONTROL --> T1 --> T2 --> T3 --> T4
    T4 --> DEPARSER
    DEPARSER --> E_PIPE --> E_BUFF
    
    P4CODE --> FRONTEND --> MIDEND --> BACKEND
    BACKEND -.->|生成| INGRESS
    
    style INGRESS fill:#e3f2fd
    style MA_TABLES fill:#fff9c4
    style EGRESS fill:#ffccbc
    style P4C fill:#c8e6c9
```

### LaTeX引用代码
```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.95\textwidth]{chapter4/p4-programmable-plane.png}
    \caption{P4可编程数据平面架构。通过P4语言定义数据包处理逻辑，编译后部署到可编程交换机或智能网卡。}
    \label{fig:p4-architecture}
\end{figure}
```

---

## 4.2 DPU架构示意图

### 图片说明
展示DPU（Data Processing Unit）的架构设计，以及CPU、DPU、GPU之间的协作关系，体现"卸载-加速-隔离"的设计理念。

### Mermaid图表代码
```mermaid
flowchart TB
    subgraph HOST["🖥️ 主机系统"]
        direction TB
        CPU["🔲 CPU<br/>通用计算<br/>业务逻辑控制"]
        MEM["💾 主机内存<br/>DDR4/DDR5"]
        NVME["💿 NVMe SSD<br/>高速存储"]
    end
    
    subgraph DPU["⚡ DPU - Data Processing Unit"]
        direction TB
        ARM["🧠 ARM核心<br/>管理控制平面<br/>Linux/OS"]
        
        subgraph ACCEL["🚀 加速引擎"]
            direction LR
            CRYPTO["加密<br/>TLS/IPSec"]
            COMPRESS["压缩<br/>解压缩"]
            REGEX["正则<br/>深度检测"]
            NVMEO["NVMe-oF<br/>存储卸载"]
        end
        
        NIC["🌐 智能网卡<br/>网络处理"]
        DPU_MEM["💾 DPU内存<br/>HBM/DDR"]
    end
    
    subgraph GPU["🎮 GPU集群"]
        direction TB
        G1["GPU-1"]
        G2["GPU-2"]
        GN["GPU-N"]
    end
    
    subgraph NETWORK["🌍 外部网络"]
        direction TB
        NET1["25G/100G/200G<br/>以太网/RDMA"]
    end
    
    CPU <-->|PCIe Gen4/5| DPU
    CPU <-->|传统模式<br/>也可走DPU| GPU
    DPU <-->|直接访问| GPU
    DPU <-->|网络卸载| NETWORK
    
    ARM --> ACCEL --> NIC
    
    style HOST fill:#e3f2fd
    style DPU fill:#ffccbc
    style ACCEL fill:#fff9c4
    style GPU fill:#c8e6c9
    style NETWORK fill:#f3e5f5
```

### LaTeX引用代码
```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.95\textwidth]{chapter4/dpu-architecture.png}
    \caption{DPU架构与异构计算协作。DPU承担网络、存储、安全等基础设施任务，释放CPU和GPU专注于业务计算。}
    \label{fig:dpu-architecture}
\end{figure}
```

---

## 4.3 CXL内存扩展架构图

### 图片说明
展示CXL（Compute Express Link）技术如何实现内存扩展和池化，包括CXL三种协议类型（CXL.io、CXL.cache、CXL.memory）的应用场景。

### Mermaid图表代码
```mermaid
flowchart TB
    subgraph ROOT["🔲 根复合体 Root Complex"]
        direction TB
        HOST_CPU["Host CPU<br/>处理器和本地内存"]
        CXL_CTRL["CXL控制器<br/>协议转换"]
    end
    
    subgraph CXL_SWITCH["🔄 CXL交换机"]
        direction TB
        SW_PORTS["多端口交换<br/>内存一致性保证"]
    end
    
    subgraph TYPE1["💾 CXL Type 1 - 缓存设备"]
        direction TB
        T1_NIC["智能网卡/加速器<br/>带缓存<br/>CXL.cache协议"]
    end
    
    subgraph TYPE2["🎮 CXL Type 2 - 内存加速器"]
        direction TB
        T2_GPU["GPU/FPGA<br/>自有内存<br/>CXL.cache + CXL.memory"]
    end
    
    subgraph TYPE3["📦 CXL Type 3 - 内存扩展"]
        direction TB
        T3_MEM["内存扩展卡<br/>纯内存设备<br/>CXL.memory协议"]
        MEM_POOL["内存池化<br/>动态分配"]
    end
    
    subgraph PROTOCOLS["📋 CXL协议栈"]
        direction TB
        IO["CXL.io<br/>IO协议兼容PCIe"]
        CACHE["CXL.cache<br/>缓存一致性"]
        MEM["CXL.memory<br/>内存访问"]
    end
    
    HOST_CPU --> CXL_CTRL
    CXL_CTRL -->|PCIe物理层| CXL_SWITCH
    CXL_SWITCH --> TYPE1
    CXL_SWITCH --> TYPE2
    CXL_SWITCH --> TYPE3
    TYPE3 --> MEM_POOL
    
    style ROOT fill:#e3f2fd
    style CXL_SWITCH fill:#fff9c4
    style TYPE1 fill:#c8e6c9
    style TYPE2 fill:#ffccbc
    style TYPE3 fill:#f3e5f5
    style PROTOCOLS fill:#e1f5fe
```

### LaTeX引用代码
```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.95\textwidth]{chapter4/cxl-memory-expansion.png}
    \caption{CXL内存扩展架构。通过CXL协议实现内存池化、设备缓存一致性和异构内存扩展，突破单节点内存限制。}
    \label{fig:cxl-architecture}
\end{figure}
```

---

## 4.4 eBPF+Cilium数据路径图

### 图片说明
展示eBPF（Extended Berkeley Packet Filter）和Cilium如何实现高性能的容器网络安全和可观测性，包括数据路径和关键hook点。

### Mermaid图表代码
```mermaid
flowchart TB
    subgraph KERNEL["🐧 Linux内核"]
        direction TB
        
        subgraph INGRESS_PATH["📥 入站数据路径"]
            direction TB
            HOOK_XDP["🔴 XDP Hook<br/>驱动层<br/>最早处理点<br/>快速丢弃/DDoS防护"]
            HOOK_TC_INGRESS["🟡 TC Ingress<br/>流量控制层<br/>策略执行"]
            HOOK_SKB["🟢 Socket Buffer<br/>协议栈处理"]
        end
        
        subgraph EBPF_PROG["🔧 eBPF程序"]
            direction LR
            PROG_L3["L3处理<br/>路由查找"]
            PROG_L4["L4处理<br/>NAT/负载均衡"]
            PROG_L7["L7代理<br/>HTTP/gRPC"]
            PROG_OBS["观测<br/>监控/追踪"]
        end
        
        subgraph EGRESS_PATH["📤 出站数据路径"]
            direction TB
            HOOK_TC_EGRESS["🟡 TC Egress<br/>流量控制层<br/>出站策略"]
            HOOK_CGROUP["🔵 Cgroup<br/>套接字层<br/>连接管理"]
        end
        
        MAPS["🗺️ eBPF Maps<br/>状态存储<br/>策略表/连接跟踪"]
    end
    
    subgraph CILIUM["🐝 Cilium控制平面"]
        direction TB
        AGENT["Cilium Agent<br/>策略管理"]
        ENDPOINTS["端点管理<br/>Pod标签映射"]
        IDENTITY["身份系统<br/>Security Identity"]
        PROXY["L7代理<br/>Envoy集成"]
    end
    
    subgraph CONTAINER["📦 容器/Pod"]
        direction TB
        POD1["Pod A"]
        POD2["Pod B"]
        POD3["Pod C"]
    end
    
    INGRESS_PATH --> EBPF_PROG --> EGRESS_PATH
    EBPF_PROG <-->|读写| MAPS
    CILIUM -->|编译加载| EBPF_PROG
    CILIUM -->|管理| MAPS
    HOOK_CGROUP --> CONTAINER
    
    style KERNEL fill:#e3f2fd
    style EBPF_PROG fill:#fff9c4
    style CILIUM fill:#c8e6c9
    style CONTAINER fill:#ffccbc
    style MAPS fill:#f3e5f5
```

### LaTeX引用代码
```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.95\textwidth]{chapter4/ebpf-cilium-datapath.png}
    \caption{eBPF+Cilium数据路径架构。利用eBPF在内核关键路径插入自定义逻辑，实现高性能的网络策略执行和可观测性。}
    \label{fig:ebpf-cilium}
\end{figure}
```

---

## 本章配图清单

| 序号 | 图号 | 图名 | 文件路径 |
|------|------|------|----------|
| 4.1 | Fig 4.1 | P4可编程数据平面架构 | chapter4/p4-programmable-plane.png |
| 4.2 | Fig 4.2 | DPU架构与异构计算协作 | chapter4/dpu-architecture.png |
| 4.3 | Fig 4.3 | CXL内存扩展架构 | chapter4/cxl-memory-expansion.png |
| 4.4 | Fig 4.4 | eBPF+Cilium数据路径 | chapter4/ebpf-cilium-datapath.png |
