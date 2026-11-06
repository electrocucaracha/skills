# Agent Skills

This repository contains reusable skill packages that extend AI coding agents with focused, domain-specific behavior.

## Purpose

The purpose of this repository is to centralize skill definitions so teams can:

- Standardize how agents handle recurring workflows.
- Capture proven guidance in reusable, versioned artifacts.
- Reduce repeated prompting by turning best practices into structured skills.

## Why It Matters

Well-designed skills improve quality and consistency across sessions.
They help agents produce better outputs by providing:

- Clear scope: what a skill should and should not be used for.
- Reliable workflows: repeatable steps for complex tasks.
- Shared context: team knowledge that can be reused over time.

In practice, this leads to faster delivery, fewer avoidable mistakes, and more predictable results.

## Local Checks

Run `make fmt` to format the repository,
then `make lint-python` to run Pylint with the Super-Linter configuration.
The [CI config](.python-lint) is a symlink to the [local config](.pylintrc),
so both use the same rules.

Scripts declare runtime dependencies in PEP 723 metadata for `uv run --script`.
Super-Linter does not install those dependencies.
Its Pylint configuration exempts only the declared external packages from import checks;
Click entry points and Pydantic data models have targeted inference exemptions.
These checks do not replace running scripts with their declared dependencies installed.
