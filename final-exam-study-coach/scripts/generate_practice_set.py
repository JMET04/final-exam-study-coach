#!/usr/bin/env python3
"""Generate a tiered practice scaffold for a topic."""

from __future__ import annotations

import argparse
from pathlib import Path


OPERATION_PROMPTS = {
    "recall": {
        "identify": "闭卷列出 `{topic}` 的 5 个关键词，并标出最容易漏的 1 个。",
        "basic": "不用看资料，写出 `{topic}` 的定义/要点/适用条件。",
        "exam": "按期末小题格式完成 1 道 `{topic}` 识记题，要求关键词完整。",
        "transfer": "换一种问法重新回答 `{topic}`，检查是否只是背原句。",
    },
    "explain": {
        "identify": "判断题目要求解释概念、原因、机制还是意义，并写触发词。",
        "basic": "用自己的话向同学解释 `{topic}`，避免照抄定义。",
        "exam": "按考试格式写一段 `{topic}` 解释题答案，包含概念、原因和例子。",
        "transfer": "把 `{topic}` 放到一个新情境中解释，说明哪些要点不变。",
    },
    "compare": {
        "identify": "列出 `{topic}` 中最容易混淆的两个概念，并写区分标准。",
        "basic": "做一张 3 列对比表：定义、适用条件、典型误区。",
        "exam": "按期末辨析/比较题格式回答 `{topic}`，至少写 3 个比较维度。",
        "transfer": "换一组相似概念，用同样维度重新比较。",
    },
    "calculate": {
        "identify": "判断题目应使用 `{topic}` 的哪个公式/步骤，并圈出已知量和所求量。",
        "basic": "完成 1 道 `{topic}` 基础计算题，写出代入前的公式。",
        "exam": "按考试格式完成 1 道 `{topic}` 计算题，保留步骤分和结果检查。",
        "transfer": "改变一个条件重做，说明公式或步骤是否变化。",
    },
    "derive_prove": {
        "identify": "写出 `{topic}` 证明题的条件、要证结论和可能使用的桥梁。",
        "basic": "补全 `{topic}` 的证明骨架：已知 -> 中间结论 -> 目标。",
        "exam": "闭卷完成 1 道 `{topic}` 推导/证明题，标出每一步依据。",
        "transfer": "把条件改弱或改强，判断原证明哪里需要调整。",
    },
    "solve_apply": {
        "identify": "判断这个情境是否适合用 `{topic}`，写出触发条件。",
        "basic": "用 `{topic}` 解决一个标准应用题，先写方法选择理由。",
        "exam": "按期末大题格式完成 1 道 `{topic}` 应用题，写清部分分步骤。",
        "transfer": "换一个材料/案例/参数，说明为什么仍可用或不能用。",
    },
    "analyze_case": {
        "identify": "从案例中划出与 `{topic}` 有关的事实、主体、冲突和问题。",
        "basic": "把案例事实映射到 `{topic}` 的概念或框架。",
        "exam": "按案例分析题格式回答：判断、依据、过程、结论。",
        "transfer": "换一个案例，保留同一分析框架重新判断。",
    },
    "design_create": {
        "identify": "列出 `{topic}` 设计任务的目标、约束、资源和评价标准。",
        "basic": "画出一个最小可行方案/结构图/流程图。",
        "exam": "按考试要求完成 1 个 `{topic}` 设计题，说明方案理由和限制。",
        "transfer": "改变约束条件，指出方案需要修改的地方。",
    },
    "critique_evaluate": {
        "identify": "判断评价对象、评价标准和需要引用的依据。",
        "basic": "列出 `{topic}` 的 2 个优点、2 个缺点和各自证据。",
        "exam": "按评价题格式回答 `{topic}`：结论、标准、依据、反例或限制。",
        "transfer": "换一个立场或标准，重新评价并说明差异。",
    },
    "translate_interpret": {
        "identify": "判断要翻译/解读的是术语、句子、图表、数据还是结果。",
        "basic": "把 `{topic}` 用另一种表达方式复述，并保留关键含义。",
        "exam": "按考试格式完成 1 道 `{topic}` 翻译/图表/文本解读题。",
        "transfer": "换一段材料或图表，用同一解读步骤处理。",
    },
    "implement_debug": {
        "identify": "判断 `{topic}` 需要的数据结构、输入输出和边界条件。",
        "basic": "写出 `{topic}` 的伪代码或核心步骤。",
        "exam": "按考试格式完成 1 道 `{topic}` 编程/调试题，说明复杂度或错误原因。",
        "transfer": "加入边界条件或错误代码，指出如何修正。",
    },
    "diagnose_classify": {
        "identify": "列出 `{topic}` 的分类标准或诊断指标。",
        "basic": "给一个简单情境，判断它属于哪一类并说明依据。",
        "exam": "按考试格式完成 1 道 `{topic}` 诊断/分类题，写出排除项。",
        "transfer": "加入干扰信息，重新诊断并说明为什么不选其他类。",
    },
    "write_argue": {
        "identify": "判断 `{topic}` 写作题的立场、关键词和评分点。",
        "basic": "写出论点、3 个分论点和每个分论点的证据。",
        "exam": "按期末论述/作文格式完成 `{topic}`，包含开头、主体和结论。",
        "transfer": "换一个角度或材料，保留论证骨架重新写。",
    },
}


