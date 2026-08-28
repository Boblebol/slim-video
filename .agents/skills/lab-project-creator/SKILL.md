---
name: "boblebol:story:lab-project-creator"
description: >-
  Creates and registers a new Lab project entry in Alexandre Enouf's portfolio (portfolio-content).
  Scans project repository or metadata to automatically configure data/lab/<project-slug>/meta.yaml
  with bilingual titles, summaries, tags, stack definitions, and live links (demo, repo, article).
---

# ⚡ Lab Project Creator Skill

Creates and configures a clean, structured Lab project card in Alexandre's portfolio content repository.

---

## ⚙️ Generation Workflow

When creating an entry for a new project in `data/lab/<project-slug>/meta.yaml`:

```yaml
id: my-project-slug
type: project
status: published
has_page: false
show_in_lab: true
featured: true

title:
  fr: "Nom du Projet"
  en: "Project Name"

subtitle:
  fr: "Sous-titre percutant décrivant la proposition de valeur en 1 phrase"
  en: "Punchy subtitle describing the core value proposition in 1 sentence"

summary:
  fr: "Description claire du problème résolu, du besoin personnel et de la solution technique apportée."
  en: "Clear description of the problem solved, personal context, and technical implementation."

start_date: "YYYY-MM-DD"
published_date: "YYYY-MM-DD"

tags: [tag1, tag2, tag3]

links:
  demo: "https://my-project.alexandre-enouf.fr/"
  repo: "https://github.com/Boblebol/my-project"
  article: "" # Will be populated if a blog post exists
  other: []

stack:
  - Language / Framework (e.g. Python, React, TypeScript)
  - Key Tools / Libs (e.g. FastAPI, Tailwind CSS, Chrome Extension)
```

---

## 🧪 Validation Checklist
- [ ] Folder created at `data/lab/<project-slug>/`
- [ ] File `meta.yaml` validated against schema
- [ ] Regenerate portfolio static HTML via `python scripts/generate_all.py && make build`
