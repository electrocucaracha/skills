<!-- Markdownlint-disable MD024 -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [5.3.1] - 2026-11-02

### Changed

- Standardized documentation formatting across several skills to improve consistency and readability, with updated indentation and rewritten headings to enhance clarity and uniformity. [30e102b3](https://github.com/electrocucaracha/skills/commit/30e102b304cf5a154784be08556bc1f2ba6d49a6)

## [5.3.0] - 2026-11-02

### Added

- Enabled users to efficiently and consistently resolve Super-Linter GitHub issues through the introduction of a standardized documentation process outlined in the SKILL.md file. [0f2d4c97](https://github.com/electrocucaracha/skills/commit/0f2d4c974202e243cbeeabb5abe46ae5fcb970e3)

## [5.2.0] - 2026-11-02

### Added

- Enabled explicit standard-library preflight checks for analyses and market data downloads, preventing silent or irrecoverable execution failures and improving deployment reliability and operator guidance. [e2d30935](https://github.com/electrocucaracha/skills/commit/e2d309351ced690d67b37fa88d2eba23bc3804b5)

## [5.1.1] - 2026-11-02

### Changed

- Clarified and streamlined documentation for k8s-es-translation-audit, repair-knowledge-base, and technical-writer skills, enabling future maintainers to quickly understand usage context, expected inputs, and validation procedures. [e61e9a63](https://github.com/electrocucaracha/skills/commit/e61e9a63e54bf11b79d8eb133963a8821557c2aa)

## [5.1.0] - 2026-11-01

### Added

- Introduced a research-only stock-exit-review skill with technical analysis workflow, enabling reproducible structured decision-making with Jev API support and immutable forecast evaluation, while maintaining compatibility with Hermes scheduling and avoiding automated trading or portfolio effects. [3d6f3e31](https://github.com/electrocucaracha/skills/commit/3d6f3e31763c858bc1440fc6e8fc897eabc52e87)

## [5.0.0] - 2026-11-01

### Removed

- Discontinued automated validation and reporting for Spanish doc contributions as the k8s-es-translation-review directory and its custom scripts have been removed from the repository. [6779aef3](https://github.com/electrocucaracha/skills/commit/6779aef317ce9051ec9da01be18172843e31357a)

## [4.6.2] - 2026-11-01

### Changed

- Updated markdownlint-cli and ai-prepare-commit-msg pre-commit hooks to their latest versions, ensuring access to new features and fixes. [cbfa7608](https://github.com/electrocucaracha/skills/commit/cbfa7608749816606145c113006044b3a039d578)

## [4.6.1] - 2026-11-01

### Changed

- Standardized documentation terminology and style to ensure editorial coherence and unambiguous content review and navigation. [4dba5daa](https://github.com/electrocucaracha/skills/commit/4dba5daa5b498b6a12672467850c7d1e02bed9e2)

## [4.6.0] - 2026-09-12

### Added

- Enabled project transparency and upgrade planning by introducing a detailed CHANGELOG.md file following Keep a Changelog and Semantic Versioning guidelines. [7a2b7bf4](https://github.com/electrocucaracha/skills/commit/7a2b7bf44cb1b5cbf114bb26d466efeca6d5d903)

## [4.5.0] - 2026-09-12

### Added

- Enabled support for multiple H1 headings in Markdown files, allowing authors to write self-contained documents with one clause per line. [b750a796](https://github.com/electrocucaracha/skills/commit/b750a79681b706c0e923ab312878666522e43545)

## [4.4.0] - 2026-09-12

### Added

- Introduced a Meeting Expert agent that analyzes meeting transcripts and provides actionable evidence-based recommendations for improving meeting facilitation, participation, and agenda discipline, with the added feature of flagging meetings that should be async. [ebc94e1e](https://github.com/electrocucaracha/skills/commit/ebc94e1e28d971bc4fcae93ab45b737018df8338)

## [4.3.0] - 2026-09-12

### Added

- BREAKING: Enabled more accurate Spanish translation reviews by introducing a diff-based findings filter that suppresses unchanged-line findings and duplicates from existing PR comments, and improves detection of reordered or missing content across a wider set of section sizes. [eec3f312](https://github.com/electrocucaracha/skills/commit/eec3f3120a7dcbe2fa84b619d0daf697acbac836)

## [4.2.1] - 2026-09-12

### Changed

- Optimized the ai-prepare-commit-msg hook to v15.4.2, providing improved compatibility and access to the latest features with no breaking behavior or migration requirements. [0b31a168](https://github.com/electrocucaracha/skills/commit/0b31a1681e83713c27cc32b221b20b3018a7881c)

## [4.2.0] - 2026-09-04

### Added

- Automated code and documentation formatting have been enabled across the project, allowing users to maintain consistent formatting through the 'fmt' target without introducing any breaking behavior or API changes. [af500d01](https://github.com/electrocucaracha/skills/commit/af500d01144bd0b4e8bf1e415f668d5f0e74ecf8)

## [4.1.0] - 2026-09-04

### Added

- Enforced code quality standards to improve consistency and adherence to best practices by integrating checks for trailing whitespace, YAML syntax, shell script conventions, and Markdown formatting, and enabling AI-based commit message preparation. [6a72939d](https://github.com/electrocucaracha/skills/commit/6a72939da6373309d6fe8413721084baecede952)

## [4.0.0] - 2026-09-04

### Removed

- Simplified the repository by eliminating the internal documentation for the minutes-transcriber skill, including the SKILL.md file and the minutes protocol template, which are no longer needed for downstream automation and do not affect functional application code. [f268d2e0](https://github.com/electrocucaracha/skills/commit/f268d2e0219b809c0b3fe5683e3327ee6abad6a5)

## [3.2.0] - 2026-08-16

### Added

- BREAKING: Enabled exclusive management of repair knowledge via a structured CLI and schema, replacing ad hoc repair notes and providing actionable guidance for new failures through outcome tracking. [7c89f1da](https://github.com/electrocucaracha/skills/commit/7c89f1da1e60e34ec660ded5209b39471f36c2dc)

## [3.1.0] - 2026-08-05

### Added

- Enabled spell checking for unknown Spanish words in prose lines, excluding domain terms, code, and allowlisted tokens, with centralized dictionary data and terminology rules in a shared JSON file. [8206a73c](https://github.com/electrocucaracha/skills/commit/8206a73c275edd3357571ee95777a8cc71f3cca4)

## [3.0.0] - 2026-08-05

### Removed

- Simplified table formatting to reduce unnecessary whitespace, removing redundant empty lines before and after code blocks and headings without altering content or meaning. [694834e8](https://github.com/electrocucaracha/skills/commit/694834e8a3ddde79351e28e1717b8101a4d18e64)

## [2.3.0] - 2026-08-03

### Added

- Standardized documentation guidelines have been introduced to ensure skills are reliable, maintainable, and discoverable, and provide clear guidance for contributors and support automated validation. [a44b249a](https://github.com/electrocucaracha/skills/commit/a44b249aa4838e350cd7f5c19b707d78aa68c47d)

## [2.2.0] - 2026-08-03

### Added

- BREAKING: Enabled consistent, high-signal reviews for Spanish localization PRs by introducing a new review workflow that clones the repository, fetches the PR, and runs four deterministic checks, and generates a Markdown report with actionable comments in Spanish, with a follow-up mode verifying whether previous review suggestions were addressed, and requiring reviewers to use this tool for all future Spanish localization PRs. [a7e83f4b](https://github.com/electrocucaracha/skills/commit/a7e83f4b8c13ef51f78f64c3090e1cea9695d1a6)

## [2.1.0] - 2026-07-29

### Added

- BREAKING: Introduces a reproducible audit workflow for Kubernetes Spanish documentation, enabling maintainers to systematically identify and prioritize translation gaps, stale content, and style inconsistencies, accelerating Spanish docs coverage and quality. [9638efc1](https://github.com/electrocucaracha/skills/commit/9638efc10a2e3c5f4ce624f98379b52ee37e16c7)

## [2.0.1] - 2026-07-21

### Changed

- Clarified meeting minutes as work-log concept documents, requiring OKF-style YAML frontmatter and strict filename conventions, to ensure machine-friendly and consistent output for downstream workflows. [443f51c9](https://github.com/electrocucaracha/skills/commit/443f51c90a3242bce42a773343e81a15ff46141c)

## [2.0.0] - 2026-05-21

### Removed

- Migrated weekly-summary and wrap-up skills, requiring users to regenerate these summaries and wrap-ups according to new requirements. [21add099](https://github.com/electrocucaracha/skills/commit/21add099898c8c4d892aa47760dbcbe7f818c0fb)

## [1.0.0] - 2026-05-16

### Added

- Enabled developers to extend AI coding agents with focused, domain-specific behavior through the introduction of reusable skill packages. [b4844ba7](https://github.com/electrocucaracha/skills/commit/b4844ba71624e796dde171bbceb3a514ff24d0e5)
