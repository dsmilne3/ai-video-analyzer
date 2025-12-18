# Contributing to AI Video Analyzer

Thanks for your interest in contributing! This guide outlines how to set up your environment, run tests, propose changes, and open pull requests so we can keep the project healthy and easy to collaborate on.

## Ways to Contribute
- Bug reports and reproduction steps
- Feature proposals with clear user value
- Documentation improvements (README, docs/*)
- Tests (unit, integration, E2E, Docker smoke)
- Small, focused code changes that improve quality and stability

## Development Environment

- See the Quickstart document for prerequisites and setup procedures

API keys are required for full qualitative evaluation. See docs for details:
- docs/API_KEYS.md
- docs/TESTING.md

### Running Tests
- Full test suite:
```bash
./run.sh test
```

- Pytest quick/verbose:
```bash
venv/bin/python -m pytest -q
venv/bin/python -m pytest -v
```

- E2E browser tests (requires Playwright; see docs/TESTING.md):
```bash
venv/bin/python -m pytest -m e2e tests/e2e -v
```

- Docker smoke tests (requires Docker daemon):
```bash
venv/bin/python -m pytest -m docker tests/integration/test_docker_smoke.py -v
```

Notes:
- A session-scoped cleanup fixture removes test artifacts in `results/` after the test session.
- If you add new tests that persist files, ensure they either clean up or integrate with the shared cleanup patterns.

## Coding Guidelines
- Python 3.9+ with type hints where practical.
- Keep functions small and cohesive; favor readability over cleverness.
- Follow existing project structure (see `src/`, `pages/`, `tests/`).
- Update or add tests alongside code changes.
- Document user-facing behavior in `docs/` when it changes.

## Commit Style
Use Conventional Commits to keep history readable and automate changelog generation later:
- `feat:` new user-facing features
- `fix:` bug fixes
- `docs:` documentation only changes
- `test:` add/adjust tests
- `refactor:` code changes that neither fix a bug nor add a feature
- `chore:` maintenance tasks (deps, tooling, CI), no production code changes

Examples:
- `feat: add rubric import validation`
- `fix: handle missing ffmpeg error gracefully`
- `docs: add Docker smoke test instructions`

## Branching and PRs
- Create feature branches from `main` (e.g., `feat/rubric-editor`).
- Keep PRs focused and reviewable (aim < 300 lines changed when possible).
- Reference related issues and include a brief description of intent.
- Prefer squash merge to keep history linear.

### PR Checklist
- [ ] Tests pass locally (`./run.sh test`)
- [ ] New/updated tests cover the change
- [ ] Docs updated if behavior or usage changed
- [ ] No unintended artifacts left in `results/` or `rubrics\`
- [ ] Commit messages follow Conventional Commits

## Dependencies
- Minimize new dependencies. If you must add one, explain why in the PR.
- Pin versions in `requirements.txt` and verify `./run.sh check` still passes.

## Security
Please avoid filing public issues for security vulnerabilities. Instead, open a private security advisory on GitHub (Security tab) or contact the maintainer privately. Provide clear reproduction steps and affected versions.

## License
By contributing, you agree that your contributions will be licensed under the MIT License (see `LICENSE`).
