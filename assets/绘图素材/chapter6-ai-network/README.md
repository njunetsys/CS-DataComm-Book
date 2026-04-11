# 第6章 - AI训练网络配图

## 6.1 BAG跨区域互联拓扑图

### 图片说明
展示BAG（Backend Aggregation Group）架构如何实现多个地理分布的数据中心互联，支持大规模分布式AI训练。

### Mermaid图表代码
```mermaid
flowchart TB
    subgraph REGION1["🌍 区域1 - 数据中心集群"]
        direction TB
        R1_DC1["🏢 DC-1A<br/>32K GPU"]
        R1_DC2["🏢 DC-1B<br/>32K GPU"]
        R1_BSW["区域骨干交换<br/>Regional Backbone"]
        R1_DCI["DCI网关<br/>长距互联"]
        R1_DC1 & R1_DC2 --> R1_BSW --> R1_DCI
    end
    
    subgraph REGION2["🌍 区域2 - 数据中心集群"]
        direction TB
        R2_DC1["🏢 DC-2A<br/>32K GPU"]
    R2_DC2["🏢 DC-2B<br/>32K GPU"]
        R2_BSW["区域骨干交换<br/>Regional Backbone"]
        R2_DCI["DCI网关<br/>长距互联"]
        R2_DC1 & R2_DC2 --> R2_BSW --> R2_DCI
    end
    
    subgraph REGION3["🌍 区域3 - 数据中心集群"]
        direction TB
        R3_DC1["🏢 DC-3A<br/>32K GPU"]
        R3_DC2["🏢 DC-3B<br/>32K GPU"]
        R3_BSW["区域骨干交换<br/>Regional Backbone"]
        R3_DCI["DCI网关<br/>长距互联"]
        R3_DC1 & R3_DC2 --> R3_BSW --> R3_DCI
    end
    
    subgraph BAG["🌐 BAG - Backend Aggregation Group"]
        direction TB
        BAG_SS1["Super-Spine-1<br/>超脊层交换"]
        BAG_SS2["Super-Spine-2<br/>超脊层交换"]
        BAG_SS3["Super-Spine-N<br/>超脊层交换"]
        
        subgraph BAG_CTRL["控制平面"]
            CTRL1["拓扑管理"]
            CTRL2["流量工程"]
            CTRL3["故障恢复"]
        end
    end
    
    R1_DCI -->|长距链路<br/>400G/800G| BAG
    R2_DCI -->|长距链路<br/>400G/800G| BAG
    R3_DCI -->|长距链路<br/>400G/800G| BAG
    
    BAG_SS1 & BAG_SS2 & BAG_SS3 --> CTRL1 & CTRL2 & CTRL3
    
    style REGION1 fill:#e3f2fd
    style REGION2 fill:#e8f5e9
    style REGION3 fill:#fff3e0
    style BAG fill:#ffccbc
    style BAG_CTRL fill:#f3e5f5
```

### LaTeX引用代码
```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.95\textwidth]{chapter6/bag-interconnect.png}
    \caption{BAG跨区域互联拓扑。通过BAG超级脊层连接多个区域的数据中心，实现跨地域的大规模AI训练集群。}
    \label{fig:bag-interconnect}
\end{figure}
```

---

## 6.2 DSF三级扩展架构图

### 图片说明
展示DSF（Disaggregated Scheduled Fabric）的三级扩展架构：L1（机架内）、L2（集群内）、L3（跨集群）。

