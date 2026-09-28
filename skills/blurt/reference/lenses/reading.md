# lens: reading — the author's reaction to a source

Use for: the author reads a paper, book, judgment or statute on screen (Zotero reader, PDF viewer, browser,
CNKI, Westlaw…) and reacts ("这个观点正好能反驳…", "这里他把两个概念混了", "这段可以放第三节"). A highlight or
an opened page is not a reaction; only what the author says counts.

Fields:
- `source_ref` — read off the frame, never guessed:
  `{ "title", "authors", "url", "zotero_key", "viewer_page", "printed_page", "passage" }`.
  `viewer_page` is the page number the viewer shows (file page order); `printed_page` only when the printed page
  number is visible on the page image. `passage` = the text on screen the author reacted to, verbatim.
  `zotero_key` only when you actually looked it up (e.g. `zotero-cli` search on the visible title); else omit.
- `relation` — optional, your candidate: `supports` · `challenges` · `qualifies` · `defines` · `method` · `example`,
  plus which claim of the paper, in a few words.
- `use_in` — where the author said it could go (section / claim), in their words; empty if they did not say.
- `restatement` — your reading of the reaction, for the author to check.
- `questions`.

Frames: the passage itself (box it), plus the viewer's title bar or page number when that is what identifies it.
The on-screen passage is a lead, not a verified quote: citing it in the paper still goes through the original.
