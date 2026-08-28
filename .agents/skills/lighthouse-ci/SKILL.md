---
name: "boblebol:web:lighthouse-ci"
description: >-
  Configures, executes, and fixes Lighthouse CI automated audits (Performance, SEO, Accessibility, Best Practices)
  with strict budget thresholds (>=90/95) across Mobile and Desktop in local runs and GitHub Actions CI pipelines.
---

# 🚦 Lighthouse CI Master Skill

Automates Core Web Vitals and quality audits in local environments and CI pipelines, with **automated rich Markdown reporting posted directly as PR comments**.

---

## 🛠️ Configuration Standards

### 1. Budgets & Configurations (`.lighthouserc.mobile.json` & `.lighthouserc.desktop.json`)
- **Performance**: >= 0.90 (Mobile & Desktop)
- **Accessibility**: >= 0.95
- **Best Practices**: >= 0.95
- **SEO**: >= 0.95
- Configure assertions to fail PRs on regressions.

---

## 💬 Automated PR Commenting Workflow (GitHub Actions)

Every Pull Request must receive an automated, beautiful Markdown report with scores, badges, and median report links:

```yaml
      - name: Run Lighthouse CI Audit (${{ matrix.device }})
        id: lhci
        uses: treosh/lighthouse-ci-action@v12
        with:
          configPath: "./.lighthouserc.${{ matrix.device }}.json"
          uploadHandler: "temporary-public-storage"
          temporaryPublicStorage: true

      - name: Generate Visual Summary
        if: always()
        run: |
          python scripts/lighthouse_summary.py .lighthouseci --device ${{ matrix.device }} --output lighthouse_summary_${{ matrix.device }}.md
          cat lighthouse_summary_${{ matrix.device }}.md >> $GITHUB_STEP_SUMMARY

      - name: Post or Update PR Comment (${{ matrix.device }})
        if: always() && github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          script: |
            const fs = require('fs');
            const summaryFile = 'lighthouse_summary_${{ matrix.device }}.md';
            if (!fs.existsSync(summaryFile)) return;
            const body = fs.readFileSync(summaryFile, 'utf8');
            const commentHeader = '<!-- lighthouse-ci-comment-${{ matrix.device }} -->';
            const commentBody = `${commentHeader}\n${body}`;

            const { data: comments } = await github.rest.issues.listComments({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
            });

            const botComment = comments.find(c => c.body && c.body.includes(commentHeader));

            if (botComment) {
              await github.rest.issues.updateComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                comment_id: botComment.id,
                body: commentBody,
              });
            } else {
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.issue.number,
                body: commentBody,
              });
            }
```

### 2. Summary Helper Script (`scripts/lighthouse_summary.py`)
Generates a markdown table displaying:
- Audited URL
- Device badge (📱 Mobile / 🖥️ Desktop)
- Performance, Accessibility, Best Practices, SEO scores (with 🟢 / 🟡 / 🔴 color indicators)
- Direct clickable link to the full Lighthouse report

