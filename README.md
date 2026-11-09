# nossaifd-talks

**A guide for talks that AI models write.** A talk has a plan, slides and a spoken script. This repository holds a
guide for them, a template for the plan, a checker, an agent skill and worked examples. It is the home for guides on
talks, slides and visuals, and it will take more of them later.

The site is at https://rahuldave.com/nossaifd-talks/.

Most of the advice comes from "Communicating Your Work", a tutorial by Rosalind Reid. She taught it at
Harvard in 2015, and she was the editor of *American Scientist* magazine from 1992 to 2008. Each rule that
uses her work names her and gives the page. The plan of a talk comes from Jonathan Schwabish's book *Better
Presentations*, and each rule from it gives its pages. See [Sources and credit](docs/sources.md).

## The guide for reports

This repository grew out of [nossaifd](https://github.com/rahuldave/nossaifd), "Not so shitty AI first
drafts". nossaifd holds [GUIDE.md](https://github.com/rahuldave/nossaifd/blob/main/GUIDE.md), the guide for
reports, and its checker `check.py`. Its site is at https://rahuldave.com/nossaifd/.

The words of a script follow GUIDE.md, with the exceptions in [TALKS.md](TALKS.md). A listener cannot go
back and hear a sentence again, but a reader can read it again. So a spoken sentence puts the news first,
and a written sentence puts it last. A slide holds a few words that a person sees for less than a minute.
The checker for reports would fail every good slide, so a talk has its own checker.

## What is here

| File | What it is |
|---|---|
| [`TALKS.md`](TALKS.md) | The rules for talks: the plan, the shape, the story, the audience, slides, figures, the spoken script and delivery |
| [`WORKSHEET.md`](WORKSHEET.md) | Jonathan Schwabish's presentation worksheet and his section on it, quoted under fair use |
| [`templates/plan.md`](https://github.com/rahuldave/nossaifd-talks/blob/main/templates/plan.md) | The template of the plan of a talk |
| [`examples/cache/`](https://github.com/rahuldave/nossaifd-talks/tree/main/examples/cache) | An example talk, with its plan and its slides in the Markdown of htmpres |
| [`check_talk.py`](https://github.com/rahuldave/nossaifd-talks/blob/main/check_talk.py) | It checks a plan, a deck and its script against the rules that a program can measure. See [the talk checker](docs/check-talk.md) |
| [`EXAMPLES.md`](EXAMPLES.md) | Worked examples for the rules of TALKS.md, from Rosalind Reid, Jonathan Schwabish and Shreya Shankar. Each example names its source |
| [`sources/reid/`](https://github.com/rahuldave/nossaifd-talks/tree/main/sources/reid) | The PDFs of Rosalind Reid's tutorial, which the guide cites page by page |
| `docs/` | The pages of the site, about the checker, the sources, the choices of the guide and a summary of Schwabish's book |
| [`.agents/skills/presentations/`](https://github.com/rahuldave/nossaifd-talks/tree/main/.agents/skills/presentations) | The agent skill for talks, with copies of `TALKS.md`, `EXAMPLES.md`, `WORKSHEET.md`, the plan template and `check_talk.py` |

## How to use it

1. Give `TALKS.md` to the model with the task.
2. Give the model GUIDE.md of nossaifd too, for the words of the slides and the script.
3. Copy `templates/plan.md` into the folder of the talk as `plan.md`, and fill in every section. Run the
   checker on it until it passes.
4. Write the slides as `slides.qmd`, in the Markdown of [htmpres](https://github.com/rahuldave/htmpres). A
   line that starts with `##` starts a slide, and the spoken script is in the notes of each slide. The
   section "The files of a talk" of TALKS.md gives the format.
5. Run the checker on the slides, and fix each hard problem:

   ```
   uv run --no-project python check_talk.py talk/plan.md
   uv run --no-project python check_talk.py -v talk/slides.qmd
   ```

6. Read the plan and the slides. The checker cannot judge the story or the tone.

The checker needs only Python 3.11 or later, with no other packages and no other file. `uv run` gives that
Python, so the machine needs only `uv`.

## The skill

The repository is also an agent skill package with one skill, `.agents/skills/presentations/`. It holds
copies of the guide, the worksheet, the examples, the plan template and the checker, and a `SKILL.md` that tells an agent how to use them.
The skill tells the agent to read GUIDE.md from the skill `nossaifd` when that skill is installed, and from
GitHub when it is not. The package file
[`skill-package.json`](https://github.com/rahuldave/nossaifd-talks/blob/main/skill-package.json) names the
skill. To add the skill to a project with `npx`, run this command:

```
npx skills add rahuldave/nossaifd-talks -a codex --skill presentations -y
```

After you change the guide, the worksheet, the examples, the template or the checker, run `just sync` to copy them into the skill.
`just check` fails while the copies differ.

## Work on this repository

The [`Justfile`](https://github.com/rahuldave/nossaifd-talks/blob/main/Justfile) holds every task. The
machine needs `just` and `uv`.

- `just check` runs the lint, the tests, the prose checks and the check of the site.
- `just site` builds the site into `_site/` with smalldocs.
- `just package-lint` checks `skill-package.json`.

## Where the rules come from

[Sources and credit](docs/sources.md) says what each source gives, and [Why the rules](docs/why.md) says
what the guide chose where the sources disagree.

- **"Communicating Your Work", a tutorial by Rosalind Reid**, for the course AC297r at Harvard in March
  2015. It gives the structure of a talk, the rules for slides and figures, and most of the advice on
  delivery. Her PDFs are in
  [`sources/reid/`](https://github.com/rahuldave/nossaifd-talks/tree/main/sources/reid). She gave
  permission to use them on one condition. Every place that uses her work credits her.
- **Better Presentations, by Jonathan Schwabish**, Columbia University Press, 2017. It gives the plan of a
  talk, the hourglass, the opening and closing statements and the sections. The worksheet quotes the book
  under fair use, and the rest of the guide states its advice in its own words.
- **The Chicago Guide to Communicating Science, by Scott L. Montgomery.** Rosalind Reid's presentation
  tips draw mostly on it.
- **The plain-writing skill by Shreya Shankar**, at
  https://github.com/docwriter-org/plain-writing-skill, under the MIT licence. The guide cites it on
  contractions and questions in the script.
- **["Five Principles for Generating Readable AI Text in Bulk"](https://fsdatalab.github.io/blog/agent-text-at-scale/),
  by Shreya Shankar.** It gives the rule that a slide title starts with the words that set it apart.

## Licence

The code and the guide are under the MIT licence, in
[`LICENSE`](https://github.com/rahuldave/nossaifd-talks/blob/main/LICENSE). Rosalind Reid's PDFs in
`sources/reid/` are her work, used with her permission, and they are not under the MIT licence. The text of
Jonathan Schwabish in `WORKSHEET.md` and in the examples S1 and S2 is his, quoted under fair use, and it is
not under the MIT licence.

Rosalind Reid lets others use her work on one condition. Every place that uses it credits her. So text in
the guide, the examples and the skill that comes from her work must keep its credit to Rosalind Reid. The
condition holds in every copy and in every changed version, and the MIT licence does not remove it.
