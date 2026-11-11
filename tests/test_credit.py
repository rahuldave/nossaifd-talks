"""Rosalind Reid lets this project use her material on one condition: every place that uses it credits her.

These tests fail when a page that uses her work does not name her in full, when a rule of TALKS.md or an example
of EXAMPLES.md links to her PDFs and does not name her in full there, when a page drops the notice that her credit
must stay, and when the site would publish her PDFs in place of linking to them on GitHub.
"""
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
TEXT = {'.md', '.py', '.yaml', '.yml', '.json', '.just'}
# The skills nossaifd and declaude, installed from nossaifd with npx for its prose flow. They are its files
INSTALLED = ('.agents/skills/nossaifd/', '.agents/skills/declaude/', 'skills-lock.json')   # and the lock file of npx
# The pages that must name her whether or not they mention her by surname: each one is built on her work.
MUST = ['README.md', 'TALKS.md', 'EXAMPLES.md', 'docs/sources.md', 'docs/why.md', 'docs/check-talk.md', 'check_talk.py',
        '.agents/skills/presentations/SKILL.md', '.agents/skills/presentations/agents/openai.yaml',
        '.agents/skills/presentations/references/TALKS.md', '.agents/skills/presentations/references/EXAMPLES.md',
        '.agents/skills/presentations/scripts/check_talk.py']
GITHUB = 'https://github.com/rahuldave/nossaifd-talks/blob/main/sources/reid/'
# The pages that carry the notice that text from her work keeps its credit, and that her PDFs are not under MIT
NOTICE = ['README.md', 'TALKS.md', 'EXAMPLES.md', '.agents/skills/presentations/SKILL.md',
          '.agents/skills/presentations/references/TALKS.md', '.agents/skills/presentations/references/EXAMPLES.md']
PDFS = ['reid-2015-communicating-your-work-deck.pdf', 'reid-2015-written-reports.pdf', 'reid-presentation-tips.pdf']


def rule_blocks(text):  # [(first line, text)] of each rule, list item and paragraph of a guide
    "Split a guide into blocks. A line with no indent starts a block after a blank line, or as a list item or a heading."
    out, block, blank = [], [], True
    for number, line in enumerate(text.split('\n'), 1):
        starts = line[:1] not in ('', ' ', '\t') and (blank or re.match(r'^(\d+\.|[-*+]|#+)\s', line))
        if starts and block:
            out.append(block)
            block = []
        if line.strip() or block:
            block.append((number, line))
        blank = not line.strip()
    if block:
        out.append(block)
    return [(b[0][0], '\n'.join(line for _, line in b)) for b in out]


def uncredited(text):  # The first line of each block that links to her PDFs and does not name her in full
    "The rules that use Rosalind Reid's PDFs must each name her in full, so that a rule copied alone keeps her credit."
    return [line for line, block in rule_blocks(text) if 'sources/reid/' in block and 'Rosalind Reid' not in block]


# Phrases that mark one of her rules in a step or a checklist item of the presentations skill
MARKERS = ('five parts', '90 to 120', 'minute test', '20 seconds', 'movie', 'video', 'still image', 'background',
           'thank', 'the occasion', 'the questions', 'plain words', 'says what it means')
PRESENTATIONS = '.agents/skills/presentations/SKILL.md'


def list_items(text):  # [(first line, text)] of each list item, with its indented lines
    "Split a page into its list items. An item runs until a blank line or a line with no indent."
    out, item = [], None
    for number, line in enumerate(text.split('\n'), 1):
        if re.match(r'^(\d+\.|[-*+])\s', line):
            item = [number, line]
            out.append(item)
        elif item and line.startswith(' ') and line.strip():
            item[1] += '\n' + line
        else:
            item = None
    return [(line, ' '.join(text.split())) for line, text in out]


def uncredited_items(text):  # The first line of each item that uses one of her rules and does not name her
    "Each step and checklist item that carries a rule of Rosalind Reid must name her in that item."
    return [line for line, item in list_items(text)
            if any(marker in item.lower() for marker in MARKERS) and 'Rosalind Reid' not in item]


def uncredited_examples(text):  # The heading of each example from her work that does not name her in its own block
    "Each example of EXAMPLES.md whose letter is W, D or P comes from her work, and must name her in its block."
    found, heading, block, fence = [], None, [], False
    for line in text.split('\n') + ['### END']:
        if line.startswith('```'):
            fence = not fence
        if not fence and re.match(r'^#{1,3} ', line):
            if heading and 'Rosalind Reid' not in '\n'.join(block):
                found.append(heading)
            heading, block = (line if re.match(r'^### [WDP]\d+\. ', line) else None), []
        block.append(line)
    return found