### Mermaid图表代码
```mermaid
flowchart TB
    subgraph L1["🏗️ L1 - 机架内扩展<br/>Intra-Rack"]
        direction TB
        L1_SVR["服务器节点<br/>GPU/TPU/CPU"]
        L1_TOR["ToR Switch<br/>Top of Rack"]
        L1_IN["IN - Interface Node<br/>RDSW接入"]
        
        L1_SVR -->|PCIE/NVLink| L1_SVR
        L1_SVR -->|100G/200G| L1_TOR
        L1_SVR -->|400G| L1_IN
    end
    
    subgraph L2["🏢 L2 - 集群内扩展<br/>Intra-Cluster"]
        direction TB
        L2_RACK1["机架组1<br/>L1 Fabric"]
        L2_RACK2["机架组2<br/>L1 Fabric"]
        L2_RACKN["机架组N<br/>L1 Fabric"]
        L2_FN["FN - Fabric Node<br/>FDSW交换层"]
        
        L2_RACK1 & L2_RACK2 & L2_RACKN -->|800G| L2_FN
    end
    
    subgraph L3["🌍 L3 - 跨集群扩展<br/>Inter-Cluster"]
        direction TB
        L3_CLUSTER1["集群1<br/>完整DSF"]
        L3_CLUSTER2["集群2<br/>完整DSF"]
        L3_CLUSTERN["集群N<br/>完整DSF"]
        L3_BAG["BAG层<br/>Super-Spine"]
        
        L3_CLUSTER1 & L3_CLUSTER2 & L3_CLUSTERN -->|800G/1.6T| L3_BAG
    end
    
    subgraph SCALE["📈 扩展能力"]
        direction TB
        S1["L1: 64-128 GPU/机架"]
        S2["L2: 4K-16K GPU/集群"]
        S3["L3: 100K+ GPU/系统"]
    end
    
    L1 --> L2 --> L3
    L1 -.-> S1
    L2 -.-> S2
    L3 -.-> S3
    
    style L1 fill:#c8e6c9
    style L2 fill:#e3f2fd
    style L3 fill:#ffccbc
    style SCALE fill:#fff9c4
```

### LaTeX引用代码
```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.95\textwidth]{chapter6/dsf-three-tier.png}
    \caption{DSF三级扩展架构。L1实现机架内高速互联，L2实现集群内全连接，L3通过BAG实现跨集群扩展，支持百万级GPU规模。}
    \label{fig:dsf-tiers}
\end{figure}
```

---

## 6.3 AI训练集群网络架构全景图

### 图片说明
展示大规模AI训练集群的完整网络架构，包括前端网络（管理/存储）、后端网络（训练/计算）、以及各种网络平面之间的关系。

### Mermaid图表代码
```mermaid
flowchart TB
    subgraph FRONTEND["🌐 前端网络 Frontend"]
        direction TB
        FE_ADMIN["管理平面<br/>BMC/IPMI"]
        FE_STORAGE["存储网络<br/>NFS/Object"]
        FE_USER["用户接入<br/>SSH/Jupyter"]
        FE_OOB["带外管理<br/>OOB Network"]
    end
    
    subgraph COMPUTE["🖥️ 计算节点"]
        direction TB
        NODE["GPU服务器"]
        CPU["Host CPU<br/>管理/协调"]
        GPU0["GPU-0"]
        GPU1["GPU-1"]
        GPU7["GPU-7"]
        NIC_FE["前端网卡<br/>25G/100G"]
        NIC_BE["后端网卡<br/>200G/400G"]
        
        NODE --> CPU --> GPU0 & GPU1 & GPU7
        CPU --> NIC_FE
        GPU0 --> NIC_BE
    end
    
    subgraph BACKEND["⚡ 后端网络 Backend"]
        direction TB
        BE_TOR["ToR Switch<br/>接入层"]
        BE_AGG["Aggregation<br/>汇聚层"]
        BE_SPINE["Spine<br/>骨干层"]
        BE_DSF["DSF Fabric<br/>调度Fabric"]
        BE_BAG["BAG<br/>跨区域互联"]
    end
    
    subgraph STORAGE["💾 存储系统"]
        direction TB
        ST_PARALLEL["并行文件系统<br/>Lustre/GPFS"]
        ST_OBJ["对象存储<br/>S3兼容"]
        ST_LOCAL["本地NVMe<br/>高速缓存"]
    end
    
    subgraph ORCH["🎮 编排管理"]
        direction TB
        K8S["Kubernetes<br/>容器编排"]
        SLURM["Slurm<br/>作业调度"]
        MONITOR["监控告警<br/>Prometheus/Grafana"]
    end
    
    FE_ADMIN & FE_STORAGE & FE_USER --> COMPUTE
    FE_OOB -.-> COMPUTE
    NIC_FE --> FRONTEND
    NIC_BE --> BE_TOR --> BE_AGG --> BE_SPINE --> BE_DSF --> BE_BAG
    STORAGE --> FRONTEND & BACKEND
    ORCH -.-> FRONTEND & COMPUTE
    
    style FRONTEND fill:#e3f2fd
    style COMPUTE fill:#c8e6c9
    style BACKEND fill:#ffccbc
    style STORAGE fill:#fff9c4
    style ORCH fill:#f3e5f5
```

