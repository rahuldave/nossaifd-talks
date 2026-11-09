# The talk checker

`check_talk.py` is a short Python program. It reads the plan and the slides of a talk. It reports where
the plan, the slides or the script break a rule of [TALKS.md](../TALKS.md) that a program can measure. It needs Python
3.11 or later, and no other packages.

Most rules of TALKS.md come from the tutorial deck and the presentation tips of Rosalind Reid. Her
presentation tips draw on The Chicago Guide to Communicating Science, by Scott Montgomery. The plan comes from the presentation worksheet of Jonathan Schwabish, in his book *Better Presentations*. The
check that titles start with different words comes from a post by Shreya Shankar. Several numbers are the guide's own,
and TALKS.md marks each one.

## Run it

Give the checker one or more files:

```
uv run --no-project python check_talk.py talk/plan.md
uv run --no-project python check_talk.py talk/slides.qmd
uv run --no-project python check_talk.py -v talk/slides.qmd
```

The checker reads a file by its name. A file named `plan.md` is a plan, and it is checked alone. A file that
ends in `.qmd` is a deck in the Markdown of htmpres, and the checker also checks the `plan.md` next to it. A
`.qmd` file whose front matter has the key `format`, such as a Quarto deck for reveal.js, is a deck from another
tool. Any other file is a deck from another tool, with no plan.

The first command shows the hard problems of the plan. The `-v` option also shows the soft notes. The checker
does not check pace, and it has no option for a time slot. It reads the time from the plan.

The program ends with one of three exit statuses:

| Status | Meaning |
|---|---|
| 0 | Every file passes |
| 1 | A file has a hard problem, so a script or a CI job can stop on it |
| 2 | A usage error, such as a missing file or an unknown option |

