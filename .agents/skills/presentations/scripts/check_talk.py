"""Check a talk against the measurable rules in TALKS.md: its slides, its script and its plan.

    uv run --no-project python check_talk.py slides.qmd [deck.md ...]   report each file; exit 1 on a hard problem
    uv run --no-project python check_talk.py -v slides.qmd              also show the soft notes, for a person to judge
    uv run --no-project python check_talk.py plan.md                    check only the plan of a talk

A talk made by this guide has two files in one folder. plan.md is the plan, from the template templates/plan.md,
and slides.qmd holds the slides in the Markdown of htmpres. In a .qmd file, a line that starts with "## " starts a
slide, and a line that is only --- must come right before such a line. The checker fails slides.qmd when plan.md
is missing or has an empty section. It reads the time of the talk from the plan, and it notes a deck with more
slides than 75 percent of the minutes, the time to plan for. As in htmpres, the first slide with
{data-kind="appendix"} on its title line starts the appendix, and every later slide is in it. The appendix is
not counted.

Any other file is a Markdown deck, in which a line that is only --- starts a new slide. YAML front matter can open
the file. The checker reads only its key "marp", and it does not check speaking time in such a deck.

The spoken script of a slide is in its notes: a "::: notes" block (Pandoc, Quarto, htmpres), an HTML comment
(Marp, Slidev) or an <aside class="notes"> block (reveal.js). In a deck with no "marp:" key, a line that starts
with "Note:" also starts the script on a slide that has no other notes. The script then runs to the end of the
slide. A line of the notes that starts with "Cue:" is the cue of the slide, and it is not script.

The exit status is 0 when every file passes, 1 when a file has a hard problem, and 2 for a usage error, such as a
missing file or an unknown option.

The slide rules come from the tutorial "Communicating Your Work" and the presentation tips of Rosalind Reid,
which draw on The Chicago Guide to Communicating Science by Scott L. Montgomery. The plan comes from the
presentation worksheet of Jonathan Schwabish, Better Presentations. The rule that a title starts with the words
that set it apart comes from the post "Five Principles for Generating Readable AI Text in Bulk" by Shreya Shankar.
TALKS.md names the numbers that are this guide's own. This checker shares no writing rule with check.py, the
checker for reports in nossaifd. It needs no other file, because it holds a copy of the Markdown reader of check.py.
"""

import re
import sys
from pathlib import Path


# The Markdown reader: blocks(), plain() and sentences() are copied from check.py, the checker for reports in
# nossaifd (https://github.com/rahuldave/nossaifd/blob/main/check.py). Keep them the same as that copy, so that
# both checkers read a page the same way.

def blocks(text: str) -> list[tuple[int, str, str]]:  # (line, text, kind) with kind "para", "item", "cell" or "head"
    "Read the prose of a page: paragraphs, list items and headings. Code and tables are left out."
    out, block, start, fence, kind = [], [], 0, "", "para"   # fence: the run of ` or ~ that opened the code, or ""

    def flush() -> None:
        nonlocal block
        if block:
            out.append((start, " ".join(block), kind))
        block = []

    lines = text.split("\n")
    if lines and lines[0].strip() == "---":
        # Front matter keeps its own syntax: skip it to its closing line, so the line numbers stay the same.
        # Only YAML counts as front matter. A page can also start with a --- rule, and its prose is checked.
        end = next((i for i in range(1, len(lines)) if lines[i].strip() in ("---", "...")), None)
        body = lines[1:end] if end is not None else []
        yaml = re.compile(r"^(?:[A-Za-z0-9_-]+:(?:\s|$)|\s+\S|-\s|#)")
        key = re.compile(r"^[A-Za-z0-9_-]+:(?:\s|$)")
        if end is not None and body and key.match(body[0]) and all(yaml.match(line) for line in body if line.strip()):
            lines[: end + 1] = [""] * (end + 1)
    for number, line in enumerate(lines, 1):
        stripped = line.strip()
        mark = re.match(r"^(`{3,}|~{3,})", stripped)
        if fence:
            # As CommonMark: only the same character, at least as many times, with nothing after it, closes the code
            if mark and mark.group(1)[0] == fence[0] and len(mark.group(1)) >= len(fence) and not stripped[len(mark.group(1)):].strip():
                fence = ""
            continue
        if mark:
            fence = mark.group(1)
            flush()
            continue
        if re.match(r"^:::+(\s*[\w{].*)?$", stripped):
            flush()
            continue  # a fenced div, such as ::: do or :::, is markup, as a code fence is
        if not stripped or stripped.startswith("![") or stripped.startswith("<"):
            flush()
            continue
        if stripped.startswith("#"):
            flush()
            out.append((number, stripped.lstrip("#").strip(), "head"))
            continue
        if stripped.startswith("|"):
            flush()
            continue  # tables are exempt: a cell can be a short phrase, a fragment or a value
        item = re.match(r"^\s*(?:[-*+]|\d+\.)\s+(.*)", line)
        if item:
            flush()
            start, kind, block = number, "item", [item.group(1)]
            continue
        if not block:
            start, kind = number, "para"
        block.append(stripped)
    flush()
    return out


