# /// script
# requires-python = ">=3.10"
# ///
"""Writing-project helpers: the predictable parts of turning a narrated reading session into writing records.
The model decides what each item means; these functions only copy, match and lay out — they never write
the manuscript, the argument state, or anything outside the session unless --out says so.

  writing.py said   SESSION                       fill each item's `said` with the raw ASR text of its time range
  writing.py locate SESSION [--manuscript PATH …] resolve each item's draft_ref.anchor to path:line in the manuscript
  writing.py export SESSION [--out FILE]          discussion record (A/M/C/S/Q identities) + revision list + gaps

Manuscript paths default to `.blurt/config.json` → writing.manuscript (relative to the project root).
"""
from __future__ import annotations

import argparse
import difflib
import json
import platform
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import die, fmt_ts, live_items, load_json, load_session, project_config, project_root, save_session  # noqa: E402

PAD = 0.3            # seconds of slack around an item's time range when collecting ASR segments
FUZZY_MIN = 0.8      # share of the anchor that must match a manuscript paragraph for a fuzzy hit
NO_SPACE_LANGS = ("zh", "ja", "ko", "yue")


# ------------------------------------------------------------------ said: raw ASR per item
def cmd_said(a) -> None:
    session = Path(a.session)
    data = load_session(session) or die("no items.json in this session")
    tr = load_json(session / "transcript.json") or die("no transcript.json — run transcribe.py first")
    segs = tr.get("segments", [])
    sep = "" if str(data.get("language", "")).startswith(NO_SPACE_LANGS) else " "
    filled = 0
    for it in data.get("items", []):
        t = it.get("time") or {}
        if "start" not in t or "end" not in t:
            continue
        parts = [s["text"].strip() for s in segs if s["end"] > t["start"] - PAD and s["start"] < t["end"] + PAD]
        it["said"] = sep.join(p for p in parts if p)
        filled += 1
    data["asr"] = {k: tr.get(k) for k in ("backend", "model") if tr.get(k)}
    save_session(session, data)
    print(json.dumps({"filled": filled, "items": len(data.get("items", []))}))


# ------------------------------------------------------------------ locate: anchor text → path:line
def _norm(s: str) -> tuple[str, list[int]]:
    """NFKC, drop whitespace, punctuation and Markdown marks; return the normalized text and each char's line."""
    out, lines = [], []
    for n, line in enumerate(s.splitlines(), 1):
        for ch in unicodedata.normalize("NFKC", line):
            if ch.isspace() or unicodedata.category(ch)[0] in "PS" or ch in "*_`#>":
                continue
            out.append(ch.lower())
            lines.append(n)
    return "".join(out), lines


def _paragraphs(text: str) -> list[tuple[int, str]]:
    paras, start, buf = [], 1, []
    for n, line in enumerate(text.splitlines(), 1):
        if line.strip():
            if not buf:
                start = n
            buf.append(line)
        elif buf:
            paras.append((start, "\n".join(buf)))
            buf = []
    if buf:
        paras.append((start, "\n".join(buf)))
    return paras


def locate(anchor: str, files: dict[str, str]) -> dict:
    target, _ = _norm(anchor)
    if len(target) < 4:
        return {"match": "none", "reason": "anchor too short"}
    hits = []
    for path, text in files.items():
        norm, lines = _norm(text)
        i = norm.find(target)
        while i >= 0:
            hits.append((path, lines[i]))
            i = norm.find(target, i + 1)
    if len(hits) == 1:
        return {"path": hits[0][0], "line": hits[0][1], "match": "exact"}
    if hits:
        return {"match": "ambiguous", "candidates": [f"{p}:{n}" for p, n in hits[:10]]}
    best = (0.0, "", 0)
    for path, text in files.items():
        for start, para in _paragraphs(text):
            norm, lines = _norm(para)
            if not norm:
                continue
            sm = difflib.SequenceMatcher(None, norm, target, autojunk=False)
            blocks = [b for b in sm.get_matching_blocks() if b.size]
            score = sum(b.size for b in blocks) / len(target)
            if score > best[0]:
                best = (score, path, start + lines[max(blocks, key=lambda b: b.size).a] - 1 if blocks else start)
    if best[0] >= FUZZY_MIN:
        return {"path": best[1], "line": best[2], "match": "fuzzy", "score": round(best[0], 2)}
    return {"match": "none", "score": round(best[0], 2)}


def _excerpt(text: str, line: int, width: int = 120) -> str:
    s = text.splitlines()[line - 1].strip()
    return s if len(s) <= width else s[:width] + "…"


