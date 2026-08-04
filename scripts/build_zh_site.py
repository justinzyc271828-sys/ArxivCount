"""Build Chinese UI + event translations under web/timeline/zh/."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EN_DIR = ROOT / "web" / "timeline"
ZH_DIR = EN_DIR / "zh"

# id -> Chinese fields for every navigable event
EVENT_ZH: dict[str, dict[str, str]] = {
    "minerva": {
        "label": "Minerva（数学大模型）",
        "note": "面向定量推理的语言模型；仍以基准测试为主，尚未进入研究级证明。",
    },
    "chatgpt": {
        "label": "ChatGPT 公开发布",
        "note": "大规模采用开始；写作辅助与早期数学实验大量涌现。",
        "keystone_reason": "大众数学实验的公共大模型入口。",
    },
    "gpt4": {
        "label": "GPT-4 时代的数学演示",
        "note": "非形式化数学演示明显增强；对研究级断言仍不可靠。",
    },
    "alphageometry": {
        "label": "AlphaGeometry",
        "note": "奥赛几何；为后续研究系统提供神经—符号模板。",
        "keystone_reason": "奥赛级神经—符号里程碑。",
    },
    "alphaproof": {
        "label": "AlphaProof / IMO 级形式化证明",
        "note": "IMO 规模的形式化定理证明；Lean 成为验证骨干。",
        "keystone_reason": "形式化 IMO 级证明；Lean 作骨干。",
    },
    "lean_ai_wave": {
        "label": "Lean + LLM 研究向形式化浪潮",
        "note": "自动形式化 / 智能体式 Lean 开始出现研究邻域用途。",
        "keystone_reason": "研究邻域自动形式化浪潮的标志。",
    },
    "2509.18057": {
        "label": "AI 发现的小工具改进不可近似界",
        "note": "AlphaEvolve 自主搜索并发现新组合小工具与 Ramanujan 图，还演化出更快验证器，从而改进硬度结果。",
    },
    "2510.20013": {
        "label": "AI 发现开放问题的反例",
        "note": "GPT-5 Pro 在数值实验后提出特定布尔函数反例；作者手工验证并证明局部最优性定理。",
        "open_problem_name": "带擦除的 NICD 中 majority 最优性",
    },
    "2510.23513": {
        "label": "AI 辅助解决 NAG 点列收敛",
        "note": "ChatGPT 生成候选证明并最终给出连续时间情形的完整证明，再适配到离散 NAG。",
        "open_problem_name": "Nesterov 加速梯度法的点列收敛",
    },
    "2511.18828": {
        "label": "AI 辅助解决稳健统计中的开放问题",
        "note": "GPT-5 提出新技术（动态 Benamou–Brenier、更尖偏置界）并协助验证明，但正确性与补洞仍依赖人类专长。",
        "open_problem_name": "Wasserstein 污染下稳健密度估计的极小极大最优速率",
    },
    "2512.10220": {
        "label": "AI 解决学习曲线单调性开放问题",
        "note": "AI 生成全部证明（含主定理），并推广到高维与其他分布；人类负责提示与验证。",
        "open_problem_name": "MLE（高斯方差估计）学习曲线的单调性",
    },
    "formal_open_problems": {
        "label": "智能体 Lean / 开放问题形式化结果集群",
        "note": "2026 上半年 Erdős 问题与形式化 AI 证明成簇出现。",
    },
    "2601.07421": {
        "label": "首个 AI 自主解决 Erdős 问题的高可见写本",
        "note": "GPT-5.2 Pro 生成非形式论证；Aristotle 产出形式 Lean 证明；ChatGPT 协助写作与推广。",
        "keystone_reason": "早期高可见的 Erdős 问题 AI 解决写本。",
        "open_problem_name": "Erdős 问题 #728",
    },
    "2602.16807": {
        "label": "超立方体切片上界改进",
        "note": "CPro1 生成多样搜索算法并浮现结构约束（如相同初始列）；经人类综合后得到改进上界。",
        "open_problem_name": "超立方体切片问题（确定 S(n)）",
    },
    "2603.09680": {
        "label": "椭圆曲线「低语」现象的发现",
        "note": "AI/ML（PCA、逻辑回归、可解释性）在椭圆曲线数据中检出 murmurations，引导人类形式化该现象。",
    },
    "2603.19215": {
        "label": "解决 Manin 1972 年关于 R-等价的问题",
        "note": "Gemini 3 Deep Think 写出关键引理与定理的严格证明，人类引导与润色；AlphaEvolve 自动搜索有效交点。",
        "open_problem_name": "Manin 关于对角三次曲面 R-等价的问题",
    },
    "2603.28636": {
        "label": "精确解决 Erdős 问题 #650",
        "note": "ChatGPT 提出初始证明策略；Aristotle 补洞并提供 Lean 形式化；人类撰写最终表述。",
        "open_problem_name": "Erdős 问题 #650",
    },
    "erdos_1196": {
        "label": "Erdős #1196（GPT 辅助，公开报道）",
        "note": "本原集问题；常被引用为从「奥赛感」跃入「仍在被研究的开放问题」。",
        "keystone_reason": "GPT 辅助的 Erdős #1196；开放问题波的锚点。",
    },
    "2604.21187": {
        "label": "AI 辅助解决 1982 年 Ramsey 图问题",
        "note": "LLM 写代码找构造、猜想无穷族、产出证明，并在 Lean 中自动形式化。",
        "open_problem_name": "Grinstead–Roberts 1982 关于双重饱和 Ramsey 图的问题",
    },
    "2604.23468": {
        "label": "8 维球堆积的形式化证明",
        "note": "Gauss 自动形式化并完成球堆积定理的 Lean 证明，补充关键证明并完成验证。",
    },
    "2605.00301": {
        "label": "AI 辅助解决多项 Erdős 猜想",
        "note": "AI 为定理 1.1、1.6 生成初证，并协助 1.2–1.4；人类 refinement 与形式化。",
        "keystone_reason": "多项 Erdős 相关 AI 辅助结果的 arXiv 写本。",
        "open_problem_name": "Erdős 问题 #1196",
    },
    "2605.08033": {
        "label": "AI 证明 Coxeter 组合中的猜想",
        "note": "ChatGPT 5.4 Pro 自主证明主定理（定理 1.3），并发现 Hamaker–Reiner 猜想的反例；人类提供笔记与提示。",
        "open_problem_name": "Escobar–Klein–Weigandt 关于 Cohen–Macaulay ASM 簇的猜想",
    },
    "2605.11656": {
        "label": "反证 GCM 猜想",
        "note": "AI 发现显式概率测度反例；人类给出严格证明与验证。",
        "open_problem_name": "高斯完全单调（GCM）猜想",
    },
    "2605.19979": {
        "label": "AI 解决多项组合猜想",
        "note": "AI 自主发现并生成文中全部证明，解决若干开放猜想；人类选题、验证明并润色表述。",
        "open_problem_name": "Defant 等、Hopkins、Sagan–Wilson 的猜想",
    },
    "2605.20527": {
        "label": "AI 辅助证明 L2 稳定 STFT 相位恢复",
        "note": "LLM 先提出错误约化，再 refined 成定理 2.1 的完整证明，并在大量协助下于 Lean 4 自动形式化。",
        "open_problem_name": "STFT 相位恢复的 L2 稳定性",
    },
    "unit_distance": {
        "label": "单位距离猜想被反证（OpenAI 模型）",
        "note": "高可见离散几何里程碑；随后出现人类消化的 arXiv 写本。叙事锚点：「AI 能动摇重大开放问题」。",
        "keystone_reason": "单位距离猜想反证；重大公共里程碑。",
    },
    "2605.20623": {
        "label": "AI 生成新的 PDE 下界证明",
        "note": "QED 自主生成并验证三则定理的完整证明；人类仅提出问题并审阅最终正确性。",
    },
    "2605.20585": {
        "label": "AI 解决 Kollár–Kovács 问题",
        "note": "ChatGPT 5.5 pro 提供一般想法；Rethlas 系统生成具体例子并可能参与证明构造。",
        "open_problem_name": "Kollár–Kovács 问题 1.1",
    },
    "2605.20594": {
        "label": "AI 解决代数几何中的开放问题",
        "note": "ChatGPT 5.5 pro 提供例子与初证；Rethlas 验改证明；作者组装最终论文。",
        "open_problem_name": "Ciliberto 等问题 1.1",
    },
    "2605.22250": {
        "label": "AI 辅助解决 Han–Jiang 问题",
        "note": "ChatGPT Pro 5.5 提出一般构造想法；Rethlas 找到并证明显式反例；作者验证并撰写。",
        "open_problem_name": "Han–Jiang 关于平坦族中 klt 型开性的问题",
    },
    "2605.22052": {
        "label": "AI 发现 Mauri–Moraga 问题的反例",
        "note": "ChatGPT 5.5 pro 生成两个反例；Rethlas 修补一处证明漏洞并给出长验证。",
        "open_problem_name": "Mauri–Moraga 关于 log Calabi–Yau 对的问题",
    },
    "2605.24160": {
        "label": "解决 Crandall 关于 Erdős–Borwein 常数的问题",
        "note": "AI 参与探索与证明发展，建议引理与结构；人类验证并纠正全部细节。",
        "open_problem_name": "Crandall 关于 Erdős–Borwein 常数二进制数字的问题",
    },
    "2605.27563": {
        "label": "量化线性映射的次高斯性：AI 辅助札记",
        "note": "Gemini 3.5 Flash 发现并证明定理 1（良条件协方差下有界映射的次高斯界），并推广到 Hölder 连续函数。",
        "open_problem_name": "Bombari 关于符号量化线性映射次高斯性的问题",
    },
    "2605.29151": {
        "label": "AI 辅助证明 Aluffi–Chen–Marcolli 猜想",
        "note": "AI 提出二元变形 F_m(y,t)，改写为交错，并给出严格证明步骤；人类验证、补洞并推广到 FM 空间。",
        "open_problem_name": "Aluffi–Chen–Marcolli 关于 M_{0,n} Poincaré 多项式实根性的猜想",
    },
    "2606.05117": {
        "label": "AI 辅助解决 Andrews–Dhar 分拆问题",
        "note": "AxiomProver 在 Lean 中自主生成并验证等分布定理，并与人类共发现双射；形式验证。",
        "open_problem_name": "Andrews–Dhar 双射证明问题",
    },
    "2606.05438": {
        "label": "填补非凸优化下界中的开放缺口",
        "note": "ChatGPT 5.5 Pro 发现 block-chain 构造并开始校验；作者随后验证明、简化路径并改进表述。",
        "open_problem_name": "高阶光滑非凸优化的最优一阶 oracle 复杂度",
    },
    "2607.22580": {
        "label": "AI 辅助解决排队论开放问题",
        "note": "GPT-5.5 Pro 生成初证想法与草稿；作者验改、重写严格性，并在 Lean 4 中形式化关键引理。",
        "open_problem_name": "一快两慢服务器排队系统阈值策略的最优性",
    },
    "2606.11773": {
        "label": "OMWU 末次迭代收敛的首次证明",
        "note": "ChatGPT 证明了建立非活跃坐标最优性的缺失引理（引理 9），这是主定理的关键。",
        "open_problem_name": "光滑凸凹鞍点问题中 OMWU 的末次迭代收敛",
    },
    "2606.15159": {
        "label": "解决 Erdős–Graham ω=2 猜想",
        "note": "Claude 在 Lean 形式化、Python 验证脚本与部分表述上贡献很大；人类主导数学并对内容负责。",
        "open_problem_name": "受限分母埃及分数的 Erdős–Graham 问题（ω=2 情形）",
    },
    "2606.16738": {
        "label": "AI 反证 Elekes–Rónyai 猜想",
        "note": "ChatGPT 5.5 Pro 与 Rethlas 提出路线、找到反例多项式并生成完整证明；人类组织与验证。",
        "keystone_reason": "AI 反证 Elekes–Rónyai 型扩张子猜想。",
        "open_problem_name": "实数上近二次 Elekes–Rónyai 扩张子猜想",
    },
    "2607.22620": {
        "label": "解决 COLT 开放问题",
        "note": "GPT-5.5 Pro 生成证明想法与反例；Claude Code 组装文稿；作者验证与润色。",
        "open_problem_name": "Yun–Sra–Jadbabaie SS–RS–GD 不等式",
    },
    "2606.22636": {
        "label": "解决二进制交换链的 KTV 猜想",
        "note": "ChatGPT 5.5 Pro 生成全部证明策略、技术引理与初证；人类提出问题、引导搜索、评估并在 Lean 中形式化。",
        "open_problem_name": "二进制固定边缘交换链的 KTV 猜想（Kannan–Tetali–Vempala）",
    },
    "2606.22548": {
        "label": "证明孙智伟猜想 3.4",
        "note": "ChatGPT 生成完整证明与初稿；作者独立验证、修改表述，并在 Lean 4 中形式化部分组件。",
        "open_problem_name": "孙智伟猜想 3.4",
    },
    "2606.29593": {
        "label": "AI 解决 SGD 中的开放问题",
        "note": "Gemini 提出泛函分析联系并猜想算子界；ChatGPT 给出初等证明；人类验证。",
        "open_problem_name": "随机 Kaczmarz 最坏情形末次迭代收敛",
    },
    "2606.29687": {
        "label": "机器验证的 FGG 猜想证明",
        "note": "Claude Fable 5 在 Lean 中生成证明，利用编译器反馈与数值检查，闭合开放缺口。",
        "open_problem_name": "FGG 猜想",
    },
    "2607.00708": {
        "label": "解决 Jin–Rubinstein 问题 1.2",
        "note": "AI 生成主定理证明草图与最终文稿；人类验证与润色。",
        "open_problem_name": "Jin–Rubinstein 问题 1.2",
    },
    "2607.01924": {
        "label": "AI 解决拓扑中的开放问题",
        "note": "ChatGPT 5.5 生成主定理完整证明；作者提问、验证正确性并调整表述。",
        "open_problem_name": "Hilbert 球及其亲属的同胚问题",
    },
    "2607.03639": {
        "label": "解决带符号 BAR 唯一性猜想",
        "note": "AI 生成约 150 页证明大纲、做边界层展开并建议关键文献；作者验证并定稿。",
        "open_problem_name": "带符号 BAR 唯一性猜想（Dai–Dieker 开放问题）",
    },
    "2607.04891": {
        "label": "AI 发现 Moraga 猜想的反例",
        "note": "ChatGPT 5.5 pro 生成反例与证明草图；Danus 系统验证并撰写；人类润色。",
        "open_problem_name": "Moraga 关于 Abel p-群作用奇维秩界的猜想",
    },
    "2607.06693": {
        "label": "证明 Calderbank–Daubechies–Freeman–Freeman 猜想",
        "note": "LLM 提出关键概念原则并生成定量证明策略；亦将证明译入 Lean，人类引导显著。",
        "open_problem_name": "独立随机变量稳定相位恢复猜想（CDFF）",
    },
    "2607.20525": {
        "label": "自主反证实数上 sum-product 猜想",
        "note": "AI 在 8 次试验中有 7 次自主给出 sum-product 猜想反证的正确证明；人类验证并准备论文。",
        "keystone_reason": "自主风格反证实数上 sum-product 猜想。",
        "open_problem_name": "实数上的 Erdős–Szemerédi sum-product 猜想",
    },
    "2607.12208": {
        "label": "反证 FDR 控制猜想",
        "note": "GPT-5.6 Pro 生成反例、证明与数值证书；人类验证并撰写终稿。",
        "open_problem_name": "相关双侧高斯检验的 FDR 控制",
    },
    "2607.11376": {
        "label": "AI 形式化 type D ASEP 渐近",
        "note": "Claude / Fable 撰写证明并在 Lean 中形式化；人类验证与指导。",
        "open_problem_name": "超过两个对偶粒子的联合 q-矩塔",
    },
    "2607.14238": {
        "label": "解决在线 Spencer 猜想",
        "note": "AI 给出 T=n 时 O(√n) 在线前缀差异的完整证明，并推广到 Beck–Fiala 与更长视野；人类验证与重写。",
        "open_problem_name": "在线 Spencer 猜想（[8] 猜想 1）",
    },
    "2607.19184": {
        "label": "Batyrev 猜想的反例",
        "note": "AI 协助发现反例（可能通过候选簇或计算建议）；人类验证并证明结果。",
        "open_problem_name": "Batyrev 关于 stringy Hodge 数非负性的猜想",
    },
    "2607.19513": {
        "label": "反证 Deré 猜想",
        "note": "Claude Fable 提供过渡到线性条件的关键想法，并自主证明定理 4.5（反例核心）。",
        "open_problem_name": "Deré 猜想（猜想 1.1）",
    },
    "2607.18619": {
        "label": "解决 Balabdaoui–Wellner 猜想",
        "note": "GPT-5.6 Sol 经迭代尝试生成含关键引理与恒等式的全部证明；作者检查、修改表述并加注。",
        "open_problem_name": "Balabdaoui–Wellner 关于 Chernoff 密度强对数凹性的猜想",
    },
    "2607.21508": {
        "label": "Stanley 与 Monical 猜想的反例",
        "note": "AI 借助 SAT 求解器独立发现两猜想的反例；作者验证并呈现。",
        "open_problem_name": "Stanley 关于无爪图 Schur 正性的猜想",
    },
    "2607.23307": {
        "label": "尖锐薄壳不等式获解决",
        "note": "GPT-5.6 Pro 生成初证与关键三阶矩计算；作者验证、修改与润色。",
        "open_problem_name": "方差猜想（薄壳不等式）",
    },
    "2607.23828": {
        "label": "解决 Monical–Tokcan–Yong 猜想 2.25",
        "note": "Codex 生成均匀偶次幂构造、Dyson 常数项证明与完整证明草稿；作者检查、组织并在 Lean 中形式化。",
        "open_problem_name": "Monical–Tokcan–Yong 猜想 2.25",
    },
    "2607.24528": {
        "label": "解决 Feige 猜想",
        "note": "GPT-5.6 Sol 协助发现与探索证明；作者独立验证全部论证并撰写手稿。",
        "open_problem_name": "Feige 猜想",
    },
    "2607.24483": {
        "label": "黄金尖劈的精确解",
        "note": "AI 搜索极值曲线、起草论证并写 Lean 形式化；人类提供数学洞见与验证。",
        "open_problem_name": "Bellman「迷途于林」问题",
    },
    "2607.23980": {
        "label": "Feige 猜想在 δ≥1 时的解决",
        "note": "ChatGPT 5.6 Pro 发现结合 Vlassis–Thomas 与 Grünbaum 的初证；作者检查、修改并用 Codex 形式化。",
        "open_problem_name": "Feige 猜想",
    },
    "2607.26396": {
        "label": "解决 CMR 关于公共拐点线的开放问题",
        "note": "AI 生成主证明与结果；人类验证与润色。",
        "open_problem_name": "Ciliberto–Miranda–Roé 关于一般三次曲线束公共拐点线数目的问题",
    },
    "2607.26419": {
        "label": "Lukic 猜想的反例",
        "note": "GPT-5.6 构造反例序列并可能识别混合共振机制；作者验证并证明结果。",
        "open_problem_name": "Lukic 猜想",
    },
    "2608.00377": {
        "label": "反证 Schubitope 的 Ehrhart 正性猜想",
        "note": "GPT-5.6 找到反例 Schubitope 并生成 SageMath 验证代码；人类认证结果并撰写论文。",
        "open_problem_name": "Schubitope 的 Ehrhart 正性",
    },
    "2608.01040": {
        "label": "解决 Ehrhart 体积猜想的等式情形",
        "note": "Danus 系统自主完成证明、找到后半机制，并在 3 小时 16 分内产出内部自洽证明；人类提供初始观察与最终验证。",
        "open_problem_name": "Ehrhart 体积猜想（等式情形）",
    },
    "2608.02327": {
        "label": "反证 Connes 刚性猜想",
        "note": "GPT-5.6 Sol、Codex、Danus 等找到主构造并组装预证；作者引导与验证。",
        "open_problem_name": "ICC 性质 (T) 群的 Connes 刚性猜想",
    },
    "2608.02537": {
        "label": "超指数奇圈 Ramsey 数",
        "note": "AI 自主发现并起草证明；人类作者编辑并验证正确性。",
        "open_problem_name": "奇圈多色 Ramsey 数的超指数增长",
    },
    "2608.01673": {
        "label": "格点特征函数的尖锐支撑增长",
        "note": "AI 生成全部数学论证与证明；人类作者验证并承担责任。",
    },
}

PHASE_ZH = {
    "prehistory": "ChatGPT 前的工具期",
    "mass_llm": "大众大模型入场",
    "olympiad_formal": "奥赛与形式系统",
    "research_entry": "研究级进入",
    "open_problem_wave": "开放问题波",
}

SUBFIELD_ZH = {
    "combinatorics": "组合",
    "optimization": "优化",
    "cs_theory_adjacent": "理论 CS 邻域",
    "probability_stats": "概率统计",
    "dynamical_systems": "动力系统",
    "analysis": "分析",
    "number_theory": "数论",
    "discrete_geometry": "离散几何",
    "algebraic_geometry": "代数几何",
    "graph_theory": "图论",
    "algebra": "代数",
    "mathematical_physics": "数学物理",
    "general_or_multiple": "综合/多领域",
    "topology_geometry": "拓扑几何",
    "convex_geometry": "凸几何",
    "other": "其他",
}

INDEX_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>ArxivCount · 时间轴</title>
  <meta name="description" content="arXiv 上 AI 辅助数学的交互时间轴（中文版）" />
  <link rel="stylesheet" href="../styles.css?v=6" />
</head>
<body>
  <main class="hero" id="hero">
    <header class="hero-bar">
      <div class="brand">
        <span class="brand-mark" aria-hidden="true">∫</span>
        <span class="brand-name">ArxivCount</span>
        <span class="brand-sep">/</span>
        <span class="brand-sub">时间轴</span>
      </div>
      <div class="hero-bar-right">
        <span class="pill" id="progressPill">—</span>
        <a class="text-link" href="../" hreflang="en">English</a>
        <a class="text-link" href="#data">数据 ↓</a>
      </div>
    </header>

    <p class="dual-banner" id="dualBanner">
      双轨道：<strong>核心贡献</strong> · <strong>严格过程</strong>
    </p>

    <div class="stage">
      <button type="button" class="nav-fab prev" id="btnPrev" aria-label="上一项">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
      </button>

      <article class="focus" id="focusCard">
        <div class="keystone-banner" id="keystoneBanner" hidden>
          <span class="keystone-banner-star" aria-hidden="true">★</span>
          <span id="keystoneBannerText">关键节点</span>
        </div>
        <div class="focus-icon-wrap" id="focusIcon" aria-hidden="true"></div>
        <div class="focus-meta">
          <span class="chip chip-kind" id="focusKind">—</span>
          <span class="chip chip-track" id="focusTrack">—</span>
          <span class="chip chip-date" id="focusDate">—</span>
        </div>
        <h1 class="focus-title" id="focusTitle">…</h1>
        <p class="focus-note" id="focusNote"></p>
        <div class="focus-tags" id="focusTags"></div>
        <div class="focus-cta">
          <a class="btn-primary" id="focusLink" href="#" target="_blank" rel="noopener">打开论文</a>
          <a class="btn-secondary" id="focusPdf" href="#" target="_blank" rel="noopener" style="display:none">PDF</a>
          <button type="button" class="btn-ghost" id="btnHintKeys">← → 全部 · Shift+←/→ 关键节点</button>
        </div>
      </article>

      <button type="button" class="nav-fab next" id="btnNext" aria-label="下一项">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg>
      </button>
    </div>

    <section class="keystone-strip" aria-label="十大关键节点">
      <div class="keystone-strip-head">
        <span class="keystone-strip-title">★ 10 个关键节点</span>
        <span class="keystone-strip-hint">点击数字 · 或 Shift+←/→</span>
      </div>
      <div class="keystone-buttons" id="keystoneButtons"></div>
    </section>

    <div class="scrub">
      <div class="scrub-label">完整时间轴 <span class="scrub-legend"><i class="lg-key"></i> 关键节点 &nbsp; <i class="lg-dot"></i> 其他</span></div>
      <div class="scrub-track" id="scrubTrack" role="listbox" aria-label="时间轴"></div>
    </div>

    <a class="scroll-cue" href="#data">
      <span>下滑查看计数与渗透率</span>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
    </a>
  </main>

  <section class="data-zone" id="data">
    <div class="data-inner">
      <header class="data-head">
        <h2>数据面板</h2>
        <p>
          与故事视图分离。我们将 arXiv <code>math.*</code> 的可观测代理样本分为两条公开轨道：
          <strong>核心贡献</strong>（实质数学主张）与
          <strong>严格过程</strong>（形式化 / 验证步骤）。
          这不是全部数学的普查。
        </p>
      </header>

      <div class="metric-row" id="metricRow"></div>

      <div class="grid-2">
        <div class="panel">
          <div class="panel-title">
            <span class="dot wide"></span>
            核心 vs 严格 · 逐年计数
          </div>
          <div id="chartCounts" class="chart-area"></div>
          <p class="legend"><span class="sw wide"></span> 核心 &nbsp; <span class="sw strict"></span> 严格过程</p>
        </div>
        <div class="panel">
          <div class="panel-title">
            <span class="dot strict"></span>
            核心渗透率 · 每万篇 math.* 论文
          </div>
          <div id="chartPen" class="chart-area"></div>
          <p class="legend" id="penFoot">分母：arXiv API <code>cat:math*</code>（严格/核心实质集合）</p>
        </div>
      </div>

      <div class="panel phases-panel">
        <div class="panel-title">阶段</div>
        <div class="phase-grid" id="phaseGrid"></div>
      </div>

      <footer class="data-foot" id="dataFoot"></footer>
    </div>
  </section>

  <script src="../data.js?v=6"></script>
  <script src="./i18n.js?v=6"></script>
  <script src="./app.js?v=6"></script>
</body>
</html>
"""