def plain(text: str) -> str:  # Prose with inline code as one word, link text kept, markup gone
    "Reduce Markdown inline syntax to plain words."
    text = re.sub(r"`[^`]*`", "CODE", text)
    text = re.sub(r"\[([^\]]*)\]\{[^}]*\}", r"\1", text)  # a span such as [words]{.key .fragment}
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"https?://\S+", "URL", text)
    text = re.sub(r'"[^"\n]*"', "QUOTE", text)  # quoted words are examples being talked about, not prose
    return re.sub(r"[*_]", "", text)


def sentences(text: str) -> list[str]:  # The sentences of a block
    "Split after a full stop, question mark or exclamation mark that ends a sentence."
    # A new sentence can start in lower case, as with a name like "timewalk" or "git". The full stops of "e.g."
    # and "i.e." do not end a sentence, so they are hidden while the text is split, and then put back.
    hidden = re.sub(r"\b(?:e\.g|i\.e)\.", lambda m: m.group(0).replace(".", "\0"), text, flags=re.I)
    return [s.strip().replace("\0", ".") for s in re.split(r"(?<=[.!?])\s+(?=[A-Za-z\"(])", hidden) if s.strip()]


ITEMS_SOFT = 5          # items on a slide before a soft note: this guide's number, to prefer fewer
ITEMS_HARD = 9          # items on a slide: Rosalind Reid's limit of short-term memory, 3 to 9 items
WORDS_SOFT = 30         # words on a slide: about 30 is this guide's number
WORDS_HARD = 40         # more than 40 words fails: this guide's number
MAX_EQUATIONS = 2       # equations on a slide: this guide's number for "few"
SENTENCE_SOFT = 25      # words in a spoken sentence before a soft note: usually 20 to 25 at most
SECTIONS_SOFT = 5       # sections in the outline before a soft note: Schwabish's "about five"
PLANNED_SHARE = 75      # percent of the time of the talk to plan for: rule 87

# The sections of a plan, from templates/plan.md, and the shapes of a talk
PLAN_SECTIONS = ("The occasion", "The kind of talk", "The audience", "The headline", "The action",
                 "The opening statement", "The closing statement", "The outline", "The questions")
SHAPES = ("asymmetric hourglass", "symmetric hourglass", "funnel")
PLACEHOLDERS = {"a point", "the first section, named by its point"}   # template text that is not an answer
FILLERS = re.compile(r"\b(?:um+|uh+|the thing is)\b", re.I)          # fillers that Schwabish lists

MARP_KEYS = {"theme", "style", "headingDivider", "size", "math", "title", "description", "author", "image",
             "keywords", "url", "marp", "lang", "paginate", "header", "footer", "class", "backgroundColor",
             "backgroundImage", "backgroundPosition", "backgroundRepeat", "backgroundSize", "color", "transition"}
DIRECTIVE = re.compile(r"^\s*_?([A-Za-z]+)\s*:")
WORD = re.compile(r"[A-Za-z0-9][\w'\-./]*")
IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)|<img\b[^>]*>", re.I)
BACKGROUND = re.compile(r"!\[bg(?:\s[^\]]*)?\]")   # a Marp background image: its alt text starts with the word bg
INLINE_MATH = re.compile(r"(?<![\\$])\$(?=\S)([^$\n]*?\S)\$(?!\d)")
RELATION = re.compile(r"=|<|>|\\(?:le|ge|leq|geq|approx|propto|sim|neq|equiv)\b")
# Abbreviations that end with a full stop inside a sentence, as in "Fig. 2." or "vs. the baseline". A caption
# that opens a line, "Fig. 2. Time for each step", keeps both stops in one sentence. Inside a sentence, "in
# Fig. 2. Every run" ends at the stop after the number. "etc.", "al.", "U.S." and "p.m." end a sentence unless a
# word in lower case or a number comes next. The (?-i:...) keeps that test case-sensitive.
ABBREVIATION = re.compile(r"^Figs?\.\s*\d+[a-z]?\.(?=\s)|\b(?:Figs?|Dr|Mr|Ms|Mrs|Prof|St|Eq|Eqs|Ref|Refs)\.(?=\s)|"
                          r"\bNo\.(?=\s*\d)|\b(?:vs|approx|cf|etc|al)\.(?=\s+(?-i:[a-z0-9]))|"
                          r"\b(?:e\.g|i\.e)\.|\b(?:U\.S|U\.K|a\.m|p\.m)(?:\.(?=\s+(?-i:[a-z0-9])))?", re.I | re.M)


