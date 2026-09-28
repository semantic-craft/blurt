# lens: revision — the author's remark about their own manuscript

Use for: the author reads their draft on screen and says what is wrong or missing at a spot — a jump in the
argument, an unclear term, a claim that needs a limit, a citation to check, structure, wording ("这段跳了一步",
"这个概念前后不一致", "这里引注要补"). Only in a writing project (see `reference/writing.md`).

Fields:
- `draft_ref` — `{ "anchor": "<the sentence on screen the remark points at, read off the frame, verbatim>",
  "section": "<heading visible on screen, optional>" }`. `writing.py locate` adds `path`, `line`, `match`, `excerpt`.
- `category` — `argument` · `structure` · `term` · `citation` · `fact` · `wording`.
- `restatement` — your reading of the problem, for the author to check. Not the author's position.
- `candidates` — list, optional: your suggestions for handling it. Never replacement prose for the manuscript.
- `questions` — what only the author can decide.

The author's own fix, if they said one, stays in `quote`; do not move it into `candidates`.
Frames: the passage on screen with the anchor sentence boxed.
