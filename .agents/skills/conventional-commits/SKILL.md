---
name: "boblebol:git:conventional-commits"
description: >-
  Expert Git commit organizer and linter. Use this skill when finishing a branch, preparing commits for review,
  or reorganizing unstaged/dirty working tree changes into atomic, granular, strict Conventional Commits (feat, fix,
  perf, refactor, build, ci, docs, test, chore) with clear scopes and rationale.
---

# 🔀 Conventional Commits Master Skill

Organizes, groups, and commits file changes following the strict **Conventional Commits v1.0.0** specification.

---

## 🎯 Workflow Execution

When this skill is invoked:

1. **Analyze Working Tree & Diff**:
   - Inspect `git status -s` and `git diff`.
   - Identify distinct logical units of work (do NOT create single monolithic commits mixing refactoring, features, tests and builds).

2. **Categorize Changes by Semantic Type**:
   - `feat(<scope>)`: New feature or user-facing capability.
   - `fix(<scope>)`: Bug fix or unintended regression resolution.
   - `perf(<scope>)`: Performance optimization (Lighthouse, query reduction, bundle size).
   - `refactor(<scope>)`: Code restructuring without behavior/feature changes.
   - `build(<scope>)`: Build tooling, bundlers (esbuild, webpack, vite), dependencies (`uv.lock`, `package.json`, `Makefile`).
   - `ci(<scope>)`: CI workflows, GitHub Actions, automated test pipelines.
   - `docs(<scope>)`: Documentation updates (README, CHANGELOG, inline docs).
   - `test(<scope>)`: Adding new tests or updating existing test suites.
   - `chore(<scope>)`: Repository housekeeping, linting configs, gitignore.

3. **Synchronize CHANGELOG.md (Keep a Changelog standard)**:
   - If a `CHANGELOG.md` exists in the repository root:
     - Automatically document newly added features under `### Added` or `## [Unreleased]`.
     - Document bug fixes under `### Fixed`, performance improvements under `### Changed` / `### Performance`.
     - Document breaking changes under `### Changed` or `### Removed`.

4. **Stage & Commit Granularly**:
   - Stage exact files corresponding to each semantic group (`git add <files>`).
   - If `CHANGELOG.md` was updated, include it in the relevant commit or commit it under `docs(changelog): ...`.
   - Write imperative, lowercase commit headers: `<type>(<scope>): <action in imperative mood>`.
   - Include body bullet points for non-trivial context.

5. **Verify Clean Tree**:
   - Ensure `git status` is completely clean after committing all planned groups.