class Slide:
    "One slide: its body, its notes and the line in the file where each starts."

    def __init__(self, number: int, line: int, lines: list[str], reveal: bool = False):
        self.number, self.line, self.reveal = number, line, reveal
        self.body: list[str] = []          # the slide, with the notes blanked, so the line numbers stay the same
        self.notes: list[tuple[int, str]] = []  # (line in the file, text) of each line of the script
        self.matter: dict[str, str] = {}   # Slidev front matter of this slide, if any
        self.attrs = ""                    # the attributes of the title line of an htmpres slide, as in {.key}
        self.cues: list[tuple[int, str]] = []   # (line, text) of each "Cue:" line of the notes
        self._read(lines)
        for where, text in self.notes:
            if re.match(r"^\s*Cue:", text):
                self.cues.append((where, text))
        self.notes = [(where, "" if re.match(r"^\s*Cue:", text) else text) for where, text in self.notes]
        # The line to report for the whole slide: its first filled line
        self.first = next((line + i for i, text in enumerate(lines) if text.strip()), line)

    def _read(self, lines: list[str]) -> None:
        mode, fence, depth = "", "", 0   # mode: "", "comment", "div", "aside" or "note"; depth: divs open in notes
        comment: list[tuple[int, str]] = []
        for offset, line in enumerate(lines):
            where, stripped = self.line + offset, line.strip()
            if mode == "note":                 # a reveal.js Note: runs to the end of the slide
                self.notes.append((where, line))
                self.body.append("")
                continue
            if mode == "comment":
                end = line.find("-->")
                comment.append((where, line[:end] if end >= 0 else line))
                self.body.append("")
                if end >= 0:
                    self._comment(comment)
                    mode, comment = "", []
                continue
            if mode in ("div", "aside"):
                if mode == "div" and re.match(r"^:::+\s*\S", stripped):
                    depth += 1        # a div inside the notes, such as ::: {.callout}, closes at its own :::
                closing = re.match(r"^:::+\s*$", stripped) if mode == "div" else re.search(r"</aside>", line, re.I)
                if closing and mode == "div" and depth:
                    depth, closing = depth - 1, None
                if not closing:
                    self.notes.append((where, re.sub(r"<[^>]+>", "", line)))
                elif mode == "aside":
                    self.notes.append((where, line[: closing.start()]))
                if closing:
                    mode = ""
                self.body.append("")
                continue
            mark = re.match(r"^(`{3,}|~{3,})", stripped)
            if fence:
                if mark and mark.group(1)[0] == fence[0] and len(mark.group(1)) >= len(fence):
                    fence = ""
                self.body.append(line)
                continue
            if mark:
                fence = mark.group(1)
                self.body.append(line)
                continue
            if stripped.startswith("<!--"):
                rest = stripped[4:]
                end = rest.find("-->")
                if end >= 0:
                    self._comment([(where, rest[:end])])
                else:
                    comment, mode = [(where, rest)], "comment"
                self.body.append("")
                continue
            if re.match(r"^:::+\s*\{?\s*\.?notes\s*\}?\s*$", stripped, re.I):
                mode = "div"
                self.body.append("")
                continue
            aside = re.match(r'^<aside\s+class=["\']?notes["\']?\s*>(.*)$', stripped, re.I)
            if aside:
                text = aside.group(1)
                close = re.search(r"</aside>", text, re.I)
                self.notes.append((where, text[: close.start()] if close else text))
                mode = "" if close else "aside"
                self.body.append("")
                continue
            # A reveal.js note: a line that starts with "Note:", only on a slide that has no other notes
            note = re.match(r"^Note:(?:\s(.*))?$", line) if self.reveal else None
            if note:
                self.notes.append((where, note.group(1) or ""))
                mode = "note"
                self.body.append("")
                continue
            self.body.append(line)

    def _comment(self, lines: list[tuple[int, str]]) -> None:
        "A comment of only Marp directives is not notes. In a comment of script, only a _key: line is a directive."
        def directive(text: str) -> bool:
            match = DIRECTIVE.match(text)
            return bool(match) and match.group(1) in MARP_KEYS
        filled = [(n, t) for n, t in lines if t.strip()]
        if not filled or all(directive(t) for _, t in filled):
            return
        # A script line can start with a word such as "title:", so a line without the _ of a scoped directive stays
        self.notes.extend((n, "" if directive(t) and t.lstrip().startswith("_") else t) for n, t in lines)

    def title(self) -> tuple[int, str] | None:
        "The first heading of the slide, with its line in the file."
        for line, text, kind in blocks(_without_math(self.body)):
            if kind == "head":
                return self.line + line - 1, plain(text)
        return None


def _without_math(lines: list[str]) -> str:
    "The body with display math blanked, so that blocks() does not read it as prose."
    out, inside = [], ""
    for line in lines:
        stripped = line.strip()
        if inside:
            out.append("")
            if (inside == "$$" and stripped.endswith("$$")) or (inside == "\\[" and stripped.endswith("\\]")):
                inside = ""
            continue
        if stripped.startswith("$$") or stripped.startswith("\\["):
            opener = stripped[:2]
            closer = "$$" if opener == "$$" else "\\]"
            if not (len(stripped) > 2 and stripped.endswith(closer)):
                inside = opener
            out.append("")
            continue
        out.append(INLINE_MATH.sub("", line))
    return "\n".join(out)


