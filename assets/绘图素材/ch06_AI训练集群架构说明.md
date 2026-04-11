# AI训练集群网络架构全景图

```mermaid
graph TB
    subgraph "训练作业"
        JOB[大规模AI训练作业
        <br/>数万亿参数模型]
    end
    
    subgraph "集群调度层"
        SCHED[拓扑感知调度器
        <br/>Topology-Aware Scheduler]
        MON[集群监控系统
        <br/>Monitoring & Metrics]
    end
    
    subgraph "网络基础设施层"
        subgraph "计算节点"
            N1[GPU节点1
            <br/>8x H100 + 高速NIC]
            N2[GPU节点2]
            N3[GPU节点3]
            N4[GPU节点N]
        end
        
        subgraph "存储层"
            S1[Tectonic
            <br/>分布式存储]
            S2[Hammerspace
            <br/>并行文件系统]
        end
        
        subgraph "网络层"
            L1[DSF L1
            <br/>机架内互联]
            L2[DSF L2
            <br/>建筑内互联]
            L3[BAG
            <br/>跨区域互联]
        end
    end
    
    subgraph "通信库层"
        NCCL[NVIDIA NCCL
        <br/>集合通信库]
        RCCL[AMD RCCL
        <br/>GPU通信库]
    end
    
    subgraph "框架层"
        PY[PyTorch]
        Jax[JAX]
        MX[MXNet]
    end
    
    subgraph "性能优化工具"
        DBG[desync debug
        <br/>同步调试]
        FRC[Flight Recorder
        <br/>飞行记录器]
        TOP[拓扑可视化
        <br/>Topology Viewer]
    end
    
    JOB --> SCHED
    SCHED --> N1
    SCHED --> N2
    SCHED --> N3
    SCHED --> N4
    
    N1 --> L1
    N2 --> L1
    N3 --> L1
    N4 --> L1
    
    L1 --> L2
    L2 --> L3
    
    N1 -. 存储访问 .-> S1
    N1 -. 存储访问 .-> S2
    
    N1 --> NCCL
    NCCL --> PY
    
    MON --> DBG
    MON --> FRC
    MON --> TOP
```

## 图片说明

此图展示了大规模AI训练集群的完整网络架构栈：

### 从上到下的层次结构

**1. 训练作业层**：
- 大规模AI训练作业（数万亿参数模型）
- 分解为多个并行任务

**2. 集群调度层**：
- **拓扑感知调度器**：将通信频繁的GPU分配到物理邻近位置
- **集群监控系统**：实时监控性能和健康状态

**3. 网络基础设施层**：
- **计算节点**：配备8x H100 GPU和高速NIC的服务器
- **存储层**：Tectonic分布式存储 + Hammerspace并行文件系统
- **网络层**：DSF L1/L2 + BAG三层架构

**4. 通信库层**：
- NVIDIA NCCL：GPU间高效集合通信
- AMD RCCL：支持AMD GPU的通信库

**5. 框架层**：
- PyTorch、JAX、MXNet等深度学习框架

**6. 性能优化工具层**：
- **desync debug**：检测同步点性能异常
- **Flight Recorder**：记录集合通信历史状态
- **Topology Viewer**：可视化网络拓扑和流量

## 关键优化点

| 层级 | 优化技术 | 效果 |
|------|----------|------|
| 调度 | 拓扑感知调度 | 减少跨机架流量 |
| 网络 | DSF包喷洒 | 85-95%链路利用率 |
| 存储 | Tectonic检查点 | 数百毫秒完成 |
| 通信 | NCCL优化 | 90%+带宽利用率 |
| 调试 | desync debug | 快速定位问题 |

## 性能指标

- **规模**：18,000+ GPU互联
- **带宽**：每个GPU 400Gbps/800Gbps
- **延迟**：微秒级RDMA通信
- **利用率**：优化后90%+ vs 原始10-90%波动
