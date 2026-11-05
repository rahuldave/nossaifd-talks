# The talk checker

`check_talk.py` is a short Python program. It reads a talk, written as one Markdown deck. It reports where
the slides or the script break a rule of [TALKS.md](../TALKS.md) that a program can measure. It needs Python
3.11 or later, and no other packages.

Most rules of TALKS.md come from the tutorial deck and the presentation tips of Rosalind Reid. Her
presentation tips draw on The Chicago Guide to Communicating Science, by Scott Montgomery. The check that
titles start with different words comes from a post by Shreya Shankar. Several numbers are the guide's own,
and TALKS.md marks each one.

## Run it

Give the checker one or more decks:

```
uv run --no-project python check_talk.py deck.md
uv run --no-project python check_talk.py -v deck.md
```

The first command shows the hard problems of each deck. The `-v` option also shows the soft notes. The
checker does not check speaking time or pace, so it has no option for a time slot.

The program ends with one of three exit statuses:

| Status | Meaning |
|---|---|
| 0 | Every deck passes |
| 1 | A deck has a hard problem, so a script or a CI job can stop on it |
| 2 | A usage error, such as a missing file or an unknown option |

The checker runs from any folder, and it needs no other file. It holds a copy of the Markdown reader of
[`check.py`](https://github.com/rahuldave/nossaifd/blob/main/check.py), the checker for reports in nossaifd, so both checkers read a page the same way.

## The deck

A deck is one Markdown file, as Marp, Slidev and reveal.js read it:

- A line that is only `---` starts a new slide. A `---` inside a code block or a comment does not.
- YAML front matter can open the file. The checker reads only its key `marp`. A byte order mark before the
  front matter does not hide it.
- The first heading of a slide is its title. The first slide holds the title of the talk.
- The script of a slide is in its notes.

The checker reads four kinds of notes:

| Notes | Tools |
|---|---|
| An HTML comment, `<!-- ... -->` | Marp and Slidev. TALKS.md recommends this form. |
| A block from `::: notes` to `:::` | Pandoc and Quarto |
| A block from `<aside class="notes">` to `</aside>` | reveal.js |
| A line that starts with `Note:`, and the rest of the slide after it, on a slide with no other notes | reveal.js |

The checker reads `Note:` only in a deck with no key `marp` in its front matter. It decides for each slide.
A slide that has an HTML comment or another block as notes keeps them, and its `Note:` line is text on the
slide. So an author's comment on the title slide does not turn off `Note:` on the other slides. The line must
start with `Note:` exactly, with a capital N and no space before it. In a Marp deck, a line such as "Note:
the cache is cold" is text on the slide, and the checker checks it.

A comment in which each line sets a Marp directive, such as `<!-- _class: lead -->`, is not notes. In a
comment that also holds the script, only a line that starts with `_`, such as `_class: lead`, is a directive.
Every other line is script, so a script line such as "title: we explain the chart" stays. A slide that
has only lowercase `key: value` lines is the front matter of the next slide, as in Slidev.

## What it checks

The checker sorts what it finds into hard problems and soft notes. A hard problem breaks a rule, and the
program can be sure of it. A soft note marks something that a person must judge. The program cannot tell if
it is wrong, or the rule says "about".

| Hard problem | Rule in TALKS.md |
|---|---|
| A slide with more than 9 items. Each item of a list counts, nested or not | 36 |
| A slide with more than 40 words. Tables count, and equations and figures do not | 37 |
| A paragraph of two or more sentences on a slide. A full stop in an abbreviation, as in "Fig. 2." or "vs.", does not end a sentence | 38 |
| Two titles that start with the same two words, but are not the same title | 39 |
| More than 2 equations on a slide | 45 |
| An equation on a slide with no script | 45 |
| A figure with no line of text right above it or right below it. A Marp background, such as `![bg](photo.jpg)`, is not a figure | 46 |
| A sentence of the script that starts with "So," and a comma | 26 |
| A deck with no slides | |

| Soft note | Why a person must judge it |
|---|---|
| A slide with 6 to 9 items | Fewer items are easier to follow, and 9 is Rosalind Reid's limit |
| A slide with 31 to 40 words | The limit is about 30 words |
| A list item of two or more sentences | An item can need a second short sentence |
| A slide after the first one with no title | A slide of only a picture can do without one |
| A slide after the first one with no script | Some slides need no words |
| A spoken sentence of more than 25 words | A spoken sentence is usually 20 to 25 words, and a longer one is fine when its punctuation makes it clear |
| A sentence of the script that starts with "So" and no comma | "So" can mean "therefore" |
| Two questions in a row in the script | Questions in a row can build tension |
| A question at the end of the script of a slide | The answer can come on the next slide |

## Why the split is where it is

A check is hard when the program measures the rule exactly and the rule has a clear limit. The count of items,
the count of words and the count of equations are exact. "So," with a comma is the filler. "So" with no comma
can mean "therefore", which [GUIDE.md](https://github.com/rahuldave/nossaifd/blob/main/GUIDE.md) of nossaifd accepts.

A check is soft when the rule says "about", or when the story can need an exception. The limit of 30 words is
"about", so the checker fails a slide only above 40. TALKS.md lets a rule give way to the story. So a long
spoken sentence and questions in a row are soft notes, and a person decides if the story needs them.

The checker does not check the structure of titles. Rosalind Reid mixes questions and phrases in her titles,
so a deck can mix them too. A title of one word, such as "Thanks", has no first two words to compare, so the
checker leaves it out.

## What it does not check

The checker reads the slides and the script only. It skips code blocks, HTML, link targets and the labels
inside an image. It does not apply the rules of [GUIDE.md](https://github.com/rahuldave/nossaifd/blob/main/GUIDE.md), the guide of nossaifd for reports. Read the
words of the slides against GUIDE.md yourself. Do not run `check.py`, the checker for reports, on a deck.
It also reads the script, and it fails the contractions there.

nossaifd ships the recipe `just prose`, and jnterfaces installs it with the role `prose`. The recipe runs
`check.py` on every
Markdown file that git tracks. It leaves out only `AGENTS.md`, `CLAUDE.md` and the files in `.agents`,
`.claude` and `.codex`. The recipe has no way to leave out a deck. A deck named `talk.deck.md` still ends in `.md`, so
the recipe checks it. Do one of these things instead:

- Give the deck the extension `.markdown`, which the recipe does not match. Check first that your slide tool
  reads a file with that extension.
- Run `just prose` with the names of the pages to check, so that it checks only those pages.

The checker cannot judge these rules:

- the story and its five parts
- the news first in a spoken sentence
- the fit of the talk to its audience
- the tone, the analogies and the humor
- the speaking time and the pace
- the colors, the background and the labels inside a figure

Read the deck after it passes.

## Use it in a project

Copy `TALKS.md` and `check_talk.py` into the project, for example into `docs/talks/`. A recipe can run the
checker on every deck:

```just
# Check the decks against the talk guide. -v also shows the soft notes
talks *args:
    uv run --no-project python docs/talks/check_talk.py talks/*.md {{ args }}
```

In a project with the skill `presentations`, the skill holds copies of both files. Run
`.agents/skills/presentations/scripts/check_talk.py` instead.
