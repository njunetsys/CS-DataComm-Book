# 第7章 - 绿色计算配图

## 7.1 数据中心PUE优化示意图

### 图片说明
展示PUE（Power Usage Effectiveness，电能使用效率）的计算公式以及数据中心的优化方向，包括供电系统优化、冷却系统优化、IT设备优化等。

### Mermaid图表代码
```mermaid
flowchart TB
    subgraph PUE["📊 PUE = 数据中心总能耗 / IT设备能耗"]
        direction TB
        PUE_VAL["理想值: 1.0<br/>行业平均: 1.5-1.8<br/>Meta目标: <1.1"]
    end
    
    subgraph TOTAL["🔌 数据中心总能耗"]
        direction TB
        IT["💻 IT设备能耗<br/>服务器/存储/网络"]
        COOL["❄️ 冷却系统<br/>空调/冷却塔/液冷"]
        POWER["⚡ 供电系统<br/>UPS/变压器/配电"]
        OTHER["🏢 其他<br/>照明/消防/安防"]
    end
    
    subgraph OPTIMIZE["🎯 优化方向"]
        direction LR
        OPT1["液冷技术<br/>效率提升40%"]
        OPT2["自然冷却<br/>免费制冷"]
        OPT3["AI优化<br/>智能调控"]
        OPT4["可再生能源<br/>太阳能/风能"]
    end
    
    TOTAL --> PUE
    OPTIMIZE --> TOTAL
    
    style PUE fill:#e1f5fe
    style IT fill:#c8e6c9
    style COOL fill:#ffccbc
    style POWER fill:#fff9c4
    style OTHER fill:#f3e5f5
```

### LaTeX引用代码
```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.9\textwidth]{chapter7/pue-optimization.png}
    \caption{数据中心PUE优化示意图。PUE越接近1.0表示能效越高，主要通过优化冷却系统、采用液冷技术、利用自然冷却和可再生能源来实现。}
    \label{fig:pue-optimization}
\end{figure}
```

---

## 7.2 液冷技术架构图

### 图片说明
对比展示冷板式液冷（Cold Plate）与浸没式液冷（Immersion）两种主流液冷技术的架构差异、适用场景和优缺点。

### Mermaid图表代码
```mermaid
flowchart TB
    subgraph COLDPLATE["❄️ 冷板式液冷 Cold Plate"]
        direction TB
        CP1["CPU/GPU<br/>直接接触冷板"]
        CP2["冷却液循环<br/>去离子水或特殊冷却剂"]
        CP3["CDU冷量分配单元<br/>控制流量和温度"]
        CP4["外部冷却塔<br/>或干式冷却器"]
        CP1 --> CP2 --> CP3 --> CP4
    end
    
    subgraph IMMERSION["🌊 浸没式液冷 Immersion"]
        direction TB
        IM1["服务器整机<br/>浸入绝缘冷却液"]
        IM2["氟化液/矿物油<br/>直接接触所有组件"]
        IM3["热交换器<br/>液-液或液-气换热"]
        IM4["冷却循环系统<br/>泵+冷却塔"]
        IM1 --> IM2 --> IM3 --> IM4
    end
    
    subgraph COMPARE["📊 技术对比"]
        direction TB
        C1["冷板式: 改造成本低<br/>兼容现有基础设施"]
        C2["浸没式: 散热效率极高<br/>PUE可达1.03"]
        C3["冷板式: 适合渐进式部署<br/>风险可控"]
        C4["浸没式: 适合新建数据中心<br/>需要特殊设计"]
    end
    
    COLDPLATE --> COMPARE
    IMMERSION --> COMPARE
    
    style COLDPLATE fill:#e3f2fd
    style IMMERSION fill:#e8f5e9
    style COMPARE fill:#fff3e0
```

### LaTeX引用代码
```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.95\textwidth]{chapter7/liquid-cooling-architecture.png}
    \caption{液冷技术架构对比图。冷板式液冷适合渐进式部署，浸没式液冷提供最高散热效率但需要专门设计。}
    \label{fig:liquid-cooling}
\end{figure}
```

---

## 7.3 可再生能源应用图

### 图片说明
展示数据中心如何利用太阳能、风能等可再生能源，以及储能系统在保证供电稳定性中的作用。