def normalize_operation(operation: str, qtype: str) -> str:
    text = f"{operation} {qtype}".lower()
    aliases = [
        ("derive_prove", ["证明", "推导", "prove", "derive"]),
        ("calculate", ["计算", "求解", "calculate", "compute"]),
        ("implement_debug", ["编程", "算法", "代码", "debug", "program"]),
        ("analyze_case", ["案例", "case", "材料分析"]),
        ("design_create", ["设计", "方案", "design"]),
        ("critique_evaluate", ["评价", "评析", "evaluate", "critique"]),
        ("translate_interpret", ["翻译", "解读", "interpret", "translate"]),
        ("diagnose_classify", ["诊断", "分类", "diagnose", "classify"]),
        ("write_argue", ["论述", "作文", "写作", "argue", "essay"]),
        ("compare", ["比较", "辨析", "compare", "contrast"]),
        ("explain", ["解释", "说明", "define", "explain"]),
        ("recall", ["记忆", "背诵", "默写", "recall"]),
    ]
    if operation in OPERATION_PROMPTS:
        return operation
    for key, words in aliases:
        if any(word in text for word in words):
            return key
    return "solve_apply"


def concrete_question(course: str, topic: str, qtype: str, level: str, operation: str = "") -> str:
    text = f"{course} {topic} {qtype} {operation}".lower()
    if "特征" in text:
        if level == "identify":
            return "给出矩阵 A=[[2,0],[0,3]]，判断向量 (1,0)、(1,1) 哪个是特征向量，并说明理由。"
        if level == "basic":
            return "求 A=[[2,1],[0,2]] 的特征值，并判断它是否一定有两个线性无关特征向量。"
        if level == "exam":
            return "已知 2 阶矩阵 A 的特征值为 1,3，对应特征向量分别为 (1,1),(1,-1)，写出一种对角化表示并说明步骤。"
        return "把矩阵改成 A=[[1,1],[0,1]]，判断它能否对角化，并解释和上一题的差别。"
    if "贝叶斯" in text or "条件概率" in text:
        if level == "identify":
            return "判断题目是在求 P(A|B) 还是 P(B|A)：已知检测阳性，求真的患病概率。"
        if level == "basic":
            return "某病患病率 1%，患病时检测阳性率 99%，未患病时假阳性率 5%。求阳性后患病概率。"
        if level == "exam":
            return "三台机器生产同类产品，占比 2:3:5，次品率分别为 1%、2%、4%。随机抽到次品，求来自第三台机器的概率。"
        return "如果第三台机器产量占比变小但次品率升高，判断后验概率会如何变化，并重新计算一个自设数值例子。"
    if "导数" in text:
        if level == "identify":
            return "判断题目是求导数定义、切线斜率，还是单调性应用，并写触发词。"
        if level == "basic":
            return "用导数定义解释 f(x)=x^2 在 x=1 处导数表示什么。"
        if level == "exam":
            return "求函数 f(x)=x^3-3x 的单调区间和极值，并写出判定依据。"
        return "把函数换成含参数 f(x)=x^3-ax，讨论 a>0 时极值如何变化。"
    if "bfs" in text or "广度" in text:
        if level == "identify":
            return "给一个无权图最短路径问题，判断应优先考虑 BFS 还是 DFS，并说明理由。"
        if level == "basic":
            return "从 A 开始，对边集 AB, AC, BD, CE, EF 写出 BFS 访问顺序和队列变化。"
        if level == "exam":
            return "写出 BFS 伪代码，说明 visited 应该在入队时还是出队时标记，并分析复杂度。"
        return "把图改成有环图，说明如果不维护 visited 会发生什么，并给出修正。"
    return prompt_for(course, topic, qtype, level, operation)