def _equations(lines: list[str]) -> int:
    "Count display equations, math code blocks, and inline math that states a relation."
    count, inside = 0, ""
    for line in lines:
        stripped = line.strip()
        if inside:
            if (inside == "$$" and stripped.endswith("$$")) or (inside == "\\[" and stripped.endswith("\\]")) \
                    or (inside == "```" and stripped.startswith("```")):
                inside = ""
            continue
        if stripped.startswith("```math"):
            count, inside = count + 1, "```"
            continue
        if stripped.startswith("$$") or stripped.startswith("\\["):
            count += 1
            opener = stripped[:2]
            closer = "$$" if opener == "$$" else "\\]"
            if not (len(stripped) > 2 and stripped.endswith(closer)):
                inside = opener
            continue
        count += sum(1 for m in INLINE_MATH.finditer(line) if RELATION.search(m.group(1)))
    return count


def front_matter(lines: list[str]) -> tuple[dict[str, str], int]:
    "Read YAML front matter at the top of the file: its top-level keys, and the number of lines it takes."
    if not lines or lines[0].strip() != "---":
        return {}, 0
    end = next((i for i in range(1, len(lines)) if lines[i].strip() in ("---", "...")), None)
    if end is None:
        return {}, 0
    body = lines[1:end]
    key = re.compile(r"^([A-Za-z0-9_.-]+):(?:\s+(.*))?$")
    yaml = re.compile(r"^(?:[A-Za-z0-9_.-]+:(?:\s|$)|\s+\S|-\s|#)")
    if not body or not key.match(body[0]) or not all(yaml.match(line) for line in body if line.strip()):
        return {}, 0
    found = {}
    for line in body:
        match = key.match(line)
        if match:
            value = re.sub(r"(?:^|\s+)#.*$", "", match.group(2) or "")   # a YAML comment, as in "20 # slot"
            found[match.group(1)] = value.strip().strip("\"'")
    return found, end + 1


def split(text: str) -> tuple[dict[str, str], list[Slide]]:
    "Split a deck into its front matter and its slides. A line that is only --- starts a new slide."
    lines = text.removeprefix("\ufeff").split("\n")
    matter, skip = front_matter(lines)
    chunks: list[tuple[int, list[str]]] = []
    chunk, start, fence, comment = [], skip + 1, "", False

    def close() -> None:
        if any(line.strip() for line in chunk):
            chunks.append((start, list(chunk)))

    for number, line in enumerate(lines[skip:], skip + 1):
        stripped = line.strip()
        mark = re.match(r"^(`{3,}|~{3,})", stripped)
        if fence:
            if mark and mark.group(1)[0] == fence[0] and len(mark.group(1)) >= len(fence):
                fence = ""
        elif comment:
            comment = "-->" not in line
        elif mark:
            fence = mark.group(1)
        elif "<!--" in line and "-->" not in line.split("<!--", 1)[1]:
            comment = True
        elif stripped == "---":
            close()
            chunk, start = [], number + 1
            continue
        chunk.append(line)
    close()
    slides = [Slide(i + 1, at, part) for i, (at, part) in enumerate(chunks)]
    # "Note:" starts the script only in a deck with no "marp:" key, and only on a slide with no other notes
    if "marp" not in matter:
        slides = [Slide(s.number, s.line, part, reveal=True) if not s.notes else s
                  for s, (_, part) in zip(slides, chunks)]
    # Slidev puts the front matter of a slide between two --- lines, so it looks like a slide of only keys.
    kept: list[Slide] = []
    pending: dict[str, str] = {}
    for slide in slides:
        filled = [line for line in slide.body if line.strip()]
        if filled and not slide.notes and all(re.match(r"^[a-z][A-Za-z0-9_]*:(\s|$)", line) for line in filled):
            pending = {line.split(":", 1)[0]: line.split(":", 1)[1].strip() for line in filled}
            continue
        slide.matter, pending = pending, {}
        slide.number = len(kept) + 1
        kept.append(slide)
    return matter, kept


