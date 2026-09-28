<p align="center"><img src="assets/logo.png" width="112" alt="blurt"></p>

# blurt · 写作版

边看屏幕边说话，录下来交给 agent 整理。本仓库 fork 自 [AGIHunt/blurt](https://github.com/AGIHunt/blurt)（MIT），保留其录屏、本地转写、截图与审核页，按论文写作和 writing-infra（作者自用的写作基础设施）的约定加了写作模式。

## 写作时怎么用

在已接入 writing-infra 的论文项目里，对 agent 说“开始录”，框出要录的区域，然后照常读、照常说：

- **读自己的稿子**：“这段跳了一步”“这个概念前后不一致”。整理成**修改意见**，按画面上那句话回到正文 `path:line`。
- **读文献**（Zotero 阅读器、PDF、知网、Westlaw……）：“这个观点正好能反驳……”。整理成**阅读反应**，记下画面上的题名、阅读器页码和原段。
- **边想边说**：主张变了、冒出反驳、放下一个方向。整理成**口述思考**；口述想放进正文的句子单独标出。
- **说到要找的材料**：“这里得找个判例”。记成**资料缺口**，留给 `search-router` 去找原文。

录完点“完成”，agent 在本机转写、拆条、截图，打开审核页：`A` 保留 · `X` 丢弃 · `J/K` 上下条，原话可以直接改。最后导出一份 writing-companion 格式的讨论记录，分 A 作者原话、M 模型复述、C 模型建议、S 来源、Q 待作者决定五栏；另附按正文顺序排列的修改清单、资料缺口、口述句子，以及机器转写与原话的差异。

## 写作模式守住的事

- **正文由作者亲写。** 不改正文和 `docs/argument-state.md`，不代写段落；口述句子只在作者明确要求时，经 writing-companion 的保存工具原样写入。
- **作者原话、模型复述、机器转写分开存。** `said` 是机器转写，由函数按时间段抄出，不手改；`quote` 只纠正识别错误；复述、候选关系和建议都标成模型的。审核页“保留”只表示这条值得留，不表示采纳了复述。
- **语音不出本机。** 写作项目里 `transcribe.py` 拒绝云端转写，除非作者同意并加 `--allow-cloud`。
- **画面只是线索。** 正文位置用 `writing.py locate` 对照稿件文件确认，模糊匹配和多处匹配都会标出来；文献原段在引用前仍要核对原文。

## 安装与接线

依赖 `uv` 和 `ffmpeg`。首次运行时 agent 会跑 `doctor.py`，按机器挑选本地语音模型，并安装菜单栏 App（`⌥⇧R` 随处开录）。

论文项目按 writing-infra 的白名单接入，然后在项目的 `.blurt/config.json` 写上稿件路径：

```bash
ln -s ~/Projects/blurt/skills/blurt <论文项目>/.agents/skills/blurt
```

```json
{ "writing": { "manuscript": ["drafts/paper.md"], "glossary": "docs/glossary.md", "discussions": "docs/discussions" } }
```

建议把 `.blurt/sessions/` 加进论文项目的 `.gitignore`，录屏只留在本机。

软件项目照旧可用：bug、想法、笔记、待办，以及飞书 / CSV / GitHub 导出，行为与上游一致。

## 目录

- [skills/blurt/SKILL.md](skills/blurt/SKILL.md)：agent 的流程入口；写作模式见 [reference/writing.md](skills/blurt/reference/writing.md)，四种写作条目见 [reference/lenses/](skills/blurt/reference/lenses/)。
- `skills/blurt/scripts/`：录制、转写、截图、审核页、导出；`writing.py` 负责原话回填、正文定位和讨论记录导出。
- `skills/blurt/recorder/macos/`：原生录屏 App（ScreenCaptureKit）。
- `tests/`：`python3 -m unittest discover -s tests`。

## 与上游同步

`origin` 是 `semantic-craft/blurt`，`upstream` 是 `AGIHunt/blurt`。合并上游更新：

```bash
git fetch upstream && git merge upstream/main
```

冲突集中在 `SKILL.md`、`review.html` 和 `export_local.py` 的标签表，写作相关代码大多在单独的文件里。

<p align="center"><sub>MIT · 原作 <a href="https://github.com/AGIHunt">AGI Hunt</a> · 写作版 semantic-craft</sub></p>
