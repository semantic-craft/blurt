# lens: gap — material the argument still needs

Use for: the author names something to find or check ("这里得找个判例", "要查一下这个数据的出处", "这个说法
谁最早提的"). The gap is the output; do not fill it from memory.

Fields:
- `need` — what material, in one line (a case, a statute article, a statistic, the origin of a view…).
- `draft_ref` — `{ "anchor", "section" }` when the gap belongs to a spot in the manuscript (as in `revision`).
- `search_hint` — list, optional: your candidate queries / databases for `search-router`. Candidates only.
- `restatement`, `questions`.

Hand-off: list the gaps to the author at the end; searching is a separate step through `search-router`.