def split_qmd(text: str, hard: list[str]) -> list[Slide]:
    "Split an htmpres deck into slides. A line that starts with ## starts a slide, as htmpres reads it."
    lines = text.removeprefix("\ufeff").split("\n")
    _, skip = front_matter(lines)
    chunks: list[tuple[int, list[str], str]] = []   # (first line, lines, attributes of the title)
    chunk: list[str] = []
    start, attrs, fence, before = 0, "", "", False
    notes, comment = 0, False   # notes: the depth of divs inside a ::: notes block; comment: inside <!-- -->
    for number, line in enumerate(lines[skip:], skip + 1):
        stripped = line.strip()
        mark = re.match(r"^(`{3,}|~{3,})", stripped)
        heading = re.match(r"^##\s+(.+?)(?:\s+(\{.*\}))?\s*$", line)
        if fence:
            if mark and mark.group(1)[0] == fence[0] and len(mark.group(1)) >= len(fence):
                fence = ""
        elif mark:
            fence = mark.group(1)
        elif (notes or comment) and heading:
            # htmpres splits at every ## outside code, so this heading cuts the notes or the comment in two
            hard.append(f"line {number}: a ## line inside {'notes' if notes else 'an HTML comment'}, where htmpres "
                        f"starts a new slide")
            notes, comment = 0, False
        elif comment or notes:
            if comment:
                comment = "-->" not in line
            elif re.match(r"^:::+\s*$", stripped):
                notes -= 1
            elif re.match(r"^:::+\s*\S", stripped):
                notes += 1
        elif re.match(r"^:::+\s*\{?\s*\.?notes\s*\}?\s*$", stripped, re.I):
            notes = 1
        elif "<!--" in line and "-->" not in line.split("<!--", 1)[1]:
            comment = True
        else:
            if heading:
                if start:
                    chunks.append((start, chunk, attrs))
                chunk, start, attrs = ["## " + heading.group(1)], number, heading.group(2) or ""
                continue
            if stripped == "---":
                after = next((l for l in lines[number:] if l.strip()), "")
                if not re.match(r"^##\s", after):
                    hard.append(f"line {number}: a --- line that is not right before a ## title: htmpres starts a "
                                f"slide only at ## and shows --- as a rule")
                continue
            if not start and stripped:
                before = before or number
        if start:
            chunk.append(line)
    if start:
        chunks.append((start, chunk, attrs))
    if before:
        hard.append(f"line {before}: text before the first ## title, which htmpres leaves out")
    slides = []
    for i, (at, part, attrs) in enumerate(chunks):
        slide = Slide(i + 1, at, part)
        slide.attrs = attrs
        slides.append(slide)
    return slides


def appendix(slide: Slide) -> bool:
    "Is the slide in the appendix, marked {data-kind=\"appendix\"} on its title line?"
    # The value must be exactly appendix, as htmpres reads it: not appendix-old, and no spaces around the =.
    return bool(re.search(r"(?:^|[\s{])data-kind=(?:\"appendix\"|'appendix'|appendix)(?=[\s}]|$)", slide.attrs))


def _uncommented(text: str) -> str:
    "The text with each HTML comment blanked. A comment keeps its lines, so the line numbers stay the same."
    return re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)


def _answer(lines: list[str]) -> list[str]:
    "The filled lines of an answer. A bare label such as \"- Time:\" and the text of the template are empty."
    out = []
    for line in lines:
        text = re.sub(r"^\s*(?:[-*+]|\d+\.)\s+", "", line).strip()
        if not text or re.fullmatch(r"[A-Za-z][A-Za-z ]*:", text) or text.lower() in PLACEHOLDERS:
            continue
        out.append(text)
    return out


def _field(lines: list[str], label: str) -> str:
    "The value of a field such as \"- Shape: funnel\", in lower case, or \"\"."
    for line in lines:
        match = re.match(rf"^\s*(?:[-*+]\s+)?{re.escape(label)}:\s*(.*)$", line, re.I)
        if match:
            return match.group(1).strip().rstrip(".,;").lower()
    return ""


def read_plan(text: str) -> dict[str, tuple[int, list[str]]]:
    "The sections of a plan: the line of each ## heading, and the lines under it, with comments blanked."
    sections: dict[str, tuple[int, list[str]]] = {}
    seen: list[tuple[int, str]] = []   # (line, name) of each ## heading, in order, to find a repeated section
    name, fence = "", ""
    for number, line in enumerate(_uncommented(text.removeprefix("\ufeff")).split("\n"), 1):
        mark = re.match(r"^(`{3,}|~{3,})", line.strip())
        if fence:
            fence = "" if mark and mark.group(1)[0] == fence[0] else fence
        elif mark:
            fence = mark.group(1)
        elif line.startswith("## "):
            name = line[3:].strip()
            seen.append((number, name))
            sections.setdefault(name, (number, []))
            continue
        if name:
            sections[name][1].append(line)
    sections[""] = (0, [f"{line}\t{name}" for line, name in seen])   # the headings, for check_plan
    return sections


def minutes_of(value: str) -> int | None:
    """The minutes of a time such as "20 minutes", "1.5 hours", "90 seconds" or "an hour", rounded half up.
    A bare number is minutes. A negative time gives None."""
    found = re.search(r"(-?\d+(?:\.\d+)?|\ban?\b)\s*(hours?|hrs?|h\b|minutes?|mins?|seconds?|secs?|s\b)?",
                      value, re.I)
    if not found or (found.group(1).lower() in ("a", "an") and not found.group(2)):
        return None
    amount = 1.0 if found.group(1).lower() in ("a", "an") else float(found.group(1))
    if amount < 0:
        return None
    unit = (found.group(2) or "m").lower()
    scale = 60 if unit.startswith("h") else 1 / 60 if unit.startswith("s") else 1
    return int(amount * scale + 0.5)