def cmd_locate(a) -> None:
    session = Path(a.session)
    data = load_session(session) or die("no items.json in this session")
    root = project_root(session) or Path.cwd()
    paths = a.manuscript or project_config(session).get("writing", {}).get("manuscript") or []
    if isinstance(paths, str):
        paths = [paths]
    if not paths:
        die("no manuscript: pass --manuscript PATH or set writing.manuscript in .blurt/config.json")
    files = {}
    for p in paths:
        f = Path(p) if Path(p).is_absolute() else root / p
        if not f.is_file():
            die(f"manuscript not found: {f}")
        files[str(Path(p))] = f.read_text(encoding="utf-8")
    stats: dict[str, int] = {}
    for it in data.get("items", []):
        ref = it.get("draft_ref")
        if not isinstance(ref, dict) or not ref.get("anchor"):
            continue
        for k in ("path", "line", "match", "score", "candidates", "excerpt", "reason"):
            ref.pop(k, None)
        ref.update(locate(ref["anchor"], files))
        if ref.get("line"):
            ref["excerpt"] = _excerpt(files[ref["path"]], ref["line"])
        stats[ref["match"]] = stats.get(ref["match"], 0) + 1
    save_session(session, data)
    print(json.dumps({"manuscript": list(files), "located": stats}, ensure_ascii=False))


# ------------------------------------------------------------------ export: discussion record
def _clean(s) -> str:
    return re.sub(r"\s*\n\s*", " ", str(s or "")).replace("|", "\\|").strip()


def _same(a: str, b: str) -> bool:
    strip = lambda s: re.sub(r"[\W_]+", "", unicodedata.normalize("NFKC", s or "")).lower()  # noqa: E731
    return strip(a) == strip(b)


def _draft_loc(ref: dict) -> str:
    if ref.get("line"):
        tag = "" if ref.get("match") == "exact" else f"（{ref.get('match')} {ref.get('score', '')}，待核对）"
        return f"正文 {ref['path']}:{ref['line']}{tag}"
    if ref.get("section"):
        return f"正文 {ref['section']}（未定位到行）"
    if ref.get("candidates"):
        return "正文 多处匹配：" + "、".join(ref["candidates"][:3])
    return "正文位置未定位"


def _source_loc(ref: dict) -> str:
    bits = [ref.get("title") or "未识别文献"]
    if ref.get("authors"):
        bits.insert(0, ref["authors"] if isinstance(ref["authors"], str) else "、".join(ref["authors"]))
    if ref.get("zotero_key"):
        bits.append(f"Zotero {ref['zotero_key']}")
    if ref.get("viewer_page"):
        bits.append(f"阅读器第 {ref['viewer_page']} 页（文件页序）")
    if ref.get("printed_page"):
        bits.append(f"印刷页码 {ref['printed_page']}")
    if ref.get("url"):
        bits.append(ref["url"])
    return "，".join(str(b) for b in bits)


