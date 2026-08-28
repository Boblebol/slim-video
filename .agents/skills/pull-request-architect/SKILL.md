---
name: "boblebol:git:pull-request-architect"
description: >-
  Creates structured, world-class GitHub/GitLab Pull Requests with visual Mermaid diagrams, structured context,
  categorized changes, and testing checklists. Use this skill when opening PRs or creating PR templates.
---

# 🏗️ Pull Request Architect Skill

Generates crystal-clear, structured Pull Requests featuring architecture diagrams and comprehensive review contexts.

---

## 🎯 PR Generation Blueprint

When opening a Pull Request via GitHub CLI (`gh pr create`) or preparing a description:

```markdown
## 🎯 Purpose & Context
[Concise executive summary of what problem this PR solves or feature it introduces]

## 🏗️ Architecture & Data Flow (Mermaid Diagram)
```mermaid
graph TD
    A[Input / Trigger] --> B[Processing / Validation Layer]
    B --> C[Output / Mutation / Store]
```

## 📦 Key Changes by Scope
- **`scope/component`**: Detailed rationale and key decisions.
- **`scope/tooling`**: Configuration updates.
- **`tests/`**: Test coverage additions.

## 🧪 Validation & Quality Gates
- [x] Unit tests passing (`make test` / `npm test` / `pytest`)
- [x] CI pipeline / Linters passing (`make check` / `make ci`)
- [x] Manual testing performed
```