def check_plan(text: str, hard: list[str], soft: list[str]) -> tuple[int | None, list[str]]:
    "Check that every section of the plan has an answer. Returns the minutes of the talk and the outline sections."
    sections = read_plan(text)
    names: set[str] = set()
    for entry in sections.pop("")[1]:
        line, name = entry.split("\t", 1)
        if name in names:
            hard.append(f"line {line}: a second section \"{name}\": put its answer under the first one")
        names.add(name)
    for name in PLAN_SECTIONS:
        if name not in sections:
            hard.append(f"no section \"## {name}\": copy the sections of templates/plan.md")
        elif name != "The outline" and not _answer(sections[name][1]):
            hard.append(f"line {sections[name][0]}: the section \"{name}\" has no answer")
    minutes = None
    if "The occasion" in sections:
        line, body = sections["The occasion"]
        for label in ("Audience", "Occasion", "Time"):
            if not _field(body, label):
                hard.append(f"line {line}: the occasion has no {label.lower()}")
        minutes = minutes_of(_field(body, "Time"))
        if _field(body, "Time") and minutes is None:
            hard.append(f"line {line}: the time of the talk has no number of minutes")
        elif minutes is not None and minutes < 1:
            hard.append(f"line {line}: the time of the talk is under a minute")
    if "The kind of talk" in sections:
        line, body = sections["The kind of talk"]
        story, action, shape = _field(body, "Pure story"), _field(body, "Call to action"), _field(body, "Shape")
        for label, value in (("Pure story", story), ("Call to action", action)):
            if value not in ("yes", "no"):
                hard.append(f"line {line}: \"{label}:\" must be yes or no")
        if not _field(body, "Kind"):
            hard.append(f"line {line}: the kind of talk is empty")
        if shape not in SHAPES:
            hard.append(f"line {line}: \"Shape:\" must be one of: " + ", ".join(SHAPES))
        elif story in ("yes", "no") and action in ("yes", "no"):
            expected = "symmetric hourglass" if action == "yes" else "funnel" if story == "yes" else SHAPES[0]
            if shape != expected:
                soft.append(f"line {line}: the shape is {shape}, and the answers ask for {expected}: "
                            f"does the story need it?")
    outline: list[str] = []
    if "The outline" in sections:
        line, body = sections["The outline"]
        parts: list[tuple[int, str, list[str]]] = []
        fence = ""
        for offset, text_line in enumerate(body, 1):
            mark = re.match(r"^(`{3,}|~{3,})", text_line.strip())
            if mark or fence:
                if fence and mark and mark.group(1)[0] == fence[0]:
                    fence = ""
                elif not fence:
                    fence = mark.group(1)
                if parts:
                    parts[-1][2].append(text_line)
                continue
            if text_line.startswith("### "):
                parts.append((line + offset, text_line[4:].strip(), []))
            elif parts:
                parts[-1][2].append(text_line)
        if not parts:
            hard.append(f"line {line}: the outline has no ### section")
        for at, name, lines in parts:
            if name.lower() in PLACEHOLDERS:
                hard.append(f"line {at}: the outline still has the section of the template")
            elif not _answer(lines):
                hard.append(f"line {at}: the section \"{name}\" of the outline has no points")
            outline.append(name)
        if len(parts) > SECTIONS_SOFT:
            soft.append(f"line {line}: {len(parts)} sections in the outline (about {SECTIONS_SOFT} at most)")
    return minutes, outline


