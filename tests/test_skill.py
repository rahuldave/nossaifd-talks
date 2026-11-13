"""Check the skill package: the manifest, the files that the skill ships, and the Markdown reader of check_talk.py."""
import json
import os
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
        # The skills nossaifd and declaude are installed for the prose flow, and the package does not ship them
        self.assertEqual(sorted(p.name for p in (REPO / '.agents/skills').iterdir()), ['declaude', 'nossaifd', 'presentations'])
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
                     'docs/site.css', '.agents/just'):
            self.assertFalse((REPO / name).exists(), name)
        # .agents/skills/nossaifd is the skill installed from nossaifd for the prose flow, not the old report parts
        self.assertTrue((REPO / '.agents/skills/nossaifd/scripts/prose_gate.py').is_file())

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


class ProseFlowTest(unittest.TestCase):
    "The flow of nossaifd: the instruction, the hooks and the workflow, as its docs/flow.md installs them."
    ASSETS = REPO / '.agents/skills/nossaifd/assets'

    def test_the_parts_are_the_assets_of_the_nossaifd_skill(self):
        for part, asset in (('.claude/settings.json', 'claude-settings-hook.json'),
                            ('.codex/hooks.json', 'codex-hooks.json'),
                            ('.github/workflows/nossaifd-prose.yml', 'prose-check.yml')):
            self.assertEqual((REPO / part).read_text(encoding='utf-8'), (self.ASSETS / asset).read_text(encoding='utf-8'), part)
        self.assertIn((self.ASSETS / 'agents-prose.md').read_text(encoding='utf-8'), (REPO / 'AGENTS.md').read_text(encoding='utf-8'))
        self.assertIn('@AGENTS.md', (REPO / 'CLAUDE.md').read_text(encoding='utf-8').split())

    def test_the_installed_skills_are_whole_and_locked(self):
        for name in ('nossaifd', 'declaude'):
            self.assertTrue((REPO / '.agents/skills' / name / 'SKILL.md').is_file(), name)
        lock = json.loads((REPO / 'skills-lock.json').read_text(encoding='utf-8'))
        self.assertEqual(sorted(lock['skills']), ['declaude', 'nossaifd'])
        self.assertEqual({v['source'] for v in lock['skills'].values()}, {'rahuldave/nossaifd'})

    def test_the_readme_section_on_the_flow_credits_the_declaude_skill(self):
        text = ' '.join((REPO / 'README.md').read_text(encoding='utf-8').split())
        self.assertEqual(text.count('the skill `declaude`, by Oskar Austegard, under the MIT licence'), 1)

    def test_the_recipes_of_the_flow(self):
        justfile = (REPO / 'Justfile').read_text(encoding='utf-8')
        for line in ("nossaifd-install:\n    npx -y skills add rahuldave/nossaifd -a codex --skill '*' -y\n",
                     'prose-status:\n    {{python}} -I .agents/skills/nossaifd/scripts/prose_gate.py status\n',
                     '[no-cd]\nprose-record +pages:\n    {{python}} -I "{{justfile_directory()}}/.agents/skills/'
                     'nossaifd/scripts/prose_gate.py" record "$@"\n',
                     '[no-cd]\nprose-check *args:\n    {{python}} -I "{{justfile_directory()}}/.agents/skills/nossaifd/scripts/prose_gate.py" check-changed "$@"\n',
                     '    {{python}} -I {{check_py}} README.md'):
            self.assertIn(line, justfile)
        self.assertIn('    just prose\n', justfile[justfile.index('\ncheck:'):])

    def test_prose_check_uses_the_map_from_a_subfolder(self):
        if not shutil.which('just'):
            self.skipTest('just is not installed')
        run = subprocess.run(['just', 'prose-check', 'cache/slides.qmd', '../templates/plan.md'], cwd=REPO / 'examples',
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn('examples/cache/slides.qmd: checked by .agents/skills/presentations/scripts/check_talk.py, 0 hard',
                      run.stdout)
        # The template's answers are blank, so it keeps check.py
        self.assertIn('templates/plan.md: checked by check.py of the skill, 0 hard', run.stdout)
        failing = subprocess.run(['just', 'prose-check', '../WORKSHEET.md'], cwd=REPO / 'examples', capture_output=True, text=True)
        self.assertEqual(failing.returncode, 1, failing.stdout + failing.stderr)

    def test_the_hooks_find_the_gate_and_the_recipes_use_the_installed_tools(self):
        for name in ('nossaifd/scripts/prose_gate.py', 'nossaifd/scripts/check.py', 'declaude/scripts/declaude_lint.py'):
            self.assertTrue((REPO / '.agents/skills' / name).is_file(), name)
        for part in ('.claude/settings.json', '.codex/hooks.json'):
            self.assertEqual(sorted(json.loads((REPO / part).read_text(encoding='utf-8'))['hooks']), ['Stop', 'UserPromptSubmit'])
        justfile = (REPO / 'Justfile').read_text(encoding='utf-8')
        self.assertIn('check_py := ".agents/skills/nossaifd/scripts/check.py"', justfile)
        self.assertNotIn('raw.githubusercontent.com/rahuldave/nossaifd', justfile)
        self.assertIn('find .agents/skills/presentations -type f', justfile)   # just links reads only our skill


class PassOrderTest(unittest.TestCase):
    "The script goes through the passes of nossaifd in order: checker, declaude pass, diff, checker, linter."
    # The declaude skill, with its linter and its diff, is by Oskar Austegard (MIT licence).

    def passes(self, text):
        section = text[text.index('Revise the script with these passes'):text.index('\n## Sources')]
        return [int(n) for n in re.findall(r'(?m)^(\d+)\. ', section)], section

    def test_the_passes_run_in_the_order_of_nossaifd(self):
        numbers, section = self.passes((REPO / 'TALKS.md').read_text(encoding='utf-8'))
        self.assertEqual(numbers, [1, 2, 3, 4, 5, 6])
        steps = re.split(r'(?m)^\d+\. ', section)[1:]
        self.assertIn('check_talk.py', steps[0])
        self.assertIn('draft.md', steps[1])
        self.assertIn('--script', steps[1])
        self.assertIn('agent that did not write it', steps[2])
        self.assertIn('four exceptions', steps[2])
        self.assertIn('If no subagent tool exists', steps[2])
        self.assertIn('declaude skill is not installed', ' '.join(steps[2].split()))
        self.assertIn('declaude_diff.py draft.md script.md', steps[3])
        self.assertIn('blob/main/.agents/skills/declaude/scripts/declaude_diff.py', steps[3])
        self.assertIn('status 1', steps[3])
        self.assertIn('Keep word for word each bad example that the deck shows on purpose, by rule 55 of GUIDE.md. '
                      'Keep it even when the linter or the checker marks it. '
                      'A bad example teaches only next to its fix.', ' '.join(steps[2].split()))
        after = ' '.join(steps[5].split())   # The rule holds in every step, not only in the declaude pass
        self.assertIn('In every step, keep each bad example that the deck shows on purpose, by rule 55 of GUIDE.md.',
                      after)
        self.assertIn('in a code block, because the talk checker skips code', after)
        self.assertIn('fix only what the revision broke', steps[4])
        self.assertIn('linter once more', steps[5])

    def test_a_bad_example_in_a_code_block_on_a_slide_passes_the_checker(self):
        bad = 'This paragraph is the bad example. It has two sentences and it fills the slide.'
        deck = '---\ntitle: T\n---\n\n## Bad slides hide the point\n\n{}\n\n::: {{.notes}}\nCue: show it.\n:::\n'
        with tempfile.TemporaryDirectory() as temp:
            for body, hard in (('```\n' + bad + '\n```', 0), (bad, 1)):
                path = Path(temp) / 'deck.md'
                path.write_text(deck.format(body), encoding='utf-8')
                run = subprocess.run([sys.executable, '-I', str(REPO / 'check_talk.py'), str(path)],
                                     capture_output=True, text=True)
                self.assertIn(f'{hard} hard', run.stdout)

    def test_the_skill_and_the_choices_give_the_same_order(self):
        def order(name, phrases):
            text = ' '.join((REPO / name).read_text(encoding='utf-8').split())
            found = [text.index(p) for p in phrases]
            self.assertEqual(found, sorted(found), name)
        order('.agents/skills/presentations/SKILL.md',
              ('Run the talk checker first', 'agent that did not write the script', 'run the diff of the declaude',
               'run the talk checker again', 'the linter once more'))
        skill = ' '.join((REPO / '.agents/skills/presentations/SKILL.md').read_text(encoding='utf-8').split())
        self.assertIn('In every step, keep each bad example that the deck shows on purpose word for word, '
                      'by rule 55 of GUIDE.md.', skill)
        why = ' '.join((REPO / 'docs/why.md').read_text(encoding='utf-8').split())
        self.assertIn('to keep each bad example of a deck word for word, as rule 55 of GUIDE.md asks.', why)
        order('docs/why.md',
              ('revise the script in the order of the passes of nossaifd', 'First comes the talk checker',
               'agent that did not write the script makes the declaude pass', 'the diff of the declaude skill',
               'the talk checker runs again', 'the linter runs once more'))


class ProseCheckTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which('just'), 'needs just')
    def test_prose_check_with_no_page_checks_the_changed_pages(self):
        "With no page, just prose-check checks each page changed since HEAD, through the map."
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copy(REPO / 'Justfile', root / 'Justfile')
            shutil.copytree(REPO / '.agents', root / '.agents')
            deck = (REPO / 'examples/cache/slides.qmd').read_text(encoding='utf-8')
            (root / 'talk').mkdir()
            (root / 'talk/slides.qmd').write_text(deck, encoding='utf-8')
            shutil.copy(REPO / 'examples/cache/plan.md', root / 'talk/plan.md')
            (root / 'page.md').write_text('# A page\n\nA plain page.\n', encoding='utf-8')
            git = dict(cwd=root, check=True, capture_output=True)
            subprocess.run(['git', 'init', '-q'], **git)
            subprocess.run(['git', 'add', '-A'], **git)
            subprocess.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'base'], **git)
            # GitHub Actions sets CI, which makes check-changed compare with a base. This test is about a local run
            local = {k: v for k, v in os.environ.items() if k != 'CI' and not k.startswith('GITHUB_')}

            def run(*args, env=local):
                return subprocess.run(['just', 'prose-check', *args], cwd=root, capture_output=True, text=True, env=env)
            same = run()
            self.assertEqual(same.returncode, 0, same.stdout + same.stderr)
            self.assertIn('no page changed', same.stdout + same.stderr)
            (root / 'talk/slides.qmd').write_text(deck + '\n', encoding='utf-8')
            (root / 'page.md').write_text("# A page\n\nIt's a page with a contraction.\n", encoding='utf-8')
            changed = run()
            self.assertEqual(changed.returncode, 1, changed.stdout + changed.stderr)
            self.assertIn('talk/slides.qmd: checked by .agents/skills/presentations/scripts/check_talk.py, 0 hard', changed.stdout)
            self.assertIn('page.md: checked by check.py of the skill, 1 hard', changed.stdout)
            one = run('talk/slides.qmd')
            self.assertEqual(one.returncode, 0, one.stdout + one.stderr)
            self.assertNotIn('page.md', one.stdout)
            # In CI, with a base, it checks the pages that HEAD changed since the base
            base = subprocess.run(['git', 'rev-parse', 'HEAD'], **git).stdout.decode().strip()
            subprocess.run(['git', 'add', '-A'], **git)
            subprocess.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'change'], **git)
            ci = run('--base', base, env=dict(local, CI='true'))
            self.assertEqual(ci.returncode, 1, ci.stdout + ci.stderr)
            self.assertIn('page.md: checked by check.py of the skill, 1 hard', ci.stdout)