def prompt_for(course: str, topic: str, qtype: str, level: str, operation: str = "") -> str:
    operation_key = normalize_operation(operation, qtype)
    prompt = OPERATION_PROMPTS.get(operation_key, {}).get(level)
    if prompt:
        return prompt.format(course=course, topic=topic, qtype=qtype)
    if level == "identify":
        return f"判断下面题目应该使用 `{topic}` 还是其他方法，并写出触发关键词。"
    if level == "basic":
        return f"完成 1 道 `{topic}` 的标准基础题，要求写出定义/公式/第一步。"
    if level == "exam":
        return f"按期末考试格式完成 1 道 `{topic}` 的{qtype}题，写清可得部分分的步骤。"
    if level == "transfer":
        return f"把 `{topic}` 换一个情境或条件再做一题，说明为什么仍然适用。"
    return f"围绕 `{topic}` 做一题。"


def scoring_for(level: str) -> list[str]:
    base = ["题型判断正确", "第一步合理", "关键公式/规则正确"]
    if level in {"exam", "transfer"}:
        base.extend(["步骤完整", "能解释易错点", "结果检查"])
    return base


def build(course: str, topic: str, qtype: str, levels: list[str], operation: str = "") -> str:
    operation_key = normalize_operation(operation, qtype)
    lines = [f"# {course} - {topic} 分层练习", ""]
    lines.extend([f"- 题型：{qtype}", f"- 考试操作：{operation_key}", ""])
    for level in levels:
        lines.extend(
            [
                f"## {level}",
                "",
                f"**练习目标**：检验 `{topic}` 的 `{level}` 层能力。",
                f"**题型**：{qtype}",
                f"**考试操作**：{operation_key}",
                f"**题目**：{concrete_question(course, topic, qtype, level, operation_key)}",
                "",
                "**先写**：",
                "1. 题型判断：",
                "2. 第一步：",
                "3. 关键公式/规则：",
                "",
                "**评分点**：",
            ]
        )
        lines.extend(f"- {item}" for item in scoring_for(level))
        lines.extend(
            [
                "",
                "**不会时补**：",
                "- 读不懂题：补术语和已知/所求。",
                "- 不会第一步：补触发条件和入口。",
                "- 推不下去：补前置公式/步骤链。",
                "- 换题不会：做一道变式题。",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a tiered practice scaffold.")
    parser.add_argument("--course", required=True)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--type", default="综合")
    parser.add_argument("--operation", default="", help="Universal exam operation, e.g. recall, analyze_case, write_argue")
    parser.add_argument("--levels", nargs="+", default=["identify", "basic", "exam", "transfer"])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    text = build(args.course, args.topic, args.type, args.levels, args.operation)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
