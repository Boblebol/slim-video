---
name: "boblebol:meta:project-showcase-nexus"
description: >-
  All-in-one showcase pipeline for a project or repo. Sequentially executes: (1) portfolio-cross-footer to inject
  Alexandre's unified footer into the project, (2) blog-post-architect to interview the dev and craft a Medium-style story
  (FR & EN), (3) lab-project-creator to add a Lab card in the portfolio, and (4) binds all 3 with cross-referencing bidirectional links.
---

# 🌐 Project Showcase Nexus (The Trifecta Orchestrator)

The ultimate all-in-one skill to transform any side project or web app into a fully showcased, interconnected portfolio asset.

---

## 🧭 The 4-Step Showcase Pipeline

```mermaid
graph TD
    Project[Source Project / Repo] --> S1[1. portfolio-cross-footer: Inject unified footer in the project]
    Project --> S2[2. blog-post-architect: Interview & write Medium story FR/EN]
    Project --> S3[3. lab-project-creator: Create Lab card in portfolio]
    S1 & S2 & S3 --> S4[4. Cross-Linking: Link Demo <-> Article <-> Lab Card <-> Footer]
```

---

## 🛠️ Step-by-Step Execution:

### 1. Unified Footer Injection (`portfolio-cross-footer`)
- Injects Alexandre's clean, responsive footer into the standalone project linking to `https://alexandre-enouf.fr/`, `#lab`, and blog.

### 2. Storytelling & Blog Creation (`blog-post-architect`)
- Runs the "Sam & Max / Vibe Coding" interview.
- Generates `data/blog/<project-slug>/content/fr.md`, `content/en.md`, `images/`, and `meta.yaml`.
- Associates `project: <project-slug>`.

### 3. Lab Card Registration (`lab-project-creator`)
- Generates `data/lab/<project-slug>/meta.yaml` with stack tags, demo link, repo link, and summary.

### 4. Bidirectional Interconnection
- In the Lab `meta.yaml`: sets `links.article: "blog/<project-slug>/index.html"`.
- In the Blog `meta.yaml`: sets `project: "<project-slug>"`.
- In the Blog markdown content: embeds live demo and GitHub repo links.
- Regenerates the full portfolio distribution (`python scripts/generate_all.py && make build`).