The checker runs from any folder, and it needs no other file. It holds a copy of the Markdown reader of
[`check.py`](https://github.com/rahuldave/nossaifd/blob/main/check.py), the checker for reports in nossaifd, so both checkers read a page the same way.

## The plan

The plan has the sections of [the template](https://github.com/rahuldave/nossaifd-talks/blob/main/templates/plan.md), each under a `##` heading. A section is empty
when it holds only comments, bare labels such as `- Time:`, or the text of the template. The section "The
outline" holds its sections under `###` headings, and a `###` inside a code block is not a section. A section
that appears twice is a hard problem. The time can be in minutes or in hours, such as "1.5 hours". A number with
no unit is minutes.

## A deck in htmpres

A deck in htmpres is a `.qmd` file, as htmpres reads it:

- A line that starts with `## ` starts a slide, and the rest of the line is the title. Attributes in braces at
  the end of the line, such as `{data-kind="appendix"}`, are not part of the title. A `##` inside a code block
  does not start a slide. A `##` inside notes or an HTML comment is a hard problem, because htmpres starts a
  slide there and cuts the notes in two.
- A `---` line inside notes or a comment is part of them, and it is not checked.
- A line that is only `---` must come right before a `##` line, because htmpres does not start a slide there.
- Text before the first `##` line is left out by htmpres, so the checker fails it.
- The script of a slide is in a block from `::: notes` to `:::`. A line of the notes that starts with `Cue:`
  is the cue, and it is not script.
- A slide marked `{data-kind="appendix"}` is in the appendix. The count of slides and the check of the last
  slide leave the appendix out.

## A deck from another tool

A deck from another tool is one Markdown file, as Marp, Slidev and reveal.js read it:

- A line that is only `---` starts a new slide. A `---` inside a code block or a comment does not.
- YAML front matter can open the file. The checker reads only its key `marp`. A byte order mark before the
  front matter does not hide it.
- The first heading of a slide is its title. The first slide holds the title of the talk.
- The script of a slide is in its notes. A line of the notes that starts with `Cue:` is not script.

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
| A plan with a missing section, or a section with no answer | 5 |
| A plan with no audience, occasion or time, or a time with no number of minutes | 1 and 2 |
| A plan whose kind of talk is empty, whose "Pure story:" or "Call to action:" is not yes or no, or whose shape is not one of the three | 6 |
| A plan whose outline has no `###` section, still has the section of the template, or has a section with no points | 30 |
| A `.qmd` deck with no `plan.md` next to it, or with a plan that has a hard problem | 5 |
| A `---` line in a `.qmd` deck that is not right before a `##` line, outside notes and comments | |
| A `##` line inside the notes or an HTML comment of a `.qmd` deck | |
| A section of the plan that appears twice | 5 |
| Text before the first `##` line of a `.qmd` deck | |
| A slide with more than 9 items. Each item of a list counts, nested or not | 53 |
| A slide with more than 40 words. Tables count, and equations and figures do not | 54 |
| A paragraph of two or more sentences on a slide. A full stop in an abbreviation, as in "Fig. 2." or "vs.", does not end a sentence | 55 |
| Two titles that start with the same two words, but are not the same title | 56 |
| More than 2 equations on a slide | 65 |
| An equation on a slide with no script | 65 |
| A figure with no line of text right above it or right below it. A Marp background, such as `![bg](photo.jpg)`, is not a figure | 66 |
| A sentence of the script that starts with "So," and a comma | 40 |
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
| A question at the end of the script of a slide, other than "What questions do you have?" | The answer can come on the next slide |
| A shape that the answers of the plan do not ask for | A rule can give way to the story |
| An outline of more than 5 sections | Schwabish says about five |
| More slides than 75 percent of the minutes, leaving out the appendix | Plan for 75 percent of the time, and each slide takes at least a minute; a person decides if a slide is short |
| A last slide with no "Questions?" | The last slide shows the conclusion and asks for questions, and the words can differ |
| A slide with a script and no `Cue:` line, in a `.qmd` deck | Some slides need no cue |
| A slide whose `data-section` is not a section of the outline | The names can differ a little |
| An appendix slide before the last slide | The person may want it there |
| "um", "uh" or "the thing is" in the script | A quote can hold them |
| "Do you have any questions?" in the script | Ask "What questions do you have?" |

## Why the split is where it is

A check is hard when the program measures the rule exactly and the rule has a clear limit. The count of items,
the count of words and the count of equations are exact. "So," with a comma is the filler. "So" with no comma
can mean "therefore", which [GUIDE.md](https://github.com/rahuldave/nossaifd/blob/main/GUIDE.md) of nossaifd accepts.

A check is soft when the rule says "about", or when the story can need an exception. The limit of 30 words is
"about", so the checker fails a slide only above 40. TALKS.md lets a rule give way to the story. So a long
spoken sentence and questions in a row are soft notes, and a person decides if the story needs them.

The checker does not check the structure of titles. TALKS.md prefers a sentence that states the point, and it
lets a deck mix questions and phrases, as Rosalind Reid does. A program cannot tell a sentence from a phrase
reliably, so it leaves the form to a person. A title of one word, such as "Thanks", has no first two words to compare, so the
checker leaves it out.

## What it does not check

The checker reads the plan, the slides and the script only. It skips code blocks, HTML, link targets and the labels
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

- the quality of the answers in the plan, only that each section has one
- the story and its five parts
- whether the opening holds back the detail of the result, in an asymmetric hourglass
- the news first in a spoken sentence
- the fit of the talk to its audience
- the tone, the analogies and the humor
- the pace
- the colors, the background and the labels inside a figure

Read the plan and the deck after they pass.

## Use it in a project

Copy `TALKS.md`, `templates/plan.md` and `check_talk.py` into the project, for example into `docs/talks/`. A
recipe can run the checker on every talk:

```just
# Check the talks against the talk guide. -v also shows the soft notes
talks *args:
    uv run --no-project python docs/talks/check_talk.py talks/*/slides.qmd {{ args }}
```

In a project with the skill `presentations`, the skill holds copies of these files. Run
`.agents/skills/presentations/scripts/check_talk.py` instead.
