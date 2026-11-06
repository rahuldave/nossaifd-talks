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