### LaTeX引用代码
```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.95\textwidth]{chapter6/ai-cluster-overview.png}
    \caption{AI训练集群网络架构全景。前端网络负责管理和存储，后端网络负责训练计算，通过分离设计实现最佳性能。}
    \label{fig:ai-cluster-overview}
\end{figure}
```

---

## 6.4 性能优化工具链图

### 图片说明
展示AI训练网络性能优化的完整工具链，包括性能监控、分析、调优和自动化优化的各个环节。

### Mermaid图表代码
```mermaid
flowchart TB
    subgraph MONITORING["📊 性能监控层"]
        direction TB
        METRICS["指标采集<br/>带宽/延迟/丢包"]
        TRACE["链路追踪<br/>流级别分析"]
        LOG["日志聚合<br/>事件记录"]
        
        METRICS --> PROM["Prometheus<br/>时序数据库"]
        TRACE --> JAEGER["Jaeger<br/>分布式追踪"]
        LOG --> ES["Elasticsearch<br/>日志分析"]
    end
    
    subgraph ANALYSIS["🔍 性能分析层"]
        direction TB
        PERF1["拓扑分析<br/>拥塞热点识别"]
        PERF2["流量模式<br/>大象流检测"]
        PERF3["负载均衡<br/>路径效率分析"]
        PERF4["应用性能<br/>NCCL/AllReduce分析"]
        
        PERF1 & PERF2 & PERF3 & PERF4 --> ANALYTICS["智能分析引擎<br/>ML-based"]
    end
    
    subgraph OPTIMIZATION["⚙️ 优化执行层"]
        direction TB
        OPT1["路由优化<br/>动态ECMP调整"]
        OPT2["拥塞控制<br/>DCQCN参数调优"]
        OPT3["拓扑优化<br/>作业放置建议"]
        OPT4["P4可编程<br/>自定义转发逻辑"]
    end
    
    subgraph AUTOMATION["🤖 自动化层"]
        direction TB
        AUTO1["自动故障恢复<br/>链路切换"]
        AUTO2["流量调度<br/>基于策略的QoS"]
        AUTO3["预测性维护<br/>异常检测"]
        AUTO4["闭环优化<br/>持续改进"]
    end
    
    subgraph VISUALIZATION["📈 可视化层"]
        direction TB
        DASH1["实时仪表板<br/>Grafana"]
        DASH2["拓扑视图<br/>网络地图"]
        DASH3["告警管理<br/>PagerDuty/OpsGenie"]
    end
    
    PROM & JAEGER & ES --> ANALYSIS
    ANALYTICS --> OPTIMIZATION
    OPTIMIZATION --> AUTOMATION
    PROM & JAEGER & ES --> VISUALIZATION
    AUTOMATION -.->|反馈| MONITORING
    
    style MONITORING fill:#e3f2fd
    style ANALYSIS fill:#fff9c4
    style OPTIMIZATION fill:#c8e6c9
    style AUTOMATION fill:#ffccbc
    style VISUALIZATION fill:#f3e5f5
```

### LaTeX引用代码
```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.95\textwidth]{chapter6/performance-toolchain.png}
    \caption{AI训练网络性能优化工具链。从指标采集到智能分析，再到自动化优化，形成完整的闭环性能管理系统。}
    \label{fig:perf-toolchain}
\end{figure}
```

---

## 本章配图清单

| 序号 | 图号 | 图名 | 文件路径 |
|------|------|------|----------|
| 6.1 | Fig 6.1 | BAG跨区域互联拓扑 | chapter6/bag-interconnect.png |
| 6.2 | Fig 6.2 | DSF三级扩展架构 | chapter6/dsf-three-tier.png |
| 6.3 | Fig 6.3 | AI训练集群网络架构全景 | chapter6/ai-cluster-overview.png |
| 6.4 | Fig 6.4 | 性能优化工具链 | chapter6/performance-toolchain.png |