def build_record(session: Path, data: dict) -> str:
    items = live_items(data)
    sid = data.get("session") or session.name
    m = re.match(r"(\d{4})(\d{2})(\d{2})", sid)
    date = f"{m[1]}-{m[2]}-{m[3]}" if m else sid
    asr = data.get("asr") or {}
    cfg = project_config(session).get("writing", {})
    reviewed = "作者已在审核页过目" if data.get("reviewed") else "作者尚未审核，条目均为待核对"
    L = [f"# 口述记录：{data.get('title') or sid}", "",
         f"日期：{date}",
         f"对话对象与机器：作者录屏口述／blurt 会话 {sid}／{platform.node()}／转写 "
         f"{asr.get('backend', '未记录')} {asr.get('model') or ''}".rstrip(),
         "状态：讨论记录，候选未写回",
         "写回前置条件：正文由作者亲写；本记录不含正文保存请求，口述句子须作者明确要求后另行保存",
         f"术语依据：{cfg.get('glossary') or '本次录屏，未对照术语表'}",
         f"审核：{reviewed}；A 栏为转写经模型仅纠正识别错误后的原话，机器原文见文末", "",
         "| 身份 | 内容 | 定位或依赖 |", "| --- | --- | --- |"]
    n = {"A": 0, "M": 0, "C": 0, "S": 0, "Q": 0}
    revisions, gaps, dictated, asr_diff = [], [], [], []

    def row(tag: str, label: str, content: str, loc: str) -> str:
        n[tag] += 1
        L.append(f"| {tag}{n[tag]} {label} | {_clean(content)} | {_clean(loc)} |")
        return f"{tag}{n[tag]}"

    for it in items:
        t = it.get("time") or {}
        when = f"录屏 {fmt_ts(t['start'])}–{fmt_ts(t['end'])}" if "start" in t else "录屏"
        kept = "作者已保留" if it.get("status") == "confirmed" else "未审"
        a = row("A", "作者原话", f"“{it.get('quote') or it.get('said') or ''}”", f"{when}；{it.get('id', '')}；{kept}")
        if it.get("said") and it.get("quote") and not _same(it["said"], it["quote"]):
            asr_diff.append(f"- {a}：{_clean(it['said'])}")
        if it.get("restatement"):
            row("M", "模型复述", f"供作者核对，不是作者立场：{it['restatement']}", f"依据 {a}")
        if it.get("relation"):
            row("C", "模型建议", f"候选关系：{it['relation']}", f"依据 {a}，未采用")
        for c in it.get("candidates") or []:
            row("C", "模型建议", f"候选：{c}", f"依据 {a}，未采用")
        s = None
        if isinstance(it.get("draft_ref"), dict):
            ref = it["draft_ref"]
            text = f"“{ref['excerpt']}”" if ref.get("excerpt") else f"画面读取：“{ref.get('anchor', '')}”"
            s = row("S", "来源", text, f"{_draft_loc(ref)}；身份：作者已写正文")
        if isinstance(it.get("source_ref"), dict):
            ref = it["source_ref"]
            passage = f"画面读取：“{ref['passage']}”" if ref.get("passage") else "未读取原段"
            row("S", "来源", passage, f"{_source_loc(ref)}；身份：库内或屏幕文献，定位来自画面，待核对原文")
        if (it.get("source") or {}).get("url") and not it.get("source_ref"):
            row("S", "来源", it["source"]["url"], "身份：外部网页，画面读取")
        for q in it.get("questions") or []:
            row("Q", "待作者决定", q, f"依赖 {a}")
        if it.get("answer"):
            row("A", "作者原话", f"“{it['answer']}”", f"审核页回答；针对 {a}")
        kind = it.get("kind")
        if kind == "revision":
            ref = it.get("draft_ref") or {}
            revisions.append(((ref.get("path") or "~", ref.get("line") or 10**9),
                              f"- {_draft_loc(ref)} · {it.get('category', '')} · {it.get('title', '')} — {a}"
                              + (f"、{s}" if s else "")))
        elif kind == "gap":
            gaps.append(f"- {it.get('need') or it.get('title', '')} — {a}"
                        + (f"；检索线索（候选）：{'；'.join(it['search_hint'])}" if it.get("search_hint") else ""))
        elif kind == "thought" and it.get("dictated"):
            dictated.append(f"- {a}：“{it.get('quote', '')}”")

    L.append("")
    if revisions:
        L += ["## 修改清单（按正文位置）", "", *[r for _, r in sorted(revisions)], ""]
    if gaps:
        L += ["## 资料缺口（交 search-router 取原文，不以本记录为依据）", "", *gaps, ""]
    if dictated:
        L += ["## 口述句子（未入正文）", "",
              "作者口述、可能用作正文的原话。写入正文须作者明确要求，并经 writing-companion 的保存工具原样追加。", "",
              *dictated, ""]
    L += ["## 过程记录", "", "录屏转写后由模型拆条、复述、读取画面定位；以下供试点日志核对，不进论文。", ""]
    L += (["机器转写与 A 栏不同之处（机器原文）：", "", *asr_diff, ""] if asr_diff else ["A 栏与机器转写一致。", ""])
    return "\n".join(L)


def cmd_export(a) -> None:
    session = Path(a.session)
    data = load_session(session) or die("no items.json in this session")
    out = Path(a.out) if a.out else session / "writing-record.md"
    if a.out and out.exists() and not a.force:
        die(f"{out} exists; pass --force to overwrite, or pick another path")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_record(session, data), encoding="utf-8")
    kinds: dict[str, int] = {}
    for it in live_items(data):
        kinds[it.get("kind", "?")] = kinds.get(it.get("kind", "?"), 0) + 1
    print(json.dumps({"file": str(out), "kinds": kinds}, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("said").add_argument("session")
    lo = sub.add_parser("locate")
    lo.add_argument("session")
    lo.add_argument("--manuscript", nargs="+", help="manuscript file(s), relative to the project root")
    ex = sub.add_parser("export")
    ex.add_argument("session")
    ex.add_argument("--out", help="default: <session>/writing-record.md")
    ex.add_argument("--force", action="store_true", help="overwrite an existing --out file")
    a = p.parse_args()
    {"said": cmd_said, "locate": cmd_locate, "export": cmd_export}[a.cmd](a)


if __name__ == "__main__":
    main()
