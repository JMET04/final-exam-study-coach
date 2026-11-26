#!/usr/bin/env python3
"""Generate a tiered practice scaffold for a topic."""

from __future__ import annotations

import argparse
from pathlib import Path


PROMPTS = {
    "recall": {
        "identify": "闭卷列出 `{topic}` 的5个关键词，并标出最容易漏的1个。",
        "basic": "不用看资料，写出 `{topic}` 的定义、要点或适用条件。",
        "exam": "按期末小题格式完成1道 `{topic}` 识记题，要求关键词完整。",
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
        "basic": "做一张3列对比表：定义、适用条件、典型误区。",
        "exam": "按期末辨析/比较题格式回答 `{topic}`，至少写3个比较维度。",
        "transfer": "换一组相似概念，用同样维度重新比较。",
    },
    "calculate": {
        "identify": "判断题目应使用 `{topic}` 的哪个公式/步骤，并圈出已知量和所求量。",
        "basic": "完成1道 `{topic}` 基础计算题，写出代入前的公式。",
        "exam": "按考试格式完成1道 `{topic}` 计算题，保留步骤分和结果检查。",
        "transfer": "改变一个条件重做，说明公式或步骤是否变化。",
    },
    "solve_apply": {
        "identify": "判断这个情境是否适合用 `{topic}`，写出触发条件。",
        "basic": "用 `{topic}` 解决一个标准应用题，先写方法选择理由。",
        "exam": "按期末大题格式完成1道 `{topic}` 应用题，写清部分分步骤。",
        "transfer": "换一个材料/案例/参数，说明为什么仍可用或不能用。",
    },
    "analyze_case": {
        "identify": "从案例中划出与 `{topic}` 有关的事实、主体、冲突和问题。",
        "basic": "把案例事实映射到 `{topic}` 的概念或框架。",
        "exam": "按案例分析题格式回答：判断、依据、过程、结论。",
        "transfer": "换一个案例，保留同一分析框架重新判断。",
    },
    "write_argue": {
        "identify": "判断 `{topic}` 写作题的立场、关键词和评分点。",
        "basic": "写出论点、3个分论点和每个分论点的证据。",
        "exam": "按期末论述/作文格式完成 `{topic}`，包含开头、主体和结论。",
        "transfer": "换一个角度或材料，保留论证骨架重新写。",
    },
}

ALIASES = {
    "记忆": "recall", "背诵": "recall", "识记": "recall",
    "解释": "explain", "说明": "explain", "定义": "explain",
    "比较": "compare", "辨析": "compare",
    "计算": "calculate", "求解": "calculate",
    "应用": "solve_apply", "运用": "solve_apply",
    "案例": "analyze_case", "材料": "analyze_case",
    "论述": "write_argue", "写作": "write_argue",
}


def normalize_operation(operation: str, qtype: str) -> str:
    text = f"{operation} {qtype}"
    if operation in PROMPTS:
        return operation
    for word, key in ALIASES.items():
        if word in text:
            return key
    return "solve_apply"


def scoring_for(level: str) -> list[str]:
    base = ["题型判断正确", "第一步合理", "关键公式/规则正确"]
    if level in {"exam", "transfer"}:
        base.extend(["步骤完整", "能解释易错点", "结果检查或结论回扣"])
    return base


def concrete_question(course: str, topic: str, qtype: str, level: str, operation: str) -> str:
    text = f"{course} {topic} {qtype} {operation}"
    if "有效应力" in text:
        return {
            "identify": "判断题目给出总应力和孔隙水压力时，应写哪个有效应力公式？",
            "basic": "已知总应力 sigma=120kPa，孔隙水压力 u=35kPa，求有效应力 sigma'。",
            "exam": "解释 sigma = sigma' + u 的物理意义，并说明孔隙水压力增大时有效应力如何变化。",
            "transfer": "若地下水位上升导致 u 增大，判断土体抗剪强度趋势，并说明理由。",
        }.get(level, "")
    if "达西" in text or "渗流" in text:
        return {
            "identify": "判断 q = k i A 中 q、k、i、A 分别代表什么。",
            "basic": "已知 k=1e-5m/s, i=0.8, A=2m^2，求渗流量 q。",
            "exam": "解释水力坡降和临界水力坡降的关系，并说明何时可能发生渗透破坏。",
            "transfer": "若土样颗粒更细、孔隙更小，判断 k 和 q 的变化趋势。",
        }.get(level, "")
    if "新民主主义" in text:
        return {
            "identify": "列出新民主主义革命的对象、动力、领导力量和前途。",
            "basic": "用自己的话解释新民主主义革命为什么不是旧式资产阶级革命。",
            "exam": "论述新民主主义革命与社会主义革命的关系。",
            "transfer": "把材料中的革命任务归入新民主主义革命理论框架，并说明理由。",
        }.get(level, "")
    return PROMPTS.get(operation, PROMPTS["solve_apply"]).get(level, "").format(course=course, topic=topic, qtype=qtype)


def build(course: str, topic: str, qtype: str, levels: list[str], operation: str = "") -> str:
    op = normalize_operation(operation, qtype)
    lines = [f"# {course} - {topic} 分层练习", "", f"- 题型：{qtype}", f"- 考试操作：{op}", ""]
    for level in levels:
        lines.extend([f"## {level}", "", f"**练习目标**：检查 `{topic}` 的 `{level}` 层能力。", f"**题目**：{concrete_question(course, topic, qtype, level, op)}", "", "**先写**：", "1. 题型判断：", "2. 第一步：", "3. 关键公式/规则：", "", "**评分点**："])
        lines.extend(f"- {item}" for item in scoring_for(level))
        lines.extend(["", "**不会时补**：", "- 读不懂题：补术语和已知/所求。", "- 不会第一步：补触发条件和入口。", "- 推不下去：补前置公式/步骤链。", "- 换题不会：做一道变式题。", ""])
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a tiered practice scaffold.")
    parser.add_argument("--course", required=True)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--type", default="综合")
    parser.add_argument("--operation", default="")
    parser.add_argument("--levels", nargs="+", default=["identify", "basic", "exam", "transfer"])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    text = build(args.course, args.topic, args.type, args.levels, args.operation)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
