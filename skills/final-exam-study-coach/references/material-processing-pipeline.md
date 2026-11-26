# 材料处理流水线

目标：把教材、PPT、DOCX、TXT/Markdown、往年题、错题和用户口述转成可排计划的数据，而不是只做摘要。

## 处理顺序

1. **材料登记**
   - 文件名、类型、来源、是否官方、是否往年题、是否有答案。
   - 标出风险：扫描不清、缺页、无答案、来源不可靠。

2. **结构抽取**
   - 教材/PPT：标题、章节、页码、例题、章末题。
   - 往年题：题号、分值、题型、考点、重复模式。
   - 笔记/错题：老师强调词、易错点、学生薄弱点。

3. **主题合并**
   - 把同义主题合并成统一知识点。
   - 例如“特征值”“特征向量”“对角化”可以在同一线代链条里，但做题入口不同，要保留区别。
   - 文科、思政、历史、管理学概念课合并主题时，必须保留二级采分细节；不能把“总路线、对象、动力、性质、前途、基本纲领”全部压成一个看不见细节的主题名。
   - 理工、工程经济和管理类课程合并主题时，也必须保留二级细节：公式展开式、适用条件、图表画法、边界情况、单位口径、典型错法和老师符号。

4. **证据标注**
   - 官方范围：`explicit`
   - 往年题/作业反复出现：`repeated`
   - 课程核心但未直接出现：`inferred`
   - 证据不足：`uncertain`

5. **输出结构化结果**
   - `material_inventory.md`：给人看的材料清单和主题表。
   - `material_inventory.json`：给脚本继续排计划。
   - `coverage_checklist`：正式带学前必须有的完整知识清单，拆成 `mainline_items` 和 `detail_items`。前者用于保分进度，后者用于高分细节进度。

## 结构化 JSON 字段

```json
{
  "course": "课程名",
  "sources": [
    {
      "path": "文件路径",
      "type": "pdf/pptx/docx/txt/md/json",
      "role": "textbook/slides/past_paper/notes/scope/wrong_questions",
      "trust": "official/repeated/user/inferred",
      "summary": "材料摘要"
    }
  ],
  "topics": [
    {
      "name": "知识点",
      "evidence": "explicit/repeated/inferred/uncertain",
      "question_type": "计算/证明/简答/编程/论述",
      "source_refs": ["文件:页码或题号"],
      "signals": ["老师强调", "2023大题", "作业重复"],
      "status": "unknown",
      "coverage_layer": "mainline/detail",
      "coverage_status": "not_started/introduced/practiced/checked",
      "detail_items": ["公式变式", "图表规范", "易混边界"]
    }
  ]
}
```

## 使用脚本

可先运行：

```bash
python scripts/extract_materials.py materials_dir --course 高等数学 --output-dir extracted
```

脚本能处理 `.txt`、`.md`、`.json`，并尽量从 `.docx`、`.pptx` 中抽 XML 文本；PDF 需要本机存在 `pypdf` 才能自动抽取，否则会登记为“需要手动摘录”。

脚本结果只是初筛。最终诊断仍要由 Codex 结合用户目标、考试日期和材料可信度判断。

## 质量门槛

材料处理结果必须至少回答：

- 哪些材料最可信？
- 哪些知识点有明确考试证据？
- 哪些题型重复出现？
- 文科课哪些一级主题已经抽到二级采分细节，哪些仍只是章节标题或 OCR 噪声？
- 每门课是否已经形成主线清单和细节清单？主线覆盖率和细节覆盖率能否被当前证据支撑？
- 哪些知识点只能算“保分骨架已列出”，还不能算“高分细节已覆盖”？
- 哪些信息缺失会影响计划？
- 下一步是补材料、做诊断题，还是直接排计划？

如果文科材料处理结果只有一级标题或大多数证据为 `inferred`，只能进入“骨架级计划”；进入带练前必须补一张细节覆盖表，或明确告知用户细节覆盖不足。
