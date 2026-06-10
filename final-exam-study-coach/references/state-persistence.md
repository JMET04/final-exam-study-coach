# 学习状态持久化

目标：让复习不是一次性计划，而是能跨多天跟踪“学过什么、哪里不会、下次何时复习”。

## 状态文件

建议每门课维护一个 JSON 状态文件：

```json
{
  "course": "线性代数",
  "exam_date": "2026-06-20",
  "target": "80+",
  "current_score_estimate": null,
  "topics": {
    "特征向量": {
      "status": "can_recognize",
      "last_practiced": "2026-05-28",
      "next_review": "2026-05-29",
      "evidence": ["做了3题，错2题"],
      "mistakes": ["把 P(A|B) 和 P(B|A) 写反"]
    }
  },
  "sessions": []
}
```

## 每次学习后更新

必须更新：

- 完成了什么。
- 正确率/估分。
- 错因。
- 相关知识点状态。
- 下次复习日期。
- 当前检查点，确保上下文压缩后能继续。

## 状态升级规则

- `unknown` -> `can_recognize`：能认出题型或概念。
- `can_recognize` -> `can_explain`：能用自己的话解释。
- `can_explain` -> `can_solve_slowly`：能独立做出基础题。
- `can_solve_slowly` -> `exam_ready`：能限时、闭卷、稳定做考试题。

降级也允许：如果隔几天复测失败，状态下调一级，并安排更近的复习。

## 使用脚本

```bash
python scripts/update_study_state.py state.json --course 线性代数 --topic 特征向量 --result correct --confidence 4 --notes "限时题2/3正确"
```

脚本会更新 `last_practiced`、`next_review`、学习记录，并生成 Markdown 摘要。

如果学生没完成任务：

```bash
python scripts/update_study_state.py state.json --course 线性代数 --topic 特征向量 --result missed --confidence 1 --notes "原计划今晚90分钟未开始"
```

这会记录拖延事件、安排更近的复习，并生成 `state_checkpoint.md`。
