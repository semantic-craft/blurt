# Writing projects — read your draft or sources aloud, get writing records back

A writing project is one whose `.blurt/config.json` has a `writing` block, or one wired to writing-infra (it has
`docs/argument-state.md`). In the second case suggest adding the block once:

```json
{ "writing": { "manuscript": ["drafts/paper.md"], "glossary": "docs/glossary.md", "discussions": "docs/discussions" } }
```

Paths are relative to the project root. `manuscript` is what `writing.py locate` searches (Markdown / plain text;
convert a .docx with pandoc into the session first when that is all there is).

## What stays true here

These come from writing-infra (`docs/SPEC.md`, `writing-companion`); they override the general flow in SKILL.md.

- **The author types the manuscript.** Never edit the manuscript or `docs/argument-state.md`, never write
  replacement prose. Wording the author dictated is recorded (`thought` with `dictated: true`); it enters the
  manuscript only when the author asks, through writing-companion's save helper.
- **Their words, your words, the machine's words stay apart.** `said` is the raw ASR text, filled by
  `writing.py said` and never edited. `quote` is what the author said with only recognition errors fixed and
  fillers dropped — no paraphrase, no tidying of hedges. `title`, `restatement`, `relation`, `candidates` and
  `search_hint` are yours and are labelled as such downstream. Keeping an item on the review page means it is worth
  keeping, not that your restatement is adopted.
- **Speech stays local.** Unpublished drafts and half-formed arguments are not uploaded: use `sensevoice` or
  `mlx-whisper`. `transcribe.py` refuses cloud backends here unless the author explicitly agreed (`--allow-cloud`).
- **The screen is a lead, not a source.** Anchors and passages are read off frames. Manuscript anchors are resolved
  against the file (`writing.py locate`); a source passage must be checked against the original before it supports
  anything in the paper (`search-router`). Don't guess Zotero keys, pages or authors that are not visible.
- **Gaps stay gaps.** When the author says something must be found, record a `gap`; don't answer it from memory.

## Flow

1. Transcribe locally (§2). Whisper backends: pass the glossary's terms as `--prompt`. SenseVoice takes no prompt —
   use the glossary when fixing terms in `quote`.
2. Write `items.json` (§3) with the writing lenses — `revision` (their draft), `reading` (a source), `gap`
   (material to find), `thought` (thinking aloud) in `reference/lenses/`; `idea` / `note` / `task` still apply.
   Set `language`.
3. `writing.py said <session>` → fills `said`. Where `said` and your `quote` differ, check the fix is only a
   recognition fix.
4. `writing.py locate <session>` → `path:line` + `excerpt` for every `draft_ref.anchor`. `fuzzy` → confirm the
   excerpt is the spot; `ambiguous` → add the heading visible on screen as `section` (it picks among repeats) or
   lengthen the anchor; `none` → re-read the frame and correct the anchor. Run again. Never pick a line by guessing;
   an unlocated item keeps `section` and says so.
5. Frames (§4): box the anchor sentence or the source passage.
6. Review page (§5).
7. `writing.py export <session>` → `<session>/writing-record.md`: a discussion record in writing-companion's format
   (A author words · M restatement · C candidates · S draft/source locators · Q open decisions; answers typed on the
   review page become A rows), then a revision list in manuscript order, gaps, dictated wording, and the ASR diff.
   Copy it into the project's discussions folder (`--out docs/discussions/NN_讨论记录_<主题>_<日期>.md`) only when
   the author wants it there.

Afterwards offer the next step in one line each: the revision list is the author's to act on; gaps go to
`search-router`; a changed claim, objection or decision is for writing-companion to put in
`docs/argument-state.md` — in the author's words, after they confirm it.

Unattended runs (§5): steps 1–5 and the export into the session folder only; nothing else in the project changes.
