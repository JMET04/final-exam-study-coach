# 期末复习与大学带学 · v0.5.0

把课本、教师课件、作业和学习断点组织成可理解、可应用的知识与解题路径。支持大学课程持续学习、期末/补考复习、拍照批改、个性化计划和教师协作。

新版重点是先想完整、再讲当前问题：用途和原理、条件分支、参数查表来源、实际几何、完整验收与失败回退。新名词和符号先解释，位置量配图；有动画收益时先在对话讲因果，再展示极简手动单段。动画中不放长篇文字解说。

## 安装与选择

- **基础插件**：选择本仓库根目录，入口 `.codex-plugin/plugin.json`，只加载 `skills/`。
- **只安装skill**：把 `skills/final-exam-study-coach/` 复制到所用AI的skills目录。阅读 [SKILL.md](skills/final-exam-study-coach/SKILL.md)。
- **可选书灵**：另选 `optional/book-spirit/`，或复制其中 `skills/book-spirit/`。工具为Python 3.10+标准库，无MCP或API依赖。未启用时基础插件不会下载书、启动服务或外发请求。
- **书包**：在 [可选书库目录](optional/book-library/README.md) 按书名和版本下载。独立公共书库为 [JMET04/book-spirit-library](https://github.com/JMET04/book-spirit-library)，支持Fork/PR投稿；本仓库的可选目录提供相同格式镜像。

基础流程不依赖Python；运行辅助脚本时按 `--help` 安装相应可选依赖。各平台的插件/skill安装能力不同，纯文本AI也能直接读取规则与书包JSON。

## 使用示例

```text
根据我的课件和教材带我学受弯构件。课件优先，先讲用途和原理，
给出整题路线；每个新符号说明位置与单位，不把互动变成简单算术问答。
```

```text
用书灵的《混凝土结构设计原理》第七版解释中性轴和等效压区。
先检查这个知识快照的覆盖；我不懂时只展示相关动画段，并结合讲解词解释。
```

```text
把课程分成几个独立学习对话。同步最后学生证据和待学输出，
最新发出的内容我还没学，不要推进掌握度，也不要恢复暂停的后台整理。
```

## 书灵是可选的通用资产

公共书包按书籍版本分目录，含预建专家专题、概念关系、条件与边界、动画、关键帧和独立讲解词。JSON/JSONL、HTML和SVG可由不同AI使用；调用工具只生成上下文，不绑定模型、不自动调用API。

原页核读、知识覆盖、全书专家验收、全书动画覆盖分别公布。部分书只完成了一部分，不因上传而改成完成。公开资产不含原教材PDF、扫描页、整页OCR或学习者私人进度；引用书页需自行合法持有原书。

## 验证与贡献

```text
python optional/book-spirit/scripts/book_asset.py validate-catalog optional/book-library
python tests/test_book_assets.py optional/book-library
```

书包格式、校验、授权和投稿要求见 [书库贡献指南](optional/book-library/CONTRIBUTING.md)。欢迎通过PR提交新书、版本、解释修正及动画；未经复核的投稿不能自称全书完成。完整流程改进与边界见 [CHANGELOG](CHANGELOG.md)。

代码与原创解释采用 [MIT](LICENSE)。原书及第三方材料的权利不因资产引用而改变；不要求贡献者上传无权再分发的书籍原文。
