# blurt（写作版）· 代理指令

fork 自 `AGIHunt/blurt`（MIT）：`origin` = `semantic-craft/blurt`（公开），`upstream` = `AGIHunt/blurt`。全局规则见 `xw-tooling/AGENTS.md`。本仓库只放技能原件、脚本和录屏 App，不放任何论文内容、录屏或转写。

## 写作模式的不变量

写作模式对齐 `~/Projects/writing-infra`（私有）的 `docs/SPEC.md` 与 `writing-companion`。契约冲突时先看那边，再改这里；不要把私有仓库的论文材料、路径细节或讨论记录抄进本仓库。

- 不写正文、不写 `docs/argument-state.md`、不代写段落；口述句子只记录。
- `said`（机器转写，函数回填）、`quote`（仅纠正识别错误）、模型字段（`title` `restatement` `relation` `candidates` `search_hint`）三者分开，导出时分别进 A/M/C 栏。
- 写作项目默认只用本地转写；`transcribe.py` 的云端拦截不能被静默绕过。
- 画面读出的定位只是线索：正文位置经 `writing.py locate` 对照文件，文献原段须核对原文。

## 结构与改动

- 流程入口 `skills/blurt/SKILL.md`（控制在 200 行内），写作细则 `reference/writing.md`，条目定义 `reference/lenses/`。
- 可预测的工作进 `scripts/`（stdlib 优先，`uv` 内联依赖）；判断留给模型写在 lens 里。
- 写作相关代码尽量放独立文件（`writing.py`、写作 lens），少改上游文件，方便 `git merge upstream/main`。改到上游文件时保持其风格。
- 改 `review.html` 后在浏览器实际打开审核页核对；改 Swift 后至少 `swiftc -swift-version 5 -typecheck skills/blurt/recorder/macos/BlurtRecorder.swift`。

## 检查

```bash
python3 -m unittest discover -s tests
```

CI（`.github/workflows/check.yml`）另跑语法检查和每个脚本的 `--help`。

## 发布

改动技能行为时更新 `.claude-plugin/plugin.json` 版本和 `TODO.md`。论文项目通过 `.agents/skills/blurt` 软链接入 `skills/blurt`，软链不入 Git。
