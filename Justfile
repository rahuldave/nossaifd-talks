# nossaifd-talks: every task is a recipe here. `just` lists them.

# Each word after a recipe's name reaches its commands whole, as "$1", "$2" and so on; "$@" is all of them
set positional-arguments

# Python comes from uv, so the machine needs just and uv only
python := "uv run --no-project --quiet python"
smalldocs := "uvx --from smalldocs==0.5.5 smalldocs"

# The checker for reports, check.py of nossaifd, at a fixed commit of its main branch. Move it when
# check.py changes there.
nossaifd_commit := "ec80717f074c68dfa5fecb0c8c19ba49398a2f76"

[private]
default:
    @just --list --unsorted

# Copy the guide, the examples and the checker into the skill, which ships copies of them
sync:
    mkdir -p .agents/skills/presentations/references .agents/skills/presentations/scripts
    cp TALKS.md EXAMPLES.md .agents/skills/presentations/references/
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
    {{python}} check_talk.py tests/fixtures/deck.md
    tool_root="$(mktemp -d)"
    trap 'rm -rf -- "$tool_root"' EXIT
    curl -fsSL "https://raw.githubusercontent.com/rahuldave/nossaifd/{{nossaifd_commit}}/check.py" -o "$tool_root/check.py"
    {{python}} -I "$tool_root/check.py" README.md TALKS.md EXAMPLES.md docs/check-talk.md docs/sources.md docs/why.md \
        .agents/skills/presentations/SKILL.md

# Build the site into _site with smalldocs
site:
    {{smalldocs}} render .

# Check the site with smalldocs: the options, the links and the Markdown
site-check:
    {{smalldocs}} check .

# Everything a commit must pass: the lint, the tests, the prose and the site
check:
    just lint
    just test
    just prose
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
    find .agents/skills -type f \( -name '*.md' -o -name '*.sh' -o -name '*.py' -o -name '*.yaml' \) -exec {{python}} "$1/scripts/check_skill_links.py" --package . --resolve "$1" {} +
