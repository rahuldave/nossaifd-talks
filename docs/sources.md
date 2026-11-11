# Sources and credit

The rules of [the talk guide](../TALKS.md) and the [worked examples](../EXAMPLES.md) come from the sources
on this page. This page says who wrote each one and where to read it. Each rule of the talk guide also names
its source and links to the exact page.

## Rosalind Reid

Rosalind Reid taught "Communicating Your Work", a tutorial for the course AC297r at the
Institute for Applied Computational Science at Harvard, in March 2015.
She was the editor of *American Scientist* magazine from 1992 to 2008. She worked at the Harvard Initiative
in Innovative Computing from 2008 to 2010. She worked at the Institute for Applied Computational Science
from 2010 to 2013. In 2015 she was the executive director of the
[Council for the Advancement of Science Writing](https://casw.org/).

Rosalind Reid gave permission to use her material, on one condition. Every place that uses her work
credits her. The test file `tests/test_credit.py` checks the credit in three ways:

- It fails when a page built on her work does not name her in full. These pages are the README, the
  talk guide, the examples, the talk checker, the pages of this site and the files of the skill.
- It fails when any other file gives only her surname, or links to her PDFs, and does not name her in full.
- It checks each rule and each paragraph of TALKS.md. It fails when one links to her PDFs and does not name
  her in full.

The test cannot tell if a page uses her advice with no link and no name. A person must check that.

The talk guide states her advice in its own words. The examples quote her slides word for word, and each
example names her and links to the page. This site does not hold her PDFs. It links to them in the
repository on GitHub. Her material, as she gave it:

| File | What it holds | Pages | Used in |
|---|---|---|---|
| [Rosalind Reid, written reports](https://github.com/rahuldave/nossaifd-talks/blob/main/sources/reid/reid-2015-written-reports.pdf) | "Communicating Your Work: written reports". How a written sentence differs from a spoken one, the stress position, actions in verbs, revision | 23 | Rules 33, 38 and 71 of [the talk guide](../TALKS.md), and the examples W5 and W17 |
| [Rosalind Reid, tutorial deck](https://github.com/rahuldave/nossaifd-talks/blob/main/sources/reid/reid-2015-communicating-your-work-deck.pdf) | "Communicating Your Work: a tutorial". The story of a project, the audience, slides and figures, the storyteller's tricks, an exercise | 59 | [The talk guide](../TALKS.md), and the examples that start with D |
| [Rosalind Reid, presentation tips](https://github.com/rahuldave/nossaifd-talks/blob/main/sources/reid/reid-presentation-tips.pdf) | "Some thoughts about presentations". Preparation, pace, practice, nine common problems, layout | 5 | [The talk guide](../TALKS.md), and the examples that start with P |

The files are in the folder
[sources/reid](https://github.com/rahuldave/nossaifd-talks/tree/main/sources/reid) of the repository. Each rule
that uses them gives the page number next to its link.

Rosalind Reid credits the [Duke Scientific Writing Resource](https://sites.duke.edu/scientificwriting/) for
her rules about sentences. The presentation tips draw mostly on Scott L. Montgomery's book, below.

## Scott L. Montgomery

Scott L. Montgomery wrote *The Chicago Guide to Communicating Science*, from the University of Chicago Press.
Rosalind Reid's [presentation tips](https://github.com/rahuldave/nossaifd-talks/blob/main/sources/reid/reid-presentation-tips.pdf)
draw mostly on its chapter about talks. [The talk guide](../TALKS.md) uses the book through her tips. It
names Montgomery for each rule that she takes from him.

Rosalind Reid's presentation tips also pass on advice from Herbert L. Hirsch, *Essential Communication
Strategies for Scientists, Engineers, and Technology Professionals*, second edition, IEEE Press, 2003. The
talk guide names Hirsch at the rule that uses it, and the example P15 quotes it.

## Jonathan Schwabish

Jonathan Schwabish wrote *Better Presentations*, subtitled "A Guide for Scholars, Researchers, and Wonks",
from Columbia University Press, 2017. He is an economist and a writer on the presentation of data. The talk
guide takes from the book the plan of a talk, the hourglass, the opening and closing statements, the
sections of the outline, slides that build one point at a time, and advice on delivery. Each rule that
uses the book gives its pages, as "Schwabish, pages 14 to 23".

The book is under copyright, and no permission covers it. [The worksheet](../WORKSHEET.md) quotes his
presentation worksheet and its section, pages 14 to 23, word for word, under fair use. The examples S1 and S2
quote his openings and closings from that section. The rest of the talk guide states his advice in its own
words. [A summary of the book](schwabish-summary.md) gives each chapter in this guide's own words, and it
marks the parts of the book that are for the words of a talk, and those for the look of the slides.

## Shreya Shankar

The project uses two works by Shreya Shankar:

- [The plain-writing skill](https://github.com/docwriter-org/plain-writing-skill), under the MIT licence.
  The talk guide cites it for contractions and for questions in the script, rules 34 and 35. The examples
  E5 and B8 come from the eval of the skill.
- ["Five Principles for Generating Readable AI Text in Bulk"](https://fsdatalab.github.io/blog/agent-text-at-scale/),
  a post from October 2026. It is about many short items that a reader skims, such as titles, list
  items, notifications and the rows of a dashboard. The talk guide's rule 56, that a title starts with the
  words that set it apart, comes from it.

## Oskar Austegard

[The declaude skill by Oskar Austegard](https://github.com/oaustegard/claude-skills/tree/6baa7290da972191749acda03c63297e67b3fc26/declauding), in the repository
oaustegard/claude-skills, version 0.14.0 at commit 6baa729, under the MIT licence, copyright (c) 2025 Oskar
Austegard. Oskar Austegard calls it declauding, and nossaifd ships it as the skill `declaude`. GUIDE.md of nossaifd takes rules 50 to 55 from it, and the talk guide applies them, with four
exceptions for the script. The ban on a teaser in rule 17 of the talk guide comes from its register, entries 8
and 42. `just declaude` runs its linter on the script of a deck, from the copy that nossaifd ships. The README of
the skill names its own sources, such as the Wikipedia page "Signs of AI writing".

## The guide for reports

The words of a script follow [GUIDE.md](https://github.com/rahuldave/nossaifd/blob/main/GUIDE.md), the
guide of nossaifd for reports, with the exceptions in the talk guide. The page
[Sources and credit](https://github.com/rahuldave/nossaifd/blob/main/docs/sources.md) of nossaifd names its
sources, for example ASD-STE100.

## Where the sources disagree

The sources do not always agree. A spoken sentence puts the news first, and a written one puts it last.
Some sources ask for metaphor and humor, and others forbid them. [Why the rules](why.md) lists each
disagreement about talks, what each source says, and what the talk guide chose.