def unnamed(text):  # The first line of each block that says "Reid" and not "Rosalind Reid"
    return [line for line, block in rule_blocks(text) if re.search(r'\bReid\b', block) and 'Rosalind Reid' not in block]


def render_list(config):  # The globs in project.render of a _smalldocs.yml, read without a YAML package
    "The entries of the list under render: in the project section."
    match = re.search(r'(?m)^  render:\n((?:    - .*\n)+)', config)
    return [line.strip()[2:].strip() for line in match.group(1).splitlines()] if match else []


def files():  # Every text file in the repository that git tracks or would add, outside tests/
    listed = subprocess.run(['git', 'ls-files', '--cached', '--others', '--exclude-standard'], cwd=REPO,
                            capture_output=True, text=True, check=True).stdout.split('\n')
    for name in listed:
        path = REPO / name
        if name and path.suffix in TEXT and path.is_file() and not name.startswith(('tests/',) + INSTALLED):
            yield name, path.read_text(encoding='utf-8')


class CreditTest(unittest.TestCase):
    def test_each_page_built_on_her_work_names_her(self):
        for name in MUST:
            with self.subTest(page=name):
                self.assertTrue((REPO / name).is_file(), f'{name} is missing')
                self.assertIn('Rosalind Reid', (REPO / name).read_text(encoding='utf-8'))

    def test_a_page_that_mentions_her_or_her_files_names_her_in_full(self):
        for name, text in files():
            if re.search(r'\bReid\b|sources/reid/', text):
                with self.subTest(page=name):
                    self.assertIn('Rosalind Reid', text)

    def test_each_rule_that_links_to_her_pdfs_names_her_in_full(self):
        for name in ('TALKS.md', '.agents/skills/presentations/references/TALKS.md', 'docs/why.md', 'docs/sources.md'):
            with self.subTest(page=name):
                self.assertEqual(uncredited((REPO / name).read_text(encoding='utf-8')), [])

    def test_a_copy_with_the_credit_of_one_rule_removed_fails(self):
        for name, rule in (('TALKS.md', '19. **'), ('TALKS.md', '33. **'), ('TALKS.md', '86. **')):
            with self.subTest(page=name, rule=rule), tempfile.TemporaryDirectory() as temp:
                text = (REPO / name).read_text(encoding='utf-8')
                start = text.index(rule)
                end = text.find('\n' + str(int(rule.split('.')[0]) + 1) + '. **', start)
                end = end if end > 0 else text.index('\n\n', start)   # the last rule of a section
                self.assertIn('Rosalind Reid', text[start:end])
                copy = Path(temp) / name
                copy.write_text(text[:start] + text[start:end].replace('Rosalind Reid', 'Reid') + text[end:],
                                encoding='utf-8')
                found = uncredited(copy.read_text(encoding='utf-8'))
                self.assertEqual(len(found), 1, found)
                self.assertTrue(copy.read_text(encoding='utf-8').split('\n')[found[0] - 1].lstrip().startswith(rule))

    def test_each_example_from_her_work_names_her_in_its_own_block(self):
        for name in ('EXAMPLES.md', '.agents/skills/presentations/references/EXAMPLES.md'):
            with self.subTest(page=name):
                text = (REPO / name).read_text(encoding='utf-8')
                self.assertGreaterEqual(len(re.findall(r'(?m)^### [WDP]\d+\. ', text)), 40)
                self.assertEqual(uncredited_examples(text), [])

    def test_a_copy_of_the_examples_with_one_credit_removed_fails(self):
        text = (REPO / 'EXAMPLES.md').read_text(encoding='utf-8')
        start = text.index('### D10. ')
        end = text.index('\n### ', start + 1)
        self.assertIn('Rosalind Reid', text[start:end])
        with tempfile.TemporaryDirectory() as temp:
            copy = Path(temp) / 'EXAMPLES.md'
            copy.write_text(text[:start] + text[start:end].replace('Rosalind Reid', 'the author') + text[end:],
                            encoding='utf-8')
            self.assertEqual(uncredited_examples(copy.read_text(encoding='utf-8')),
                             ['### D10. The story of a project presentation'])

    def test_each_rule_that_says_reid_names_her_in_full(self):
        for name in ('TALKS.md', 'EXAMPLES.md', 'docs/sources.md', 'docs/why.md'):
            with self.subTest(page=name):
                self.assertEqual(unnamed((REPO / name).read_text(encoding='utf-8')), [])
        self.assertEqual(unnamed("41. **Rule.** Reid's note is advice.\n42. **Next.** Rosalind Reid says so.\n"), [1])

    def test_each_item_of_the_presentations_skill_that_uses_her_rules_names_her(self):
        text = (REPO / PRESENTATIONS).read_text(encoding='utf-8')
        found = list_items(text)
        self.assertGreaterEqual(sum(any(m in item.lower() for m in MARKERS) for _, item in found), 8, found)
        self.assertEqual(uncredited_items(text), [])

    def test_a_copy_with_the_credit_of_one_item_removed_fails(self):
        text = (REPO / PRESENTATIONS).read_text(encoding='utf-8')
        for start, stop in (('- **Each movie**', '\n- '), ('5. Draft the rest of the plan', '\n6. ')):
            with self.subTest(item=start), tempfile.TemporaryDirectory() as temp:
                begin = text.index(start)
                end = text.index(stop, begin)
                self.assertIn('Rosalind Reid', text[begin:end])
                copy = Path(temp) / 'SKILL.md'
                copy.write_text(text[:begin] + text[begin:end].replace(' of Rosalind Reid', '')
                                .replace(' The rule is from Rosalind Reid.', '') + text[end:], encoding='utf-8')
                found = uncredited_items(copy.read_text(encoding='utf-8'))
                self.assertEqual(len(found), 1, found)
                self.assertTrue(copy.read_text(encoding='utf-8').split('\n')[found[0] - 1].startswith(start))

    def test_the_pages_say_that_her_credit_must_stay(self):
        flat = lambda text: ' '.join(text.split())   # the notice can wrap across lines
        for name in NOTICE:
            with self.subTest(page=name):
                text = flat((REPO / name).read_text(encoding='utf-8'))
                self.assertIn('must keep its credit to Rosalind Reid', text)
                self.assertIn('not under the MIT licence', text)
        top = (REPO / 'TALKS.md').read_text(encoding='utf-8').split('\n## ')[0]
        self.assertIn('must keep its credit to Rosalind Reid', flat(top))
        sources = (REPO / 'EXAMPLES.md').read_text(encoding='utf-8').split('\n## Credit and licence')[1]
        self.assertIn('must keep its credit to Rosalind Reid', flat(sources.split('\n# ')[0]))
        licence = (REPO / 'README.md').read_text(encoding='utf-8').split('\n## Licence')[1]
        self.assertIn('must keep its credit to Rosalind Reid', flat(licence))

    def test_her_files_are_linked_on_github_and_not_on_the_site(self):
        for name, text in files():
            with self.subTest(page=name):
                self.assertNotRegex(text, r'rahuldave\.com/nossaifd(-talks)?/sources/')
                self.assertNotIn('rahuldave/nossaifd/blob/main/sources/', text)   # the old home of her PDFs
        self.assertEqual(sorted(p.name for p in (REPO / 'sources/reid').glob('*.pdf')), PDFS)
        for pdf in PDFS:
            with self.subTest(pdf=pdf):
                self.assertTrue(any(GITHUB + pdf in text for _, text in files()), f'nothing links to {pdf}')
                self.assertIn(GITHUB + pdf, (REPO / 'TALKS.md').read_text(encoding='utf-8'))

    def test_the_site_renders_no_file_of_sources(self):
        config = (REPO / '_smalldocs.yml').read_text(encoding='utf-8')
        render = render_list(config)
        self.assertIn('TALKS.md', render)
        self.assertEqual([glob for glob in render if not glob.startswith('!') and
                          (glob.startswith('sources') or '*' in glob or glob.endswith('/'))], [])
        for key in ('resources:',):
            self.assertNotIn(key, config)   # resources would copy files such as the PDFs into the site
        self.assertEqual(render_list('project:\n  render:\n    - index.qmd\n    - sources/reid/x.md\n'),
                         ['index.qmd', 'sources/reid/x.md'])



