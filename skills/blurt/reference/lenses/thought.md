# lens: thought — thinking out loud about the paper

Use for: claims, objections, distinctions, doubts, decisions and changes of mind spoken while looking at notes,
an outline or a discussion map ("其实我的主张不是…而是…", "这个反驳我还答不上来", "那个方向先放下，因为…").

Fields:
- `restatement` — your reading of the thought, for the author to check. Not the author's position.
- `candidates` — list, optional: your candidate relations, objections or next questions, labelled as yours.
- `dictated` — `true` only when the author was dictating wording meant for the manuscript ("这句可以这么写：…").
  Then `quote` holds exactly that wording (ASR fixes only) and nothing gets polished.
- `questions` — open decisions only the author can make.

A withdrawn direction keeps the author's stated reason in `quote`; write none for them if they gave none.
Frames: optional — only when the screen shows what the thought is about.