APP_JS = r"""/* Chinese UI — same interaction as English timeline */

(function () {
  const raw = window.ARXIVCOUNT_DATA;
  if (!raw) {
    document.body.innerHTML =
      '<p style="color:#ccc;padding:2rem;font-family:sans-serif">缺少 data.js — 请运行: python -m src.export_web</p>';
    return;
  }

  const I18N = window.ARXIVCOUNT_ZH || {};
  const EVENT_ZH = I18N.events || {};
  const PHASE_ZH = I18N.phases || {};
  const SUBFIELD_ZH = I18N.subfields || {};

  function deepClone(o) {
    return JSON.parse(JSON.stringify(o));
  }

  function localizeEvent(e) {
    if (!e) return e;
    const z = EVENT_ZH[e.id] || {};
    const out = Object.assign({}, e);
    if (z.label) out.label = z.label;
    if (z.note) out.note = z.note;
    if (z.keystone_reason) out.keystone_reason = z.keystone_reason;
    if (z.open_problem_name) out.open_problem_name = z.open_problem_name;
    if (Array.isArray(out.subfields)) {
      out.subfields = out.subfields.map((s) => SUBFIELD_ZH[s] || s);
    }
    return out;
  }

  const data = deepClone(raw);
  if (data.project) {
    data.project.title = "arXiv 上的 AI 辅助数学证明";
  }
  if (Array.isArray(data.phases)) {
    data.phases = data.phases.map((ph) =>
      Object.assign({}, ph, { label: PHASE_ZH[ph.id] || ph.label })
    );
  }
  if (Array.isArray(data.navigable)) {
    data.navigable = data.navigable.map(localizeEvent);
  }
  if (Array.isArray(data.events)) {
    data.events = data.events.map(localizeEvent);
  }
  if (data.keystones && Array.isArray(data.keystones.items)) {
    data.keystones.items = data.keystones.items.map((it) => {
      const z = EVENT_ZH[it.id] || {};
      return Object.assign({}, it, {
        label: z.label || it.label,
        reason: z.keystone_reason || it.reason,
      });
    });
  }
  if (data.dual && data.dual.labels) {
    data.dual.labels = {
      core: "核心贡献 — AI 对真实数学主张/结果有实质作用",
      rigorous: "严格过程 — AI 参与形式化 / 验证 / 严格证明步骤",
    };
  }

  const nav = data.navigable || [];
  let idx = Math.max(
    0,
    nav.findIndex(
      (e) =>
        e.type === "canon_milestone" &&
        (e.id === "chatgpt" || (e.label || "").includes("ChatGPT"))
    )
  );
  if (idx < 0) idx = 0;

  const $ = (id) => document.getElementById(id);

  const ICONS = {
    model: `<svg viewBox="0 0 24 24" fill="none" stroke="#6ea8ff" stroke-width="1.7"><rect x="4" y="5" width="16" height="12" rx="2"/><path d="M8 19h8M12 17v2"/><circle cx="9" cy="11" r="1" fill="#6ea8ff"/><circle cx="15" cy="11" r="1" fill="#6ea8ff"/></svg>`,
    system: `<svg viewBox="0 0 24 24" fill="none" stroke="#a78bfa" stroke-width="1.7"><path d="M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z"/><path d="M12 12l8-4.5M12 12v9M12 12L4 7.5"/></svg>`,
    result: `<svg viewBox="0 0 24 24" fill="none" stroke="#e8b84a" stroke-width="1.7"><path d="M12 3l2.4 4.9 5.4.8-3.9 3.8.9 5.4L12 15.9 7.2 18l.9-5.4L4.2 8.7l5.4-.8L12 3z"/></svg>`,
    trend: `<svg viewBox="0 0 24 24" fill="none" stroke="#4ade80" stroke-width="1.7"><path d="M4 18V6M4 18h16"/><path d="M7 14l4-4 3 3 5-6"/></svg>`,
    paper: `<svg viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="1.7"><path d="M7 3h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/><path d="M14 3v5h5M9 13h6M9 17h6"/></svg>`,
    policy: `<svg viewBox="0 0 24 24" fill="none" stroke="#fb7185" stroke-width="1.7"><circle cx="12" cy="12" r="9"/><path d="M12 7v6M12 16.5v.5"/></svg>`,
  };

  function iconFor(e) {
    if (e.type === "canon_milestone") return ICONS[e.kind] || ICONS.system;
    if (e.is_core_contribution || e.open_problem) return ICONS.result;
    if (e.is_rigorous_process) return ICONS.system;
    return ICONS.paper;
  }

  function fmtDate(d) {
    if (!d) return "—";
    const s = String(d).slice(0, 10);
    const [y, m, day] = s.split("-");
    if (!m) return s;
    return `${y} · ${m}-${day || "01"}`;
  }

  function kindLabel(e) {
    if (e.type === "canon_milestone") {
      const map = {
        model: "模型",
        system: "系统",
        result: "结果",
        trend: "趋势",
        policy: "政策",
        community: "社区",
      };
      return map[e.kind] || "里程碑";
    }
    return "论文";
  }

  function trackLabel(e) {
    const t = e.public_track;
    if (t === "both") return { text: "核心 + 严格", cls: "both" };
    if (t === "core" || e.is_core_contribution) return { text: "核心贡献", cls: "core" };
    if (t === "rigorous" || e.is_rigorous_process) return { text: "严格过程", cls: "rigorous" };
    if (e.type === "canon_milestone") return { text: "正典里程碑", cls: "" };
    return { text: "其他", cls: "" };
  }

  function jumpKeystone(dir) {
    const ranks = nav
      .map((e, i) => ({ i, r: e.keystone_rank, k: e.is_keystone }))
      .filter((x) => x.k);
    if (!ranks.length) return;
    ranks.sort((a, b) => (a.r || 99) - (b.r || 99));
    const pos = ranks.findIndex((x) => x.i === idx);
    let next;
    if (pos < 0) {
      next =
        dir > 0
          ? ranks.find((x) => x.i > idx) || ranks[0]
          : [...ranks].reverse().find((x) => x.i < idx) || ranks[ranks.length - 1];
    } else {
      const j = (pos + dir + ranks.length) % ranks.length;
      next = ranks[j];
    }
    idx = next.i;
    renderFocus();
  }

  function renderFocus() {
    const e = nav[idx] || {};
    const cardEl = $("focusCard");
    cardEl.style.animation = "none";
    void cardEl.offsetWidth;
    cardEl.style.animation = "";

    $("focusIcon").innerHTML = iconFor(e);
    $("focusKind").textContent = kindLabel(e);
    const tr = trackLabel(e);
    const trackEl = $("focusTrack");
    const banner = $("keystoneBanner");
    const card = $("focusCard");
    if (e.is_keystone) {
      trackEl.textContent = `关键节点 #${e.keystone_rank || "—"}`;
      trackEl.className = "chip chip-keystone";
      banner.hidden = false;
      $("keystoneBannerText").textContent = `关键节点 #${e.keystone_rank} / 10`;
      card.classList.add("is-keystone");
    } else {
      trackEl.textContent = tr.text;
      trackEl.className = "chip chip-track " + (tr.cls || "");
      banner.hidden = true;
      card.classList.remove("is-keystone");
    }
    $("focusDate").textContent = fmtDate(e.date);
    $("focusTitle").textContent = e.label || e.title || e.id || "—";
    const noteBits = [];
    if (e.is_keystone && e.keystone_reason) noteBits.push(e.keystone_reason);
    noteBits.push(e.note || e.open_problem_name || e.ai_role_summary || "暂无摘要。");
    $("focusNote").textContent = noteBits.join(" — ");

    const tags = [];
    if (e.is_keystone) tags.push(["hot", `★ 关键节点 #${e.keystone_rank}`]);
    if (e.type === "canon_milestone") tags.push(["", "正典"]);
    if (e.is_core_contribution) tags.push(["hot", "核心贡献"]);
    if (e.is_rigorous_process) tags.push(["ok", "严格过程"]);
    if (e.open_problem) tags.push(["hot", "开放问题"]);
    if (Array.isArray(e.subfields)) {
      e.subfields.slice(0, 2).forEach((s) => tags.push(["", s]));
    }
    $("focusTags").innerHTML = tags
      .map(([cls, t]) => `<span class="tag ${cls}">${t}</span>`)
      .join("");

    document.querySelectorAll(".ks-btn").forEach((btn) => {
      const bi = Number(btn.dataset.i);
      btn.classList.toggle("active", bi === idx);
    });

    const link = $("focusLink");
    const pdf = $("focusPdf");
    if (e.url) {
      link.href = e.url;
      link.style.visibility = "visible";
      link.textContent = e.arxiv_id ? `打开论文 · ${e.arxiv_id}` : "打开来源";
    } else {
      link.removeAttribute("href");
      link.style.visibility = "hidden";
    }
    if (e.pdf_url || e.arxiv_id) {
      pdf.href = e.pdf_url || `https://arxiv.org/pdf/${e.arxiv_id}.pdf`;
      pdf.style.display = "inline-flex";
    } else {
      pdf.style.display = "none";
    }

    $("progressPill").textContent = `${idx + 1} / ${nav.length}`;
    $("btnPrev").disabled = idx <= 0;
    $("btnNext").disabled = idx >= nav.length - 1;

    document.querySelectorAll(".tick").forEach((el, i) => {
      el.classList.toggle("active", i === idx);
    });
    const active = document.querySelector(".tick.active");
    if (active) {
      active.scrollIntoView({ inline: "center", block: "nearest", behavior: "smooth" });
    }
  }

  function renderKeystoneStrip() {
    const box = $("keystoneButtons");
    if (!box) return;
    const items = nav
      .map((e, i) => ({ e, i }))
      .filter((x) => x.e.is_keystone)
      .sort((a, b) => (a.e.keystone_rank || 99) - (b.e.keystone_rank || 99));
    box.innerHTML = items
      .map(({ e, i }) => {
        const lab = (e.label || "").toString().replace(/"/g, "&quot;");
        return `<button type="button" class="ks-btn${i === idx ? " active" : ""}" data-i="${i}" title="#${e.keystone_rank} ${lab}">${e.keystone_rank}</button>`;
      })
      .join("");
    box.querySelectorAll(".ks-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        idx = Number(btn.dataset.i);
        renderFocus();
      });
    });
  }

  function renderScrub() {
    const track = $("scrubTrack");
    track.innerHTML = nav
      .map((e, i) => {
        const cls = ["tick"];
        if (e.is_keystone) cls.push("keystone");
        else if (e.type === "canon_milestone") cls.push("canon");
        else if (e.is_core_contribution) cls.push("core-tick");
        if (i === idx) cls.push("active");
        const tip = (e.label || e.id || "").toString().replace(/"/g, "&quot;");
        const star = e.is_keystone ? `★#${e.keystone_rank} · ` : "";
        const num = e.is_keystone
          ? `<span class="ks-num">${e.keystone_rank}</span>`
          : "";
        return `<button type="button" class="${cls.join(" ")}" data-i="${i}" aria-label="${tip}" title="${star}${tip}">
          ${num}
          <span class="tip">${star}${fmtDate(e.date)} · ${tip.length > 32 ? tip.slice(0, 30) + "…" : tip}</span>
        </button>`;
      })
      .join("");
    track.querySelectorAll(".tick").forEach((el) => {
      el.addEventListener("click", () => {
        idx = Number(el.dataset.i);
        renderFocus();
      });
    });
  }

  function renderMetrics() {
    const d = data.dual || {};
    const c = data.contribution || {};
    const p = data.penetration || {};
    const latest = p.latest || {};
    const ks = (data.keystones && data.keystones.count) || nav.filter((e) => e.is_keystone).length;
    const items = [
      { k: "核心贡献", v: d.core_n ?? c.strict_n ?? "—", h: "实质数学主张" },
      { k: "严格过程", v: d.rigorous_n ?? "—", h: "形式化 / 验证步骤" },
      { k: "关键节点", v: ks, h: "金色刻度 · Shift+←/→" },
      {
        k: "核心 / 万篇 math",
        v: latest.strict_per_10k != null ? Number(latest.strict_per_10k).toFixed(1) : "—",
        h: latest.year ? `${latest.year} · 若为 2026 则为不完全年` : "分母",
      },
    ];
    $("metricRow").innerHTML = items
      .map(
        (r) =>
          `<div class="metric"><div class="k">${r.k}</div><div class="v">${r.v}</div><div class="h">${r.h}</div></div>`
      )
      .join("");
  }

  function renderCharts() {
    const d = data.dual || {};
    const c = data.contribution || {};
    const coreY = d.yearly_core || c.yearly_strict || {};
    const rigY = d.yearly_rigorous || {};
    const years = Array.from(new Set([...Object.keys(coreY), ...Object.keys(rigY)])).sort();

    const box = $("chartCounts");
    if (!years.length) {
      box.innerHTML = `<p class="legend">暂无逐年双轨数据。</p>`;
    } else {
      const max = Math.max(
        ...years.map((y) => Math.max(Number(coreY[y] || 0), Number(rigY[y] || 0))),
        1
      );
      box.innerHTML = years
        .map((y) => {
          const w = Number(coreY[y] || 0);
          const s = Number(rigY[y] || 0);
          const ww = Math.max(w ? 4 : 0, Math.round((w / max) * 100));
          const sw = Math.max(s ? 4 : 0, Math.round((s / max) * 100));
          return `
            <div class="bar-row"><div>${y}</div>
              <div class="bar-track"><div class="bar-fill wide" style="width:${ww}%"></div></div>
              <div>${w}</div></div>
            <div class="bar-row"><div></div>
              <div class="bar-track"><div class="bar-fill strict" style="width:${sw}%"></div></div>
              <div style="color:#e8b84a">${s}</div></div>`;
        })
        .join("");
    }

    const penYears = (data.penetration && data.penetration.years) || [];
    const penBox = $("chartPen");
    if (!penYears.length) {
      penBox.innerHTML = `<p class="legend">请运行: python -m src.denominator</p>`;
    } else {
      const show = penYears.filter((r) => r.year >= 2022);
      const max = Math.max(...show.map((r) => Number(r.strict_per_10k || 0)), 0.01);
      penBox.innerHTML = show
        .map((r) => {
          const v = Number(r.strict_per_10k || 0);
          const w = Math.max(v ? 4 : 0, Math.round((v / max) * 100));
          return `<div class="bar-row"><div>${r.year}</div>
            <div class="bar-track"><div class="bar-fill strict" style="width:${w}%"></div></div>
            <div>${v.toFixed(1)}</div></div>`;
        })
        .join("");
      $("penFoot").textContent =
        "每万篇基于核心/实质集合除以当年 math.* 总量。2026 为不完全年。为自我披露代理下界。";
    }
  }

  function renderPhases() {
    const phases = data.phases || [];
    $("phaseGrid").innerHTML = phases
      .map(
        (ph) => `<div class="phase-item">
          <div>
            <strong>${ph.label || ph.id}</strong><br/>
            <span>${ph.start} → ${ph.end}</span>
          </div>
          <div class="n">${ph.strict_like ?? 0} 核心向</div>
        </div>`
      )
      .join("");
  }

  function renderFoot() {
    const proj = data.project || {};
    const lr = data.link_report || {};
    const bits = [];
    if (proj.github) bits.push(`<a href="${proj.github}" target="_blank" rel="noopener">GitHub</a>`);
    bits.push(`带摘要页链接的论文：${lr.paper_events_with_abs ?? "—"}`);
    bits.push(`生成于 ${(data.generated_at || "").slice(0, 19)}`);
    bits.push(`<a href="../" hreflang="en">English</a>`);
    $("dataFoot").innerHTML = bits.join(" · ");
  }

  function go(d) {
    idx = Math.min(nav.length - 1, Math.max(0, idx + d));
    renderFocus();
  }

  $("btnPrev").addEventListener("click", () => go(-1));
  $("btnNext").addEventListener("click", () => go(1));
  window.addEventListener("keydown", (ev) => {
    if (ev.key === "ArrowLeft") {
      ev.preventDefault();
      if (ev.shiftKey) jumpKeystone(-1);
      else go(-1);
    }
    if (ev.key === "ArrowRight") {
      ev.preventDefault();
      if (ev.shiftKey) jumpKeystone(1);
      else go(1);
    }
  });

  let tx = null;
  $("focusCard").addEventListener(
    "touchstart",
    (e) => {
      tx = e.changedTouches[0].screenX;
    },
    { passive: true }
  );
  $("focusCard").addEventListener(
    "touchend",
    (e) => {
      if (tx == null) return;
      const dx = e.changedTouches[0].screenX - tx;
      if (Math.abs(dx) > 45) go(dx < 0 ? 1 : -1);
      tx = null;
    },
    { passive: true }
  );

  renderKeystoneStrip();
  renderScrub();
  renderFocus();
  renderMetrics();
  renderCharts();
  renderPhases();
  renderFoot();
})();
"""