def austegard_uncredited(paths):  # The files that use the declaude skill and do not name its author in full
    "Each file that mentions the declaude skill must name Oskar Austegard, as each use of Rosalind Reid names her."
    found = []
    for path in paths:
        text = path.read_text(encoding='utf-8', errors='replace')
        if re.search(r'declaud', text, re.I) and 'Oskar Austegard' not in text:
            found.append(path.relative_to(REPO).as_posix())
    return found


class AustegardCreditTest(unittest.TestCase):
    "The declaude skill by Oskar Austegard, under the MIT licence, keeps its credit at each use."

    def tracked(self):
        names = subprocess.run(['git', 'ls-files'], cwd=REPO, capture_output=True, text=True, check=True).stdout
        return [REPO / n for n in names.split() if (Path(n).suffix in TEXT or Path(n).name == 'Justfile')
                and not n.startswith(INSTALLED)]

    def test_each_file_that_uses_the_declaude_skill_names_its_author(self):
        self.assertEqual(austegard_uncredited(self.tracked()), [])

    def test_a_file_that_drops_the_name_fails(self):
        with tempfile.TemporaryDirectory(dir=REPO) as temp:
            page = Path(temp) / 'x.md'
            page.write_text('Run the linter of the declaude skill.\n', encoding='utf-8')
            self.assertEqual(len(austegard_uncredited([page])), 1)


