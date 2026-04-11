#!/usr/bin/env python3
"""
生成所有Mermaid图表的mermaid.live链接
使用方式: python3 generate_links.py
"""

import base64
import json
import zlib

def generate_url(code):
    json_str = json.dumps({"code": code, "mermaid": {"theme": "default"}})
    compressed = zlib.compress(json_str.encode('utf-8'), level=9)
    encoded = base64.urlsafe_b64encode(compressed).decode('utf-8')
    return f"https://mermaid.live/edit#pako:{encoded}"

DIAGRAMS = [
    ("01-wifi-sensing", "WiFi感知系统流程", """flowchart TD
    A[WiFi发射端] -->|原始信号| B[信号预处理]
    B --> C[去噪与清洗]
    C --> D[特征提取]
    D --> E{应用场景}
    E -->|人体活动| F[HAR分类器]
    E -->|手势识别| G[Gesture识别]
    E -->|室内定位| H[定位算法]
    E -->|呼吸监测| I[生命体征检测]
    style A fill:#e1f5fe
    style B fill:#fff3e0
    style D fill:#e8f5e9
    style E fill:#fce4ec"""),

    ("02-csi-phase", "CSI相位预处理", """graph LR
    subgraph CSI_Problem[原始CSI问题]
        A1[相位跳变] --> B1[解缠绕]
        A2[线性漂移] --> B2[拟合去趋势]
        A3[硬件噪声] --> B3[Hampel滤波]
    end
    subgraph Processing[处理方法]
        B1 --> C[连续相位]
        B2 --> C
        B3 --> C
    end
    C --> D[共轭相乘]
    D --> E[稳定相位差]
    style C fill:#e8f5e9
    style E fill:#c8e6c9"""),

    ("03-phase-ranging", "相位测距原理", """graph LR
    subgraph Core[相位测距核心关系]
        A[距离 d] -->|φ=2πd/λ| B[相位 φ]
        B -->|解算| C[距离估计]
    end
    subgraph Ambiguity[周期模糊性]
        D[真实距离] --> E{相位测量}
        E -->|φ| F[候选1:d]
        E -->|φ+2π| G[候选2:d+λ]
        E -->|φ+4π| H[候选3:d+2λ]
    end
    style B fill:#ffeb3b
    style E fill:#ffccbc"""),

    ("04-chronos-ranging", "Chronos多频测距", """graph TD
    A[多频相位测量] --> B{频率选择}
    B -->|2.4GHz| C[20MHz信道]
    B -->|5GHz| D[更多信道]
    C --> E[构建方程组]
    D --> E
    E --> F[中国剩余定理]
    F --> G[解算周期数]
    G --> H[精确距离估计]
    subgraph Accuracy[精度提升]
        I[单频:~6cm] --> J[多频融合]
        J --> K[Chronos:~10cm]
    end
    style H fill:#c8e6c9
    style K fill:#a5d6a7"""),

    ("05-aoa-ranging", "AoA测距定位", """graph LR
    subgraph Geometry[天线阵列几何]
        A[发射源] -->|距离r| B[天线1]
        A -->|距离r+Δd| C[天线2]
        B ---|d_ant| C
    end
    subgraph Calculation[相位差计算]
        D[路径差Δd] -->|Δd=d_ant·sinθ| E[相位差Δφ]
        E -->|Δφ=2πΔd/λ| F[到达角θ]
    end
    subgraph Positioning[定位]
        G[AP1的AoA] --> H[三角定位]
        I[AP2的AoA] --> H
        H --> J[目标位置]
    end
    style F fill:#e3f2fd
    style J fill:#c8e6c9"""),

    ("06-similarity-methods", "相似度度量分类", """graph TD
    A[信号相似度度量] --> B[距离度量]
    A --> C[相关性度量]
    A --> D[时间对齐]
    A --> E[分布度量]
    B --> B1[欧几里得距离]
    B --> B2[曼哈顿距离]
    B --> B3[切比雪夫距离]
    B --> B4[汉明距离]
    C --> C1[皮尔逊相关系数]
    C --> C2[余弦相似度]
    C --> C3[斯皮尔曼相关]
    D --> D1[DTW动态时间规整]
    D --> D2[约束DTW]
    D --> D3[FastDTW]
    E --> E1[Wasserstein距离]
    E --> E2[MMD最大均值差异]
    E --> E3[KL散度]
    style B1 fill:#e3f2fd
    style C1 fill:#e8f5e9
    style D1 fill:#fff3e0
    style E1 fill:#fce4ec"""),

    ("07-euclidean-cosine", "欧几里得vs余弦", """graph LR
    subgraph Euclidean[欧几里得距离]
        A1[信号A] --> C1{计算}
        B1[信号B] --> C1
        C1 -->|√Σ(xi-yi)²| D1[距离值]
        D1 -->|受幅度影响| E1[变化敏感]
    end
    subgraph Cosine[余弦相似度]
        A2[信号A] --> C2{计算}
        B2[信号B] --> C2
        C2 -->|A·B/|A||B|| D2[夹角余弦]
        D2 -->|仅关注方向| E2[幅度鲁棒]
    end
    style E1 fill:#ffccbc
    style E2 fill:#c8e6c9"""),

    ("08-dtw-concept", "DTW动态时间规整", """graph TD
    A[序列X] --> B[构建距离矩阵]
    C[序列Y] --> B
    B --> D[局部距离计算]
    D --> E[动态规划累积]
    E --> F{对齐路径}
    F -->|路径1| G[直接对齐:距离大]
    F -->|路径2| H[弯曲对齐:距离小]
    H --> I[DTW距离]
    subgraph Constraints[约束]
        J[WarpingWindow] --> K[限制搜索范围]
        L[SlopeConstraint] --> M[防止过度弯曲]
    end
    K --> E
    M --> E
    style I fill:#c8e6c9
    style H fill:#e8f5e9"""),

    ("09-time-frequency", "时频分析方法", """graph TD
    A[时频分析方法] --> B[FFT]
    A --> C[STFT]
    A --> D[小波变换]
    A --> E[EMD/HHT]
    B -->|适用| B1[平稳信号]
    B -->|优点| B2[计算高效]
    B -->|缺点| B3[无时间定位]
    C -->|适用| C1[非平稳信号]
    C -->|优点| C2[时频联合]
    C -->|缺点| C3[分辨率权衡]
    D -->|适用| D1[多尺度信号]
    D -->|优点| D2[自适应分辨率]
    D -->|缺点| D3[基函数选择]
    E -->|适用| E1[非线性信号]
    E -->|优点| E2[数据驱动]
    E -->|缺点| E3[计算复杂]
    style B fill:#e3f2fd
    style C fill:#e8f5e9
    style D fill:#fff3e0
    style E fill:#fce4ec"""),

    ("10-dwt-decomposition", "DWT多层分解", """graph TD
    A[原始信号] --> B[DWT分解]
    B --> C1[第一层细节系数]
    B --> C2[第一层近似]
    C2 --> D1[第二层细节系数]
    C2 --> D2[第二层近似]
    D2 --> E1[第三层细节系数]
    D2 --> E2[第三层近似]
    subgraph Frequency[频率范围]
        C1 -->|高频| F1[快速运动]
        D1 -->|中高频| F2[手势]
        E1 -->|中频| F3[行走]
        E2 -->|低频| F4[呼吸]
    end
    style A fill:#e3f2fd
    style E2 fill:#c8e6c9"""),

    ("11-application-pipelines", "应用场景方法组合", """graph TD
    subgraph HAR[人体活动识别HAR]
        A1[原始CSI] --> B1[Hampel滤波]
        B1 --> C1[PCA降维]
        C1 --> D1[DWT分解]
        D1 --> E1[小波能量特征]
        E1 --> F1[SVM/CNN分类]
    end
    subgraph Localization[室内定位]
        A2[CSI幅度] --> B2[去噪]
        B2 --> C2[欧几里得距离]
        C2 --> D2[k-NN匹配]
        D2 --> E2[WKNN定位]
    end
    subgraph Gesture[手势识别]
        A3[CSI流] --> B3[相位处理]
        B3 --> C3[STFT]
        C3 --> D3[频谱图]
        D3 --> E3[CNN特征]
        E3 --> F3[DTW对齐]
    end
    subgraph Breathing[呼吸检测]
        A4[相位] --> B4[Butterworth滤波]
        B4 --> C4[FFT]
        C4 --> D4[峰值检测]
    end
    style F1 fill:#c8e6c9
    style E2 fill:#c8e6c9
    style F3 fill:#c8e6c9
    style D4 fill:#c8e6c9""")
]

print("=" * 60)
print("Mermaid 图表链接生成器")
print("=" * 60)
print()
print("使用说明:")
print("1. 点击下方链接打开对应图表")
print("2. 在 mermaid.live 中预览确认")
print("3. 点击 Actions → Export → PNG 下载")
print("4. 保存到 assets/ch02/ 目录")
print("5. 在LaTeX中使用 \\includegraphics 插入")
print()
print("=" * 60)
print()

for filename, title, code in DIAGRAMS:
    url = generate_url(code)
    print(f"【{filename}】{title}")
    print(url)
    print()

print("=" * 60)
print(f"共生成 {len(DIAGRAMS)} 个图表链接")
print("=" * 60)
