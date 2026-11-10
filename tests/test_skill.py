"""Check the skill package: the manifest, the files that the skill ships, and the Markdown reader of check_talk.py."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / '.agents/skills/presentations'
sys.path.insert(0, str(REPO))
import check_talk  # noqa: E402


class PackageTest(unittest.TestCase):
    def test_the_package_has_only_the_presentations_skill_and_needs_only_uv(self):
        manifest = json.loads((REPO / 'skill-package.json').read_text())
        self.assertEqual(manifest['repository']['name'], 'nossaifd-talks')
        self.assertEqual(manifest['repository']['url'], 'https://github.com/rahuldave/nossaifd-talks')
        self.assertEqual(manifest['skills'], [{'name': 'presentations', 'path': '.agents/skills/presentations'}])
        self.assertEqual(sorted(p.name for p in (REPO / '.agents/skills').iterdir()), ['presentations'])
        self.assertNotIn('installers', manifest)
        self.assertEqual([e['name'] for e in manifest['executables']['required']], ['uv'])
        self.assertIn('rahuldave/nossaifd-talks', manifest['npx']['install'])

    def test_the_skill_ships_the_guide_the_examples_and_the_talk_checker_only(self):
        shipped = sorted(p.relative_to(SKILL).as_posix() for p in SKILL.rglob('*')
                         if p.is_file() and '__pycache__' not in p.parts)
        self.assertEqual(shipped, ['SKILL.md', 'agents/openai.yaml', 'assets/plan.md', 'references/EXAMPLES.md',
                                   'references/TALKS.md', 'references/WORKSHEET.md', 'scripts/check_talk.py'])

    def test_the_report_parts_of_nossaifd_are_gone(self):
        for name in ('GUIDE.md', 'check.py', 'tests/test_check.py', 'docs/checker.md', 'docs/build.py',
                     'docs/site.css', '.agents/skills/nossaifd', '.agents/just'):
            self.assertFalse((REPO / name).exists(), name)

    def test_the_skill_names_its_licence_and_the_licence_matches(self):
        text = (SKILL / 'SKILL.md').read_text()
        front = re.match(r'^---\nname: (.+)\ndescription: (.+)\nlicense: (.+)\n---\n', text)
        self.assertIsNotNone(front)
        self.assertRegex(front.group(3), r'^MIT, copyright \(c\) 2026 Rahul Dave\. .*rahuldave/nossaifd-talks$')
        self.assertTrue((REPO / 'LICENSE').read_text().startswith('MIT License\n\nCopyright (c) 2026 Rahul Dave\n'))

    def test_the_skill_reads_the_guide_for_reports_from_nossaifd(self):
        text = ' '.join((SKILL / 'SKILL.md').read_text().split())
        self.assertIn('`.agents/skills/nossaifd/references/GUIDE.md`', text)
        self.assertIn('https://github.com/rahuldave/nossaifd/blob/main/GUIDE.md', text)
        self.assertNotIn('scripts/check.py', text)


class CountOpeningTest(unittest.TestCase):
    "GUIDE.md rule 38 of nossaifd: a heading or a paragraph does not open with a count that only announces."
    PAGES = ['README.md', 'TALKS.md', 'EXAMPLES.md', 'WORKSHEET.md', 'docs/check-talk.md', 'docs/sources.md',
             'docs/why.md', 'docs/schwabish-summary.md', '.agents/skills/presentations/SKILL.md']
    # A count and a noun that end the line or a label, or that a verb of announcing follows. A count that says
    # what the items share, as in "Two tall prints stand side by side", stays, by rule 38.
    COUNT = re.compile(r'^(#+ +|[-*] +|\d+\. +|\*\*[^*]+\*\* +)?'
                       r'(Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|Eleven|Twelve|[2-9]|1[0-2]) +'
                       r'[a-z]+( [a-z]+)?(:|\.?$| (go|are|follow|matter|exist|apply|to know)\b)')

    def openings(self, text):
        "Each line that starts a heading, a list item or a paragraph, outside code fences."
        fenced, before = False, ''
        for number, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith('```'):
                fenced = not fenced
            elif not fenced and (not before.strip() or before.startswith('#') or re.match(r'#|[-*] |\d+\. ', line)):
                yield number, line.strip()
            before = line

    def test_no_heading_or_paragraph_opens_with_a_count(self):
        for name in self.PAGES:
            for number, line in self.openings((REPO / name).read_text()):
                with self.subTest(page=name, line=number):
                    self.assertIsNone(self.COUNT.match(line), line)

    def test_the_pattern_finds_a_count_that_only_announces(self):
        for line in ['## Two principles', '## 3 principles', 'Two things go', 'Two cautions:', 'Two problems:',
                     '- Two things go wrong.', '**Declutter.** Two things go wrong.', '3 things to know']:
            self.assertIsNotNone(self.COUNT.match(line), line)

    def test_the_pattern_keeps_a_count_that_says_what_the_items_share(self):
        for line in ['Two tall prints stand side by side.', 'Three shapes, and the fix differs for each:',
                     'Two rules of TALKS.md disagree here, 12 and 40.', 'Two theories support his principles.']:
            self.assertIsNone(self.COUNT.match(line), line)

    def test_only_openings_outside_code_are_read(self):
        text = 'A line\nTwo things go\n\n```\nTwo things go\n```\n\n- Two cautions:\n'
        self.assertEqual([n for n, _ in self.openings(text)], [1, 8])


class StandaloneTest(unittest.TestCase):
    def test_check_talk_imports_no_other_file_of_the_repository(self):
        source = (REPO / 'check_talk.py').read_text()
        self.assertNotIn('sys.path', source)
        imports = re.findall(r'(?m)^\s*(?:from ([\w.]+) import|import ([\w.]+))', source)
        self.assertEqual({a or b for a, b in imports}, {'re', 'sys', 'pathlib'})
        self.assertIn('nossaifd', source.split('def blocks')[0])   # the comment that credits the origin of the reader

    def test_check_talk_runs_alone_in_an_empty_folder(self):
        with tempfile.TemporaryDirectory() as temp:
            shutil.copy(REPO / 'check_talk.py', temp)
            shutil.copy(REPO / 'tests/fixtures/deck.md', temp)
            result = subprocess.run([sys.executable, '-I', 'check_talk.py', 'deck.md'], capture_output=True,
                                    text=True, cwd=temp)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('0 hard', result.stdout)


class ReaderTest(unittest.TestCase):
    "The Markdown reader that check_talk.py copies from check.py of nossaifd keeps its behaviour."

    def test_front_matter_is_skipped_and_the_line_numbers_stay(self):
        found = check_talk.blocks('---\nname: x\ndescription: long\n---\n\nShort text.\n')
        self.assertEqual(found, [(6, 'Short text.', 'para')])

    def test_front_matter_that_does_not_close_is_prose(self):
        found = check_talk.blocks('---\n\nword word.\n')
        self.assertEqual(found, [(1, '---', 'para'), (3, 'word word.', 'para')])

    def test_a_rule_that_opens_a_page_and_is_not_yaml_is_prose(self):
        found = check_talk.blocks('---\nThis is prose and not YAML.\n---\n')
        self.assertEqual(found, [(1, '--- This is prose and not YAML. ---', 'para')])

    def test_code_tables_images_and_html_are_left_out(self):
        text = '# Title\n\n```\ncode here\n```\n\n| a | b |\n\n![x](y.png)\n\n<div>\n\n- An item\n'
        self.assertEqual(check_talk.blocks(text), [(1, 'Title', 'head'), (13, 'An item', 'item')])

    def test_plain_keeps_link_text_and_hides_code_and_quotes(self):
        self.assertEqual(check_talk.plain('Run `x` on [the deck](d.md), "quoted", **bold**'),
                         'Run CODE on the deck, QUOTE, bold')

    def test_sentences_keep_e_g_together(self):
        self.assertEqual(check_talk.sentences('Use a tool, e.g. a linter. Then stop.'),
                         ['Use a tool, e.g. a linter.', 'Then stop.'])


if __name__ == '__main__':
    unittest.main()