class GateTest(unittest.TestCase):
    "The pages that the gate of nossaifd checks, each through the map of checkers."
    # These fail check.py on purpose: a copy of a book, the owner's notes and a test
    KNOWN = ['WORKSHEET.md', 'docs/notes/schwabish-choices.md', 'tests/fixtures/deck.md']
    TALK = ['examples/cache/plan.md', 'examples/cache/slides.qmd']
    TALK_CHECKER = '.agents/skills/presentations/scripts/check_talk.py'

    def gate(self):
        sys.path.insert(0, str(REPO / ".agents/skills/nossaifd/scripts"))
        import prose_gate
        names = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True).stdout.split()
        pages = [n for n in names if prose_gate.is_page(n)]
        run = subprocess.run([sys.executable, "-I", str(REPO / ".agents/skills/nossaifd/scripts/prose_gate.py"), "check", *pages],
                             cwd=REPO, capture_output=True, text=True)
        found = dict((page, (checker, int(hard))) for page, checker, hard in
                     re.findall(r"(?m)^(\S+): checked by (.+?), (\d+) hard", run.stdout))
        self.assertEqual(sorted(found), sorted(pages), run.stdout + run.stderr)
        return found

    def test_only_the_known_pages_fail_the_gate(self):
        failing = sorted(page for page, (_, hard) in self.gate().items() if hard)
        self.assertEqual(failing, sorted(self.KNOWN))

    def test_the_gate_checks_the_deck_and_the_plan_with_the_talk_checker(self):
        found = self.gate()
        for page in self.TALK:
            self.assertEqual(found[page][0], self.TALK_CHECKER, page)
        others = [page for page, (checker, _) in found.items() if page not in self.TALK]
        self.assertTrue(others)
        for page in others:
            self.assertNotEqual(found[page][0], self.TALK_CHECKER, page)

    def test_the_map_gives_the_decks_and_the_plans_to_the_talk_checker(self):
        mapping = json.loads((REPO / ".agents/nossaifd-checkers.json").read_text(encoding="utf-8"))
        self.assertEqual(mapping, {"version": 1, "checkers": [
            {"pages": ["**/slides.qmd", "examples/**/plan.md"], "checker": self.TALK_CHECKER}]})
        self.assertTrue((REPO / self.TALK_CHECKER).is_file())

if __name__ == '__main__':
    unittest.main()
