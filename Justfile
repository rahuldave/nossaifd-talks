# nossaifd-talks: every task is a recipe here. `just` lists them.

# Each word after a recipe's name reaches its commands whole, as "$1", "$2" and so on; "$@" is all of them
set positional-arguments

# Python comes from uv, so the machine needs just and uv only
python := "uv run --no-project --quiet python"
smalldocs := "uvx --from smalldocs==0.5.5 smalldocs"

# The skills nossaifd and declaude, from github.com/rahuldave/nossaifd, live in .agents/skills/ for the prose flow
# of nossaifd. The declaude skill is by Oskar Austegard (github.com/oaustegard/claude-skills, MIT licence).
# The package ships only presentations. The recipes use the checker and the linter of these skills.
check_py := ".agents/skills/nossaifd/scripts/check.py"
declaude_lint := ".agents/skills/declaude/scripts/declaude_lint.py"

[private]
default:
    @just --list --unsorted

# Copy the guide, the examples and the checker into the skill, which ships copies of them
sync:
    mkdir -p .agents/skills/presentations/references .agents/skills/presentations/scripts .agents/skills/presentations/assets
    cp TALKS.md EXAMPLES.md WORKSHEET.md .agents/skills/presentations/references/
    cp templates/plan.md .agents/skills/presentations/assets/plan.md
    cp check_talk.py .agents/skills/presentations/scripts/

# Check the Python and the JSON for syntax
lint:
    {{python}} -m py_compile check_talk.py tests/*.py
    {{python}} -m json.tool skill-package.json > /dev/null

# Run the tests. Extra arguments go to unittest: just test tests.test_skill
test *args:
    {{python}} -m unittest discover -s tests -q "$@"

# Check the example deck with the talk checker, and the pages of the site with check.py of nossaifd
prose:
    #!/usr/bin/env bash
    set -euo pipefail
    {{python}} check_talk.py tests/fixtures/deck.md examples/cache/plan.md examples/cache/slides.qmd
    {{python}} -I {{check_py}} README.md TALKS.md EXAMPLES.md docs/check-talk.md docs/sources.md docs/why.md \
        docs/schwabish-summary.md .agents/skills/presentations/SKILL.md

# Note the patterns of model prose in the script of each deck, with the linter of Oskar Austegard's declaude
# skill, by GUIDE.md rules 50 to 54. Its notes are candidates for a person to judge, so they never fail.
declaude *decks:
    #!/usr/bin/env bash
    set -euo pipefail
    [ $# -gt 0 ] || set -- tests/fixtures/deck.md examples/cache/slides.qmd
    tool_root="$(mktemp -d)"
    trap 'rm -rf -- "$tool_root"' EXIT
    for deck in "$@"; do
        echo "$deck:"
        {{python}} check_talk.py --script "$deck" > "$tool_root/script.md"
        # The linter exits 1 for a note, so a crash shows only on stderr
        {{python}} -I {{declaude_lint}} --skip-quoted --no-html "$tool_root/script.md" 2> "$tool_root/err" || true
        if [ -s "$tool_root/err" ]; then cat "$tool_root/err" >&2; exit 1; fi
    done

# Build the site into _site with smalldocs
site:
    {{smalldocs}} render .

# Check the site with smalldocs: the options, the links and the Markdown
site-check:
    {{smalldocs}} check .

# Install the skills nossaifd and declaude again from the main branch of nossaifd, for the prose flow
nossaifd-install:
    npx -y skills add rahuldave/nossaifd -a codex --skill '*' -y

# List the changed pages that still need the steps of the nossaifd skill
prose-status:
    {{python}} -I .agents/skills/nossaifd/scripts/prose_gate.py status

# Check pages with the checker that .agents/nossaifd-checkers.json gives each one. A path is from the current folder
[no-cd]
prose-check +pages:
    {{python}} -I "{{justfile_directory()}}/.agents/skills/nossaifd/scripts/prose_gate.py" check -v "$@"

# Record each page after step 8 of the nossaifd skill: just prose-record page.md. A path is from the current folder
[no-cd]
prose-record +pages:
    {{python}} -I "{{justfile_directory()}}/.agents/skills/nossaifd/scripts/prose_gate.py" record "$@"

# Everything a commit must pass: the lint, the tests, the prose and the site
check:
    just lint
    just test
    just prose
    just declaude
    just site-check

# Check skill-package.json with skill-package-maker at a fixed commit
package-lint:
    #!/usr/bin/env bash
    set -euo pipefail
    tool_root="$(mktemp -d)"
    trap 'rm -rf -- "$tool_root"' EXIT
    git clone --quiet https://github.com/rahuldave/agent_skill_package_maker.git "$tool_root/package-maker"
    git -C "$tool_root/package-maker" checkout --quiet 6a5938c49ca71c374dc1a234a4d15134c484a741
    uv run --no-project python "$tool_root/package-maker/skills/skill-package-maker/scripts/lint_skill_bundle.py" .

# Check that each link to a skill of another package has a fallback, with the checker of a jnterfaces clone: just links ../jnterfaces
links jnterfaces="../jnterfaces":
    find .agents/skills/presentations -type f \( -name '*.md' -o -name '*.sh' -o -name '*.py' -o -name '*.yaml' \) -exec {{python}} "$1/scripts/check_skill_links.py" --package . --resolve "$1" {} +
