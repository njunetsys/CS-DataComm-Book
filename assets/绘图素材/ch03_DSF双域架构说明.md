# DSF双域架构图

```mermaid
graph TB
    subgraph "以太网域 (Ethernet Domain)"
        A[服务器/GPU节点]
        B[服务器/GPU节点]
        C[服务器/GPU节点]
    end
    
    subgraph "接口节点 (Interface Nodes)"
        IN1[RDSW/IN 1]
        IN2[RDSW/IN 2]
        IN3[RDSW/IN 3]
    end
    
    subgraph "交换结构域 (Fabric Domain)"
        FN1[FDSW/FN 1]
        FN2[FDSW/FN 2]
        FN3[FDSW/FN 3]
        FN4[FDSW/FN 4]
    end
    
    subgraph "出口接口节点"
        IN4[RDSW/IN 4]
        IN5[RDSW/IN 5]
    end
    
    subgraph "目标服务器"
        D[目标GPU节点]
    end
    
    A --> IN1
    B --> IN2
    C --> IN3
    
    IN1 --> FN1
    IN1 --> FN2
    IN2 --> FN2
    IN2 --> FN3
    IN3 --> FN3
    IN3 --> FN4
    
    FN1 --> IN4
    FN2 --> IN4
    FN3 --> IN5
    FN4 --> IN5
    
    IN4 --> D
    IN5 --> D
```

## 图片说明

此图展示了DSF（Disaggregated Scheduled Fabric）的双域架构：

**左侧 - 以太网域**：
- 服务器/GPU节点通过标准以太网连接到接口节点（IN/RDSW）
- 使用传统以太网协议进行通信

**中间 - 接口节点**：
- 负责外部连接和路由功能
- 将数据包分割为信元（Cells）

**中间 - 交换结构域**：
- 由多个交换节点（FN/FDSW）组成
- 通过包喷洒技术将信元均匀分布到所有路径
- 实现近最优的负载均衡

**右侧 - 出口接口节点**：
- 接收来自结构域的信元
- 重新组装数据包并按序交付

这种架构的优势：
1. 突破传统机箱式交换机的物理限制
2. 实现细粒度的负载均衡
3. 支持超大规模扩展（万卡/十万卡集群）
