# DPU架构示意图

```mermaid
graph TB
    subgraph "传统架构"
        CPU1[CPU
        <br/>处理应用+网络+存储+安全]
        MEM1[主内存]
        NIC1[标准网卡
        <br/>仅数据收发]
        
        APP1[应用程序]
        NET1[网络协议栈]
        STO1[存储协议]
        SEC1[安全加密]
        
        APP1 --> NET1
        APP1 --> STO1
        APP1 --> SEC1
        NET1 --> CPU1
        STO1 --> CPU1
        SEC1 --> CPU1
        CPU1 --> MEM1
        CPU1 --> NIC1
    end
    
    subgraph "DPU架构"
        CPU2[CPU
        <br/>专注应用处理]
        MEM2[主内存]
        
        subgraph "DPU (Data Processing Unit)"
            CORE[ARM/x86核心]
            HW1[网络加速引擎
            <br/>RoCE/RDMA]
            HW2[存储加速引擎
            <br/>NVMe-oF]
            HW3[安全加速引擎
            <br/>加密/压缩]
            HW4[AI/ML推理引擎]
        end
        
        APP2[应用程序]
        
        APP2 --> CPU2
        CPU2 --> MEM2
        
        CPU2 -. 网络/存储/安全 .-> DPU
        
        DPU -->|高速网络| NET2[网络
        <br/>100G/200G/400G]
    end
```

## 图片说明

此图对比了传统架构与DPU架构的区别：

**左侧 - 传统架构**：
- CPU需要处理应用程序、网络协议栈、存储协议和安全加密
- 大量CPU资源被基础设施任务占用（可达30-50%）
- 标准网卡功能简单，仅负责数据收发

**右侧 - DPU架构**：
- **CPU**：专注应用处理，性能提升显著
- **DPU**：专门处理基础设施任务
  - ARM/x86核心：运行网络/存储/安全软件
  - 网络加速引擎：支持RoCE/RDMA、网络虚拟化
  - 存储加速引擎：支持NVMe-oF、纠删码计算
  - 安全加速引擎：SSL/TLS加密、压缩解压缩
  - AI/ML推理引擎：卸载AI推理任务

## DPU的价值

| 指标 | 传统架构 | DPU架构 | 改进 |
|------|----------|---------|------|
| CPU利用率 | 70-80% | 40-50% | -30% |
| 网络延迟 | 高 | 低 | 10-50μs |
| 存储性能 | 受限 | 大幅提升 | 2-5x |
| 安全性 | 软件加密 | 硬件加速 | 10x+ |

## 主要厂商

- **NVIDIA**: BlueField-3 DPU
- **Intel**: Infrastructure Processing Unit (IPU)
- **AMD**: Pensando DSC
- **Marvell**: OCTEON DPUs
- **Broadcom**: Stingray PS
