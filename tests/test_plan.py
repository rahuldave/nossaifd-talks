"""Check the plan of a talk and the htmpres deck in check_talk.py, and the example talk."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
import check_talk  # noqa: E402

PLAN = (REPO / 'examples/cache/plan.md').read_text(encoding='utf-8')
SLIDES = (REPO / 'examples/cache/slides.qmd').read_text(encoding='utf-8')
TEMPLATE = (REPO / 'templates/plan.md').read_text(encoding='utf-8')


def run(files, name, *args):
    "Write the files into a folder, run the checker on one of them, and return the hard and soft lines."
    with tempfile.TemporaryDirectory() as temp:
        for file, text in files.items():
            (Path(temp) / file).write_text(text, encoding='utf-8')
        out = subprocess.run([sys.executable, str(REPO / 'check_talk.py'), '-v', *args, name],
                             capture_output=True, text=True, cwd=temp)
    lines = out.stdout.splitlines()
    return ([l for l in lines if l.startswith('  HARD ')], [l for l in lines if l.startswith('  soft ')],
            out.returncode)


def plan(**changes):
    "The example plan with some lines replaced, as {old: new}."
    text = PLAN
    for old, new in changes.items():
        assert old in text, old
        text = text.replace(old, new)
    return text


def slide(title, body='A point', notes='Cue: the point\nWe cut the wait.', attrs=''):
    return f'## {title}{" " + attrs if attrs else ""}\n\n{body}\n\n::: notes\n{notes}\n:::\n'


def qmd(*slides):
    return '---\npagetitle: "Talk"\n---\n\n' + '\n'.join(slides)


class PlanTest(unittest.TestCase):
    def test_the_example_plan_and_slides_pass_with_no_notes(self):
        hard, soft, status = run({'plan.md': PLAN, 'slides.qmd': SLIDES}, 'slides.qmd')
        self.assertEqual((hard, soft, status), ([], [], 0))
        self.assertEqual(run({'plan.md': PLAN}, 'plan.md')[:2], ([], []))

    def test_the_template_fails_in_every_section(self):
        hard, _, status = run({'plan.md': TEMPLATE}, 'plan.md')
        self.assertEqual(status, 1)
        for name in check_talk.PLAN_SECTIONS:
            if name != 'The outline':
                self.assertTrue(any(f'"{name}" has no answer' in line for line in hard), name)
        self.assertTrue(any('section of the template' in line for line in hard))

    def test_a_comment_or_a_bare_label_is_not_an_answer(self):
        hard, _, _ = run({'plan.md': plan(**{'A one-minute copy of each search page cut the wait at nine from eight '
                                             'seconds to under one.': '<!-- one sentence -->\n- Headline:'})}, 'plan.md')
        self.assertTrue(any('"The headline" has no answer' in line for line in hard), hard)

    def test_a_missing_section_is_hard(self):
        text = PLAN.replace('## The questions', '## Questions')
        hard, _, _ = run({'plan.md': text}, 'plan.md')
        self.assertTrue(any('no section "## The questions"' in line for line in hard), hard)

    def test_the_time_needs_a_number(self):
        hard, _, _ = run({'plan.md': plan(**{'- Time: 12 minutes': '- Time: short'})}, 'plan.md')
        self.assertTrue(any('no number of minutes' in line for line in hard), hard)
        hard, _, _ = run({'plan.md': plan(**{'- Time: 12 minutes': '- Time:'})}, 'plan.md')
        self.assertTrue(any('has no time' in line for line in hard), hard)
        for time in ('0 minutes', '20 seconds'):
            hard, _, _ = run({'plan.md': plan(**{'- Time: 12 minutes': f'- Time: {time}'})}, 'plan.md')
            self.assertTrue(any('under a minute' in line for line in hard), (time, hard))
        hard, _, _ = run({'plan.md': plan(**{'- Time: 12 minutes': '- Time: -5 minutes'})}, 'plan.md')
        self.assertTrue(any('no number of minutes' in line for line in hard), hard)

    def test_minutes_of_reads_units_and_rounds_half_up(self):
        cases = {'20 minutes': 20, '1.5 hours': 90, 'an hour': 60, '90 seconds': 2, '0.5 minutes': 1,
                 '2.5 minutes': 3, '45': 45, '-5 minutes': None, 'short': None}
        for value, expected in cases.items():
            self.assertEqual(check_talk.minutes_of(value), expected, value)

    def test_a_one_minute_talk_allows_one_slide(self):
        _, soft, _ = run({'plan.md': plan(**{'- Time: 12 minutes': '- Time: 1 minute'}),
                          'slides.qmd': qmd(slide('The only slide', body='Questions?'))}, 'slides.qmd')
        self.assertFalse(any('slides for 1 minutes' in line for line in soft), soft)

    def test_the_two_questions_are_yes_or_no_and_the_shape_is_one_of_three(self):
        hard, _, _ = run({'plan.md': plan(**{'- Pure story: no': '- Pure story: maybe',
                                             '- Shape: asymmetric hourglass': '- Shape: pyramid'})}, 'plan.md')
        self.assertTrue(any('"Pure story:" must be yes or no' in line for line in hard), hard)
        self.assertTrue(any('"Shape:" must be one of' in line for line in hard), hard)

    def test_a_shape_that_the_answers_do_not_ask_for_is_a_soft_note(self):
        for changes, expected in (({'- Call to action: no': '- Call to action: yes'}, 'symmetric hourglass'),
                                  ({'- Pure story: no': '- Pure story: yes'}, 'funnel')):
            with self.subTest(expected=expected):
                hard, soft, _ = run({'plan.md': plan(**changes)}, 'plan.md')
                self.assertEqual(hard, [])
                self.assertTrue(any(f'ask for {expected}' in line for line in soft), soft)
        # A call to action wins over a pure story
        hard, soft, _ = run({'plan.md': plan(**{'- Pure story: no': '- Pure story: yes',
                                                '- Call to action: no': '- Call to action: yes',
                                                '- Shape: asymmetric hourglass': '- Shape: symmetric hourglass'})},
                            'plan.md')
        self.assertEqual((hard, soft), ([], []))

    def test_the_outline_needs_sections_with_points_and_about_five(self):
        empty = PLAN.replace('- Each search reads the same course rows again\n- Most students search for the same '
                             'twenty courses\n- Figure: one bar for each step of a search, the database read the '
                             'longest\n', '- Story:\n')
        hard, _, _ = run({'plan.md': empty}, 'plan.md')
        self.assertTrue(any('"The database repeats one job" of the outline has no points' in l for l in hard), hard)
        more = PLAN.replace('## The questions', ''.join(f'### Part {i}\n\n- A thing {i}\n\n' for i in range(2))
                            + '## The questions')
        _, soft, _ = run({'plan.md': more}, 'plan.md')
        self.assertTrue(any('6 sections in the outline' in line for line in soft), soft)
        none = PLAN.split('## The outline')[0] + '## The outline\n\nNothing yet.\n\n## The questions' + \
            PLAN.split('## The questions')[1]
        hard, _, _ = run({'plan.md': none}, 'plan.md')
        self.assertTrue(any('no ### section' in line for line in hard), hard)

    def test_a_heading_inside_code_is_not_a_section(self):
        text = PLAN.replace('## The action\n', '```\n## The action\n```\n\n## The action\n')
        self.assertEqual(run({'plan.md': text}, 'plan.md')[0], [])


class DeckTest(unittest.TestCase):
    def test_slides_need_a_plan_next_to_them(self):
        hard, _, status = run({'slides.qmd': SLIDES}, 'slides.qmd')
        self.assertEqual(status, 1)
        self.assertTrue(any('no plan.md next to slides.qmd' in line for line in hard), hard)

    def test_a_problem_of_the_plan_fails_the_slides(self):
        hard, _, _ = run({'plan.md': TEMPLATE, 'slides.qmd': SLIDES}, 'slides.qmd')
        self.assertTrue(hard and all(line.startswith('  HARD plan.md, ') for line in hard), hard)

    def test_a_heading_starts_a_slide_and_its_attributes_are_not_the_title(self):
        hard: list[str] = []
        slides = check_talk.split_qmd(qmd(slide('One'), slide('Two words', attrs='{data-kind="appendix"}'),
                                          '```\n## Not a slide\n```\n'), hard)
        self.assertEqual(hard, [])
        self.assertEqual([s.title()[1] for s in slides], ['One', 'Two words'])
        self.assertTrue(check_talk.appendix(slides[1]) and not check_talk.appendix(slides[0]))

    def test_a_rule_line_must_come_right_before_a_heading(self):
        hard: list[str] = []
        check_talk.split_qmd(qmd(slide('One'), '---\n', slide('Two')), hard)
        self.assertEqual(hard, [])
        check_talk.split_qmd(qmd(slide('One', body='A point\n\n---\n\nMore')), hard)
        self.assertEqual(len(hard), 1)
        self.assertIn('not right before a ## title', hard[0])

    def test_text_before_the_first_heading_is_hard(self):
        hard: list[str] = []
        check_talk.split_qmd('---\npagetitle: "x"\n---\n\nLost words\n\n' + slide('One'), hard)
        self.assertTrue(any('before the first ## title' in line for line in hard), hard)

    def test_a_cue_line_is_not_script(self):
        hard: list[str] = []
        slides = check_talk.split_qmd(qmd(slide('One', notes='Cue: um, uh, the thing is\nWe cut the wait.')), hard)
        self.assertEqual(len(slides[0].cues), 1)
        self.assertNotIn('um', ' '.join(text for _, text in slides[0].notes))

    def deck_notes(self, *slides):
        return run({'plan.md': PLAN, 'slides.qmd': qmd(*slides)}, 'slides.qmd')

    def test_more_slides_than_the_planned_minutes_is_a_soft_note_and_the_appendix_is_left_out(self):
        def deck(points, extra=0):
            return [slide('Title of the talk')] + [slide(f'Point number {i}') for i in range(points)] + \
                [slide('The end of it', body='Questions?')] + \
                [slide(f'Extra data {i}', attrs='{data-kind="appendix"}') for i in range(extra)]
        _, soft, _ = self.deck_notes(*deck(9))
        self.assertTrue(any('11 slides for 12 minutes: plan 9 minutes' in line for line in soft), soft)
        _, soft, _ = self.deck_notes(*deck(8))
        self.assertTrue(any('10 slides for 12 minutes' in line for line in soft), soft)
        _, soft, _ = self.deck_notes(*deck(7, extra=4))
        self.assertFalse(any('slides for 12 minutes' in line for line in soft), soft)

    def test_the_last_slide_asks_for_questions(self):
        _, soft, _ = self.deck_notes(slide('Title of the talk'), slide('The end of it'))
        self.assertTrue(any('no "Questions?"' in line for line in soft), soft)
        _, soft, _ = self.deck_notes(slide('Title of the talk'), slide('The end of it', body='Questions?'),
                                     slide('Extra data', attrs='{data-kind="appendix"}'))
        self.assertFalse(any('no "Questions?"' in line for line in soft), soft)

    def test_every_slide_after_the_first_appendix_slide_is_in_the_appendix(self):
        # htmpres puts every slide after the first appendix slide in the appendix, marked or not.
        body = [slide('Title of the talk'), slide('Extra data', attrs='{data-kind="appendix"}'),
                slide('The end of it', body='Questions?')]
        _, soft, _ = self.deck_notes(*body)
        self.assertTrue(any('slide 3, line' in line and 'comes after slide 2, the first appendix slide' in line
                            for line in soft), soft)
        # Only the title slide is left in the talk, so there is no last slide to check for "Questions?".
        self.assertFalse(any('no "Questions?"' in line for line in soft), soft)
        points = [slide(f'Point number {i}') for i in range(9)]
        _, soft, _ = self.deck_notes(slide('Title of the talk'), slide('The end of it', body='Questions?'),
                                     slide('Extra data', attrs='{data-kind="appendix"}'), *points)
        self.assertFalse(any('slides for 12 minutes' in line for line in soft), soft)
        self.assertEqual(sum('first appendix slide' in line for line in soft), 9, soft)
        _, soft, _ = self.deck_notes(slide('Title of the talk'), slide('The end of it', body='Questions?'),
                                     slide('Extra data', attrs='{data-kind="appendix"}'),
                                     slide('More data', attrs="{#more data-kind='appendix'}"))
        self.assertFalse(any('appendix' in line for line in soft), soft)

    def test_only_an_exact_appendix_value_starts_the_appendix(self):
        # htmpres reads data-kind exactly, so appendix-old and spaces around = do not start the appendix.
        for attrs in ('{data-kind="appendix-old"}', '{data-kind = "appendix"}'):
            slides = check_talk.split_qmd(qmd(slide('One'), slide('Two words', attrs=attrs)), [])
            self.assertFalse(check_talk.appendix(slides[1]), attrs)
        for attrs in ('{data-kind="appendix"}', "{#a data-kind='appendix'}", '{.x data-kind=appendix}'):
            slides = check_talk.split_qmd(qmd(slide('One'), slide('Two words', attrs=attrs)), [])
            self.assertTrue(check_talk.appendix(slides[1]), attrs)

    def test_span_attributes_are_not_words_on_the_slide(self):
        self.assertEqual(check_talk.plain('[Each miss reads it]{.key .fragment data-fragment-index="2"}'),
                         'Each miss reads it')
        spans = '\n\n'.join(f'[Each miss reads the database once]{{.key .fragment data-fragment-index="{i}"}}'
                              for i in range(1, 5))
        hard, soft, _ = self.deck_notes(slide('Title of the talk'), slide('Hit rate sets the load', body=spans),
                                        slide('The end of it', body='Questions?'))
        self.assertFalse(any('words' in line for line in hard + soft), hard + soft)

    def test_a_script_with_no_cue_and_a_section_not_in_the_outline(self):
        _, soft, _ = self.deck_notes(slide('Title of the talk'),
                                     slide('A point here', notes='We cut the wait.',
                                           attrs='{data-section="Not in the plan"}'),
                                     slide('The end of it', body='Questions?'))
        self.assertTrue(any('no "Cue:" line' in line for line in soft), soft)
        self.assertTrue(any('"Not in the plan" is not in the outline' in line for line in soft), soft)

    def test_fillers_and_any_questions(self):
        _, soft, _ = self.deck_notes(slide('Title of the talk'),
                                     slide('The end of it', body='Questions?',
                                           notes='Cue: end\nUm, the thing is that it works. Do you have any '
                                                 'questions?'))
        self.assertTrue(any("a filler, 'Um'" in line for line in soft), soft)
        self.assertTrue(any('What questions do you have?' in line for line in soft), soft)
        _, soft, _ = self.deck_notes(slide('Title of the talk'),
                                     slide('The end of it', body='Questions?',
                                           notes='Cue: end\nThank you. What questions do you have?'))
        self.assertEqual(soft, [])

    def test_another_deck_needs_no_plan(self):
        hard, _, status = run({'deck.md': '# Talk\n\n---\n\n# Two words\n\n<!--\nWe cut it.\n-->\n'}, 'deck.md')
        self.assertEqual((hard, status), ([], 0))


class ReviewTest(unittest.TestCase):
    "One test for each finding of the adversarial review."

    def test_a_heading_inside_notes_or_a_comment_is_hard(self):
        for text in (slide('One', notes='Cue: x\nWe cut it.\n## not a slide\nMore.'),
                     slide('One', body='<!--\n## hidden\n-->')):
            with self.subTest(text=text):
                hard: list[str] = []
                check_talk.split_qmd(qmd(text), hard)
                self.assertTrue(any('## line inside' in line for line in hard), hard)

    def test_a_rule_line_inside_notes_or_a_comment_is_not_checked(self):
        hard: list[str] = []
        check_talk.split_qmd(qmd(slide('One', body='<!--\n---\n-->', notes='Cue: x\n---\nWe cut it.')), hard)
        self.assertEqual(hard, [])

    def test_a_div_inside_the_notes_keeps_the_rest_of_the_notes(self):
        hard: list[str] = []
        slides = check_talk.split_qmd(qmd(slide('One', notes='Cue: x\n::: {.callout}\nAside.\n:::\nWe cut it. It works.')),
                                      hard)
        self.assertEqual(hard, [])
        self.assertIn('It works.', ' '.join(text for _, text in slides[0].notes))
        self.assertFalse(any('It works' in line for line in slides[0].body))

    def test_an_outline_heading_inside_code_is_not_a_section(self):
        text = PLAN.split('## The outline')[0] + '## The outline\n\n```\n### Fake section\n- a\n```\n\n## The questions' + \
            PLAN.split('## The questions')[1]
        hard, _, _ = run({'plan.md': text}, 'plan.md')
        self.assertTrue(any('no ### section' in line for line in hard), hard)

    def test_the_time_can_be_in_hours(self):
        for value, minutes in (('1.5 hours', 90), ('an hour', 60), ('1 hour', 60), ('20 minutes', 20), ('45', 45),
                               ('20 min', 20)):
            with self.subTest(value=value):
                self.assertEqual(check_talk.minutes_of(value), minutes)
        self.assertIsNone(check_talk.minutes_of('short'))

    def test_a_quarto_deck_with_a_format_is_another_tool(self):
        deck = '---\nformat: revealjs\n---\n\n# Talk\n\n---\n\n# Two words\n\n::: notes\nWe cut it.\n:::\n'
        hard, _, status = run({'talk.qmd': deck}, 'talk.qmd')
        self.assertEqual((hard, status), ([], 0))

    def test_front_matter_with_a_dotted_key_is_read(self):
        hard: list[str] = []
        check_talk.split_qmd('---\ndeck.theme: sage\n---\n\n' + slide('One'), hard)
        self.assertEqual(hard, [])

    def test_an_unreadable_plan_is_a_hard_problem_and_not_a_crash(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / 'plan.md').mkdir()   # a folder cannot be read as a file, on any system
            (Path(temp) / 'slides.qmd').write_text(SLIDES, encoding='utf-8')
            out = subprocess.run([sys.executable, str(REPO / 'check_talk.py'), 'slides.qmd'], capture_output=True,
                                 text=True, cwd=temp)
        self.assertNotIn('Traceback', out.stderr)
        self.assertIn('no plan.md next to slides.qmd', out.stdout)

    def test_smaller_gaps(self):
        self.assertEqual(run({'Plan.md': PLAN}, 'Plan.md')[2], 0)   # read as a plan, not as a deck
        self.assertIn('plan with 4 sections', subprocess.run(
            [sys.executable, str(REPO / 'check_talk.py'), str(REPO / 'examples/cache/plan.md')],
            capture_output=True, text=True).stdout)
        hard, _, _ = run({'plan.md': PLAN + '\n## The headline\n\nAnother one.\n'}, 'plan.md')
        self.assertTrue(any('a second section "The headline"' in line for line in hard), hard)
        hard, _, _ = run({'plan.md': plan(**{'- Shape: asymmetric hourglass': '- Shape: asymmetric hourglass.'})},
                         'plan.md')
        self.assertEqual(hard, [])
        _, soft, _ = run({'plan.md': PLAN, 'slides.qmd': qmd(slide('Title of the talk'),
                                                            slide('A point', attrs="{data-section='Nowhere'}"),
                                                            slide('The end', body='Questions?'))}, 'slides.qmd')
        self.assertTrue(any('"Nowhere" is not in the outline' in line for line in soft), soft)


class ExampleSyntaxTest(unittest.TestCase):
    "The example talk uses htmpres syntax that holds together: links, ids and equation steps."

    def test_links_ids_and_equation_steps_match(self):
        import re
        text = (REPO / 'examples' / 'cache' / 'slides.qmd').read_text(encoding='utf-8')
        ids = set(re.findall(r'^## .*\{#([\w-]+)', text, re.M))
        links = set(re.findall(r'\]\(#([\w-]+)\)', text))
        self.assertTrue(links and links <= ids, (links, ids))
        steps = re.search(r'data-equation-steps="([^"]+)" data-step-indices="([^"]+)"', text)
        terms = steps.group(1).replace(',', '|').split('|')
        self.assertEqual(len(steps.group(1).split('|')), len(steps.group(2).split('|')))
        for term in terms:
            self.assertIn(f'\\htmlClass{{{term}}}', text, term)
        for index in steps.group(2).split('|'):
            self.assertIn(f'data-fragment-index="{index}"', text, index)

    def test_the_guide_no_longer_says_htmpres_lacks_the_features(self):
        for name in ('TALKS.md', 'docs/check-talk.md'):
            text = (REPO / name).read_text(encoding='utf-8')
            for stale in ('does not yet typeset', 'htmpres is adding', 'ds-split'):
                self.assertNotIn(stale, text, (name, stale))


class ReferenceTest(unittest.TestCase):
    "The renumbering of TALKS.md must not change the rule numbers of other guides."

    def test_the_rule_numbers_of_guide_md_and_of_shankar_did_not_move(self):
        import re
        examples = (REPO / 'EXAMPLES.md').read_text(encoding='utf-8')
        found = sorted(re.findall(r'GUIDE\.md,? rules? (\d+(?:(?:, | and | to )\d+)*)', examples))
        self.assertEqual(found, sorted(['20', '20 and 21', '21', '21, 23, 24, 25 and 26', '23', '27', '29', '30', '30',
                                        '30', '33', '35 and 42', '42', '5', '5, 7 and 42', '7', '7']))
        talks = (REPO / 'TALKS.md').read_text(encoding='utf-8')
        self.assertIn('plain-writing skill, rule 5](', talks)
        self.assertIn('plain-writing skill, rule 23](', talks)
        why = (REPO / 'docs/why.md').read_text(encoding='utf-8')
        self.assertIn('[rule 21](https://github.com/docwriter-org', why)
        self.assertIn('[rule 23](https://github.com/docwriter-org', why)

    def test_every_talks_rule_reference_names_a_rule_that_exists(self):
        import re
        talks = (REPO / 'TALKS.md').read_text(encoding='utf-8')
        last = max(int(n) for n in re.findall(r'(?m)^(\d+)\. \*\*', talks))
        self.assertEqual(last, 87)
        for name in ('EXAMPLES.md', 'TALKS.md', 'docs/sources.md', 'docs/check-talk.md'):
            text = (REPO / name).read_text(encoding='utf-8')
            for ref in re.findall(r'TALKS\.md rules? (\d+(?:(?:, | and | to )\d+)*)', text):
                for number in re.findall(r'\d+', ref):
                    self.assertLessEqual(int(number), last, (name, ref))


if __name__ == '__main__':
    unittest.main()