OLD_NAME = re.compile(r'declauding', re.I)
HIS_LINK = re.compile(r'https://github\.com/oaustegard/claude-skills/(?:tree|blob)/[0-9a-f]{40}/')
HIS_FOLDER = re.compile(HIS_LINK.pattern + r'declauding(?=[/)\s]|$)|folder\s+`declauding`')
HIS_NAME = re.compile(r'Oskar Austegard calls (?:it|the skill) declauding')
WHY_NAME = 'because check.py and the linter read the word declauding as an -ing form'


def old_name_uses(text, name=''):
    "Each use of the old name declauding, other than his folder, one sentence that gives his name, and the reason."
    text = HIS_FOLDER.sub('', ' '.join(text.split()))
    text = HIS_NAME.sub('', text, count=1)
    if name == 'docs/why.md':
        text = text.replace(WHY_NAME, '', 1)
    return OLD_NAME.findall(text)


INTRODUCTIONS = ('README.md', 'TALKS.md', 'docs/sources.md', 'docs/check-talk.md', 'docs/why.md',
                 '.agents/skills/presentations/SKILL.md', '.agents/skills/presentations/references/TALKS.md')


def unfallen(text):
    "Each paragraph that names a path into the declaude skill and gives no fallback for a missing skill."
    return [p for p in re.split(r'\n\s*\n', text)
            if '.agents/skills/declaude/' in p and 'If the declaude skill is not installed' not in ' '.join(p.split())]


class DeclaudeNameTest(unittest.TestCase):
    "nossaifd renamed its copy of the skill to declaude. Links to his repository keep his folder, declauding."

    def files(self):
        return [(p, p.relative_to(REPO).as_posix(), p.read_text(encoding='utf-8', errors='replace'))
                for p in AustegardCreditTest().tracked() if p.name != 'test_credit.py']

    def test_no_file_uses_the_old_name_outside_his_folder(self):
        for _, name, text in self.files():
            self.assertEqual(old_name_uses(text, name), [], name)

    def test_the_old_path_the_old_skill_name_and_a_second_exempt_phrase_fail(self):
        self.assertTrue(old_name_uses('.agents/skills/declauding/scripts/declaude_lint.py'))
        self.assertTrue(old_name_uses('the declauding skill'))
        self.assertTrue(old_name_uses('the word declauding as an -ing form'))   # outside docs/why.md
        twice = 'Oskar Austegard calls it declauding. Oskar Austegard calls it declauding.'
        self.assertTrue(old_name_uses(twice))
        self.assertFalse(old_name_uses('https://github.com/oaustegard/claude-skills/tree/'
                                       '6baa7290da972191749acda03c63297e67b3fc26/declauding/references'))

    def test_every_link_to_his_repository_keeps_his_folder(self):
        count = 0
        for _, name, text in self.files():
            for match in HIS_LINK.finditer(text):
                count += 1
                self.assertRegex(text[match.end():match.end() + 11], r'^declauding[/)\s]', name)
        self.assertGreater(count, 0)

    def test_each_page_that_introduces_the_skill_gives_his_name_for_it_once(self):
        for name in INTRODUCTIONS:
            text = ' '.join((REPO / name).read_text(encoding='utf-8').split())
            self.assertEqual(len(HIS_NAME.findall(text)), 1, name)

    def test_each_paragraph_with_a_path_into_the_skill_gives_the_fallback(self):
        for path, name, text in self.files():
            if path.suffix == '.md':   # The Justfile runs the installed linter, so it needs no fallback
                self.assertEqual(unfallen(text), [], name)
        self.assertTrue(unfallen('Run .agents/skills/declaude/scripts/declaude_lint.py on the script.'))

    def test_the_justfile_runs_the_linter_of_the_installed_declaude_skill(self):
        justfile = (REPO / 'Justfile').read_text(encoding='utf-8')
        self.assertIn('declaude_lint := ".agents/skills/declaude/scripts/declaude_lint.py"', justfile)
        self.assertIn('{{python}} -I {{declaude_lint}} --skip-quoted --no-html', justfile)
        self.assertTrue((REPO / '.agents/skills/declaude/scripts/declaude_lint.py').is_file())


if __name__ == '__main__':
    unittest.main()