def check_deck(slides: list[Slide], minutes: int | None, outline: list[str], soft: list[str]) -> None:
    "Check the deck of a talk with a plan: the count of slides, the last slide, the cues and the sections."
    # As in htmpres, the first appendix slide starts the appendix, and every later slide is in it.
    start = next((i for i, slide in enumerate(slides) if appendix(slide)), len(slides))
    main = slides[:start]
    for slide in slides[start + 1:]:
        if not appendix(slide):
            soft.append(f"slide {slide.number}, line {slide.first}: this slide is in the appendix, because it "
                        f"comes after slide {slides[start].number}, the first appendix slide")
    planned = max(1, minutes * PLANNED_SHARE // 100) if minutes else None
    if planned is not None and len(main) > planned:
        soft.append(f"{len(main)} slides for {minutes} minutes: plan {planned} minutes, {PLANNED_SHARE} percent of "
                    f"the time, and at least a minute for each slide, and fewer slides is better")
    if main and len(main) > 1 and not any(re.search(r"\bquestions\?", line, re.I) for line in main[-1].body):
        soft.append(f"slide {main[-1].number}, line {main[-1].first}: the last slide has no \"Questions?\" under "
                    f"its conclusion")
    for slide in slides[1:]:
        if "".join(text for _, text in slide.notes).strip() and not slide.cues:
            soft.append(f"slide {slide.number}, line {slide.first}: a script with no \"Cue:\" line")
        section = re.search(r"data-section\s*=\s*(?:\"([^\"]*)\"|'([^']*)')", slide.attrs)
        name = section and (section.group(1) if section.group(1) is not None else section.group(2))
        if section and outline and name not in outline:
            soft.append(f"slide {slide.number}, line {slide.first}: the section \"{name}\" is not in "
                        f"the outline of the plan")


def said(text: str) -> list[str]:
    "The sentences of a text. A full stop in an abbreviation, as in \"Fig. 2.\" or \"vs.\", does not end a sentence."
    return sentences(ABBREVIATION.sub(lambda m: m.group(0).replace(".", ""), text))


def check_slides(slides: list[Slide], hard: list[str], soft: list[str]) -> None:
    "Check the body of each slide: items, words, paragraphs, equations and figures."
    for slide in slides:
        where = f"slide {slide.number}, line {slide.first}"
        text = _without_math(slide.body)
        found = blocks(text)
        items = sum(1 for _, _, kind in found if kind == "item")
        if items > ITEMS_HARD:
            hard.append(f"{where}: {items} items (at most {ITEMS_HARD})")
        elif items > ITEMS_SOFT:
            soft.append(f"{where}: {items} items (fewer is easier to follow)")
        words = sum(len(WORD.findall(plain(raw))) for _, raw, _ in found)
        for line in slide.body:   # table cells are words on the slide too
            if line.strip().startswith("|") and not re.match(r"^\|[\s:|-]+\|?$", line.strip()):
                words += len(WORD.findall(plain(line.replace("|", " "))))
        if words > WORDS_HARD:
            hard.append(f"{where}: {words} words (about {WORDS_SOFT}, at most {WORDS_HARD})")
        elif words > WORDS_SOFT:
            soft.append(f"{where}: {words} words (about {WORDS_SOFT})")
        for line, raw, kind in found:
            count = len(said(plain(raw)))
            at = f"slide {slide.number}, line {slide.line + line - 1}"
            if kind == "para" and count > 1:
                hard.append(f"{at}: a paragraph of {count} sentences on a slide: {plain(raw)[:60]}")
            elif kind == "item" and count > 1:
                soft.append(f"{at}: an item of {count} sentences: {plain(raw)[:60]}")
        equations = _equations(slide.body)
        if equations > MAX_EQUATIONS:
            hard.append(f"{where}: {equations} equations (at most {MAX_EQUATIONS})")
        if equations and not "".join(text for _, text in slide.notes).strip():
            hard.append(f"{where}: an equation with no script to explain it")
        check_figures(slide, hard)


def check_figures(slide: Slide, hard: list[str]) -> None:
    "Each figure needs a caption or a label: a line of text right above or right below it."
    if any(re.search(r"<figcaption\b", line, re.I) for line in slide.body):
        return
    lines = slide.body
    for index, line in enumerate(lines):
        images = IMAGE.findall(line)
        if not images or all(BACKGROUND.match(image) for image in images):
            continue  # a Marp background, ![bg](photo.jpg), is not a figure
        rest = IMAGE.sub("", line).strip()
        if re.sub(r"<[^>]+>", "", rest).strip():
            continue  # the image shares its line with text
        if _text_near(lines, index, -1) or _text_near(lines, index, 1):
            continue
        hard.append(f"slide {slide.number}, line {slide.line + index}: a figure with no caption or label next to it")


def _text_near(lines: list[str], index: int, step: int) -> bool:
    "Is the nearest filled line in this direction a line of text that is not a heading, an image or markup?"
    index += step
    while 0 <= index < len(lines) and not lines[index].strip():
        index += step
    if not 0 <= index < len(lines):
        return False
    line = lines[index].strip()
    if line.startswith(("#", "<", "|", "```", "~~~", "$$", ":::")) or IMAGE.search(line):
        return False
    return bool(WORD.search(plain(line)))


def check_titles(slides: list[Slide], hard: list[str], soft: list[str]) -> None:
    "Titles start with the words that set the slide apart. They can mix questions, phrases and sentences."
    titles = [(slide, slide.title()) for slide in slides[1:]]   # the first slide holds the title of the talk
    for slide, title in titles:
        if title is None:
            soft.append(f"slide {slide.number}, line {slide.first}: no title")
    titled = [(slide, t) for slide, t in titles if t is not None]
    first: dict[str, tuple[int, str]] = {}
    for slide, (line, text) in titled:
        words = text.lower().split()
        if len(words) < 2:
            continue
        key = " ".join(words[:2])
        if key in first and first[key][1].lower() != text.lower():
            hard.append(f"slide {slide.number}, line {line}: the title starts with the same two words as slide "
                        f"{first[key][0]}: {text[:50]}")
        first.setdefault(key, (slide.number, text))


def check_script(slides: list[Slide], hard: list[str], soft: list[str]) -> int:
    "Check the spoken script: its sentences, the filler So, and its questions. Speaking time is not checked."
    total = 0
    for slide in slides:
        text = "\n".join(t for _, t in slide.notes)
        if not text.strip():
            if slide.number > 1:
                soft.append(f"slide {slide.number}, line {slide.first}: no script")
            continue
        start = slide.notes[0][0]
        found = blocks(text.replace('"', ""))   # quoted words are spoken, so they count
        words = sum(len(WORD.findall(plain(raw))) for _, raw, _ in found)
        total += words
        spoken: list[tuple[int, str]] = []
        for line, raw, _ in found:
            spoken.extend((start + line - 1, s) for s in said(plain(raw)))
        for index, (line, sentence) in enumerate(spoken):
            at = f"slide {slide.number}, line {line}"
            count = len(WORD.findall(sentence))
            if count > SENTENCE_SOFT:
                soft.append(f"{at}: a spoken sentence of {count} words (usually at most {SENTENCE_SOFT}): "
                            f"{sentence[:60]}")
            if re.match(r"^so\s*,", sentence, re.I):
                hard.append(f"{at}: the filler 'So,' at the start of a sentence")
            elif re.match(r"^so\b", sentence, re.I):
                soft.append(f"{at}: a sentence that starts with 'So': is it 'therefore'?")
            if FILLERS.search(sentence):
                soft.append(f"{at}: a filler, {FILLERS.search(sentence).group(0)!r}: {sentence[:60]}")
            if re.search(r"\b(?:do|does|are there) (?:you|anybody|anyone) (?:have )?any questions\b", sentence, re.I):
                soft.append(f"{at}: ask \"What questions do you have?\" in place of {sentence[:40]!r}")
            if sentence.endswith("?") and not re.fullmatch(r"what questions do you have\?", sentence, re.I):
                after = spoken[index + 1][1] if index + 1 < len(spoken) else ""
                if after.endswith("?"):
                    soft.append(f"{at}: two questions in a row: do they build tension?")
                elif not after:
                    soft.append(f"{at}: a question that the script of this slide does not answer")
    return total


def check(path: Path) -> tuple[list[str], list[str], str]:
    "Check one file. Returns the hard problems, the soft notes and a summary."
    text = path.read_text(encoding="utf-8")
    hard: list[str] = []
    soft: list[str] = []
    if path.name.lower() == "plan.md":
        _, outline = check_plan(text, hard, soft)
        return hard, soft, f"a plan with {len(outline)} section{'' if len(outline) == 1 else 's'} in its outline"
    matter = front_matter(text.removeprefix("\ufeff").split("\n"))[0]
    if path.suffix.lower() == ".qmd" and "format" not in matter:   # a Quarto deck with a format: is another tool
        slides = split_qmd(text, hard)
        plan = path.parent / "plan.md"
        minutes, outline = None, []
        if not plan.is_file():
            hard.append(f"no plan.md next to {path.name}: fill in the plan from templates/plan.md before the slides")
        else:
            try:
                plan_hard: list[str] = []
                minutes, outline = check_plan(plan.read_text(encoding="utf-8"), plan_hard, soft)
                hard.extend("plan.md, " + problem for problem in plan_hard)
            except UnicodeDecodeError:
                hard.append("plan.md is not UTF-8 text")
            except OSError as error:
                hard.append(f"plan.md cannot be read: {error.strerror}")
        check_deck(slides, minutes, outline, soft)
    else:
        _, slides = split(text)
    if not slides:
        hard.append("no slides: the deck is empty")
    check_slides(slides, hard, soft)
    check_titles(slides, hard, soft)
    words = check_script(slides, hard, soft)
    return hard, soft, f"{len(slides)} slide{'' if len(slides) == 1 else 's'}, {words} words of script"


def main() -> None:
    "Check every deck named on the command line."
    args, verbose, names = sys.argv[1:], False, []

    def usage(message: str) -> None:
        print(f"check_talk.py: {message}", file=sys.stderr)
        print(__doc__.strip().split("\n\n")[1], file=sys.stderr)
        sys.exit(2)

    while args:
        arg = args.pop(0)
        if arg == "-v":
            verbose = True
        elif arg.startswith("-") and arg != "-":
            usage(f"unknown option {arg}")
        else:
            names.append(arg)
    if not names:
        usage("name at least one deck")
    for name in names:
        if not Path(name).is_file():
            usage(f"no such file: {name}")
        try:
            Path(name).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            usage(f"{name} is not UTF-8 text: save the deck as UTF-8")
        except OSError as error:
            usage(f"{name} cannot be read: {error.strerror}")
    failed = False
    for name in names:
        hard, soft, summary = check(Path(name))
        print(f"{name}: {summary}: {len(hard)} hard, {len(soft)} soft")
        for problem in hard:
            print("  HARD " + problem)
        if verbose:
            for note in soft:
                print("  soft " + note)
        failed = failed or bool(hard)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
