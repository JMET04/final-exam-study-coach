#!/usr/bin/env python3
"""Audit smart-course blueprints against detailed guide requirements."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIREMENTS = [
    ("student_centered", "以学生为中心", ["guide_alignment.student_centered"]),
    ("digital_intelligence", "AI与大数据数智赋能", ["guide_alignment.digital_intelligence"]),
    ("teacher_student_ai", "师-生-机三元协同", ["teacher_student_ai_model.teacher_role", "teacher_student_ai_model.student_role", "teacher_student_ai_model.ai_role"]),
    ("hybrid_teaching", "线上线下混合教学", ["guide_alignment.hybrid_teaching", "hybrid_teaching_design.online", "hybrid_teaching_design.offline"]),
    ("personalized_learning", "个性化学习路径", ["guide_alignment.personalized_learning", "student_digital_profile"]),
    ("dynamic_optimization", "数据驱动动态优化", ["guide_alignment.dynamic_optimization", "feedback_loop", "resource_lifecycle_management"]),
    ("program_alignment", "对齐学校与专业培养目标", ["course_objectives.school_program_alignment"]),
    ("knowledge_objective", "知识目标", ["course_objectives.knowledge"]),
    ("ability_objective", "能力目标", ["course_objectives.ability"]),
    ("quality_objective", "素质目标", ["course_objectives.quality"]),
    ("digital_literacy_ethics_objective", "数字素养与AI伦理目标", ["course_objectives.digital_literacy_ethics"]),
    ("interdisciplinary_objective", "跨学科或真实情境目标", ["course_objectives.interdisciplinary"]),
    ("measurable_verbs", "可测量行为动词", ["course_objectives.measurable_verbs"]),
    ("smart_preview", "智能预习", ["smart_preview.before_class", "smart_preview.diagnosis"]),
    ("resource_on_demand", "资源按需推送", ["resource_on_demand.resource_types", "resource_on_demand.matching_rule"]),
    ("ai_qa", "AI问答支持", ["ai_qa_support.scope", "agent_qa_coverage"]),
    ("offline_high_order", "线下高阶讨论实践项目", ["offline_high_order_activities"]),
    ("knowledge_graph", "知识图谱", ["knowledge_graph"]),
    ("ability_graph", "能力图谱", ["ability_graph"]),
    ("problem_graph", "问题图谱", ["problem_graph"]),
    ("ideological_graph", "课程思政图谱", ["ideological_political_graph"]),
    ("layered_tasks", "基础-提升-挑战分层任务", ["layered_tasks"]),
    ("ai_case_virtual_simulation", "AI案例分析或虚拟仿真", ["ai_case_virtual_simulation_tasks"]),
    ("learning_behavior_tracking", "学习行为采集分析", ["learning_behavior_tracking.events", "learning_behavior_tracking.metrics"]),
    ("course_knowledge_base", "课程知识库", ["course_knowledge_base.materials", "course_knowledge_base.governance"]),
    ("mooc_video_plan", "MOOC式单元视频资源", ["mooc_video_plan.unit_videos"]),
    ("assessment_bank", "按知识点组织的测评资源库", ["assessment_bank"]),
    ("formative_summative", "形成性与终结性评价", ["evaluation_design.formative", "evaluation_design.summative"]),
    ("multi_subject_evaluation", "多主体评价", ["evaluation_design.multi_subject"]),
    ("student_digital_profile", "学生数字画像", ["student_digital_profile.knowledge_mastery", "student_digital_profile.resource_trajectory", "student_digital_profile.interaction_data"]),
    ("mistake_profile", "错题错因画像与考前提醒", ["student_digital_profile.mistake_profile"]),
    ("ai_initial_human_review", "AI初评与人工审核", ["evaluation_design.ai_initial_human_review", "ai_ethics_review.human_review_required"]),
    ("resource_lifecycle", "资源动态管理与审核", ["resource_lifecycle_management.versioning", "resource_lifecycle_management.audit"]),
    ("privacy_integrity_ip", "隐私、学术诚信和知识产权", ["ai_ethics_review.privacy", "ai_ethics_review.academic_integrity", "ai_ethics_review.ip_compliance"]),
    ("construction_path", "四阶段建设路径", ["construction_path"]),
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def get_path(data: Any, dotted: str) -> Any:
    current = data
    for part in dotted.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def audit(data: dict[str, Any]) -> dict[str, Any]:
    items = []
    for req_id, title, paths in REQUIREMENTS:
        evidence = [path for path in paths if has_value(get_path(data, path))]
        ok = len(evidence) == len(paths)
        items.append(
            {
                "id": req_id,
                "requirement": title,
                "status": "pass" if ok else "missing",
                "evidence": evidence,
                "missing_paths": [path for path in paths if path not in evidence],
                "next_action": "" if ok else f"补充 {title} 对应字段和样例证据。",
            }
        )
    return {
        "version": "smart-course-alignment-audit-v2",
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "summary": {
            "pass": sum(1 for item in items if item["status"] == "pass"),
            "missing": sum(1 for item in items if item["status"] == "missing"),
            "total": len(items),
        },
        "items": items,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# 智慧课程建设指南对齐审计",
        "",
        f"- 通过: {report['summary']['pass']}/{report['summary']['total']}",
        f"- 缺失: {report['summary']['missing']}",
        "",
        "| 要求 | 状态 | 证据字段 | 下一步 |",
        "| --- | --- | --- | --- |",
    ]
    for item in report["items"]:
        lines.append(
            f"| {item['requirement']} | {item['status']} | {', '.join(item['evidence']) or '无'} | {item['next_action']} |"
        )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit smart-course blueprint alignment.")
    parser.add_argument("blueprint", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()

    report = audit(load_json(args.blueprint))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(report, args.markdown)
    print(f"wrote {args.output}")
    print(f"wrote {args.markdown}")


if __name__ == "__main__":
    main()