### Mermaid图表代码
```mermaid
flowchart LR
    subgraph SOURCES["🌱 可再生能源"]
        direction TB
        SOLAR["☀️ 太阳能<br/>光伏板阵列<br/>峰值: 白天"]
        WIND["💨 风能<br/>风力发电机<br/>峰值: 夜间/大风"]
        HYDRO["💧 水能<br/>小水电/潮汐<br/>稳定基荷"]
    end
    
    subgraph STORAGE["🔋 储能系统"]
        direction TB
        BATTERY["锂电池储能<br/>短时调节<br/>2-4小时容量"]
        HYDROGEN["氢能储能<br/>长期储能<br/>季节性平衡"]
        FUEL["备用燃料<br/>柴油/天然气<br/>应急保障"]
    end
    
    subgraph GRID["⚡ 电网互联"]
        direction TB
        MAIN["主电网<br/>双向输电<br/>余电上网"]
        MICRO["微电网<br/>本地调度<br/>区域自治"]
    end
    
    subgraph DC["🏢 数据中心"]
        direction TB
        LOAD["IT负载<br/>计算/存储/网络"]
        COOL["冷却系统<br/>空调/液冷"]
        INFRA["基础设施<br/>照明/安防"]
    end
    
    SOURCES --> STORAGE
    SOURCES --> GRID
    STORAGE --> DC
    GRID --> DC
    
    style SOURCES fill:#c8e6c9
    style STORAGE fill:#fff9c4
    style GRID fill:#e1f5fe
    style DC fill:#ffccbc
```

### LaTeX引用代码
```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.95\textwidth]{chapter7/renewable-energy.png}
    \caption{数据中心可再生能源应用架构。通过多源互补发电、储能缓冲和电网互联，实现高比例可再生能源供电。}
    \label{fig:renewable-energy}
\end{figure}
```

---

## 7.4 Meta可持续发展时间线

### 图片说明
展示Meta（Facebook）从2011年到2024年在数据中心可持续发展方面的重要里程碑和承诺。

### Mermaid图表代码
```mermaid
timeline
    title Meta 数据中心可持续发展里程碑
    
    section 2011-2014
        2011 : Open Compute Project发布
             : 开源服务器设计
             : 提升能效30%+
        2013 : 首个可再生能源项目
             : 爱荷华州风电场
             : 100%可再生能源承诺
        2014 : Luleå数据中心启用
             : 自然冷却技术
             : 靠近北极圈
    
    section 2015-2018
        2016 : 可再生能源里程碑
             : 50%运营用电来自清洁能
             : 太阳能项目扩展
        2017 : 100%可再生能源目标
             : 承诺2020年实现
             : 全球数据中心
        2018 : 先进冷却技术
             : 蒸发冷却优化
             : 水资源效率提升
    
    section 2019-2022
        2020 : 100%可再生能源达成
             : 提前实现目标
             : 新增6GW清洁能源
        2021 : 净零排放承诺
             : 价值链碳中和目标
             : 2030年全范围净零
        2022 : 液冷技术规模化
             : AI训练集群部署
             : 水冷服务器普及
    
    section 2023-2024
        2023 : 下一代数据中心设计
             : 液冷成为默认配置
             : PUE目标<1.1
        2024 : AI基础设施可持续
             : 训练能耗降低30%
             : 100%可再生能源训练
```

### LaTeX引用代码
```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.95\textwidth]{chapter7/meta-sustainability-timeline.png}
    \caption{Meta数据中心可持续发展时间线（2011-2024）。从Open Compute Project到100%可再生能源，再到AI时代的可持续基础设施。}
    \label{fig:meta-timeline}
\end{figure}
```

---

## 本章配图清单

| 序号 | 图号 | 图名 | 文件路径 |
|------|------|------|----------|
| 7.1 | Fig 7.1 | 数据中心PUE优化示意图 | chapter7/pue-optimization.png |
| 7.2 | Fig 7.2 | 液冷技术架构对比图 | chapter7/liquid-cooling-architecture.png |
| 7.3 | Fig 7.3 | 可再生能源应用架构图 | chapter7/renewable-energy.png |
| 7.4 | Fig 7.4 | Meta可持续发展时间线 | chapter7/meta-sustainability-timeline.png |
