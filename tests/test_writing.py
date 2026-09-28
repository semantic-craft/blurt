"""Writing-project helpers: said / locate / export, and project config discovery (stdlib only).

  python -m unittest discover -s tests
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "blurt" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import writing  # noqa: E402
from _common import project_config, project_root  # noqa: E402

DRAFT = """# 一、问题

公开规则并不等于个别理由。
申请人仍然无法知道这次拒绝为何适用于自己。

## 二、例外

紧急维护时可以先通知、后补理由。
公开规则并不等于个别理由。
"""

TRANSCRIPT = {"backend": "sensevoice", "model": "sense-voice-small-int8", "segments": [
    {"start": 1.0, "end": 4.0, "text": "这里论症跳了一步"},
    {"start": 4.2, "end": 7.0, "text": "申请人为什么不知道没有说清"},
    {"start": 20.0, "end": 24.0, "text": "这个观点可以用来反驳管理负担"},
    {"start": 40.0, "end": 44.0, "text": "这里要找一个判例"},
]}

ITEMS = {
    "session": "20260928-101500", "language": "zh", "title": "读第一节", "reviewed": True,
    "items": [
        {"id": "R-1", "kind": "revision", "title": "论证跳步", "time": {"start": 1.0, "end": 7.0},
         "quote": "这里论证跳了一步，申请人为什么不知道没有说清", "status": "confirmed", "category": "argument",
         "draft_ref": {"anchor": "申请人仍然无法知道这次拒绝为何适用于自己", "section": "一、问题"},
         "restatement": "规则公开与个别理由之间缺一步说明", "candidates": ["补一句说明规则为何不自明"],
         "questions": ["这一步放正文还是脚注？"], "answer": "放正文"},
        {"id": "S-1", "kind": "reading", "title": "可反驳管理负担", "time": {"start": 20.0, "end": 24.0},
         "quote": "这个观点可以用来反驳管理负担", "relation": "challenges：管理负担反驳",
         "source_ref": {"title": "示例文献", "viewer_page": 12, "passage": "说明理由的成本被高估"}},
        {"id": "G-1", "kind": "gap", "title": "找判例", "time": {"start": 40.0, "end": 44.0},
         "quote": "这里要找一个判例", "need": "拒绝说明理由的判例", "search_hint": ["说明理由 拒绝 判决"],
         "draft_ref": {"anchor": "紧急维护时可以先通知后补理由"}},
        {"id": "T-1", "kind": "thought", "title": "口述一句", "quote": "规则公开不等于理由公开。", "dictated": True},
        {"id": "X-1", "kind": "thought", "title": "被丢弃", "quote": "不要这条", "status": "deleted"},
    ],
}


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPTS / "writing.py"), *map(str, args)], capture_output=True,
                          text=True, encoding="utf-8", timeout=30)


class Writing(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name) / "paper"
        self.session = self.root / ".blurt" / "sessions" / "20260928-101500"
        self.session.mkdir(parents=True)
        (self.root / "drafts").mkdir()
        (self.root / "drafts" / "paper.md").write_text(DRAFT, encoding="utf-8")
        (self.root / ".blurt" / "config.json").write_text(json.dumps(
            {"writing": {"manuscript": ["drafts/paper.md"], "glossary": "docs/glossary.md"}}), encoding="utf-8")
        (self.session / "items.json").write_text(json.dumps(ITEMS, ensure_ascii=False), encoding="utf-8")
        (self.session / "transcript.json").write_text(json.dumps(TRANSCRIPT, ensure_ascii=False), encoding="utf-8")

    def items(self):
        return {i["id"]: i for i in json.loads((self.session / "items.json").read_text(encoding="utf-8"))["items"]}

    def test_project_config_found_from_session(self):
        self.assertEqual(project_root(self.session), self.root.resolve())
        self.assertEqual(project_config(self.session)["writing"]["manuscript"], ["drafts/paper.md"])

    def test_said_copies_raw_segments_without_touching_quote(self):
        p = run("said", self.session)
        self.assertEqual(p.returncode, 0, p.stderr)
        it = self.items()
        self.assertEqual(it["R-1"]["said"], "这里论症跳了一步申请人为什么不知道没有说清")  # zh: no spaces added
        self.assertEqual(it["R-1"]["quote"], ITEMS["items"][0]["quote"])
        self.assertNotIn("said", it["T-1"])  # no time range → nothing to copy

    def test_locate_exact_fuzzy_ambiguous(self):
        files = {"drafts/paper.md": DRAFT}
        self.assertEqual(writing.locate("申请人仍然无法知道 这次拒绝为何适用于自己", files),
                         {"path": "drafts/paper.md", "line": 4, "match": "exact"})
        nopunct = writing.locate("紧急维护时可以先通知后补理由", files)  # OCR dropped the comma
        self.assertEqual((nopunct["match"], nopunct["line"]), ("exact", 8))  # punctuation is ignored
        near = writing.locate("紧急维修时可以先通知、后补理由", files)  # one wrong character
        self.assertEqual((near["match"], near["line"]), ("fuzzy", 8))
        amb = writing.locate("公开规则并不等于个别理由", files)
        self.assertEqual(amb["match"], "ambiguous")
        self.assertEqual(amb["candidates"], ["drafts/paper.md:3", "drafts/paper.md:9"])
        self.assertEqual(writing.locate("完全无关的一句话在这里出现", files)["match"], "none")
        by_sec = writing.locate("公开规则并不等于个别理由", files, section="二、例外")  # heading seen on screen
        self.assertEqual((by_sec["line"], by_sec["match"]), (9, "exact"))
        self.assertEqual(writing.locate("公开规则并不等于个别理由", files, section="三、结论")["match"], "ambiguous")

    def test_locate_writes_refs_from_config_manuscript(self):
        p = run("locate", self.session)
        self.assertEqual(p.returncode, 0, p.stderr)
        ref = self.items()["R-1"]["draft_ref"]
        self.assertEqual((ref["path"], ref["line"], ref["match"]), ("drafts/paper.md", 4, "exact"))
        self.assertEqual(ref["excerpt"], "申请人仍然无法知道这次拒绝为何适用于自己。")
        self.assertEqual(ref["anchor"], ITEMS["items"][0]["draft_ref"]["anchor"])  # anchor kept

    def test_export_record_keeps_identities_apart(self):
        run("said", self.session)
        run("locate", self.session)
        p = run("export", self.session)
        self.assertEqual(p.returncode, 0, p.stderr)
        md = (self.session / "writing-record.md").read_text(encoding="utf-8")
        self.assertIn("状态：讨论记录，候选未写回", md)
        self.assertIn("转写 sensevoice sense-voice-small-int8", md)
        self.assertIn("术语依据：docs/glossary.md", md)
        self.assertIn("| A1 作者原话 | “这里论证跳了一步，申请人为什么不知道没有说清” |", md)
        self.assertIn("| M1 模型复述 | 供作者核对，不是作者立场：", md)
        self.assertIn("| C1 模型建议 | 候选：补一句说明规则为何不自明 | 依据 A1，未采用 |", md)
        self.assertIn("正文 drafts/paper.md:4；身份：作者已写正文", md)
        self.assertIn("| Q1 待作者决定 | 这一步放正文还是脚注？ | 依赖 A1 |", md)
        self.assertIn("| A2 作者原话 | “放正文” | 审核页回答；针对 A1 |", md)  # review answers are author words
        self.assertIn("阅读器第 12 页（文件页序）", md)
        self.assertNotIn("印刷页码", md)  # never invented
        self.assertIn("## 资料缺口", md)
        self.assertIn("## 口述句子（未入正文）", md)
        self.assertNotIn("不要这条", md)  # deleted items stay out
        revisions = md.split("## 修改清单（按正文位置）")[1].split("##")[0]
        self.assertIn("drafts/paper.md:4", revisions)
        self.assertIn("- A1：这里论症跳了一步申请人为什么不知道没有说清", md)  # the model's ASR fix stays visible
        self.assertNotIn("- A3：", md)  # punctuation-only differences are not listed

    def test_export_refuses_to_overwrite(self):
        out = self.root / "docs" / "discussions" / "01_讨论记录.md"
        out.parent.mkdir(parents=True)
        out.write_text("existing", encoding="utf-8")
        p = run("export", self.session, "--out", out)
        self.assertEqual(p.returncode, 1)
        self.assertEqual(out.read_text(encoding="utf-8"), "existing")


class ProjectRootSkipsGlobalHome(unittest.TestCase):
    def test_global_blurt_home_is_not_a_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / ".blurt").mkdir()
            (home / ".blurt" / "config.json").write_text('{"writing": {}}', encoding="utf-8")
            session = home / "Blurt" / "recordings" / "20260928-101500"
            session.mkdir(parents=True)
            code = ("import sys; sys.path.insert(0, sys.argv[1]); from _common import project_root; "
                    "print(project_root(sys.argv[2]))")
            env = {**os.environ, "BLURT_HOME": str(home / ".blurt")}
            out = subprocess.run([sys.executable, "-c", code, str(SCRIPTS), str(session)], capture_output=True,
                                 text=True, env=env, timeout=30).stdout.strip()
            self.assertEqual(out, "None")


if __name__ == "__main__":
    unittest.main()
