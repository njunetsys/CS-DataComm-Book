# LaTeX图片引用代码示例

## 第3章 - DSF/BAG架构配图

```latex
% DSF双域架构图
\begin{figure}[htbp]
    \centering
    \includegraphics[width=\textwidth]{ch03-DSF双域架构.png}
    \caption{DSF（解耦式调度交换架构）双域架构示意图。左侧为以太网域，右侧为交换结构域，中间通过接口节点（IN）和交换节点（FN）实现高效互联。}
    \label{fig:dsf-architecture}
\end{figure}

% BAG架构拓扑图
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.9\textwidth]{ch03-BAG架构拓扑.png}
    \caption{BAG（后端聚合）架构实现跨区域数据中心互联。通过超级脊层将多个DSF L2区域连接成统一的超大规模GPU集群。}
    \label{fig:bag-topology}
\end{figure}

% 包喷洒示意图
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.85\textwidth]{ch03-包喷洒技术.png}
    \caption{包喷洒技术将大数据包分割为信元，均匀喷洒到所有可用路径，实现近最优负载均衡。}
    \label{fig:packet-spraying}
\end{figure}
```

## 第4章 - P4/DPU/CXL配图

```latex
% P4可编程架构图
\begin{figure}[htbp]
    \centering
    \includegraphics[width=\textwidth]{ch04-P4可编程架构.png}
    \caption{P4可编程数据平面架构。P4程序经过编译器生成目标设备配置，控制平面通过管理接口下发到数据平面。}
    \label{fig:p4-architecture}
\end{figure}

% DPU架构图
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.9\textwidth]{ch04-DPU架构.png}
    \caption{DPU（数据处理器）架构将网络、存储、安全等基础设施任务从CPU卸载到专用硬件。}
    \label{fig:dpu-architecture}
\end{figure}

% CXL内存扩展图
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.9\textwidth]{ch04-CXL内存架构.png}
    \caption{CXL（Compute Express Link）技术支持缓存一致性内存扩展和池化，实现多主机共享内存资源。}
    \label{fig:cxl-memory}
\end{figure}
```

## 第5章 - RoCEv2/RDMA配图

```latex
% RoCEv2 vs InfiniBand对比图
\begin{figure}[htbp]
    \centering
    \includegraphics[width=\textwidth]{ch05-RoCEv2-InfiniBand对比.png}
    \caption{RoCEv2与InfiniBand架构对比。RoCEv2基于标准以太网基础设施，具有更好的兼容性和成本优势。}
    \label{fig:roce-vs-ib}
\end{figure}

% DCQCN拥塞控制流程图
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.9\textwidth]{ch05-DCQCN拥塞控制.png}
    \caption{DCQCN拥塞控制算法的四个阶段：速率增加、拥塞检测、速率降低、拥塞避免。}
    \label{fig:dcqcn-flow}
\end{figure}
```

## 第6章 - AI训练网络配图

```latex
% AI训练集群架构全景图
\begin{figure}[htbp]
    \centering
    \includegraphics[width=\textwidth]{ch06-AI训练集群架构.png}
    \caption{大规模AI训练集群的完整网络架构栈，涵盖调度层、网络基础设施层、通信库层和性能优化工具。}
    \label{fig:ai-cluster-arch}
\end{figure}
```

## 第7章 - 绿色计算配图

```latex
% PUE优化示意图
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.9\textwidth]{ch07-PUE优化.png}
    \caption{数据中心PUE优化路径。通过冷却优化、供电优化和架构优化，将PUE从1.5-1.7降至1.15-1.20。}
    \label{fig:pue-optimization}
\end{figure}

% 液冷技术对比图
\begin{figure}[htbp]
    \centering
    \includegraphics[width=\textwidth]{ch07-液冷技术对比.png}
    \caption{三种数据中心冷却技术对比：传统风冷、冷板液冷和浸没式液冷。液冷技术显著提升散热密度并降低PUE。}
    \label{fig:cooling-comparison}
\end{figure}
```

## 使用说明

1. **图片命名规范**：`chXX-图片描述.png`
2. **图片存放位置**：`assets/chXX/`
3. **引用格式**：`\ref{fig:label}`
4. **图片格式**：推荐使用PNG或PDF矢量图

## 图片生成建议

可以使用以下工具将Mermaid图转换为图片：
- Mermaid Live Editor (https://mermaid.live)
- mermaid-cli (命令行工具)
- 在线转换服务

生成的图片应满足：
- 分辨率：300 DPI以上（用于打印）
- 尺寸：宽度不超过页面宽度（约16cm）
- 格式：PNG或PDF
- 字体：清晰可读，不小于8pt
