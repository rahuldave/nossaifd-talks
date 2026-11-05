"""Check a talk, written as one Markdown deck, against the measurable rules in TALKS.md.

    uv run --no-project python check_talk.py deck.md [deck.md ...]   report each deck; exit 1 if a hard rule is broken
    uv run --no-project python check_talk.py -v deck.md              also show the soft notes, for a person to judge

The deck is one Markdown file. A line that is only --- starts a new slide. YAML front matter can open the file.
The checker reads only its key "marp", and it does not check speaking time. The spoken script of a slide is in its
notes: an HTML comment (Marp, Slidev), a "::: notes" block (Pandoc, Quarto) or an <aside class="notes"> block
(reveal.js). In a deck with no "marp:" key, a line that starts with "Note:" also starts the script on a slide
that has no other notes. The script then runs to the end of the slide.

The exit status is 0 when every deck passes, 1 when a deck has a hard problem, and 2 for a usage error, such as a
missing file or an unknown option.

The slide rules come from the tutorial "Communicating Your Work" and the presentation tips of Rosalind Reid,
which draw on The Chicago Guide to Communicating Science by Scott L. Montgomery. The rule that a title starts with
the words that set it apart comes from the post "Five Principles for Generating Readable AI Text in Bulk" by Shreya
Shankar. TALKS.md names the numbers that are this guide's own. This checker shares no writing rule with check.py, the
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
        self._read(lines)
        # The line to report for the whole slide: its first filled line
        self.first = next((line + i for i, text in enumerate(lines) if text.strip()), line)

    def _read(self, lines: list[str]) -> None:
        mode, fence = "", ""   # mode: "", "comment", "div", "aside" or "note"
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
                closing = re.match(r"^:::+\s*$", stripped) if mode == "div" else re.search(r"</aside>", line, re.I)
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
    key = re.compile(r"^([A-Za-z0-9_-]+):(?:\s+(.*))?$")
    yaml = re.compile(r"^(?:[A-Za-z0-9_-]+:(?:\s|$)|\s+\S|-\s|#)")
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
            if sentence.endswith("?"):
                after = spoken[index + 1][1] if index + 1 < len(spoken) else ""
                if after.endswith("?"):
                    soft.append(f"{at}: two questions in a row: do they build tension?")
                elif not after:
                    soft.append(f"{at}: a question that the script of this slide does not answer")
    return total


def check(path: Path) -> tuple[list[str], list[str], str]:
    "Check one deck. Returns the hard problems, the soft notes and a summary."
    _, slides = split(path.read_text(encoding="utf-8"))
    hard: list[str] = []
    soft: list[str] = []
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
