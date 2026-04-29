# Python Calculator — Git & CI/CD Implementation
github link where this activity is done: https://github.com/AshwinaSedhain/git_implementation
## Project Overview

This project was built as a practical demonstration of Git version control, GitHub collaboration, Python testing with pytest, and CI/CD pipeline automation.

A simple Python calculator library was chosen as the base application because it is straightforward enough to understand quickly, yet complex enough to demonstrate all required concepts in a meaningful way.

The calculator supports eight operations: addition, subtraction, multiplication, division, power, modulo, square root, and absolute value.

---

## Repository Structure

The repository is organized into three main areas:

- The "calculator" folder contains the source code where all mathematical operations are defined.
- The "tests" folder contains both unit tests and integration tests written using pytest.
- The "github"folder contains the CI/CD pipeline configuration that runs automatically on GitHub whenever code is pushed.

---

## Git Initialization and Commit History

The repository was initialized using "git init", and a ".gitignore" file was created to ensure that unnecessary files such as "__pycache__", ".pytest_cache", virtual environments, and log files were never tracked by Git.

Over the course of the project, more than fifteen meaningful commits were made, each following a conventional commit message format.

Commit messages were prefixed with labels such as:
- `feat:` for new features  
- `fix:` for bug fixes  
- `test:` for test additions  
- `ci:` for pipeline changes  
- `docs:` for documentation updates  
- `refactor:` for code improvements  

This approach ensures the commit history is readable and professional, allowing reviewers to understand what changed and why.

---

## Branch Strategy

Three types of branches were used in this project:

- `main`: stable, production-ready branch  
- `develop`: integration branch for completed features  
- `feature`: individual feature branches  

Feature branches included:
- `feature/power-modulo`
- `feature/sqrt-abs`

Each feature branch was merged into `develop`, and once stable, `develop` was merged into `main`. All feature branches were deleted after merging to keep the repository clean.

---

## Merge Types

Two types of merges were demonstrated:

### Fast-forward merge
A fast-forward merge occurred when `feature/power-modulo` was merged into `develop`. Since no new commits existed on `develop`, Git simply moved the pointer forward without creating a merge commit, resulting in a linear history.

### Non-fast-forward merge
A non-fast-forward merge was performed using the `--no-ff` flag when merging `feature/sqrt-abs` into `develop`, and later when merging `develop` into `main`.

This ensures that a merge commit is always created, preserving branch history and making feature development visible in the commit graph.

---

## Merge Conflict

A merge conflict was intentionally created using `feature/conflict-demo` and `develop`, where the same file had different changes.

Git was unable to automatically resolve the conflict, so it was manually fixed by editing the file and keeping the correct final version.

The resolution was committed as:
`fix: resolve merge conflict in conflict_demo.py manually`

---

## Tagging and Versioning

Two annotated tags were created:

| Tag  | Description |
|------|------------|
| v1.0 | Core calculator operations with unit tests and CI setup |
| v2.0 | Full feature set with integration tests, QA, and conflict resolution |

Both tags were pushed to GitHub and are visible under Releases and Tags.

---

## Unit Testing

Unit tests were written using pytest and are located in `tests/test_unit.py`.

A total of 30 unit tests were implemented covering:

- Normal cases (e.g., `add(2, 3) = 5`)
- Edge cases (zero, negative values)
- Failure cases (e.g., division by zero raises error)

This ensures each function behaves correctly across all scenarios.

---

## Integration Testing

Integration tests in `tests/test_integration.py` verify that multiple functions work together.

For example:
- `divide(subtract(100, 20), 4)` returns `20.0`
- Multi-step chained operations simulate real-world usage

These tests ensure correct interaction between components.

---

## Quality Assurance

Quality assurance was demonstrated in two ways:

### 1. Bug Introduction & Fix
A bug was intentionally introduced where the divide function returned multiplication instead of division. It was then fixed, demonstrating the full QA cycle:
- bug introduced
- failure detected
- fix applied

### 2. Code Quality Checks
`flake8` was used to detect style issues such as:
- unused imports
- long lines
- missing spacing

All issues were fixed, resulting in a clean codebase.

---

## CI/CD Pipeline

A CI/CD pipeline was configured using GitHub Actions in `.github/workflows/ci.yml`.

It runs automatically on:
- push to `main`, `develop`, or `feature/*`
- pull requests

### Pipeline Jobs:

1. **Quality Check**
   - Runs `flake8` to ensure code quality

2. **Testing**
   - Runs unit and integration tests using pytest
   - Generates coverage report using pytest-cov

This ensures only tested and clean code is merged.

---

## How to Run the Project

Install dependencies:
pip install pytest pytest-cov flake8

Run tests:
pytest -v

Run coverage:
pytest --cov=calculator --cov-report=term-missing

Run linting:
flake8 calculator/ tests/