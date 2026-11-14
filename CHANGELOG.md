<!-- Markdownlint-disable MD024 -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [6.0.0] - 2026-11-14

### Removed

- Simplified argument lists in analyze.py, capture.py, and check_workflow.py scripts by consolidating multiline options into single lines, improving readability and consistency without introducing functional changes. [a1ae149c](https://github.com/electrocucaracha/skills/commit/a1ae149caf7212aeede2217f1021085318cc834b)

## [5.12.5] - 2026-11-14

### Changed

- Clarified Super-Linter issue handling and linter fix guidance to improve developer experience with enhanced reporting, stricter commit selection, and streamlined workflows. [1a45aec3](https://github.com/electrocucaracha/skills/commit/1a45aec3e8fb22addb2fc65ba61d46dcf9c60fc8)

## [5.12.4] - 2026-11-14

### Changed

- Clarified code intent and behavior across Python scripts, enabling future contributors to better understand and maintain the codebase. [bec9e0c8](https://github.com/electrocucaracha/skills/commit/bec9e0c8ed98c829abd5314db3f381c8375fe015)

## [5.12.3] - 2026-11-14

### Changed

- Unified the Python formatting workflow by replacing Black with Ruff for style checking and formatting, reducing tooling dependencies and aligning with other Ruff-based lint steps. [b26c7df7](https://github.com/electrocucaracha/skills/commit/b26c7df7806316d5358dc7e09b9df505175ab600)

## [5.12.2] - 2026-11-14

### Changed

- Clarified guidance for selecting and reconciling formatters across project and CI configurations, ensuring that the CI formatter is treated as the authoritative source, and refined verification steps to improve fix stability and prevent over-expansion of fixes to unrelated issues. [549f02d2](https://github.com/electrocucaracha/skills/commit/549f02d26f675f40e598676a891312f08ccdb499)

## [5.12.1] - 2026-11-14

### Changed

- Unified the identity helper function definition, removing the duplicate implementation in history.py and importing it from capture.py, with no behavioral changes introduced. [d9106f98](https://github.com/electrocucaracha/skills/commit/d9106f982c21624f8b89cd2d1053e0df6311687f)

## [5.12.0] - 2026-11-14

### Added

- Enabled durable capture records and reconciliation with OpenViking, ensuring every decision is reliably stored and verifiable, and requiring capture before mirroring to maintain accurate audit trails. [cef841a3](https://github.com/electrocucaracha/skills/commit/cef841a3cbf992c6a90b32e2d49618e17a2b2b7e)

## [5.11.0] - 2026-11-11

### Added

- Enabled automated assessment of skill correctness, automated review requests for code changes, and simplified GitHub Actions workflow, while updating plugin and workflow versions to ensure consistency with recent improvements and fixes from dependencies, and introducing codebase consistency enhancements through editor and linter configuration files, refined markdownlint settings, and updated Python script docstrings and documentation. [dbb5ccf5](https://github.com/electrocucaracha/skills/commit/dbb5ccf5256aa5259c1a2af06aeaa6427ea8e427)

## [5.10.2] - 2026-11-11

### Changed

- Updated plugin and workflow versions to ensure consistency with recent improvements and fixes from dependencies, bumping the technical-writer and fix-gh-lint-issue plugins to 5.10.1 and the pre-commit hook ai-prepare-commit-msg to v20.14.1, and updating workflow references in linter.yml and update.yml to use electrocucaracha/gh-workflows v13.3.1. [62b8911e](https://github.com/electrocucaracha/skills/commit/62b8911e2965350d745bcc3ca55ef5ec67524cdb)

## [5.10.1] - 2026-11-11

### Changed

- Enabled automated assessment of skill correctness and adherence to process requirements through the introduction of evaluation specifications for fixing GitHub linting issues, repairing knowledge bases, stock exit reviews, and technical writing. [9c164541](https://github.com/electrocucaracha/skills/commit/9c1645412f16c74205abea6ef19db7995e63cbc1)

## [5.10.0] - 2026-11-06

### Added

- Enabled automatic review requests for code changes by introducing a CODEOWNERS file that designates @electrocucaracha as the default code owner for all files in the repository. [79ba745d](https://github.com/electrocucaracha/skills/commit/79ba745d1094bb970fdbf520c7b382cc423def5f)

## [5.9.3] - 2026-11-06

### Changed

- Simplified the GitHub Actions workflow to use correct YAML syntax and permissions, resolving issues with YAML linting and improving workflow maintainability. [df5e1f98](https://github.com/electrocucaracha/skills/commit/df5e1f98360167fde30386a08695d48a2a520d3c)

## [5.9.2] - 2026-11-05

### Changed

- Normalized Pylint and script lint flow with Super-Linter config, enabling improved linting consistency across runtime and CI environments. [5c504d63](https://github.com/electrocucaracha/skills/commit/5c504d63ca1d4c0ba0c942d9df23e7f97b71afb9)

## [5.9.1] - 2026-11-05

### Changed

- Enabled consistent formatting and static analysis across the codebase through the introduction of editor and linter configuration files, refined markdownlint settings, and updated Python script docstrings and documentation. [53094d5a](https://github.com/electrocucaracha/skills/commit/53094d5a88198ca3059d70f43a9fa82fd539f94c)

## [5.9.0] - 2026-11-04

### Added

- Detailed entries were introduced for versions 5.4.0 through 5.8.1, documenting new features, plugin metadata improvements, automation enhancements, and notable bugfixes, providing clearer project history and ensuring transparency for recent changes. [6ff1b864](https://github.com/electrocucaracha/skills/commit/6ff1b8647f58434f55c3a6792e37a08a76ff6a3c)

## [5.8.1] - 2026-11-04

### Changed

- Updated plugin versions and CI workflows to reference the latest releases, ensuring the repository and CI/CD integration remains current. [d43ed9a4](https://github.com/electrocucaracha/skills/commit/d43ed9a43d4df930c9505e886a63d217c1435e6f)

## [5.8.0] - 2026-11-04

### Added

- Introduced a marketplace.json manifest specifying plugin metadata and available plugins for reusable documentation and engineering skills, enabling discovery and integration with plugin management tools. [a8e166ba](https://github.com/electrocucaracha/skills/commit/a8e166ba393034be7f0d3d2d9170713d690470b6)

## [5.7.0] - 2026-11-04

### Added

- Enabled repository CI automation with reusable workflow callers that trigger linter validation on push and pull requests, and schedule dependency updates with PR automation, while requiring configuration of WORKFLOW_TOKEN and COPILOT_TOKEN secrets. [822452e6](https://github.com/electrocucaracha/skills/commit/822452e6169539bc7a63f6721f88dd5012b885ba)

## [5.6.0] - 2026-11-04

### Added

- Automated dependency and version updates are now enabled, improving maintainability by keeping dependencies and plugin metadata up to date with minimal manual intervention. [5808ce35](https://github.com/electrocucaracha/skills/commit/5808ce351289ccdc85b7c11fe248e07be3313797)

## [5.5.3] - 2026-11-04

### Changed

- Stabilized code block formatting and presentation consistency across technical writing guides, ensuring proper rendering and editing of tables and command-line examples. [e7a005d8](https://github.com/electrocucaracha/skills/commit/e7a005d88ad09fc801ea7a3105fdcbdaea19ae59)

## [5.5.2] - 2026-11-04

### Changed

- Normalized the fmt target to respect .gitignore exclusions and apply consistent formatting and style checks across supported file types. [f79fef94](https://github.com/electrocucaracha/skills/commit/f79fef9433411cbacf26442b22f1a7f8f53681ae)

## [5.5.1] - 2026-11-04

### Fixed

- Resolved the issue of false positives in documents with reused subheadings by limiting MD024 to check for duplicate header names among siblings. [d6e12e41](https://github.com/electrocucaracha/skills/commit/d6e12e41fe4685528253a16f175fcd5260d72dc1)

## [5.5.0] - 2026-11-04

### Added

- Enabled plugin metadata visibility by introducing plugin.json manifests for fix-gh-lint-issue and technical-writer plugins, providing essential information for integration and discovery within the project. [5130de9f](https://github.com/electrocucaracha/skills/commit/5130de9fd6bd6b68f9d5daad38969e3f0ce6d108)

## [5.4.0] - 2026-11-02

### Added

- Enabled project transparency by documenting new features, documentation improvements, standardization efforts, and removals in the CHANGELOG.md file for releases 4.6.0 through 5.3.1. [927cd107](https://github.com/electrocucaracha/skills/commit/927cd1077bf1ae69b2f849f716d0fabc657e48ec)

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

- BREAKING: Enabled consistent, high-signal reviews for Spanish localization PRs
  by introducing a new review workflow that clones the repository,
  fetches the PR, and runs four deterministic checks,
  and generates a Markdown report with actionable comments in Spanish,
  with a follow-up mode verifying whether previous review suggestions were addressed,
  and requiring reviewers to use this tool for all future Spanish localization PRs.
  [a7e83f4b](https://github.com/electrocucaracha/skills/commit/a7e83f4b8c13ef51f78f64c3090e1cea9695d1a6)

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