def main() -> None:
    ZH_DIR.mkdir(parents=True, exist_ok=True)

    # Verify coverage against current data.js
    data_js = (EN_DIR / "data.js").read_text(encoding="utf-8")
    payload = data_js.replace("window.ARXIVCOUNT_DATA = ", "").rstrip().rstrip(";")
    data = json.loads(payload)
    nav_ids = [e["id"] for e in data.get("navigable") or []]
    missing = [i for i in nav_ids if i not in EVENT_ZH]
    if missing:
        raise SystemExit(f"Missing Chinese translations for: {missing}")

    i18n = {
        "events": EVENT_ZH,
        "phases": PHASE_ZH,
        "subfields": SUBFIELD_ZH,
    }
    i18n_js = (
        "/* Auto-generated by scripts/build_zh_site.py — Chinese overlay for timeline data */\n"
        "window.ARXIVCOUNT_ZH = "
        + json.dumps(i18n, ensure_ascii=False, indent=2)
        + ";\n"
    )
    (ZH_DIR / "i18n.js").write_text(i18n_js, encoding="utf-8")
    (ZH_DIR / "index.html").write_text(INDEX_HTML, encoding="utf-8")
    (ZH_DIR / "app.js").write_text(APP_JS, encoding="utf-8")
    (ZH_DIR / "README.md").write_text(
        """# 中文时间轴

与英文版交互完全一致，文案与事件摘要为中文。

- 本地：打开 `web/timeline/zh/`（需同时有上级 `data.js`、`styles.css`）
- 线上：`https://justinzyc271828-sys.github.io/ArxivCount/zh/`

更新英文数据后若增删时间轴事件，请同步 `scripts/build_zh_site.py` 中的 `EVENT_ZH` 并重新运行：

```powershell
python scripts/build_zh_site.py
```
""",
        encoding="utf-8",
    )
    print(f"Wrote Chinese site → {ZH_DIR}")
    print(f"Translated events: {len(EVENT_ZH)} (nav={len(nav_ids)})")


if __name__ == "__main__":
    main()
